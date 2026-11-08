"""统一单题/批量入口；父进程逐题隔离，900秒超时可终止整个工具进程树。"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.src.parse import parse_task
from agent.src.task_card import make_skeleton, build_context
from agent.src.generate import Provider, extract_st, generation_messages
from agent.src.tools import Toolchain, run_process
from agent.src.repair import feedback, apply_patch, diff, regresses
from agent.src.terminate import StopRun, rank, success, classify, check_limits
from agent.src.logging import write_json, event, now, save_result

def load_config(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    try:
        return json.loads(text)
    except ValueError:
        try:
            import yaml
        except ImportError:
            raise ValueError('本配置不是JSON子集；普通YAML配置须先安装PyYAML') from None
        return yaml.safe_load(text)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def evaluate(tc, source, directory, tag, repairs=0, token_count=0):
    compilation = tc.compile(source, tag)
    tests = tc.test(source, tag) if compilation['status'] == 'pass' else {
        'status':'skipped', 'total':0, 'passed':0, 'passed_ids':[], 'failures':[]}
    result = {'source':source, 'compile':compilation, 'test':tests,
              'repair_rounds':repairs, 'token_count':token_count, 'tag':tag}
    write_json(Path(directory) / (tag + '.evaluation.json'), result)
    event(directory, 'evaluation', tag=tag, compile_status=compilation['status'],
          test_status=tests['status'], test_passed=tests.get('passed',0),
          test_total=tests.get('total',0))
    return result

def worker(job):
    directory = Path(job['directory'])
    config = job['config']
    started = time.monotonic()
    deadline = started + config['task_timeout_s']
    card = parse_task(job['task'], root=ROOT)
    write_json(directory / 'task_card.json', card)
    skeleton = make_skeleton(card)
    (directory / 'skeleton.st').write_text(skeleton, encoding='utf-8')
    config['tools']['task_card'] = str(directory / 'task_card.json')
    config['tools']['task_id'] = card['task_id']
    tc = Toolchain(config['tools'], deadline, directory, mode=job['mode'])
    provider = Provider(config['provider'], job['model'], job['seed'],
                        directory/'api_cache', deadline, job['mode'], job['retry_uncertain'])
    best = None
    generated = repairs = 0
    first_status = None
    reason = None
    baseline_usage = None
    context_trace = []
    no_improvement = 0
    prompt = (ROOT/'agent/prompts/generate_v1.md').read_text(encoding='utf-8')
    repair_prompt = (ROOT/'agent/prompts/repair_v1.md').read_text(encoding='utf-8')
    try:
        blocked_types = [name for name in config['tools'].get('unsupported_types', [])
                         if any(re.search(r'\b'+re.escape(name)+r'\b', str(row.get('data_type','')), re.I)
                                for row in card.get('io_table',[]) if isinstance(row,dict))]
        if blocked_types and job['mode']=='live':
            card['environment_blockers'] = [{'code':'unsupported_type','data_type':name}
                                             for name in blocked_types]
            write_json(directory/'task_card.json',card)
            raise StopRun('unsupported_type')
        if card.get('degraded') and job['mode'] == 'live' and not job['allow_degraded']:
            raise StopRun('data_degraded')
        if job['framework'] == 'baseline':
            from baseline.adapter import generate_baseline
            context = build_context(card, budget=config['context_budget'])
            if context['overflow']:
                raise StopRun('budget')
            source, baseline_usage = generate_baseline(context, skeleton, job, deadline)
            generated = 1
            best = evaluate(tc, source, directory, 'baseline')
            first_status = best['compile']['status']
            if best['compile']['status'] in ('tool_error','timeout') or best['test']['status'] in ('tool_error','timeout'):
                raise StopRun('timeout' if 'timeout' in (best['compile']['status'],best['test']['status']) else 'tool_error')
            # 现成Agent自身的编辑/工具策略属于基线；外层不再套自研候选/修复策略。
        else:
            for index in range(config['candidates']):
                check_limits(deadline, provider.estimated_tokens, config['total_token_budget'])
                context = build_context(card, reference=config.get('reference',''),
                                        budget=config['context_budget'] - len(prompt.encode('utf-8')) - 256)
                context_trace.append({'stage':'generate', 'candidate':index+1, **context['trace']}
                                     if isinstance(context['trace'],dict) else
                                     {'stage':'generate','candidate':index+1,'trace':context['trace']})
                if context['overflow']:
                    raise StopRun('budget')
                scenario = config.get('fixture_scenario','repair')
                marker = {'repair':'FIXTURE_COMPILE_FAIL', 'best-effort':'FIXTURE_TEST_FAIL',
                          'abandoned':'FIXTURE_COMPILE_FAIL', 'timeout':'FIXTURE_TIMEOUT',
                          'tool-error':'FIXTURE_TOOL_ERROR'}.get(scenario, '')
                fixture = skeleton + '\n(* ' + marker + ' *)\n'
                messages = generation_messages(context, '', index, prompt)
                usage_before = provider.tokens_in + provider.tokens_out
                response = provider.complete(messages, config['temperatures'][index % len(config['temperatures'])], fixture)
                generated += 1
                try:
                    source = extract_st(response)
                except ValueError as exc:
                    event(directory, 'invalid_generation', candidate=index+1, message=str(exc))
                    continue
                candidate = evaluate(tc, source, directory, 'candidate_' + str(index+1),
                                     token_count=provider.tokens_in + provider.tokens_out - usage_before)
                if first_status is None:
                    first_status = candidate['compile']['status']
                if best is None or rank(candidate) > rank(best):
                    best = candidate
                    (directory/'best.st').write_text(source, encoding='utf-8')
                    write_json(directory/'best.evaluation.json', best)
                if candidate['compile']['status'] in ('tool_error','timeout') or candidate['test']['status'] in ('tool_error','timeout'):
                    raise StopRun('timeout' if 'timeout' in (candidate['compile']['status'],candidate['test']['status']) else 'tool_error')
            for round_idx in range(1, config['max_repairs']+1):
                if not best or success(best):
                    break
                check_limits(deadline, provider.estimated_tokens, config['total_token_budget'])
                error_feedback = feedback(best['source'], best['compile'], best['test'])
                context = build_context(card, feedback=error_feedback,
                    budget=config['context_budget'] - len(repair_prompt.encode('utf-8')) - 128)
                context_trace.append({'stage':'repair','round':round_idx,'trace':context['trace']})
                if context['overflow']:
                    raise StopRun('budget')
                marker = 'FIXTURE_COMPILE_FAIL' if 'FIXTURE_COMPILE_FAIL' in best['source'] else 'FIXTURE_TEST_FAIL'
                new_marker = '' if config.get('fixture_scenario','repair')=='repair' else marker
                patch_fixture = json.dumps({'patches':[{'old':marker,'new':new_marker}]})
                messages = [{'role':'system','content':context['system']+'\n'+repair_prompt},
                            {'role':'user','content':context['user']}]
                usage_before = provider.tokens_in + provider.tokens_out
                response = provider.complete(messages, 0.2, patch_fixture)
                repairs += 1
                try:
                    source = apply_patch(best['source'], response)
                except (ValueError,KeyError,TypeError) as exc:
                    no_improvement += 1
                    event(directory, 'patch_rejected', round=round_idx, message=str(exc))
                    if no_improvement >= config['stagnation_rounds']:
                        break
                    continue
                (directory/f'repair_{round_idx}.diff').write_text(diff(best['source'],source), encoding='utf-8')
                current = evaluate(tc, source, directory, 'repair_'+str(round_idx),
                                   repairs=repairs, token_count=best.get('token_count',0) +
                                   provider.tokens_in + provider.tokens_out - usage_before)
                if current['compile']['status'] in ('tool_error','timeout') or current['test']['status'] in ('tool_error','timeout'):
                    raise StopRun('timeout' if 'timeout' in (current['compile']['status'],current['test']['status']) else 'tool_error')
                rollback = regresses(best,current)
                def quality(item):
                    return (int(item['compile']['status']=='pass'), item['test'].get('passed',0),
                            -len([e for e in item['compile'].get('errors',[]) if e.get('severity')=='error']))
                improved = quality(current) > quality(best)
                event(directory, 'repair_decision', round=round_idx, rollback=rollback, improved=improved)
                if not rollback and quality(current) >= quality(best):
                    best = current
                    (directory/'best.st').write_text(source, encoding='utf-8')
                    write_json(directory/'best.evaluation.json',best)
                no_improvement = 0 if improved else no_improvement + 1
                if no_improvement >= config['stagnation_rounds']:
                    break
    except StopRun as exc:
        reason = exc.reason
        event(directory, 'stop', reason=reason)
    except Exception as exc:
        # 过程异常只记录类型；不把HTTP凭证或环境值写入错误。
        reason = 'tool_error'
        event(directory, 'exception', exception_type=type(exc).__name__)
    verify = {'status':'skipped'}
    if best:
        (directory/'final.st').write_text(best['source'], encoding='utf-8')
        if best['compile']['status']=='pass' and time.monotonic()<deadline:
            try:
                verify = tc.verify(best['source'],'final')
            except Exception as exc:
                verify = {'status':'tool_error'}
                event(directory,'optional_verifier_exception',exception_type=type(exc).__name__)
    result = base_result(job)
    compile_status = best['compile']['status'] if best else 'fail'
    result.update(latency_s=round(time.monotonic()-started,4), candidates=generated,
        repair_rounds=repairs, compile_status=compile_status if compile_status in ('pass','fail','timeout') else 'fail',
        compile_stage='after_repair' if best and best.get('repair_rounds',0)>0 else 'first',
        compile_errors=best['compile'].get('errors',[]) if best else [],
        test_total=best['test'].get('total',0) if best else 0,
        test_passed=best['test'].get('passed',0) if best else 0,
        verify_status=verify['status'] if verify['status'] in ('pass','violated','timeout','skipped') else 'skipped',
        final_status=classify(best,reason),
        tokens_in=provider.tokens_in if provider.usage_known else None,
        tokens_out=provider.tokens_out if provider.usage_known else None)
    if job['framework']=='baseline':
        result['tokens_in'] = baseline_usage.get('tokens_in') if baseline_usage else None
        result['tokens_out'] = baseline_usage.get('tokens_out') if baseline_usage else None
    write_json(directory/'context_trace.json',context_trace)
    write_json(directory/'metadata.json', {
        'execution_mode':job['mode'], 'eligible_for_experiments':job['mode']=='live' and not card.get('degraded')
            and reason is None
            and bool(best and best['compile'].get('authoritative_available')
                     and best['compile']['status'] in ('pass','fail')
                     and best['test']['status'] not in ('tool_error','timeout')),
        'status':'timeout' if reason=='timeout' else 'completed', 'failure_reason':reason,
        'first_compile_status':first_status, 'selected_candidate':best.get('tag') if best else None,
        'semantic_warnings':card.get('semantic_warnings',[]), 'degraded':card.get('degraded'),
        'environment_blockers':card.get('environment_blockers',[]),
        'fingerprint':job['fingerprint'], 'seed_sent_to_api':config['provider'].get('send_seed',False),
        'tokens_estimate_upper_bound':provider.estimated_tokens, 'tool_verify_status':verify['status']})
    save_result(directory,result)

def base_result(job):
    raw = Path(job['task']).read_bytes()
    return dict(run_id=job['run_id'],setting_id=job['setting_id'],framework=job['framework'],
        model=job['model'],task_id=Path(job['task']).stem,task_version=sha(raw)[:8],
        repeat_idx=job['repeat_idx'],seed=job['seed'],start_ts=job['start_ts'],latency_s=0,
        candidates=0,repair_rounds=0,compile_status='fail',compile_stage='first',compile_errors=[],
        test_total=0,test_passed=0,verify_status='skipped',final_status='abandoned:tool_error',
        artifact_path=job['artifact_path'],tokens_in=None,tokens_out=None)

def execute_job(job):
    directory = Path(job['directory'])
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory/'manifest.json'
    if manifest.exists():
        old = json.loads(manifest.read_text(encoding='utf-8'))
        if old['fingerprint'] != job['fingerprint']:
            raise ValueError('相同run_id对应的数据/参数/源码已变化，请使用新输出目录：' + job['run_id'])
    if (directory/'result.json').exists():
        print('SKIP '+job['run_id'], flush=True)
        return json.loads((directory/'result.json').read_text(encoding='utf-8'))
    lock = directory/'running.lock'
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        # 不自动删除锁：另一个批次可能还在工作；显式恢复前先核实PID。
        raise ValueError('发现运行锁，核实进程已退出后删除该锁再续跑：' + job['run_id']) from None
    with os.fdopen(fd,'w') as handle:
        handle.write(str(os.getpid()))
    try:
        write_json(manifest, {'fingerprint':job['fingerprint'],'execution_mode':job['mode'],
            'run_id':job['run_id'],'config':job['config']})
        write_json(directory/'job.json', job)
        proc = run_process([sys.executable,str(Path(__file__).resolve()),'--worker',str(directory/'job.json')],
                           timeout_s=job['config']['task_timeout_s'], cwd=str(ROOT))
        (directory/'worker.stdout.txt').write_text(proc.get('stdout',''),encoding='utf-8')
        (directory/'worker.stderr.txt').write_text(proc.get('stderr',''),encoding='utf-8')
        if not (directory/'result.json').exists():
            result = base_result(job)
            is_timeout = proc.get('status')=='timeout'
            result.update(final_status='abandoned:'+('timeout' if is_timeout else 'tool_error'),
                          latency_s=proc.get('elapsed_s',0), compile_status='timeout' if is_timeout else 'fail')
            prior = directory/'best.evaluation.json'
            if prior.exists():
                best = json.loads(prior.read_text(encoding='utf-8'))
                (directory/'final.st').write_text(best['source'],encoding='utf-8')
                result.update(compile_status=best['compile']['status'] if best['compile']['status'] in ('pass','fail','timeout') else 'fail',
                    compile_errors=best['compile'].get('errors',[]),test_total=best['test'].get('total',0),
                    test_passed=best['test'].get('passed',0),repair_rounds=best.get('repair_rounds',0),
                    compile_stage='after_repair' if best.get('repair_rounds',0) else 'first',
                    final_status=classify(best,'timeout' if is_timeout else 'tool_error'))
            write_json(directory/'metadata.json', {'execution_mode':job['mode'],
                'eligible_for_experiments':False,'status':'timeout' if is_timeout else 'tool_error',
                'fingerprint':job['fingerprint'],'failure_reason':'parent_deadline' if is_timeout else 'worker_exit'})
            save_result(directory,result)
        result = json.loads((directory/'result.json').read_text(encoding='utf-8'))
        print(job['run_id']+' '+result['final_status'],flush=True)
        return result
    finally:
        lock.unlink(missing_ok=True)

def main():
    if len(sys.argv)>2 and sys.argv[1]=='--worker':
        worker(json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--framework',choices=['self','baseline'],default='self')
    parser.add_argument('--model',required=True, help='从DMXAPI页面复制准确模型名；fixture模式填fixture')
    parser.add_argument('--tasks',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--repeat',type=int,default=1)
    parser.add_argument('--setting-id',choices=['E1','E2','E3','E4'])
    parser.add_argument('--config',default=str(ROOT/'agent/configs/default.yaml'))
    parser.add_argument('--mode',choices=['live','fixture'],default='live')
    parser.add_argument('--task-set',choices=['core32','all34'],default='core32')
    parser.add_argument('--allow-degraded',action='store_true')
    parser.add_argument('--retry-uncertain',action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    if not 1 <= config['candidates'] <= 5 or not 0 <= config['max_repairs'] <= 5:
        parser.error('candidates必须1..5，max_repairs必须0..5')
    if args.repeat<1 or config['concurrency']<1 or config['task_timeout_s']<=0:
        parser.error('repeat/concurrency/timeout须为正数')
    setting = args.setting_id or ('E3' if args.framework=='self' else 'E1')
    if (setting in ('E3','E4')) != (args.framework=='self'):
        parser.error('E1/E2用于baseline，E3/E4用于self')
    task_path = Path(args.tasks).resolve()
    if task_path.is_dir():
        paths = sorted(task_path.glob('*.yaml'))
        if args.task_set=='core32':
            ids = {'P'+str(i).zfill(2) for i in range(1,21)} | {'S'+str(i).zfill(2) for i in range(1,13)}
            paths = [p for p in paths if p.stem in ids]
        expected = 32 if args.task_set=='core32' else 34
        if len(paths)!=expected:
            parser.error(f'题目录须完整覆盖{expected}题，实际{len(paths)}题；单题请传yaml文件')
    else:
        paths = [task_path]
    if not all(p.exists() for p in paths):
        parser.error('找不到题面')
    if args.mode=='live':
        if args.framework=='self' and not os.environ.get(config['provider'].get('key_env','DMXAPI_API_KEY')):
            parser.error('缺少DMXAPI_API_KEY环境变量；演示请显式使用--mode fixture')
        if not config['tools']['authoritative'].get('command'):
            parser.error('尚未配置权威CODESYS编译命令，请按docs/toolchain.md配置')
    output = Path(args.out).resolve() / ('fixture' if args.mode=='fixture' else 'live')
    output.mkdir(parents=True,exist_ok=True)
    sources = sorted((ROOT/'agent').rglob('*.py')) + sorted((ROOT/'baseline').glob('*.py')) + sorted((ROOT/'agent/prompts').glob('*.md'))
    code_hash = sha(b''.join(p.read_bytes() for p in sources))
    jobs = []
    for repeat_idx in range(1,args.repeat+1):
        for path in paths:
            card = parse_task(path,root=ROOT)
            run_id = f'{setting}_{path.stem}_{repeat_idx}_{args.seed}'
            fingerprint = sha(json.dumps({'config':config,'model':args.model,'mode':args.mode,
                'framework':args.framework,'task':sha(path.read_bytes()),'spec':card.get('spec_sha256'),
                'seed':args.seed,'repeat':repeat_idx,'allow_degraded':args.allow_degraded,
                'code':code_hash,'tests_digest':digest_tree(ROOT/'tests'/'cases')},sort_keys=True).encode())
            jobs.append(dict(config=config,model=args.model,mode=args.mode,task=str(path),framework=args.framework,
                seed=args.seed,repeat_idx=repeat_idx,setting_id=setting,run_id=run_id,
                directory=str(output/run_id),artifact_path=str(Path(output.name)/run_id).replace('\\','/'),
                fingerprint=fingerprint,start_ts=now(),allow_degraded=args.allow_degraded,retry_uncertain=args.retry_uncertain))
    with ThreadPoolExecutor(max_workers=config['concurrency']) as executor:
        results = list(executor.map(execute_job,jobs))
    # 每题文件为唯一真源；汇总从本目录全部终态重建，续跑不会重复追加。
    all_results = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(output.glob('*/result.json'))]
    (output/'runs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in all_results),encoding='utf-8')
    write_json(output/'batch_manifest.json', {'execution_mode':args.mode,'setting_id':setting,
        'task_set':args.task_set,'task_ids':[p.stem for p in paths], 'repeat':args.repeat,
        'seed':args.seed,'code_hash':code_hash,'count':len(results)})
    return 0

def digest_tree(path):
    return sha(b''.join(p.relative_to(path).as_posix().encode()+p.read_bytes()
                       for p in sorted(path.rglob('*')) if p.is_file())) if path.exists() else None

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(2)
