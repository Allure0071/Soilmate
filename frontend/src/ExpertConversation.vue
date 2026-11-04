<template>
  <section ref="conversation" class="expert-conversation" :class="[`expert-${mode}`, { 'expert-resizing': drag }]" aria-label="沃壤知行土壤健康专家">
    <header class="expert-head">
      <div class="expert-ident"><span class="expert-symbol"><WorkspaceIcon name="chat" /></span><h2>研究助手</h2></div>
      <div v-if="mode === 'side'" class="expert-head-actions"><button type="button" @click="$emit('expand')" aria-label="打开完整 AI 助手" title="打开完整 AI 助手"><WorkspaceIcon name="expand" /></button><button type="button" @click="$emit('collapse')" aria-label="收起 AI 讨论栏" title="收起讨论栏"><WorkspaceIcon name="close" /></button></div>
    </header>

    <div v-if="checkingModel || modelStatus.available || modelStatus.local_fallback" class="expert-model-status" :class="{ 'is-connected': modelStatus.available, 'is-local': modelStatus.local_fallback && !modelStatus.available }" role="status"><span>{{ checkingModel ? '正在检查模型连接…' : modelStatus.message }}</span><button v-if="allowModel && !modelStatus.available && !modelStatus.local_fallback" type="button" :disabled="checkingModel" @click="checkModel">检查连接</button><small v-if="modelStatus.available">{{ modelStatus.model?.name }} · 研究试用，回答需结合证据复核</small></div>
    <div v-if="showContext && (context?.project || context?.sample)" class="expert-context">
      <div class="expert-context-heading"><span class="expert-context-dot"></span><b>当前研究</b><button v-if="mode === 'full'" type="button" @click="$emit('unlink')">解除关联</button></div>
      <strong>{{ context.project || '当前项目' }}<template v-if="context.sample"> · {{ context.sample }}</template></strong>
      <p>{{ context.runId ? `${runLabel} · ${context.dataVersion || '版本待确认'}` : '分析结果尚未生成' }}</p>
    </div>
    <p v-if="evidenceLoading" class="expert-evidence-state" role="status">正在读取本次评价证据链…</p>
    <p v-else-if="evidenceError" class="expert-evidence-state">证据链暂不可用：{{ evidenceError }}</p>
    <EvidenceChain v-else-if="evidenceChain.length" :chain="evidenceChain" :rule="evidenceRule" :default-open="mode === 'full'" title="本次评价证据链" />


    <div class="expert-body" :role="mode === 'full' ? 'region' : undefined" :tabindex="mode === 'full' ? 0 : undefined" :aria-label="mode === 'full' ? 'AI 回答内容' : undefined">
      <div v-if="answer" class="expert-answer" :data-answer-type="answer.answer_type" role="status">
        <span class="expert-answer-label">{{ answerLabel }}</span>
        <p>{{ answer.answer }}</p>
        <small v-if="answer.evidence_refs?.length">依据 {{ answer.evidence_refs.length }} 条研究记录</small><small v-if="answer.uncertainty">{{ answer.uncertainty }}</small><small v-if="answer.truncated">回答达到输出上限，可缩小问题范围后继续提问。</small>
      </div>
      <div v-if="!answer" class="expert-intro"><component :is="mode === 'full' ? 'h1' : 'h3'">{{ context?.sample ? '关于这次研究，\n你想了解什么？' : '想了解什么？' }}</component></div>
      <div v-if="!answer" class="expert-prompts" role="group" aria-label="问题示例">
        <button v-for="question in prompts" :key="question" type="button" @click="$emit('update:draft', question)">{{ question }} <WorkspaceIcon name="arrow" /></button>
      </div>
    </div>

    <div v-if="mode === 'full'" ref="resizeHandle" class="expert-compose-resizer" role="separator" tabindex="0" aria-label="调整输入面板高度" aria-orientation="horizontal" :aria-controls="`expert-compose-${mode}`" :aria-valuemin="resizeBounds.min" :aria-valuemax="resizeBounds.max" :aria-valuenow="measuredHeight" :aria-valuetext="`输入面板高度 ${measuredHeight} 像素`" title="按住上下拖动调整高度，双击恢复；也可使用上下方向键" @pointerdown="startResize" @pointermove="moveResize" @pointerup="stopResize" @pointercancel="stopResize" @lostpointercapture="drag = null" @keydown="resizeWithKeyboard" @dblclick="composeHeight = null"></div>
    <div :id="`expert-compose-${mode}`" ref="composer" class="expert-compose" :class="{ 'expert-compose-resizable': mode === 'full' }" :style="composeHeight == null ? undefined : { height: `${composeHeight}px` }"><label class="visually-hidden" :for="`expert-question-${mode}`">{{ mode === 'full' ? '向土壤健康专家提问' : '记下研究问题' }}</label><textarea :id="`expert-question-${mode}`" :value="draft" rows="3" maxlength="4000" placeholder="输入问题…" @input="$emit('update:draft', $event.target.value)"></textarea><div><span role="status">{{ loading ? '模型正在生成回答…' : sendError || (mode === 'full' && !storageAvailable ? '无法保存，请复制保留草稿' : taskId ? '回答将引用当前研究记录' : '独立问答') }}</span><button type="button" :disabled="loading || !draft.trim() || (!modelStatus.available && !modelStatus.local_fallback) || !allowModel" @click="send">{{ loading ? '读取中…' : '发送' }}<WorkspaceIcon name="send" /></button></div></div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
import EvidenceChain from './EvidenceChain.vue'
const props = defineProps({ mode: { type: String, default: 'side' }, context: { type: Object, default: null }, draft: { type: String, default: '' }, showContext: { type: Boolean, default: true }, storageAvailable: { type: Boolean, default: true }, csrfToken: { type: String, default: '' }, allowModel: { type: Boolean, default: true } })
const emit = defineEmits(['expand', 'collapse', 'unlink', 'update:draft'])
const answer = ref(null)
const loading = ref(false)
const sendError = ref('')
const evidenceChain = ref([])
const evidenceRule = ref('')
const evidenceLoading = ref(false)
const evidenceError = ref('')
let evidenceController
const taskId = computed(() => props.context?.taskId || props.context?.task_id || null)
const answerLabel = computed(() => ({ task_fact: '当前任务事实', domain_fact: '土壤健康知识', clarification: '需要补充证据', model_explanation: '微调模型回答 · 研究试用' })[answer.value?.answer_type] || '专家回答')
const modelStatus=ref({available:false,message:'模型连接待检查',model:null})
const checkingModel=ref(false)
let statusController,answerController,answerTimer,requestVersion=0
async function checkModel(){
  statusController?.abort()
  if(!props.allowModel){modelStatus.value={available:false,message:'审核预览不调用真实模型'};return}
  checkingModel.value=true
  const controller=new AbortController();statusController=controller
  const timer=setTimeout(()=>controller.abort(),12000)
  try{
    const response=await fetch('/api/agent/model/status',{credentials:'same-origin',signal:controller.signal})
    const data=await response.json()
    if(!response.ok)throw new Error(response.status===401?'登录后连接研究模型':'暂时无法读取模型连接状态')
    if(statusController===controller)modelStatus.value=data
  }catch(error){if(statusController===controller)modelStatus.value={available:false,message:controller.signal.aborted?'模型连接检查超时，请重试':error.message}}
  finally{clearTimeout(timer);if(statusController===controller)checkingModel.value=false}
}
async function loadEvidenceChain() {
  evidenceController?.abort()
  evidenceChain.value = []
  evidenceRule.value = ''
  evidenceError.value = ''
  if (!taskId.value) { evidenceLoading.value = false; return }
  const controller = new AbortController()
  evidenceController = controller
  evidenceLoading.value = true
  try {
    const response = await fetch(`/api/assessment/tasks/${encodeURIComponent(taskId.value)}/evidence`, { credentials: 'same-origin', signal: controller.signal })
    const data = await response.json()
    if (!response.ok) throw new Error(data?.error?.message || '证据链暂不可用')
    if (evidenceController !== controller) return
    evidenceChain.value = data?.data?.chain || []
    evidenceRule.value = data?.data?.rule_version || ''
  } catch (error) {
    if (controller.signal.aborted) return
    if (evidenceController === controller) evidenceError.value = error.message || '证据链暂不可用'
  } finally {
    if (evidenceController === controller) evidenceLoading.value = false
  }
}

async function send() {
  if (!props.draft.trim() || loading.value || (!modelStatus.value.available && !modelStatus.value.local_fallback) || !props.allowModel) return
  const version=++requestVersion
  answerController?.abort();const controller=new AbortController();answerController=controller
  const timer=setTimeout(()=>controller.abort(),110000);answerTimer=timer
  loading.value=true;sendError.value='';answer.value=null
  try {
    const response=await fetch('/api/agent/expert',{method:'POST',credentials:'same-origin',signal:controller.signal,headers:{'Content-Type':'application/json','X-CSRF-Token':props.csrfToken},body:JSON.stringify({query:props.draft.trim(),task_id:taskId.value})})
    const data=await response.json()
    if(!response.ok){
      const code=data.detail?.code
      if(response.status===401 || ['MODEL_NOT_CONFIGURED','MODEL_IDENTITY_MISMATCH','MODEL_AUTH_FAILED','MODEL_UNAVAILABLE'].includes(code))modelStatus.value={...modelStatus.value,available:false,message:'模型连接暂不可用，请检查连接'}
      throw new Error(typeof data.detail==='object'?data.detail.message:data.detail || '问答请求失败')
    }
    if(version!==requestVersion)return
    answer.value=data
    if (Array.isArray(data.evidence_chain) && data.evidence_chain.length) { evidenceChain.value = data.evidence_chain; evidenceError.value = '' }
    emit('update:draft','')
  } catch(error){if(version===requestVersion)sendError.value=error.name==='AbortError'?'等待模型回答超时，问题草稿已保留。':error.message || '问答请求失败'}
  finally{clearTimeout(timer);if(version===requestVersion)loading.value=false}
}
watch(()=>props.allowModel,()=>{checkModel()})
watch(taskId,()=>{requestVersion++;answerController?.abort();clearTimeout(answerTimer);loading.value=false;answer.value=null;sendError.value='';loadEvidenceChain()})
onMounted(() => { checkModel(); loadEvidenceChain() })
const runLabel = computed(() => ({ raw_data: '仅有原始数据', exploratory_assessment: '探索性结果', validated_assessment: '经验证结果', insufficient_data: '数据不足' })[props.context?.runStatus] || '已有关联运行')
const prompts = computed(() => props.context?.sample ? ['当前还缺少哪些证据？', '为什么保留这个指标？'] : ['土壤健康包含哪些维度？', '什么是最小数据集 MDS？'])
const conversation = ref(null), composer = ref(null), resizeHandle = ref(null)
const composeHeight = ref(null), measuredHeight = ref(0), conversationHeight = ref(0), drag = ref(null)
const resizeBounds = computed(() => {
  const max = Math.max(0, conversationHeight.value - 96 - (resizeHandle.value?.offsetHeight || 12))
  return { min: Math.min(200, max), max }
})
function setComposeHeight(height) {
  composeHeight.value = Math.round(Math.min(resizeBounds.value.max, Math.max(resizeBounds.value.min, height)))
}
function startResize(event) {
  if (event.button !== 0 || !event.isPrimary) return
  event.preventDefault()
  event.currentTarget.focus({ preventScroll: true })
  drag.value = { pointerId: event.pointerId, y: event.clientY, height: composer.value.getBoundingClientRect().height }
  event.currentTarget.setPointerCapture(event.pointerId)
}
function moveResize(event) {
  if (drag.value?.pointerId !== event.pointerId) return
  setComposeHeight(drag.value.height + drag.value.y - event.clientY)
}
function stopResize(event) {
  if (drag.value?.pointerId !== event.pointerId) return
  drag.value = null
  if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId)
}
function resizeWithKeyboard(event) {
  const step = event.shiftKey ? 40 : 16
  const heights = { ArrowUp: measuredHeight.value + step, ArrowDown: measuredHeight.value - step, Home: resizeBounds.value.min, End: resizeBounds.value.max }
  if (!(event.key in heights)) return
  event.preventDefault()
  setComposeHeight(heights[event.key])
}
let resizeObserver
onMounted(() => {
  if (props.mode !== 'full') return
  resizeObserver = new ResizeObserver(() => {
    conversationHeight.value = conversation.value.clientHeight
    measuredHeight.value = Math.round(composer.value.getBoundingClientRect().height)
    if (composeHeight.value != null) setComposeHeight(composeHeight.value)
  })
  resizeObserver.observe(conversation.value)
  resizeObserver.observe(composer.value)
})
onBeforeUnmount(() => {requestVersion++;statusController?.abort();answerController?.abort();evidenceController?.abort();clearTimeout(answerTimer);resizeObserver?.disconnect()})
</script>
