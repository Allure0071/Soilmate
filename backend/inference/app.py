"""Authenticated, non-streaming chat endpoint for the supplied LoRA adapter."""
import hmac
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import List,Literal

from fastapi import Depends,FastAPI,Header,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from starlette.concurrency import run_in_threadpool
from .engine import ModelEngine,InferenceFailure,PROFILE

class Message(BaseModel):
    model_config=ConfigDict(extra='forbid')
    role:Literal['system','user','assistant']
    content:str=Field(min_length=1,max_length=24000)

class ChatInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model:str
    messages:List[Message]=Field(min_length=1,max_length=20)
    max_tokens:int=Field(default=512,ge=1,le=512)
    stream:Literal[False]=False

def create_app(engine=None,load=True):
    engine=engine or ModelEngine()
    @asynccontextmanager
    async def lifespan(app):
        if load:await run_in_threadpool(engine.load)
        yield
    app=FastAPI(title='Soilmate private model service',lifespan=lifespan)
    def authorize(authorization:str=Header(default='')):
        key=os.getenv('SOILMATE_INFERENCE_API_KEY','')
        if not key:raise HTTPException(503,'服务端尚未配置访问密钥。')
        if not hmac.compare_digest(authorization,'Bearer '+key):raise HTTPException(401,'模型服务认证失败。')
    @app.get('/v1/health',dependencies=[Depends(authorize)])
    def health():return {'ready':engine.ready,'code':engine.error,'model':engine.metadata()}
    @app.get('/v1/models',dependencies=[Depends(authorize)])
    def models():
        if not engine.ready:raise HTTPException(503,'模型尚未就绪。')
        return {'object':'list','data':[{'id':PROFILE['id'],'object':'model','owned_by':'soilmate','model_metadata':engine.metadata()}]}
    @app.post('/v1/chat/completions',dependencies=[Depends(authorize)])
    def chat(payload:ChatInput):
        if payload.model!=PROFILE['id']:raise HTTPException(404,'模型标识不匹配。')
        messages=[item.model_dump() for item in payload.messages]
        if sum(len(item['content']) for item in messages)>24000:raise HTTPException(413,'输入过长。')
        try:result=engine.generate(messages,payload.max_tokens)
        except InferenceFailure as error:raise HTTPException(error.status,str(error))
        except (RuntimeError,ValueError,TypeError):raise HTTPException(503,'模型本次生成失败，请稍后重试。')
        return {'id':'soilmate-'+uuid.uuid4().hex,'object':'chat.completion','created':int(time.time()),'model':PROFILE['id'],'model_metadata':engine.metadata(),'choices':[{'index':0,'message':{'role':'assistant','content':result['text']},'finish_reason':result['finish_reason']}],'usage':{'prompt_tokens':result['prompt_tokens'],'completion_tokens':result['completion_tokens'],'total_tokens':result['prompt_tokens']+result['completion_tokens']}}
    return app

app=create_app()
