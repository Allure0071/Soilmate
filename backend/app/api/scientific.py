"""Scientific Agent API inside the existing Soilmate FastAPI service."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from ..scientific.cnps_adapter import read_ko_matrix
from ..scientific.research_flow import ROOT, public_context, next_action, execute_action, study_report
from .point import query_point
from .preview import preview_point
import json

router=APIRouter(prefix='/api/scientific',tags=['Scientific Agent'])

class ResearchRequest(BaseModel):
    lon: float=Field(ge=-180,le=180)
    lat: float=Field(ge=-90,le=90)
    res: int=5
    microbial_id: str
    module_id: str
    action: Optional[str]=None
    completed: List[str]=[]

def soil_at(request):
    if request.res not in (1,5):raise HTTPException(400,'分辨率仅支持 1 或 5 km')
    point=query_point(lon=request.lon,lat=request.lat,res=request.res)
    if not point['found']:raise HTTPException(404,'选中位置无土壤指标记录')
    values=point['values']
    def v(key, scale=1):
        item=values.get(key)
        if item and item.get('value') is not None:
            return str(item['value']/scale)
        return ''
    an=v('soil_an')
    an_source='Soilmate 点位库'
    if not an and request.res == 5:
        try:
            preview=preview_point(lon=request.lon,lat=request.lat)['values'].get('n01_an')
            if preview is not None:
                an=str(preview)
                an_source='研究预览图层；单位与采样来源待核'
        except Exception:
            pass
    return {'record_id':f"{request.res}km-grid-{point['row']}-{point['col']}",'lon':request.lon,'lat':request.lat,
            'soil_ph':v('soil_ph',100),'AN':an,'AN_source':an_source,'TN':v('soil_tn',100),'soil_soc':v('soil_soc',100),'EC':v('ece'),
            'quality':'Soilmate 地图点位；指标单位按原数据字典，采样时间与土层须核验；非微生物配对样本',
            'source_file':f'Soilmate {request.res} km SQLite 点位库'}

def context_for(request):
    try:return public_context(request.microbial_id,request.module_id)
    except (ValueError,StopIteration) as exc:raise HTTPException(400,str(exc))

@router.get('/catalog')
def catalog():
    samples,_=read_ko_matrix(ROOT/'N_cycle_ko_abun.tsv')
    modules=json.loads((ROOT/'pathway_definitions_kegg.json').read_text(encoding='utf-8'))['modules']
    return {'samples':samples,'modules':[{'id':m['module_id'],'name':m['name'],'source_url':m['source_url']} for m in modules],
            'pairing':'公开 KO 样本与 Soilmate 地图点位无可靠样本级配对'}

@router.post('/analyze')
def analyze(request:ResearchRequest):return {'soil':soil_at(request),'context':context_for(request)}

@router.post('/action')
def action(request:ResearchRequest):
    soil_at(request)
    return next_action(context_for(request),request.completed)

@router.post('/execute')
def execute(request:ResearchRequest):
    soil_at(request)
    try:return execute_action(context_for(request),request.action)
    except ValueError as exc:raise HTTPException(400,str(exc))

@router.post('/report',response_class=PlainTextResponse)
def report(request:ResearchRequest):
    soil=soil_at(request);context=context_for(request);decision=next_action(context,request.completed)
    execution=execute_action(context,request.action) if request.action else None
    return study_report(soil,context,decision,execution)

