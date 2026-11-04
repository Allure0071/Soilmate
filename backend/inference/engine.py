import hashlib
import json
import os
import threading
from pathlib import Path

PROFILE = json.loads((Path(__file__).resolve().parents[1]/'model_profiles/soilmate-qwen3-8b.json').read_text())

class InferenceFailure(Exception):
    def __init__(self, message, status=503):
        super().__init__(message);self.status=status

def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()

class ModelEngine:
    def __init__(self):
        self.ready=False;self.error='MODEL_NOT_LOADED';self.lock=threading.Lock()
        self.model=None;self.tokenizer=None;self.torch=None

    def metadata(self):
        return {'id':PROFILE['id'],'name':PROFILE['display_name'],'base_model':PROFILE['base_model'],'is_fine_tuned':self.ready,'adapter_sha256':PROFILE['adapter_sha256'] if self.ready else None,'release_status':'research_preview','prompt_version':PROFILE['prompt_version']}

    def load(self):
        base=Path(os.environ.get('SOILMATE_BASE_MODEL_PATH',''))
        adapter=Path(os.environ.get('SOILMATE_ADAPTER_PATH',''))
        if not os.environ.get('SOILMATE_BASE_MODEL_PATH') or not os.environ.get('SOILMATE_ADAPTER_PATH'):
            self.error='MODEL_PATHS_NOT_CONFIGURED';return
        try:
            for name,expected in PROFILE['base_metadata_sha256'].items():
                if digest(base/name)!=expected:raise ValueError('BASE_METADATA_MISMATCH')
            if digest(adapter/'adapter_model.safetensors')!=PROFILE['adapter_sha256'] or digest(adapter/'adapter_config.json')!=PROFILE['adapter_config_sha256']:raise ValueError('ADAPTER_HASH_MISMATCH')
            import torch
            from transformers import AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
            from peft import PeftModel
            if not torch.cuda.is_available():self.error='CUDA_REQUIRED';return
            self.torch=torch
            self.tokenizer=AutoTokenizer.from_pretrained(str(adapter),local_files_only=True,trust_remote_code=False)
            quantized=os.environ.get('SOILMATE_LOAD_4BIT','true').lower()=='true'
            options={'local_files_only':True,'trust_remote_code':False,'use_safetensors':True,'torch_dtype':torch.bfloat16,'device_map':'auto'}
            if quantized:options['quantization_config']=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
            base_model=AutoModelForCausalLM.from_pretrained(str(base),**options)
            self.model=PeftModel.from_pretrained(base_model,str(adapter),is_trainable=False,local_files_only=True)
            self.model.eval();self.ready=True;self.error=''
        except ImportError:self.error='MODEL_DEPENDENCY_MISSING';self.ready=False
        except OSError:self.error='MODEL_FILES_MISSING';self.ready=False
        except ValueError as error:self.error=str(error) if str(error) in ('BASE_METADATA_MISMATCH','ADAPTER_HASH_MISMATCH') else 'MODEL_LOAD_FAILED';self.ready=False
        except RuntimeError:self.error='MODEL_LOAD_FAILED';self.ready=False

    def generate(self,messages,max_tokens):
        if not self.ready:raise InferenceFailure('模型权重尚未就绪。')
        if not self.lock.acquire(blocking=False):raise InferenceFailure('模型正在处理另一条请求，请稍后重试。',429)
        try:
            text=self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            inputs=self.tokenizer([text],return_tensors='pt')
            if inputs['input_ids'].shape[-1]>PROFILE['max_input_tokens']:raise InferenceFailure('输入超过模型上下文上限，未截断研究证据。',413)
            inputs=inputs.to(self.model.device)
            with self.torch.inference_mode():
                outputs=self.model.generate(**inputs,max_new_tokens=min(max_tokens,PROFILE['max_output_tokens']),do_sample=False,pad_token_id=self.tokenizer.eos_token_id)
            generated=outputs[0][inputs['input_ids'].shape[-1]:]
            answer=self.tokenizer.decode(generated,skip_special_tokens=True).strip()
            # Never return raw reasoning blocks as the final user-visible answer.
            if '</think>' in answer:answer=answer.rsplit('</think>',1)[-1].strip()
            if not answer or '<think>' in answer:raise InferenceFailure('模型没有形成可展示的最终回答。')
            eos=self.model.generation_config.eos_token_id
            eos=eos if isinstance(eos,list) else [eos]
            finish='stop' if generated.numel() and generated[-1].item() in eos else 'length'
            return {'text':answer,'finish_reason':finish,'prompt_tokens':inputs['input_ids'].shape[-1],'completion_tokens':generated.numel()}
        finally:self.lock.release()
