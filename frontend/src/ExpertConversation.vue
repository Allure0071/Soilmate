<template>
  <section class="expert-conversation" :class="`expert-${mode}`" aria-label="沃壤知行土壤健康专家">
    <header class="expert-head">
      <div class="expert-ident"><span class="expert-symbol"><WorkspaceIcon name="chat" /></span><h2>土壤健康专家</h2></div>
      <div v-if="mode === 'side'" class="expert-head-actions"><button type="button" @click="$emit('expand')" aria-label="打开完整 AI 助手" title="打开完整 AI 助手"><WorkspaceIcon name="expand" /></button><button type="button" @click="$emit('collapse')" aria-label="收起 AI 讨论栏" title="收起讨论栏"><WorkspaceIcon name="close" /></button></div>
    </header>

    <div v-if="showContext && (context?.project || context?.sample)" class="expert-context">
      <div class="expert-context-heading"><span class="expert-context-dot"></span><b>当前研究</b><button v-if="mode === 'full'" type="button" @click="$emit('unlink')">解除关联</button></div>
      <strong>{{ context.project || '当前项目' }}<template v-if="context.sample"> · {{ context.sample }}</template></strong>
      <p>{{ context.runId ? `${runLabel} · ${context.dataVersion || '版本待确认'}` : '分析结果尚未生成' }}</p>
    </div>
    <div v-else-if="showContext" class="expert-context expert-context-unbound"><div class="expert-context-heading"><span class="expert-context-dot"></span><b>{{ mode === 'side' ? '录入草稿' : '独立问答' }}</b></div><p>{{ mode === 'side' ? '数据尚未提交，暂不关联评价结果。' : '未关联研究任务。' }}</p></div>

    <div class="expert-body">
      <div v-if="answer" class="expert-answer" :data-answer-type="answer.answer_type" role="status">
        <span class="expert-answer-label">{{ answerLabel }}</span>
        <p>{{ answer.answer }}</p>
        <small v-if="answer.evidence_refs?.length">依据 {{ answer.evidence_refs.length }} 个 Artifact · {{ answer.uncertainty }}</small>
      </div>
      <div class="expert-intro"><component :is="mode === 'full' ? 'h1' : 'h3'">{{ context?.sample ? '关于这次研究，\n你想知道什么？' : '从一个问题开始。' }}</component><p>土壤科学、指标选择与评价方法。</p></div>
      <div class="expert-prompts" role="group" aria-label="问题示例">
        <button v-for="question in prompts" :key="question" type="button" @click="$emit('update:draft', question)">{{ question }} <WorkspaceIcon name="arrow" /></button>
      </div>
    </div>

    <div class="expert-compose"><label :for="`expert-question-${mode}`">{{ mode === 'full' ? '向土壤健康专家提问' : '记下研究问题' }}</label><textarea :id="`expert-question-${mode}`" :value="draft" rows="3" maxlength="4000" placeholder="写下你关注的指标、方法或证据…" @input="$emit('update:draft', $event.target.value)" @keydown.enter.exact.prevent="send"></textarea><div><span role="status">{{ loading ? '正在读取任务证据…' : sendError || (mode === 'full' && !storageAvailable ? '无法保存，请复制保留草稿' : taskId ? '回答将引用当前任务 Artifact' : '独立知识问答') }}</span><button type="button" :disabled="loading || !draft.trim()" @click="send">{{ loading ? '读取中…' : '发送' }}<WorkspaceIcon name="send" /></button></div></div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
const props = defineProps({ mode: { type: String, default: 'side' }, context: { type: Object, default: null }, draft: { type: String, default: '' }, showContext: { type: Boolean, default: true }, storageAvailable: { type: Boolean, default: true }, csrfToken: { type: String, default: '' } })
const emit = defineEmits(['expand', 'collapse', 'unlink', 'update:draft'])
const answer = ref(null)
const loading = ref(false)
const sendError = ref('')
const taskId = computed(() => props.context?.taskId || props.context?.task_id || null)
const answerLabel = computed(() => ({ task_fact: '当前任务事实', domain_fact: '土壤健康知识', clarification: '需要补充证据' })[answer.value?.answer_type] || '专家回答')
async function send() {
  if (!props.draft.trim() || loading.value) return
  loading.value = true
  sendError.value = ''
  answer.value = null
  try {
    const endpoint = taskId.value ? `/api/agent/tasks/${encodeURIComponent(taskId.value)}/expert` : '/api/agent/messages'
    const body = taskId.value ? { query: props.draft.trim() } : { text: props.draft.trim() }
    const response = await fetch(endpoint, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': props.csrfToken }, body: JSON.stringify(body) })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '问答请求失败')
    answer.value = taskId.value ? data : { answer: '问题已提交。请在关联的研究任务中查看后续结果。', answer_type: 'clarification', evidence_refs: [] }
    emit('update:draft', '')
  } catch (error) { sendError.value = error.message || '问答请求失败' }
  finally { loading.value = false }
}
const runLabel = computed(() => ({ raw_data: '仅有原始数据', exploratory_assessment: '探索性结果', validated_assessment: '经验证结果', insufficient_data: '数据不足' })[props.context?.runStatus] || '已有关联运行')
const prompts = computed(() => props.context?.sample ? ['当前还缺少哪些证据？', '为什么保留这个指标？'] : ['土壤健康包含哪些维度？', '什么是最小数据集 MDS？'])
</script>
