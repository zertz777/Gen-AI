"""DMXAPI Chat Completions；标准库HTTP，缓存已完成请求并阻止不明状态重复计费。"""
import hashlib
import json
import os
import re
import socket
import time
import urllib.request
import urllib.error
from pathlib import Path
from .logging import write_json
from .terminate import StopRun

def extract_st(text):
    match = re.search(r'```(?:st|iecst|structuredtext)?\s*\n(.*?)```', text, re.I | re.S)
    source = (match.group(1) if match else text).strip()
    if not re.search(r'\b(?:PROGRAM|FUNCTION_BLOCK|FUNCTION)\b', source, re.I):
        raise ValueError('Model response contains no ST POU')
    return source + '\n'

class Provider:
    def __init__(self, config, model, seed, directory, deadline, mode='live', retry_uncertain=False):
        self.config, self.model, self.seed = config, model, seed
        self.directory, self.deadline, self.mode = Path(directory), deadline, mode
        self.retry_uncertain = retry_uncertain
        self.tokens_in = self.tokens_out = 0
        self.usage_known = True
        self.estimated_tokens = 0
        self._accounted = set()

    def complete(self, messages, temperature=0.2, fixture_response=None):
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = {'model': self.model, 'messages': messages, 'stream': False}
        # DMX文档只保证model/messages/stream；可选采样参数须按所选模型能力启用。
        if self.config.get('send_temperature', False):
            payload['temperature'] = temperature
        if self.config.get('send_seed', False):
            payload['seed'] = self.seed
        if self.config.get('max_output_tokens'):
            payload['max_tokens'] = self.config['max_output_tokens']
        key = hashlib.sha256(json.dumps([payload, self.mode, fixture_response], sort_keys=True,
                                        ensure_ascii=False).encode()).hexdigest()[:20]
        dest = self.directory / (key + '.json')
        pending = self.directory / (key + '.pending.json')
        if dest.exists():
            response = json.loads(dest.read_text(encoding='utf-8'))
        else:
            if pending.exists() and not self.retry_uncertain:
                raise StopRun('uncertain_request')
            if self.mode == 'fixture':
                response = {'choices': [{'message': {'content': fixture_response or ''}}],
                            'usage': {'prompt_tokens': 0, 'completion_tokens': 0}, 'fixture': True}
            else:
                secret = os.environ.get(self.config.get('key_env', 'DMXAPI_API_KEY'))
                if not secret:
                    raise StopRun('api_key_missing')
                base = os.environ.get('DMXAPI_BASE_URL', self.config['base_url']).rstrip('/')
                if not base.startswith('https://') and not self.config.get('allow_local_http', False):
                    raise StopRun('insecure_endpoint')
                write_json(pending, {'request_hash': key, 'state': 'in_flight',
                                     'note': '远端是否计费未知；不得自动重发'})
                timeout = min(self.config.get('request_timeout_s', 120), self.deadline-time.monotonic())
                if timeout <= 0:
                    raise StopRun('timeout')
                req = urllib.request.Request(base + '/chat/completions',
                    data=json.dumps(payload).encode(), headers={
                        'Content-Type': 'application/json', 'Authorization': 'Bearer ' + secret})
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as handle:
                        response = json.loads(handle.read().decode('utf-8'))
                except urllib.error.HTTPError as exc:
                    # 不落盘服务器响应正文，避免网关回显凭证。
                    write_json(pending, {'request_hash': key, 'state': 'http_error', 'status': exc.code})
                    raise StopRun('api_http_' + str(exc.code)) from None
                except (TimeoutError, socket.timeout):
                    raise StopRun('timeout') from None
                except (OSError, ValueError):
                    raise StopRun('api_transport_error') from None
            write_json(dest, response)
            pending.unlink(missing_ok=True)
        usage = response.get('usage') or {}
        if key not in self._accounted:
            self._accounted.add(key)
            valid_usage = all(isinstance(usage.get(k), int) and not isinstance(usage.get(k), bool)
                              and usage[k] >= 0 for k in ('prompt_tokens','completion_tokens'))
            if not valid_usage:
                self.usage_known = False
            else:
                self.tokens_in += usage['prompt_tokens']
                self.tokens_out += usage['completion_tokens']
            self.estimated_tokens += len(json.dumps(messages, ensure_ascii=False).encode('utf-8')) + len(str(response).encode('utf-8'))
        try:
            text = response['choices'][0]['message']['content']
            if not isinstance(text, str):
                raise ValueError('Response content is not a string')
            return text
        except (KeyError, IndexError, TypeError, ValueError):
            raise StopRun('api_response_invalid') from None

def generation_messages(context, skeleton, variant, prompt):
    variants = ['直接按I/O与逐周期语义实现。', '先检查边界、联锁与错误优先级，再实现。',
                '先检查初态、边沿和状态保持，再实现。', '先检查数值范围，再实现。', '先检查复位和异常退出，再实现。']
    return [{'role': 'system', 'content': context['system'] + '\n' + prompt},
            {'role': 'user', 'content': context['user'] + '\n候选策略：' + variants[variant]
             + ('\n接口骨架（补全逻辑，可增加内部变量）：\n' + skeleton if skeleton else '')}]
