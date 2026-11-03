<template>
  <section class="assessment-run" aria-labelledby="assessment-run-title">
    <header class="assessment-run-heading"><div><h2 id="assessment-run-title" tabindex="-1">{{ result ? '本次分析结果' : '研究任务' }}</h2><p>{{ statusLabel }}</p></div><button type="button" class="assessment-secondary-button" @click="$emit('back-input')">返回录入</button></header>
    <p v-if="demo" class="assessment-run-demo" role="status">流程审核示例 · 非实测、非模型推理。仅使用预置示例，未发送当前录入草稿。</p>
    <div v-if="busy" class="assessment-run-progress" role="status" aria-live="polite"><strong>{{ state.phase === 'submitting' ? state.stage || '准备提交' : state.task?.status === 'queued' ? '任务已排队' : state.task?.status === 'running' ? '正在分析当前检测记录' : '正在读取任务状态' }}</strong><p>进度以服务端返回为准，离开页面不会取消服务端任务。</p><ul v-if="state.task?.agent_tasks?.length"><li v-for="agent in state.task.agent_tasks" :key="agent.id">{{ agent.summary }} · {{ taskLabel(agent.status) }}</li></ul><button v-if="state.taskId" type="button" class="assessment-secondary-button" @click="controller.pause()">暂停自动刷新</button></div>
    <div v-if="state.error" class="assessment-run-error" role="alert"><h3>暂时无法继续</h3><p>{{ state.error.message }}</p><ul v-if="state.error.fields?.length"><li v-for="(field,i) in state.error.fields" :key="i">{{ field.path }}：{{ field.message }}</li></ul><p v-if="state.error.requestId">请求编号：{{ state.error.requestId }}</p><a v-if="state.error.status===401" :href="loginHref">重新登录并返回</a><button v-else-if="state.error.retryable" type="button" class="assessment-secondary-button" @click="controller.retry()">{{ state.taskId ? '重新查询原任务' : '重试原提交' }}</button></div>
    <div v-if="state.phase==='paused'" class="assessment-run-progress"><h3>{{ state.taskId ? '已暂停自动刷新' : '有尚未完成的提交' }}</h3><p>{{ state.taskId ? '继续查询原任务，不会创建新任务。' : '使用原提交标识继续，防止连接中断造成重复记录。' }}</p><button type="button" class="assessment-primary-button" @click="controller.resume()">继续{{ state.taskId ? '查询' : '提交' }}</button></div>
    <div v-if="failed" class="assessment-run-error" role="alert"><h3>{{ state.task.status==='interrupted' ? '任务已中断' : '本次任务未完成' }}</h3><p>{{ state.task.error?.message || '服务端未形成可展示结果，原检测记录保留。' }}</p><button v-if="state.measurementId" type="button" class="assessment-primary-button" @click="controller.retry()">用原检测记录重新分析</button><p>重新分析会创建新任务，不改写原检测值。</p></div>
    <details class="assessment-run-input"><summary>查看本次输入与任务标识</summary>
    <dl v-if="state.sessionId || state.taskId" class="assessment-run-meta"><div v-if="state.sessionId"><dt>研究会话</dt><dd>{{ state.sessionId }}</dd></div><div v-if="state.taskId"><dt>当前任务</dt><dd>{{ state.taskId }}</dd></div><div v-if="state.measurementId"><dt>检测记录</dt><dd>{{ state.measurementId }}</dd></div></dl>
    <section v-if="state.measurement?.values || state.snapshot?.measurement?.values" class="assessment-run-section"><h3>本次提交的检测值</h3><div class="assessment-source-scroll"><table><thead><tr><th>指标</th><th>检测值</th><th>报告单位</th></tr></thead><tbody><tr v-for="value in state.measurement?.values || state.snapshot.measurement.values" :key="value.indicator_code"><th scope="row">{{ indicatorName(value.indicator_code) }}</th><td>{{ value.value }}</td><td>{{ value.unit || '无量纲' }}</td></tr></tbody></table></div></section>
    <p v-if="state.inputError" class="assessment-run-limits">{{ state.inputError }}</p>
    </details>
    <template v-if="result">
      <div v-if="state.task.status==='partial'" class="assessment-run-limits">本次只形成有限范围的结果，已结束等待。请结合下方证据缺口阅读。</div>
      <section class="assessment-run-summary"><h3>{{ result.assessment.summary }}</h3><p>{{ scopeLabel }}</p><p v-if="result.assessment.composite_score != null" class="assessment-run-score">综合分数 <strong>{{ result.assessment.composite_score }}</strong></p><p v-else>未形成综合分数</p><p>{{ result.assessment.score_explanation }}</p></section>
      <section class="assessment-run-section"><h3>指标判读</h3><p>已测 {{ new Set(result.coverage?.measured_codes || []).size }} 项指标；缺失项不作为零值。</p><article v-for="item in result.assessment.indicator_assessments || []" :key="item.indicator_code"><h4>{{ indicatorName(item.indicator_code) }} <span>{{ indicatorStatus(item.status) }}</span></h4><p>{{ item.explanation }}</p><ul class="assessment-run-evidence"><li v-for="(evidence,i) in item.evidence || []" :key="i">{{ evidence.label }} · {{ evidence.source_id }}</li></ul></article></section>
      <section v-if="result.problems?.length" class="assessment-run-section"><h3>问题与待核实事项</h3><article v-for="problem in result.problems" :key="problem.id"><h4>{{ problem.title }}</h4><p><b>观察事实：</b>{{ problem.observation }}</p><div v-if="problem.possible_causes?.length"><b>可能成因</b><ul><li v-for="cause in problem.possible_causes" :key="cause">{{ cause }}</li></ul></div><div v-if="problem.verification_needed?.length"><b>仍需核实</b><ul><li v-for="item in problem.verification_needed" :key="item">{{ item }}</li></ul></div><ul class="assessment-run-evidence"><li v-for="(evidence,i) in problem.evidence || []" :key="i">{{ evidence.label }} · {{ evidence.source_id }}</li></ul></article></section>
      <section v-if="result.decisions?.length" class="assessment-run-section"><h3>建议与适用条件</h3><article v-for="decision in result.decisions" :key="decision.id"><h4>{{ decision.action }}</h4><p>{{ decision.reason }}</p><ul><li v-for="condition in decision.conditions || []" :key="condition">{{ condition }}</li></ul><p v-if="decision.verification_goal">核对目标：{{ decision.verification_goal }}</p></article></section>
      <section class="assessment-run-section"><h3>证据缺口与限制</h3><ul><li v-for="(item,i) in [...(result.gaps || []), ...(result.limitations || [])]" :key="i">{{ item }}</li></ul><dl class="assessment-run-meta"><div><dt>模型</dt><dd>{{ result.model_info?.model_name || '未登记' }}</dd></div><div><dt>模型版本</dt><dd>{{ result.model_info?.model_version || '未登记' }}</dd></div><div><dt>规则版本</dt><dd>{{ result.model_info?.rule_version || '未登记' }}</dd></div></dl></section>
    </template>
    <section v-if="history.length" class="assessment-run-section"><h3>最近研究任务</h3><p>本浏览器保存任务入口；结果仍从所属账号的服务端读取。</p><ul class="assessment-run-history"><li v-for="item in history" :key="item.taskId"><button type="button" :disabled="busy || item.taskId===state.taskId" @click="restoreHistory(item)">{{ item.sample || '检测样本' }} · {{ taskLabel(item.status) }}<small>{{ item.time }}</small></button></li></ul></section>
    <p v-if="state.storageFailed" role="status" class="assessment-run-limits">浏览器暂存不可用，请保留当前任务地址，刷新后可按任务标识查询。</p>
    <p v-if="!busy && state.phase==='idle'" class="assessment-run-empty">尚未发起本次分析。请返回录入页核对检测值。</p>
  </section>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { createRunController } from './runController.js'
import { createAssessmentApi } from './runClient.js'
import { reviewIndicators } from './measurementDraft.js'
import './run.css'
const props=defineProps({ account:{type:Object,default:null}, csrfToken:{type:String,default:''}, submission:{type:Object,default:null}, preview:{type:Boolean,default:false} })
const emit=defineEmits(['back-input','run-context','submission-consumed'])
const params=new URLSearchParams(location.search)
const demo=import.meta.env.DEV && props.preview && params.has('assessmentDemo')
const storagePrefix='soilmate.assessment.run.v1.'+(demo?'demo':props.preview?'preview':props.account?.id || 'guest')
let store
try{store=sessionStorage}catch{store=null}
const state=ref({phase:'idle'}),history=ref([])
try{const saved=JSON.parse(localStorage.getItem(storagePrefix+'.history') || '[]');history.value=Array.isArray(saved)?saved.filter(item=>item && typeof item.taskId==='string' && typeof item.sessionId==='string').slice(0,20):[]}catch{history.value=[]}
const taskLabel=value=>({queued:'排队中',running:'进行中',completed:'已完成',partial:'有限结果',failed:'失败',interrupted:'已中断'})[value] || '等待查询'
const busy=computed(()=>['submitting','polling'].includes(state.value.phase))
const failed=computed(()=>state.value.phase==='settled' && ['failed','interrupted'].includes(state.value.task?.status))
const result=computed(()=>['completed','partial'].includes(state.value.task?.status) ? state.value.task.result?.analysis : null)
const statusLabel=computed(()=>state.value.task ? taskLabel(state.value.task.status) : state.value.phase==='error' ? '当前未获得有效结果' : state.value.phase==='submitting' ? '正在保存与提交' : '按任务标识恢复')
const scopeLabel=computed(()=>({single_indicator:'判读范围：单项指标',partial_indicators:'判读范围：部分指标',recommended_set:'判读范围：推荐指标集'})[result.value?.assessment.scope] || '判读范围以结果说明为准')
const indicatorName=code=>reviewIndicators.find(item=>item.code===code)?.name || code
const indicatorStatus=value=>({needs_attention:'需关注',within_reference:'在参考范围内',uncertain:'待核实',descriptive_only:'仅作描述'})[value] || value
const loginHref=computed(()=>{state.value;return '/account/index.html?next='+encodeURIComponent(location.pathname+location.search)})
function changed(value){
 state.value=value
 if(!demo && value.sessionId){const url=new URL(location.href);url.searchParams.set('assessmentSession',value.sessionId);if(value.taskId)url.searchParams.set('assessmentTask',value.taskId);else url.searchParams.delete('assessmentTask');historyReplace(url)}
 if(value.taskId && !demo){
  const item={taskId:value.taskId,sessionId:value.sessionId,sample:value.snapshot?.measurement.sample_alias || '检测样本',status:value.task?.status || 'queued',time:new Date().toLocaleString('zh-CN',{hour12:false})}
  history.value=[item,...history.value.filter(old=>old.taskId!==item.taskId)].slice(0,20)
  try{localStorage.setItem(storagePrefix+'.history',JSON.stringify(history.value))}catch{}
 }
 emit('run-context',value)
}
function historyReplace(url){window.history.replaceState(window.history.state,'',url.pathname+url.search+url.hash)}
const realRequest=createAssessmentApi({csrf:()=>props.csrfToken})
let demoTransport
const request=(...args)=>demo ? demoTransport(...args) : realRequest(...args)
const controller=createRunController({request,storage:store,storageKey:storagePrefix,onChange:changed,pollMs:demo?600:2000})
function restoreHistory(item){controller.restore(item.sessionId,item.taskId)}
function historyChanged(){if(demo)return;const params=new URLSearchParams(location.search);const session=params.get('assessmentSession'),task=params.get('assessmentTask') || '';if(session && (session!==state.value.sessionId || task!==state.value.taskId))controller.restore(session,task)}
onMounted(async()=>{
 document.getElementById('assessment-run-title')?.focus({preventScroll:true})
 window.addEventListener('soilmate:history-commit',historyChanged)
 if(demo){const {demoSnapshot,demoRequest}=await import('./runDemo.js');demoTransport=demoRequest(params.get('assessmentDemo'));controller.start(demoSnapshot);return}
 if(props.preview)return
 if(props.submission){controller.start(props.submission);emit('submission-consumed');return}
 const saved=controller.load(),session=params.get('assessmentSession'),task=params.get('assessmentTask') || ''
 if(session){if(saved.sessionId===session && saved.taskId===task && saved.taskId)controller.resume();else controller.restore(session,task);return}
 if(saved.taskId)controller.resume()
})
onBeforeUnmount(()=>{controller.dispose();window.removeEventListener('soilmate:history-commit',historyChanged)})
</script>
