<template>
  <section class="assessment-run" aria-labelledby="assessment-run-title">
    <header class="assessment-run-heading"><div><h2 id="assessment-run-title" tabindex="-1">{{ heading }}</h2><p>{{ statusLabel }}</p></div><button type="button" class="assessment-secondary-button" @click="$emit('back-input')">返回录入</button></header>
    <p v-if="demo" class="assessment-run-demo" role="status">流程审核示例 · 非实测、非模型推理。仅使用预置示例，未发送当前录入草稿。</p>

    <div v-if="busy" class="assessment-run-progress" role="status" aria-live="polite"><strong>{{ state.phase === 'submitting' ? state.stage || '准备提交' : state.task?.status === 'queued' ? '任务已排队' : state.task?.status === 'running' ? '正在分析当前检测记录' : '正在读取任务状态' }}</strong><p>进度以服务端返回为准，离开页面不会取消服务端任务。</p><ul v-if="state.task?.agent_tasks?.length"><li v-for="agent in state.task.agent_tasks" :key="agent.id">{{ agent.summary }} · {{ taskLabel(agent.status) }}</li></ul><button v-if="state.taskId" type="button" class="assessment-secondary-button" @click="controller.pause()">暂停自动刷新</button></div>
    <div v-if="state.error" class="assessment-run-error" role="alert"><h3>暂时无法继续</h3><p>{{ state.error.message }}</p><ul v-if="state.error.fields?.length"><li v-for="(field,i) in state.error.fields" :key="i">{{ field.path }}：{{ field.message }}</li></ul><p v-if="state.error.requestId">请求编号：{{ state.error.requestId }}</p><a v-if="state.error.status===401" :href="loginHref">重新登录并返回</a><button v-else-if="state.error.retryable" type="button" class="assessment-secondary-button" @click="controller.retry()">{{ state.taskId ? '重新查询原任务' : '重试原提交' }}</button></div>
    <div v-if="state.phase==='paused'" class="assessment-run-progress"><h3>{{ state.taskId ? '已暂停自动刷新' : '有尚未完成的提交' }}</h3><p>{{ state.taskId ? '继续查询原任务，不会创建新任务。' : '使用原提交标识继续，防止连接中断造成重复记录。' }}</p><button type="button" class="assessment-primary-button" @click="controller.resume()">继续{{ state.taskId ? '查询' : '提交' }}</button></div>
    <div v-if="failed" class="assessment-run-error" role="alert"><h3>{{ state.task.status==='interrupted' ? '任务已中断' : '本次任务未完成' }}</h3><p>{{ state.task.error?.message || '服务端未形成可展示结果，原检测记录保留。' }}</p><button v-if="state.measurementId" type="button" class="assessment-primary-button" @click="controller.retry()">用原检测记录重新分析</button><p>重新分析会创建新任务，不改写原检测值。</p></div>

    <template v-if="result">
      <section v-if="view === 'analysis'" class="assessment-run-summary"><h3>{{ result.assessment.summary }}</h3><p>{{ scopeLabel }}</p><p v-if="result.assessment.composite_score != null" class="assessment-run-score">综合分数 <strong>{{ result.assessment.composite_score }}</strong></p><p v-else>未形成综合分数</p><p>{{ result.assessment.score_explanation }}</p></section>

      <template v-if="view === 'analysis'">
        <section class="assessment-run-section"><h3>指标判读</h3><p>已测 {{ new Set(result.coverage?.measured_codes || []).size }} 项指标；缺失项不作为零值。</p><article v-for="item in result.assessment.indicator_assessments || []" :key="item.indicator_code"><h4>{{ indicatorName(item.indicator_code) }} <span>{{ indicatorStatus(item.status) }}</span></h4><p>{{ item.explanation }}</p><ul class="assessment-run-evidence"><li v-for="(evidence,i) in item.evidence || []" :key="i">{{ evidence.label }} · {{ evidence.source_id }}</li></ul></article></section>
        <section v-if="result.problems?.length" class="assessment-run-section"><h3>问题与待核实事项</h3><article v-for="problem in result.problems" :key="problem.id"><h4>{{ problem.title }}</h4><p><b>观察事实：</b>{{ problem.observation }}</p><div v-if="problem.possible_causes?.length"><b>可能成因</b><ul><li v-for="cause in problem.possible_causes" :key="cause">{{ cause }}</li></ul></div><div v-if="problem.verification_needed?.length"><b>仍需核实</b><ul><li v-for="item in problem.verification_needed" :key="item">{{ item }}</li></ul></div><ul class="assessment-run-evidence"><li v-for="(evidence,i) in problem.evidence || []" :key="i">{{ evidence.label }} · {{ evidence.source_id }}</li></ul></article></section>
        <section v-if="result.decisions?.length" class="assessment-run-section"><h3>建议与适用条件</h3><article v-for="decision in result.decisions" :key="decision.id"><h4>{{ decision.action }}</h4><p>{{ decision.reason }}</p><ul><li v-for="condition in decision.conditions || []" :key="condition">{{ condition }}</li></ul><p v-if="decision.verification_goal">核对目标：{{ decision.verification_goal }}</p></article></section>
        <section class="assessment-run-section"><h3>适用范围与限制</h3><ul><li v-for="(item,i) in [...(result.gaps || []), ...(result.limitations || [])]" :key="i">{{ item }}</li></ul><dl class="assessment-run-meta"><div><dt>模型</dt><dd>{{ result.model_info?.model_name || '未登记' }}</dd></div><div><dt>模型版本</dt><dd>{{ result.model_info?.model_version || '未登记' }}</dd></div><div><dt>规则版本</dt><dd>{{ result.model_info?.rule_version || '未登记' }}</dd></div></dl></section>
      </template>

      <template v-else-if="view === 'evidence'">
        <section class="assessment-run-section"><h3>数据来源与本次输入</h3><p>所有结论均来自当前检测记录；未测指标不参与评分，也不作为零值。样本：{{ sampleLabel }}<span v-if="samplingDate"> · 采样 {{ samplingDate }}</span></p><div class="assessment-source-scroll"><table><thead><tr><th>指标</th><th>检测值</th><th>报告单位</th><th>检测方法</th></tr></thead><tbody><tr v-for="value in inputValues" :key="value.indicator_code"><th scope="row">{{ indicatorName(value.indicator_code) }}</th><td>{{ value.value }}</td><td>{{ value.unit || '无量纲' }}</td><td>{{ value.method || '未登记' }}</td></tr></tbody></table></div></section>
        <section class="assessment-run-section"><h3>指标判读依据</h3><article v-for="item in result.assessment.indicator_assessments || []" :key="item.indicator_code"><h4>{{ indicatorName(item.indicator_code) }} <span>{{ indicatorStatus(item.status) }}</span></h4><p>{{ item.explanation }}</p><ul class="assessment-run-evidence"><li v-for="(evidence,i) in item.evidence || []" :key="i">{{ evidence.label }} · {{ evidence.source_id }}</li></ul></article></section>
        <section class="assessment-run-section"><h3>适用范围与限制</h3><ul><li v-for="(item,i) in [...(result.gaps || []), ...(result.limitations || [])]" :key="i">{{ item }}</li></ul></section>
        <section class="assessment-run-section"><h3>运行版本</h3><dl class="assessment-run-meta"><div><dt>研究会话</dt><dd>{{ state.sessionId }}</dd></div><div><dt>当前任务</dt><dd>{{ state.taskId }}</dd></div><div><dt>检测记录</dt><dd>{{ state.measurementId }}</dd></div><div><dt>模型</dt><dd>{{ result.model_info?.model_name || '未登记' }}</dd></div><div><dt>模型版本</dt><dd>{{ result.model_info?.model_version || '未登记' }}</dd></div><div><dt>规则版本</dt><dd>{{ result.model_info?.rule_version || '未登记' }}</dd></div></dl></section>
      </template>

      <template v-else-if="view === 'report'">
        <section class="assessment-run-section assessment-report-card">
          <div class="assessment-report-head"><div><p class="assessment-report-kicker">土壤健康评价报告</p><h3>{{ sampleLabel }} · {{ cropLabel }}</h3><p class="assessment-report-sub">生成时间 {{ reportTime }} · 任务 {{ state.taskId }}</p></div><button type="button" class="assessment-primary-button" @click="downloadReport">下载评价报告 <span aria-hidden="true">↓</span></button></div>
          <dl class="assessment-report-facts"><div><dt>评价方式</dt><dd>{{ result.mode === 'deep' ? '深度分析' : '快速试用' }}</dd></div><div><dt>判读范围</dt><dd>{{ scopeLabel }}</dd></div><div v-if="samplingDate"><dt>采样日期</dt><dd>{{ samplingDate }}</dd></div><div><dt>已测指标</dt><dd>{{ (result.coverage?.measured_codes || []).length }} 项</dd></div><div v-if="result.assessment.composite_score != null"><dt>综合分数</dt><dd><strong>{{ result.assessment.composite_score }}</strong></dd></div><div><dt>规则版本</dt><dd>{{ result.model_info?.rule_version || '未登记' }}</dd></div></dl>
          <h4>结论摘要</h4><p>{{ result.assessment.summary }}</p><p>{{ result.assessment.score_explanation }}</p>
          <h4>优先核查项</h4>
          <ul v-if="result.problems?.length"><li v-for="problem in result.problems" :key="problem.id">{{ problem.title }}：{{ problem.observation }}</li></ul>
          <p v-else>本次未触发优先核查项；单一检测记录仍不能判断趋势。</p>
          <h4>建议与核对目标</h4>
          <ul><li v-for="decision in result.decisions || []" :key="decision.id">{{ decision.action }}{{ decision.verification_goal ? `（核对：${decision.verification_goal}）` : '' }}</li></ul>
          <h4>适用范围与限制</h4>
          <ul><li v-for="(item,i) in [...(result.gaps || []), ...(result.limitations || [])]" :key="i">{{ item }}</li></ul>
          <p class="assessment-report-foot">报告由当前任务结果生成，含检测记录、规则版本与限制声明；可按 Ctrl/Cmd + P 打印为 PDF。</p>
        </section>
      </template>
    </template>
    <p v-else-if="!busy && !failed && view !== 'analysis'" class="assessment-run-empty">任务结果读取中；请稍后在此页面查看。</p>

    <section v-if="view === 'analysis' && history.length" class="assessment-run-section"><h3>最近研究任务</h3><p>本浏览器保存任务入口；结果仍从所属账号的服务端读取。</p><ul class="assessment-run-history"><li v-for="item in history" :key="item.taskId"><button type="button" :disabled="busy || item.taskId===state.taskId" @click="restoreHistory(item)">{{ item.sample || '检测样本' }} · {{ taskLabel(item.status) }}<small>{{ item.time }}</small></button></li></ul></section>
    <p v-if="state.storageFailed" role="status" class="assessment-run-limits">浏览器暂存不可用，请保留当前任务地址，刷新后可按任务标识查询。</p>
    <p v-if="!busy && state.phase==='idle' && view === 'analysis'" class="assessment-run-empty">尚未发起本次分析。请返回录入页核对检测值。</p>
  </section>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { createRunController } from './runController.js'
import { createAssessmentApi } from './runClient.js'
import { reviewIndicators } from './measurementDraft.js'
import './run.css'
const props=defineProps({ account:{type:Object,default:null}, csrfToken:{type:String,default:''}, submission:{type:Object,default:null}, preview:{type:Boolean,default:false}, stage:{type:String,default:'analysis'}, initialRestore:{type:Object,default:null} })
const emit=defineEmits(['back-input','run-context','submission-consumed'])
const params=new URLSearchParams(location.search)
const demo=import.meta.env.DEV && props.preview && params.has('assessmentDemo')
const storagePrefix='soilmate.assessment.run.v1.'+(demo?'demo':props.preview?'preview':props.account?.id || 'guest')
let store
try{store=sessionStorage}catch{store=null}
const state=ref({phase:'idle'}),history=ref([])
try{const saved=JSON.parse(localStorage.getItem(storagePrefix+'.history') || '[]');history.value=Array.isArray(saved)?saved.filter(item=>item && typeof item.taskId==='string' && typeof item.sessionId==='string').slice(0,20):[]}catch{history.value=[]}
const view=computed(()=>['analysis','evidence','report'].includes(props.stage) ? props.stage : 'analysis')
const heading=computed(()=>({analysis:'本次分析结果',evidence:'依据与版本',report:'报告与记录'})[view.value])
const taskLabel=value=>({queued:'排队中',running:'进行中',completed:'已完成',partial:'有限结果',failed:'失败',interrupted:'已中断'})[value] || '等待查询'
const busy=computed(()=>['submitting','polling'].includes(state.value.phase))
const failed=computed(()=>state.value.phase==='settled' && ['failed','interrupted'].includes(state.value.task?.status))
const result=computed(()=>['completed','partial'].includes(state.value.task?.status) ? state.value.task.result?.analysis : null)
const inputValues=computed(()=>state.value.measurement?.values || state.value.snapshot?.measurement?.values || [])
const sampleLabel=computed(()=>state.value.measurement?.sample_alias || state.value.snapshot?.measurement?.sample_alias || '未命名样本')
const samplingDate=computed(()=>state.value.measurement?.sampling_date || state.value.snapshot?.measurement?.sampling_date || '')
const cropLabel=computed(()=>state.value.session?.crop_name || state.value.snapshot?.session?.crop_name || '作物未填写')
const reportTime=computed(()=>new Date().toLocaleString('zh-CN',{hour12:false}))
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
 emit('run-context',{...value})
}
function historyReplace(url){window.history.replaceState(window.history.state,'',url.pathname+url.search+url.hash)}
const realRequest=createAssessmentApi({csrf:()=>props.csrfToken})
let demoTransport
const request=(...args)=>demo ? demoTransport(...args) : realRequest(...args)
const controller=createRunController({request,storage:store,storageKey:storagePrefix,onChange:changed,pollMs:demo?600:2000})
function restoreHistory(item){controller.restore(item.sessionId,item.taskId)}
function historyChanged(){if(demo)return;const params=new URLSearchParams(location.search);const session=params.get('assessmentSession'),task=params.get('assessmentTask') || '';if(session && (session!==state.value.sessionId || task!==state.value.taskId))controller.restore(session,task)}
function escapeHtml(value){return String(value ?? '').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
function downloadReport(){
 const analysis=result.value;if(!analysis)return
 const rows=inputValues.value.map(value=>`<tr><td>${escapeHtml(indicatorName(value.indicator_code))}</td><td>${escapeHtml(value.value)} ${escapeHtml(value.unit || '无量纲')}</td><td>${escapeHtml(value.method || '未登记')}</td></tr>`).join('')
 const indicators=(analysis.assessment.indicator_assessments || []).map(item=>`<tr><td>${escapeHtml(indicatorName(item.indicator_code))}</td><td>${escapeHtml(indicatorStatus(item.status))}</td><td>${escapeHtml(item.explanation)}</td></tr>`).join('')
 const problems=(analysis.problems || []).map(problem=>`<li><b>${escapeHtml(problem.title)}</b>：${escapeHtml(problem.observation)}<br><small>可能成因：${escapeHtml((problem.possible_causes || []).join('、') || '待核实')}</small></li>`).join('')
 const decisions=(analysis.decisions || []).map(decision=>`<li><b>${escapeHtml(decision.action)}</b>：${escapeHtml(decision.reason)}${decision.verification_goal ? `<br><small>核对目标：${escapeHtml(decision.verification_goal)}</small>` : ''}</li>`).join('')
 const gaps=[...(analysis.gaps || []),...(analysis.limitations || [])].map(item=>`<li>${escapeHtml(item)}</li>`).join('')
 const score=analysis.assessment.composite_score != null ? analysis.assessment.composite_score : '未形成综合分数'
 const html=`<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>土壤健康评价报告</title><style>
 body{margin:0;background:#eef1e9;font-family:"HarmonyOS Sans SC","Microsoft YaHei UI",sans-serif;color:#23382d;line-height:1.7}
 .paper{max-width:860px;margin:28px auto;padding:52px 60px;background:#fff;box-shadow:0 16px 50px rgba(20,45,30,.12)}
 h1{margin:0 0 6px;font-size:25px;color:#1c3a28}.sub{color:#5d7264;font-size:13px;margin:0}
 h2{font-size:15px;margin:26px 0 9px;padding-bottom:6px;border-bottom:1px solid #dfe6dc;color:#2b4c34}
 table{width:100%;border-collapse:collapse;font-size:12.5px}th,td{text-align:left;padding:7px 6px;border-bottom:1px solid #edf0eb;vertical-align:top}
 th{color:#6f8373;background:#f7f9f3}ul{margin:6px 0 0;padding-left:20px;font-size:12.5px}
 .meta{display:grid;grid-template-columns:1fr 1fr;gap:5px 22px;font-size:12.5px;color:#3d5345}
 .note{background:#fdf6ee;border:1px solid #f0dcc4;border-radius:8px;padding:12px 16px;font-size:12px;color:#7c5a35;margin-top:18px}
 .foot{margin-top:26px;padding-top:12px;border-top:1px solid #dfe6dc;color:#839586;font-size:11px}
 @media print{body{background:#fff}.paper{box-shadow:none;margin:0;padding:26px 32px}}
 </style></head><body><div class="paper">
 <h1>农田土壤健康评价报告</h1><p class="sub">${escapeHtml(sampleLabel.value)} · ${escapeHtml(cropLabel.value)} · ${escapeHtml(analysis.mode === 'deep' ? '深度分析' : '快速试用')}</p>
 <div class="meta"><div>生成时间：${escapeHtml(reportTime.value)}</div><div>研究会话：${escapeHtml(state.value.sessionId)}</div><div>任务标识：${escapeHtml(state.value.taskId)}</div><div>检测记录：${escapeHtml(state.value.measurementId)}</div><div>采样日期：${escapeHtml(samplingDate.value || '未填写')}</div><div>规则版本：${escapeHtml(analysis.model_info?.rule_version || '未登记')}</div></div>
 <h2>一、结论摘要</h2><p>${escapeHtml(analysis.assessment.summary)}</p><p>综合分数：${escapeHtml(score)}；${escapeHtml(analysis.assessment.score_explanation)}</p>
 <h2>二、检测记录</h2><table><thead><tr><th>指标</th><th>检测值</th><th>检测方法</th></tr></thead><tbody>${rows}</tbody></table>
 <h2>三、指标判读</h2><table><thead><tr><th>指标</th><th>状态</th><th>说明</th></tr></thead><tbody>${indicators}</tbody></table>
 <h2>四、优先核查项</h2><ul>${problems || '<li>本次未触发优先核查项。</li>'}</ul>
 <h2>五、建议与核对目标</h2><ul>${decisions || '<li>维持当前管理并定期复测。</li>'}</ul>
 <h2>六、适用范围与限制</h2><ul>${gaps}</ul>
 <div class="note"><b>说明</b>：本报告由平台评价引擎依据本次检测记录生成，评价规则版本见报告信息；报告中不含施肥剂量，田间措施需结合现场条件与农技人员复核。</div>
 <div class="foot">沃壤知行 · 土壤健康智能决策平台 · 报告可在浏览器中打印或另存为 PDF</div>
 </div></body></html>`
 const blob=new Blob([html],{type:'text/html;charset=utf-8'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`沃壤知行_土壤健康评价报告_${sampleLabel.value}.html`;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),4000)
}
onMounted(async()=>{
 document.getElementById('assessment-run-title')?.focus({preventScroll:true})
 window.addEventListener('soilmate:history-commit',historyChanged)
 if(demo){const {demoSnapshot,demoRequest}=await import('./runDemo.js');demoTransport=demoRequest(params.get('assessmentDemo'));controller.start(demoSnapshot);return}
 if(props.preview)return
 if(props.submission){controller.start(props.submission);emit('submission-consumed');return}
 if(props.initialRestore?.sessionId){controller.restore(props.initialRestore.sessionId, props.initialRestore.taskId || '');return}
 const saved=controller.load(),session=params.get('assessmentSession'),task=params.get('assessmentTask') || ''
 if(session){if(saved.sessionId===session && saved.taskId===task && saved.taskId)controller.resume();else controller.restore(session,task);return}
 if(saved.taskId)controller.resume()
})
onBeforeUnmount(()=>{controller.dispose();window.removeEventListener('soilmate:history-commit',historyChanged)})
</script>
<style scoped>
.assessment-report-card{border:1px solid #dfe8da;border-radius:12px;background:#fbfdf8;padding:20px 22px}
.assessment-report-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:14px}
.assessment-report-kicker{margin:0 0 4px;color:#6f8a76;font-size:11px;font-weight:700;letter-spacing:.18em}
.assessment-report-head h3{margin:0;font-size:19px;color:#234a32}
.assessment-report-sub{margin:5px 0 0;color:#7d9182;font-size:12px}
.assessment-report-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px 18px;margin:0 0 14px}
.assessment-report-facts dt{color:#8b9c8f;font-size:11px}
.assessment-report-facts dd{margin:2px 0 0;color:#36523f;font-size:13px}
.assessment-report-card h4{margin:16px 0 6px;font-size:13.5px;color:#2b4c34}
.assessment-report-card p{margin:0 0 6px;font-size:13px;color:#4b6354;line-height:1.75}
.assessment-report-foot{margin-top:14px !important;padding-top:10px;border-top:1px dashed #dfe8da;color:#8b9c8f !important;font-size:11.5px !important}
@media (max-width:760px){.assessment-report-facts{grid-template-columns:1fr 1fr}}
</style>
