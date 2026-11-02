"""Auditable soil-to-microbial research flow; no biological claims from KO presence alone."""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[3] / 'data' / 'scientific'

def soil_records():
    path = ROOT / 'soilmate_soil_records.csv'
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def public_context(sample_id, module_id):
    from .cnps_adapter import read_ko_matrix
    from .pipeline import stage_status
    samples, matrix = read_ko_matrix(ROOT / 'N_cycle_ko_abun.tsv')
    modules = json.loads((ROOT / 'pathway_definitions_kegg.json').read_text(encoding='utf-8'))['modules']
    if sample_id not in samples: raise ValueError('公开 KO 样本不存在')
    module = next((m for m in modules if m['module_id'] == module_id), None)
    if module is None: raise ValueError('通路模块不存在')
    stages = [stage_status(s, matrix, sample_id, 0.0) for s in module['stages']]
    observed = sum(s['any_route_complete'] for s in stages)
    unknown = sorted({ko for s in stages for ko in s['kos_not_in_matrix']})
    present = sorted({ko for s in stages for a in s['alternatives'] for ko in a['route_kos'] if ko in matrix and matrix[ko].get(sample_id,0)>0})
    status = '存在相关线索' if observed else ('数据不足，无法判断' if unknown else '当前未检出')
    gaps = ['缺少样本级测序深度与质控', '缺少逐条注释可信度及数据库版本', '土壤和微生物样本未核验配对']
    if unknown or observed < len(stages): gaps.insert(0, '需核验通路关键步骤及输入矩阵过滤规则')
    return {'sample_id':sample_id,'module_id':module_id,'module_name':module['name'],
            'source_url':module['source_url'],'definition':module['definition'],
            'data_source':'CNPS.cycle 官方仓库已处理 KO 丰度表（公开数据）',
            'source_type':'公开数据；非试验田数据；非原始 FASTQ',
            'stages':stages,'observed_stages':observed,'total_stages':len(stages),
            'observed_kos':present,'kos_not_in_matrix':unknown,'status':status,
            'detectability_probability':None,'support_probability':None,
            'reason':'可描述输入表中的 KO 与模块步骤；缺少测序及注释质量，不能估计检出能力或判定真实活性。',
            'gaps':gaps,'sample_paired':False}

ACTION_META = {
    'CHECK_QC': ('检查数据质量','获取样本级测序深度、读长、过滤与质控记录',2,0),
    'REANNOTATE': ('核验功能注释','核对 KO 命中、参考库版本与注释可信度',3,1),
    'CHECK_PATHWAY': ('检查通路关键步骤','按 KEGG 模块公式复核缺失步骤和上游过滤',1,0),
    'SEARCH_SOURCES': ('检索文献与数据库','查看本地已登记的 KEGG 与 CNPS.cycle 来源',1,0),
    'VERIFY_PAIRING': ('核验样本配对','检查样本 ID、时间、地点、土层是否对应',2,0),
    'STOP_AND_REQUEST': ('停止推断并提出补测','保留缺口清单，请求缺失的原始记录或独立验证',0,0),
}

def next_action(context, completed=()):
    completed=set(completed)
    gaps=context['gaps']
    priorities=[]
    if any('测序深度' in x for x in gaps): priorities.append(('CHECK_QC',5))
    if any('通路关键' in x for x in gaps): priorities.append(('CHECK_PATHWAY',4))
    if any('注释' in x for x in gaps): priorities.append(('REANNOTATE',4))
    if not context['sample_paired']: priorities.append(('VERIFY_PAIRING',4))
    priorities.append(('SEARCH_SOURCES',2))
    candidates=[]
    for action,benefit in priorities:
        label,detail,cost,risk=ACTION_META[action]
        candidates.append({'action':action,'label':label,'benefit':benefit,'cost':cost,'risk':risk,
                           'score':round(benefit/(cost+1)-0.25*risk,2), 'completed':action in completed})
    remaining=[c for c in candidates if not c['completed']]
    # Quality gates override utility ranking: no probability inference without QC.
    chosen=next((c for c in remaining if c['action']=='CHECK_QC'),None)
    if chosen is None: chosen=max(remaining,key=lambda c:c['score']) if remaining else None
    if chosen is None:
        label,detail,_,_=ACTION_META['STOP_AND_REQUEST']
        chosen={'action':'STOP_AND_REQUEST','label':label,'benefit':0,'cost':0,'risk':0,'score':0,'completed':False}
    reason=ACTION_META[chosen['action']][1]
    if chosen['action']=='CHECK_QC': reason+='；QC 缺失是检出能力判断的前置门槛。'
    return {'chosen':chosen,'reason':reason,'candidates':candidates,
            'baseline_action':'CHECK_PATHWAY', 'baseline_note':'固定通路核验基线；不保证适合每种缺口',
            'before':{'status':context['status'],'open_gaps':len(gaps)}}

def execute_action(context, action):
    if action not in ACTION_META: raise ValueError('未知动作')
    if action=='CHECK_PATHWAY':
        result=f"已复核 {context['module_id']} 的 {context['total_stages']} 个步骤；{context['observed_stages']} 个步骤在输入表中有完整 KO 组合。"
        state='执行成功：完成本地结构核验；外部生物学判断仍受 QC 限制'
    elif action=='SEARCH_SOURCES':
        result=f"已定位 KEGG 模块定义：{context['source_url']}；公开 KO 数据来源：CNPS.cycle。"
        state='执行成功：仅返回本地登记来源，未进行实时联网检索'
    else:
        result=ACTION_META[action][1]+'；当前包内没有完成该动作所需的独立记录。'
        state='需要补充数据：已生成明确的收集任务'
    return {'action':action,'state':state,'result':result,
            'after':{'status':context['status'],'open_gaps':len(context['gaps']),
                     'note':'没有新证据进入系统，因此科学判断未改变。'}}

def study_report(soil, context, action=None, execution=None):
    measures=', '.join(f'{k}={soil.get(k) or "缺失"}' for k in ('soil_ph','AN','TN','soil_soc','EC'))
    return '\n'.join(['# 壤脉天玑｜研究流程报告','',
      '## 1. 土壤健康状态',f"Soilmate 点位/记录 {soil['record_id']}；{measures}。原始单位与采样元数据未完全核验，不作健康等级判断。AN 来源：{soil.get('AN_source','未提供')}。AN 若来自研究预览图层，其单位与采样来源待核，不用于指标诊断。",'',
      '## 2. 研究问题','氮素状态与微生物过程之间是否存在可进一步检验的线索？当前数据能支持到什么程度？','',
      '## 3. 微生物基因与通路',f"公开数据样本 {context['sample_id']}；{context['module_id']} {context['module_name']}。输入表中 {context['observed_stages']}/{context['total_stages']} 个步骤有完整 KO 组合。",f"来源：{context['source_url']}",'',
      '## 4. 当前判断',f"{context['status']}。{context['reason']}",'',
      '## 5. 尚未解决的问题',*['- '+x for x in context['gaps']],'',
      '## 6. 下一步行动',f"{action['chosen']['label']}：{action['reason']}" if action else '尚未选择',
      execution['state']+'；'+execution['result'] if execution else '', '',
      '## 7. 解释边界','土壤记录和公开微生物样本未配对，两类结果不能用于样本级相关或因果分析。KO 丰度不等于 RNA 表达、酶活、氮转化速率。'])


