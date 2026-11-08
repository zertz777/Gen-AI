"""Aider CLI适配DMXAPI；与自研共用外部编译/功能判定。"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from agent.src.tools import run_process
from agent.src.terminate import StopRun

def generate_baseline(context, skeleton, job, deadline):
    folder = Path(job['directory'])/'baseline_workspace'
    folder.mkdir(parents=True,exist_ok=True)
    source = folder/'solution.st'
    source.write_text(skeleton,encoding='utf-8')
    if job['mode']=='fixture':
        # 只验证入口路径与相同judge schema；不模拟Aider真实智能行为。
        return skeleton+'\n(* FIXTURE_BASELINE *)\n', {'tokens_in':0,'tokens_out':0}
    cfg = job['config']['baseline']
    if cfg.get('kind')!='aider':
        raise StopRun('baseline_not_configured')
    env = os.environ.copy()
    key = env.get(job['config']['provider'].get('key_env','DMXAPI_API_KEY'))
    if not key:
        raise StopRun('api_key_missing')
    env['OPENAI_API_KEY'] = key
    env['OPENAI_API_BASE'] = env.get('DMXAPI_BASE_URL',job['config']['provider']['base_url'])
    judge_job = folder/'judge_job.json'
    judge_job.write_text(json.dumps({'tools':job['config']['tools'],'deadline':deadline,
        'artifact_dir':str(folder/'judge'), 'source':str(source)},ensure_ascii=False),encoding='utf-8')
    judge_args = [sys.executable,str(Path(__file__).with_name('judge.py')),'--job',str(judge_job)]
    judge_command = subprocess.list2cmdline(judge_args) if os.name=='nt' else shlex.join(judge_args)
    prompt = folder/'prompt.txt'
    prompt.write_text(context['system']+'\n'+context['user']+
        '\n请直接编辑solution.st为完整ST；保持接口。每次修改后使用配置的test命令检查并修复。',encoding='utf-8')
    executable = cfg.get('command') or ['aider']
    if not isinstance(executable,list):
        raise StopRun('baseline_command_invalid')
    model = 'openai/'+job['model']
    command = executable + ['--model',model,'--weak-model',model,
        '--openai-api-base',env['OPENAI_API_BASE'],'--message-file',str(prompt),
        '--yes-always','--no-stream','--no-git','--no-auto-commits',
        '--no-check-update','--no-analytics','--no-auto-lint','--map-tokens','0',
        '--edit-format','whole','--auto-test','--test-cmd',judge_command,
        str(source)]
    result = run_process(command, timeout_s=min(deadline-time.monotonic(),cfg.get('timeout_s',900)),
                         cwd=str(folder),env=env)
    # CLI输出可能有网关错误回显，写盘前过滤密钥。
    for channel in ('stdout','stderr'):
        (folder/(channel+'.txt')).write_text(result.get(channel,'').replace(key,'[REDACTED]'),encoding='utf-8')
    if result['status']=='timeout':
        raise StopRun('timeout')
    if result['status']!='pass':
        raise StopRun('baseline_tool_error')
    output = source.read_text(encoding='utf-8')
    if output.strip()==skeleton.strip():
        raise StopRun('baseline_no_edit')
    # 不从自然语言终端摘要猜token；未提供机器可读usage时留null。
    return output, {'tokens_in':None,'tokens_out':None}
