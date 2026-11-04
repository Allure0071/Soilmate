"""Backend-only connection to the authenticated Soilmate inference service."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx

PROFILE = json.loads((Path(__file__).resolve().parents[2]/'model_profiles/soilmate-qwen3-8b.json').read_text())

class ModelUnavailable(Exception):
    def __init__(self, message, code='MODEL_UNAVAILABLE'):
        super().__init__(message)
        self.code = code

class ModelGateway:
    def __init__(self, base_url=None, api_key=None, transport=None):
        self.base_url = (os.getenv('SOILMATE_MODEL_BASE_URL', '') if base_url is None else base_url).rstrip('/')
        self.api_key = os.getenv('SOILMATE_MODEL_API_KEY', '') if api_key is None else api_key
        self.transport = transport

    @property
    def configured(self):
        try:
            value = urlsplit(self.base_url)
            return bool(value.scheme in ('http','https') and value.hostname and not value.username and not value.password and not value.query and not value.fragment and self.api_key)
        except ValueError:return False

    def _request(self, method, path, payload=None, timeout=100):
        if not self.configured: raise ModelUnavailable('微调模型尚未配置连接，请先启动云端推理服务。','MODEL_NOT_CONFIGURED')
        try:
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(timeout, connect=5), follow_redirects=False, trust_env=False) as client:
                with client.stream(method, self.base_url+path, headers={'Authorization':'Bearer '+self.api_key,'Accept':'application/json'}, json=payload) as response:
                    if response.status_code != 200:
                        if response.status_code == 429: raise ModelUnavailable('模型正在处理另一条请求，请稍后重试。','MODEL_BUSY')
                        if response.status_code == 413: raise ModelUnavailable('当前问题与研究证据超过模型上下文，请缩小范围后重试。','CONTEXT_TOO_LONG')
                        if response.status_code in (401,403): raise ModelUnavailable('模型服务认证失败，请检查后端连接配置。','MODEL_AUTH_FAILED')
                        raise ModelUnavailable('微调模型服务暂不可用，请稍后重试。')
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data)>256*1024: raise ModelUnavailable('模型响应过大，未作为有效回答展示。','MODEL_PROTOCOL_ERROR')
                    return json.loads(data)
        except ModelUnavailable: raise
        except (httpx.HTTPError, ValueError, OSError):
            raise ModelUnavailable('无法连接微调模型服务，请检查云端进程与网络。')

    def _verify(self, metadata):
        if not isinstance(metadata,dict) or metadata.get('id') != PROFILE['id'] or metadata.get('adapter_sha256') != PROFILE['adapter_sha256'] or metadata.get('is_fine_tuned') is not True:
            raise ModelUnavailable('服务返回的模型身份与本次微调适配器不匹配。','MODEL_IDENTITY_MISMATCH')

    def status(self):
        result = {'configured':self.configured,'available':False,'model':{'id':PROFILE['id'],'name':PROFILE['display_name'],'release_status':'research_preview'},'message':'微调模型尚未连接'}
        if not self.configured: return result
        try:
            data = self._request('GET','/health',timeout=8)
            if not isinstance(data,dict) or not data.get('ready'):
                messages={'MODEL_PATHS_NOT_CONFIGURED':'模型服务未配置基础模型和适配器路径。','MODEL_FILES_MISSING':'模型文件尚未就绪。','MODEL_DEPENDENCY_MISSING':'推理环境缺少模型依赖。','BASE_METADATA_MISMATCH':'基础模型版本与训练记录不匹配。','ADAPTER_HASH_MISMATCH':'适配器校验未通过。','CUDA_REQUIRED':'推理服务需要可用的 CUDA GPU。'}
                raise ModelUnavailable(messages.get(data.get('code') if isinstance(data,dict) else '', '模型服务已连接，权重尚未就绪。'))
            self._verify(data.get('model'))
            result.update(available=True,message='微调模型已连接 · 研究试用')
        except ModelUnavailable as error: result.update(message=str(error),code=error.code)
        return result

    def answer(self, messages):
        data = self._request('POST','/chat/completions',{'model':PROFILE['id'],'messages':messages,'max_tokens':512,'stream':False})
        if not isinstance(data,dict): raise ModelUnavailable('模型响应格式无效。','MODEL_PROTOCOL_ERROR')
        self._verify(data.get('model_metadata'))
        try:
            choice=data['choices'][0];text=choice['message']['content'];finish=choice['finish_reason']
            if not isinstance(text,str) or not text.strip() or len(text)>16000 or finish not in ('stop','length'): raise ValueError()
            if '<think>' in text or '</think>' in text: raise ValueError()
        except (KeyError,IndexError,TypeError,ValueError): raise ModelUnavailable('模型未返回可展示的最终回答。','MODEL_PROTOCOL_ERROR')
        return {'text':text.strip(),'truncated':finish=='length','model':{'id':PROFILE['id'],'name':PROFILE['display_name'],'is_fine_tuned':True,'adapter_sha256':PROFILE['adapter_sha256'],'release_status':'research_preview'},'request_id':str(data.get('id',''))}
