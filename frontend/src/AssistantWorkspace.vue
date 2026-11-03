<template>
  <main class="assistant-workspace" aria-label="沃壤知行 AI 助手">
    <button v-if="sidebarOpen" type="button" class="assistant-mobile-shade" aria-label="关闭会话列表" @click="sidebarOpen = false"></button>
    <aside class="assistant-sidebar" :class="{ 'assistant-sidebar-open': sidebarOpen }" :inert="(compact && !sidebarOpen) || (inspectorOverlay && inspectorOpen)" :role="compact && sidebarOpen ? 'dialog' : undefined" :aria-modal="compact && sidebarOpen ? true : undefined" aria-label="对话草稿" @keydown.esc="sidebarOpen = false" @keydown.tab="trapWorkspaceFocus($event, compact)">
      <div class="assistant-sidebar-head"><strong>AI 助手</strong><button type="button" class="assistant-sidebar-close" aria-label="关闭会话列表" @click="sidebarOpen = false"><WorkspaceIcon name="close" /></button></div>
      <button type="button" class="assistant-new-chat" @click="newThread"><WorkspaceIcon name="plus" />新建对话</button>
      <div class="assistant-thread-group"><span>本机草稿</span><button v-for="thread in threads" :key="thread.id" type="button" :class="{ active: thread.id === activeId }" :aria-current="thread.id === activeId ? 'page' : undefined" @click="selectThread(thread.id)"><strong>{{ thread.title }}</strong><small>{{ thread.context?.sample ? thread.context.sample : '独立问答' }}</small></button></div>
      <div class="assistant-sidebar-foot"><WorkspaceIcon name="panel" /><p>草稿保留在当前浏览器<br>最多保存最近 20 个对话</p></div>
    </aside>

    <section class="assistant-main" aria-label="当前对话" :inert="(compact && sidebarOpen) || (inspectorOverlay && inspectorOpen)">
      <header class="assistant-toolbar"><button type="button" class="assistant-menu-button" aria-label="打开会话列表" :aria-expanded="sidebarOpen" @click="sidebarOpen = true"><WorkspaceIcon name="menu" /></button><div><span>{{ activeThread?.context?.sample ? '已关联健康研究' : '独立专业问答' }}</span><strong :title="activeThread?.title">{{ activeThread?.title || '新对话' }}</strong></div><button type="button" class="assistant-context-button" :aria-expanded="inspectorOpen" @click="inspectorOpen = !inspectorOpen"><WorkspaceIcon name="panel" />研究上下文</button></header>
      <ExpertConversation mode="full" :show-context="false" :context="activeThread?.context || null" :draft="activeThread?.draft || ''" :storage-available="storageAvailable" :csrf-token="csrfToken" @update:draft="updateDraft" />
    </section>

    <aside v-if="inspectorOpen" class="assistant-inspector" :role="inspectorOverlay ? 'dialog' : undefined" :aria-modal="inspectorOverlay ? true : undefined" aria-label="研究上下文与依据" @keydown.esc="inspectorOpen = false" @keydown.tab="trapWorkspaceFocus($event, inspectorOverlay)"><header><h2>研究上下文</h2><button type="button" aria-label="关闭研究上下文" @click="inspectorOpen = false"><WorkspaceIcon name="close" /></button></header>
      <template v-if="activeThread?.context?.sample"><div class="assistant-context-status"><span></span>{{ runLabel }}</div><h3>{{ activeThread.context.project || '当前项目' }}</h3><p class="assistant-context-sample">{{ activeThread.context.sample }}</p><dl><div><dt>数据版本</dt><dd>{{ activeThread.context.dataVersion || '未登记' }}</dd></div><div><dt>分析运行</dt><dd>{{ activeThread.context.runId || '尚未生成' }}</dd></div><div><dt>数据集</dt><dd>{{ activeThread.context.dataset || '未登记' }}</dd></div></dl><button type="button" class="assistant-open-research" @click="$emit('navigate-research')">打开健康研究<WorkspaceIcon name="arrow" /></button><button type="button" class="assistant-unlink" @click="unlinkContext">解除任务关联</button></template>
      <div v-else class="assistant-context-empty"><WorkspaceIcon name="panel" /><h3>未关联研究</h3><p>从健康研究打开 AI 助手时，会带入当前样本和运行版本。</p><button type="button" @click="$emit('navigate-research')">前往健康研究<WorkspaceIcon name="arrow" /></button></div>
      <p class="assistant-inspector-note">正式对话接入后，这里会列出本轮使用的字段、运行记录和文献来源。</p>
    </aside>
  </main>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ExpertConversation from './ExpertConversation.vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
import { trapWorkspaceFocus } from './workspaceFocus.js'

const props = defineProps({ accountId: { type: String, default: 'local' }, context: { type: Object, default: null }, draft: { type: String, default: '' }, csrfToken: { type: String, default: '' } })
const emit = defineEmits(['update:context', 'update:draft', 'navigate-research'])
const storageKey = `soilmate.assistant.drafts.v1.${props.accountId}`
const storageAvailable = ref(true)
function readSaved() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || 'null')
    if (!saved || !Array.isArray(saved.threads)) return null
    return { activeId: saved.activeId, threads: saved.threads.slice(0, 20).filter(item => item && typeof item.id === 'string').map(item => ({ id: item.id, title: String(item.title || '新对话').slice(0, 40), draft: String(item.draft || '').slice(0, 4000), context: item.context && typeof item.context === 'object' ? item.context : null })) }
  } catch { return null }
}
function makeThread(context = null, draft = '') { return { id: `draft-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, title: draft.trim().slice(0, 18) || '新对话', draft, context } }
const saved = readSaved()
const threads = ref(saved?.threads?.length ? saved.threads : [makeThread(props.context, props.draft)])
const matching = props.context?.sample ? threads.value.find(item => (props.context.projectId ? item.context?.projectId === props.context.projectId : item.context?.project === props.context.project) && (props.context.sampleId ? item.context?.sampleId === props.context.sampleId : item.context?.sample === props.context.sample) && item.context?.runId === props.context.runId && item.context?.dataVersion === props.context.dataVersion) : null
if (props.context?.sample && !matching) threads.value.unshift(makeThread(props.context, props.draft))
if (matching && props.draft) matching.draft = props.draft
let importedThread = null
if (!props.context?.sample && props.draft && !threads.value.some(item => item.draft === props.draft)) { importedThread = makeThread(null, props.draft); threads.value.unshift(importedThread) }
const activeId = ref(matching?.id || importedThread?.id || (props.context?.sample ? threads.value[0].id : saved?.activeId && threads.value.some(item => item.id === saved.activeId) ? saved.activeId : threads.value[0].id))
const activeThread = computed(() => threads.value.find(item => item.id === activeId.value) || threads.value[0])
const sidebarOpen = ref(false)
const sidebarMedia = window.matchMedia('(max-width: 850px)')
const inspectorMedia = window.matchMedia('(max-width: 1180px)')
const compact = ref(sidebarMedia.matches)
const inspectorOverlay = ref(inspectorMedia.matches)
const inspectorOpen = ref(Boolean(activeThread.value?.context?.sample) && typeof window !== 'undefined' && window.matchMedia('(min-width: 1180px)').matches)
function syncLayout() {
  compact.value = sidebarMedia.matches
  inspectorOverlay.value = inspectorMedia.matches
  sidebarOpen.value = false
  if (inspectorOverlay.value) inspectorOpen.value = false
}
onMounted(() => { sidebarMedia.addEventListener('change', syncLayout); inspectorMedia.addEventListener('change', syncLayout) })
onBeforeUnmount(() => { sidebarMedia.removeEventListener('change', syncLayout); inspectorMedia.removeEventListener('change', syncLayout) })
watch(sidebarOpen, async open => { if (!compact.value) return; await nextTick(); document.querySelector(open ? '.assistant-sidebar-close' : '.assistant-menu-button')?.focus() })
watch(inspectorOpen, async open => { if (!inspectorOverlay.value) return; await nextTick(); document.querySelector(open ? '.assistant-inspector header button' : '.assistant-context-button')?.focus() })
const runLabel = computed(() => ({ raw_data: '仅有原始数据', exploratory_assessment: '探索性结果', validated_assessment: '经验证结果', insufficient_data: '数据不足' })[activeThread.value?.context?.runStatus] || '尚无评价结果')

function syncActive() { emit('update:context', activeThread.value?.context || null); emit('update:draft', activeThread.value?.draft || '') }
function selectThread(id) { activeId.value = id; sidebarOpen.value = false; inspectorOpen.value = Boolean(activeThread.value?.context?.sample) && window.matchMedia('(min-width: 1180px)').matches; syncActive() }
function newThread() { const thread = makeThread(); threads.value.unshift(thread); activeId.value = thread.id; sidebarOpen.value = false; inspectorOpen.value = false; syncActive() }
function updateDraft(value) { if (!activeThread.value) return; activeThread.value.draft = value.slice(0, 4000); activeThread.value.title = value.trim().slice(0, 18) || '新对话'; emit('update:draft', activeThread.value.draft) }
function unlinkContext() { if (!activeThread.value) return; activeThread.value.context = null; emit('update:context', null) }
watch([threads, activeId], () => { try { localStorage.setItem(storageKey, JSON.stringify({ activeId: activeId.value, threads: threads.value.slice(0, 20) })); storageAvailable.value = true } catch { storageAvailable.value = false } }, { deep: true, immediate: true, flush: 'sync' })
syncActive()
</script>
