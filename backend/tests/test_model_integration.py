import asyncio
import importlib.util
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from backend.app.models.gateway import ModelGateway,ModelUnavailable,PROFILE
from backend.app.models.grounded import answer_question
from backend.inference.app import create_app
from backend.inference.engine import ModelEngine
import test_agent_phase2_api as fixture
from backend.app import main


def metadata():
    return {'id':PROFILE['id'],'adapter_sha256':PROFILE['adapter_sha256'],'is_fine_tuned':True}

def completion(text='仅根据已给出的证据解释，缺失信息需要补充。'):
    return {'id':'request-test','model_metadata':metadata(),'choices':[{'message':{'content':text},'finish_reason':'stop'}]}

class GatewayTests(unittest.TestCase):
    def gateway(self,handler):return ModelGateway('http://inference.test/v1','server-secret',httpx.MockTransport(handler))
    def test_configuration_and_verified_identity(self):
        self.assertFalse(ModelGateway('', '').status()['available'])
        seen=[]
        def handler(request):
            seen.append(request)
            if request.method=='GET':return httpx.Response(200,json={'ready':True,'model':metadata()})
            return httpx.Response(200,json=completion())
        gateway=self.gateway(handler)
        self.assertTrue(gateway.status()['available'])
        answer=gateway.answer([{'role':'user','content':'解释土壤健康'}])
        self.assertTrue(answer['model']['is_fine_tuned'])
        self.assertEqual(seen[1].headers['Authorization'],'Bearer server-secret')
        self.assertEqual(json.loads(seen[1].content)['model'],PROFILE['id'])
        self.assertNotIn('server-secret',json.dumps(answer))
    def test_base_model_masquerading_as_adapter_is_rejected(self):
        for value in [{}, {**metadata(),'adapter_sha256':'wrong'}, {**metadata(),'is_fine_tuned':False}]:
            gateway=self.gateway(lambda request:httpx.Response(200,json={**completion(),'model_metadata':value}))
            with self.assertRaises(ModelUnavailable) as error:gateway.answer([])
            self.assertEqual(error.exception.code,'MODEL_IDENTITY_MISMATCH')
    def test_service_failure_has_no_model_fallback_and_no_reasoning_leak(self):
        for status in [401,403,429,503]:
            with self.assertRaises(ModelUnavailable):self.gateway(lambda request:httpx.Response(status)).answer([])
        for text in ['<think>private reasoning</think>answer','', 'x'*16001]:
            with self.assertRaises(ModelUnavailable):self.gateway(lambda request:httpx.Response(200,json=completion(text))).answer([])
        with self.assertRaises(ModelUnavailable):self.gateway(lambda request:httpx.Response(200,content=b'x'*300000)).answer([])
    def test_grounding_keeps_evidence_owned_and_output_non_authoritative(self):
        class FakeGateway:
            def answer(inner,messages):
                self.assertIn('不得编造',messages[0]['content'])
                self.assertIn('artifact-owned',messages[1]['content'])
                return {'text':'待核对的解释','model':metadata(),'request_id':'test','truncated':False}
        result=answer_question('为什么选择这个指标',[{'artifact_id':'artifact-owned','kind':'result','content':{'row_count':10}}],gateway=FakeGateway())
        self.assertEqual(result['answer_type'],'model_explanation')
        self.assertEqual(result['evidence_refs'][0]['artifact_id'],'artifact-owned')
        with self.assertRaises(ModelUnavailable):answer_question('q',[{'artifact_id':'a','content':'x'*19000}],gateway=FakeGateway())

class InferenceTests(unittest.TestCase):
    def test_private_service_auth_model_identity_and_input_limits(self):
        class Engine:
            ready=True;error=''
            def metadata(self):return metadata()
            def generate(self,messages,max_tokens):return {'text':'服务端测试最终回答','finish_reason':'stop','prompt_tokens':10,'completion_tokens':5}
        client=TestClient(create_app(Engine(),load=False))
        with patch.dict(os.environ,{'SOILMATE_INFERENCE_API_KEY':'test-key'}):
            self.assertEqual(client.get('/v1/health').status_code,401)
            headers={'Authorization':'Bearer test-key'}
            self.assertTrue(client.get('/v1/health',headers=headers).json()['ready'])
            body={'model':PROFILE['id'],'messages':[{'role':'user','content':'测试问题'}]}
            response=client.post('/v1/chat/completions',headers=headers,json=body)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['model_metadata']['adapter_sha256'],PROFILE['adapter_sha256'])
            self.assertEqual(client.post('/v1/chat/completions',headers=headers,json={**body,'model':'base-qwen'}).status_code,404)
            self.assertEqual(client.post('/v1/chat/completions',headers=headers,json={**body,'max_tokens':9999}).status_code,422)
            self.assertEqual(client.post('/v1/chat/completions',headers=headers,json={**body,'stream':True}).status_code,422)
    def test_missing_model_paths_do_not_load_or_download_weights(self):
        with patch.dict(os.environ,{'SOILMATE_BASE_MODEL_PATH':'','SOILMATE_ADAPTER_PATH':''}):
            engine=ModelEngine();engine.load()
            self.assertFalse(engine.ready);self.assertFalse(engine.metadata()['is_fine_tuned'])
            self.assertEqual(engine.error,'MODEL_PATHS_NOT_CONFIGURED')
    def test_installer_rejects_links_and_leaves_no_partial_install(self):
        spec=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[2]/'scripts/install_soilmate_adapter.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'unsafe.tar.gz'
            with tarfile.open(archive,'w:gz') as bundle:
                entry=tarfile.TarInfo('runs/8b_sft/adapter_final/unsafe');entry.type=tarfile.SYMTYPE;entry.linkname='/tmp/outside';bundle.addfile(entry)
            destination=Path(tmp)/'installed'
            with self.assertRaises(ValueError):module.install(archive,destination)
            self.assertFalse(destination.exists())

class ModelApiTests(unittest.TestCase):
    setUp=fixture.AgentApiTests.setUp
    tearDown=fixture.AgentApiTests.tearDown
    def test_auth_csrf_task_ownership_and_no_fabricated_offline_answer(self):
        async def scenario():
            with patch.dict(os.environ,{'SOILMATE_MODEL_BASE_URL':'','SOILMATE_MODEL_API_KEY':''}):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://test') as client:
                    self.assertEqual((await client.get('/api/agent/model/status')).status_code,401)
                    client.cookies.set('soilmate_session','session-one-token-123456789012345')
                    status=await client.get('/api/agent/model/status')
                    self.assertFalse(status.json()['available'])
                    self.assertTrue(status.json()['local_fallback'])
                    self.assertEqual((await client.post('/api/agent/expert',json={'query':'什么是MDS'})).status_code,403)
                    headers={'X-CSRF-Token':'csrf-1'}
                    response=await client.post('/api/agent/expert',headers=headers,json={'query':'什么是MDS'})
                    self.assertEqual(response.status_code,200)
                    self.assertEqual(response.json()['answer_type'],'domain_fact')
                    self.assertIsNone(response.json()['model'])
                    created=await client.post('/api/agent/messages',headers=headers,json={'text':'帮我分析数据','project_id':'p1'})
                    task_id=created.json()['task_id']
                    empty=await client.post('/api/agent/expert',headers=headers,json={'query':'解释本次结果','task_id':task_id})
                    self.assertEqual(empty.status_code,200);self.assertIsNone(empty.json()['model'])
                    client.cookies.set('soilmate_session','session-two-token-123456789012345')
                    denied=await client.post('/api/agent/expert',headers={'X-CSRF-Token':'csrf-2'},json={'query':'解释本次结果','task_id':task_id})
                    self.assertEqual(denied.status_code,404)
                    self.assertEqual((await client.post('/api/soiledge/ai',json={})).status_code,403)
        asyncio.run(scenario())
