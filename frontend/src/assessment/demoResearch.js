import { reviewIndicators } from './measurementDraft.js'
import { AssessmentError } from './runClient.js'
export const DEMO_KEY='soilmate.demo.research.v1'
const copy=value=>JSON.parse(JSON.stringify(value))
const uid=kind=>'demo-'+kind+'-'+(globalThis.crypto?.randomUUID?.() || Date.now()+'-'+Math.random().toString(36).slice(2))
const now=()=>new Date().toISOString()
const empty=()=>({version:1,sessions:{},measurements:{},tasks:{},feedback:{},chats:{},keys:{}})
export function demoData(storage=globalThis.localStorage){
 try{const data=JSON.parse(storage?.getItem(DEMO_KEY)||'null');return data?.version===1 && ['sessions','measurements','tasks','feedback','chats','keys'].every(key=>data[key] && typeof data[key]==='object' && !Array.isArray(data[key])) ? data : empty()}
 catch{throw new AssessmentError('无法读取演示存储，请允许浏览器存储或清空演示记录后重试。',{retryable:false})}
}
function save(data,storage){
 try{storage.setItem(DEMO_KEY,JSON.stringify(data))}catch{throw new AssessmentError('演示记录未能保存，浏览器存储可能已满。原实际账号数据不受影响。',{retryable:false})}
 if(typeof window!=='undefined')window.dispatchEvent(new Event('soilmate:demo-change'))
}
function find(collection,id){const value=collection[id];if(!value)throw new AssessmentError('找不到这条演示记录，请返回演示记录列表。',{status:404,retryable:false});return value}
const name=code=>reviewIndicators.find(item=>item.code===code)?.name || code
function analysisFor(data,task){
 const session=find(data.sessions,task.session_id),measurement=find(data.measurements,task.measurement_ids[0]),values=measurement.values
 const evidence=values.map(value=>({source_type:'measurement',source_id:measurement.id,indicator_code:value.indicator_code,label:'演示录入：'+name(value.indicator_code)}))
 const gaps=['本次未调用微调模型、N+X 或正式评分规则。']
 if(!measurement.sampling_date)gaps.push('演示记录未填写采样日期。')
 if(values.some(value=>!value.method))gaps.push('部分指标未填写检测方法。')
 return {id:uid('analysis'),mode:session.mode,measurement_ids:[measurement.id],input_snapshot:evidence,coverage:{recommended_codes:[],measured_codes:values.map(value=>value.indicator_code),missing_codes:[],extra_codes:values.map(value=>value.indicator_code)},assessment:{summary:`演示流程已完成：${measurement.sample_alias}，已录入 ${values.length} 项指标。`,scope:values.length===1?'single_indicator':'partial_indicators',composite_score:null,score_explanation:'本页演示产品流程，未计算真实土壤健康分数，也不判定肥力或污染等级。',indicator_assessments:values.map((value,i)=>({indicator_code:value.indicator_code,status:'descriptive_only',explanation:`演示录入回显：${value.value} ${value.unit || '无量纲'}。仅保留输入，不应用科学阈值。`,evidence:[evidence[i]]}))},problems:[{id:uid('problem'),title:'正式判读所需条件仍待核实',observation:`当前演示共收到 ${values.length} 项指标，真实模型与评分规则未执行。`,possible_causes:[],priority:'undetermined',evidence,verification_needed:gaps}],decisions:[{id:uid('decision'),action:'核对检测记录并补充背景资料',reason:'用于展示从结果到后续记录的产品路径。',conditions:['演示建议不代表农艺处方，不提供具体施用剂量。'],timing:null,verification_goal:'确认单位、方法、日期与样本身份。',evidence}],gaps,optional_tests:[],next_plan_id:session.mode==='deep'?session.id+'-plan':null,model_info:{model_name:'产品演示脚本（未调用真实模型）',model_version:'demo-1.0',is_fine_tuned:false,rule_version:'demo-ui-1.0'},limitations:['所有进度、解释和报告均为模拟输出，不作为研究结论。','演示输入只在当前浏览器保存，不上传服务器。'],created_at:now()}
}
export function createDemoResearch({storage=globalThis.localStorage,scenario='completed'}={}){
 let context={}
 const request=async(method,path,body,key)=>{
  const data=demoData(storage),wrap=value=>({data:copy(value),origin:'mock',requestId:uid('request')})
  const fingerprint=JSON.stringify(body||null),keyId=method+':'+path+':'+key
  if(method==='POST' && key && data.keys[keyId]){
   const previous=data.keys[keyId];if(previous.fingerprint!==fingerprint)throw new AssessmentError('同一演示提交标识对应的内容发生变化。',{status:409,retryable:false})
   return wrap(previous.value)
  }
  let value
  if(method==='GET' && path==='/indicators')value={items:reviewIndicators.map(item=>({...item,units:item.units,unit_required:!!item.units.length})),dictionary_version:'demo-ui-1.0'}
  else if(method==='POST' && path==='/sessions'){
   const id=uid('session');value={...body,id,measurement_ids:[],latest_task_id:null,created_at:now(),demo_context:copy(context),checkpoints:body.mode==='deep'?[{id:uid('checkpoint'),name:'基线记录',status:'completed'},{id:uid('checkpoint'),name:'补充观察',status:'planned'},{id:uid('checkpoint'),name:'后续复测',status:'planned'}]:[]};data.sessions[id]=value
  }else if(method==='POST' && path==='/measurements'){
   const session=find(data.sessions,body.session_id),id=uid('measurement');value={...body,id,warnings:['演示输入，未作为真实科研数据验证。'],created_at:now()};data.measurements[id]=value;session.measurement_ids.push(id)
  }else if(method==='POST' && path==='/tasks'){
   const session=find(data.sessions,body.session_id)
   for(const id of body.measurement_ids || [])if(find(data.measurements,id).session_id!==session.id)throw new AssessmentError('演示检测记录不属于当前会话。',{retryable:false})
   const id=uid('task'),previous=session.latest_task_id&&data.tasks[session.latest_task_id]
   data.tasks[id]={...body,task_id:id,status:'queued',current_stage:'演示：排队中',agent_tasks:[],result:null,error:null,created_at:now(),updated_at:now(),reads:0,scenario:previous && ['failed','interrupted'].includes(previous.status)?'completed':scenario}
   session.latest_task_id=id;value={task_id:id,type:body.type,status:'queued'}
  }else if(method==='GET' && path.startsWith('/sessions/'))value=find(data.sessions,decodeURIComponent(path.split('/').at(-1)))
  else if(method==='GET' && path.startsWith('/measurements/'))value=find(data.measurements,decodeURIComponent(path.split('/').at(-1)))
  else if(method==='GET' && path.startsWith('/tasks/')){
   const task=find(data.tasks,decodeURIComponent(path.split('/').at(-1)))
   if(!['completed','partial','failed','interrupted'].includes(task.status)){
    task.reads++;task.status=task.reads===1?'queued':task.reads===2?'running':task.scenario
    task.current_stage=task.status==='queued'?'演示：排队中':task.status==='running'?'演示：整理输入与模拟解释':'演示：本轮结束';task.updated_at=now()
    if(task.type==='deep_analysis')task.agent_tasks=['data_check','diagnosis','agronomy','review'].map(role=>({id:task.task_id+'-'+role,role,status:task.status==='running'?'running':task.status==='queued'?'queued':'completed',summary:'模拟角色进度：'+role,error:null}))
    if(['completed','partial'].includes(task.status))task.result={kind:'analysis',analysis:analysisFor(data,task)}
    if(['failed','interrupted'].includes(task.status))task.error={code:task.status==='failed'?'TASK_FAILED':'TASK_INTERRUPTED',message:'这是用于演示恢复操作的模拟'+(task.status==='failed'?'失败。':'中断。'),fields:[],retryable:true}
   }
   value=task
  }else throw new AssessmentError('演示模式不支持此操作。',{retryable:false})
  if(method==='POST' && key)data.keys[keyId]={fingerprint,value:copy(value)}
  save(data,storage);return wrap(value)
 }
 request.prepare=snapshot=>{
  context=copy(snapshot.demo_context || {})
  const prepared=copy(snapshot)
  if(prepared.session.mode==='deep'){prepared.session.field_id=uid('field');prepared.session.cycle_id=uid('cycle')}
  return prepared
 }
 return request
}
export function demoSessions(storage=globalThis.localStorage){const data=demoData(storage);return Object.values(data.sessions).sort((a,b)=>b.created_at.localeCompare(a.created_at)).map(session=>({...session,measurement:data.measurements[session.measurement_ids.at(-1)],task:data.tasks[session.latest_task_id]}))}
export function demoContext(sessionId,taskId='',storage=globalThis.localStorage){
 const data=demoData(storage),session=data.sessions[sessionId];if(!session)return null
 const task=data.tasks[taskId || session.latest_task_id],measurement=data.measurements[task?.measurement_ids[0] || session.measurement_ids.at(-1)]
 return {session,task,measurement,feedback:Object.values(data.feedback).filter(item=>item.session_id===sessionId)}
}
export function addDemoFeedback(sessionId,text,checkpointId='',storage=globalThis.localStorage){
 const data=demoData(storage),session=find(data.sessions,sessionId)
 if(!text.trim())throw new Error('请填写本轮观察或补充信息。')
 const entry={id:uid('feedback'),session_id:sessionId,text:text.trim().slice(0,2000),checkpoint_id:checkpointId,created_at:now()};data.feedback[entry.id]=entry
 if(checkpointId){const point=session.checkpoints.find(item=>item.id===checkpointId);if(point)point.status='completed'}
 save(data,storage);return entry
}
export async function rerunDemo(sessionId,storage=globalThis.localStorage){
 const data=demoData(storage),session=find(data.sessions,sessionId),body={type:session.mode==='deep'?'deep_analysis':'quick_analysis',session_id:sessionId,measurement_ids:[session.measurement_ids.at(-1)]}
 if(session.mode==='deep'){body.field_id=session.field_id;body.cycle_id=session.cycle_id}
 const response=await createDemoResearch({storage})('POST','/tasks',body,uid('key'))
 return {sessionId,taskId:response.data.task_id}
}
export function demoChatMessages(key,storage=globalThis.localStorage){return demoData(storage).chats[key] || []}
export function askDemo(query,sessionId='',taskId='',thread='standalone',storage=globalThis.localStorage){
 const data=demoData(storage),key=sessionId || thread,context=demoContext(sessionId,taskId,storage),values=context?.measurement?.values || [],sample=context?.measurement?.sample_alias || '未关联样本'
 let answer
 if(/缺|补|证据/.test(query))answer=context?.task?.result?.analysis.gaps.join('\n') || '演示中可以先录入指标，再核对日期、土层、方法和样本身份。真实模型尚未执行。'
 else if(/建议|接下来|怎么办|改良/.test(query))answer='模拟说明：先核对检测单位和方法，再到“报告与记录”补记观察。当前未运行农艺推荐模型，不提供具体施用剂量。'
 else if(/为什么|原因/.test(query))answer='模拟说明：当前记录只能回显输入，不能凭单次测量确定成因。请在依据页检查原始值和缺失信息。'
 else if(/MDS|最小数据集/i.test(query))answer='模拟说明：最小数据集用于用较少指标表征研究对象。本演示只展示流程，未执行真实指标筛选。'
 else answer=context?`当前演示关联“${sample}”，已录入 ${values.length} 项指标：\n${values.map(value=>`${name(value.indicator_code)}：${value.value} ${value.unit || '无量纲'}`).join('\n')}\n这些是演示输入回显，未生成真实健康等级。`:'这是模拟研究助手。可从健康研究录入样本，查看模拟分析、证据和报告；当前未调用微调模型。'
 const messages=data.chats[key] || []
 messages.push({id:uid('message'),role:'user',text:query.slice(0,4000)},{id:uid('message'),role:'assistant',text:answer})
 data.chats[key]=messages.slice(-50);save(data,storage);return copy(data.chats[key])
}
export function demoReportText(sessionId,taskId='',storage=globalThis.localStorage){
 const context=demoContext(sessionId,taskId,storage);if(!context?.task?.result)throw new Error('尚无已完成的模拟报告。')
 const {session,measurement,task,feedback}=context,analysis=task.result.analysis
 return ['Soilmate 演示报告（模拟输出，不作科研或诊断结论）',`样本：${measurement.sample_alias}`,`模式：${session.mode==='deep'?'深度分析演示':'快速试用演示'}`,`记录：${task.task_id}`,`生成时间：${analysis.created_at}`,'\n演示输入',...measurement.values.map(value=>`${name(value.indicator_code)}：${value.value} ${value.unit || '无量纲'}`),'\n模拟结果',analysis.assessment.summary,'综合分数：未计算','\n证据缺口',...analysis.gaps,'\n补充记录',...feedback.map(item=>`${item.created_at} ${item.text}`),'\n未调用 Qwen3-8B、N+X 或正式评分规则。演示数据仅保存在本浏览器。'].join('\n')
}
