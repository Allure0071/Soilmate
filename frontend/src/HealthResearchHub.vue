<template>
  <main class="health-hub" aria-labelledby="health-hub-title">
    <header class="health-hub-header"><div><h1 id="health-hub-title">健康研究</h1></div><div class="health-hub-status"><span class="health-status-dot" aria-hidden="true"></span><span :title="context?.sample ? `${context.project} · ${context.sample}` : undefined">{{ stage === 'input' ? '录入草稿 · 尚未提交' : stage==='analysis' && showAssessmentRun ? runState?.phase==='error' ? '分析暂不可用' : runState?.task ? ({queued:'任务排队中',running:'正在分析',completed:'本次分析完成',partial:'有限范围结果',failed:'任务未完成',interrupted:'任务已中断'})[runState.task.status] : '研究任务' : context?.sample ? `${context.project} · ${context.sample}` : '尚未选择样本' }}</span></div></header>
    <HoverSwitch as="nav" class="health-stages" :inert="compact && assistantOpen" aria-label="健康研究阶段"><button v-for="item in stages" :key="item.id" type="button" :class="{ active: stage === item.id }" :aria-current="stage === item.id ? 'step' : undefined" @click="$emit('update:stage', item.id)"><span>{{ item.number }}</span><b>{{ item.label }}</b></button></HoverSwitch>
    <div class="health-hub-columns" :class="{ 'health-hub-ai-hidden': !assistantOpen }">
      <div class="health-hub-content" :inert="compact && assistantOpen">
        <AssessmentWorkspace v-show="stage === 'input'" embedded :active="stage==='input'" :account="account" :preview="preview" :map-point="mapPoint" @navigate="$emit('navigate', $event)" @submit-analysis="startAnalysis" @open-demo="startDemo" />
        <AssessmentRun v-if="stage==='analysis' && showAssessmentRun" :key="runVersion" :account="account" :csrf-token="csrfToken" :submission="submission" :preview="preview" @submission-consumed="submission=null" @run-context="runState=$event" @back-input="$emit('update:stage','input')" />
        <ResearchWorkspace v-if="account && !preview" v-show="stage !== 'input' && !(stage==='analysis' && showAssessmentRun)" embedded :stage="stage" :initial-context="context" :map-point="mapPoint" :csrf-token="csrfToken" @context-change="$emit('context-change', $event)" @navigate-stage="$emit('update:stage', $event)" @back="$emit('navigate', 'explore')" />
        <section v-else-if="stage !== 'input' && !showAssessmentRun" class="research-preview-empty"><h2>登录后继续研究</h2><p>登录以查看分析、来源与报告。</p><a :href="`/account/index.html?next=${encodeURIComponent('/research?stage=' + stage)}`">登录并继续 <WorkspaceIcon name="arrow" /></a></section>
      </div>
      <aside v-if="assistantOpen" class="health-hub-assistant" :role="compact ? 'dialog' : undefined" :aria-modal="compact ? true : undefined" aria-label="研究讨论" @keydown.esc="changeAssistant(false)" @keydown.tab="trapWorkspaceFocus($event, compact)"><ExpertConversation mode="side" :context="stage === 'input' ? null : context" :draft="draft" :csrf-token="csrfToken" @update:draft="$emit('update:draft', $event)" @expand="$emit('open-assistant')" @collapse="changeAssistant(false)" /></aside>
      <button v-else type="button" class="health-ai-reopen" @click="changeAssistant(true)"><WorkspaceIcon name="chat" />研究讨论</button>
    </div>
  </main>
</template>

<script setup>
import HoverSwitch from './design-system/HoverSwitch.vue'
import { defineAsyncComponent, computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
const AssessmentRun = defineAsyncComponent(() => import('./assessment/AssessmentRun.vue'))
import AssessmentWorkspace from './assessment/AssessmentWorkspace.vue'
import ResearchWorkspace from './ResearchWorkspace.vue'
import ExpertConversation from './ExpertConversation.vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
import { trapWorkspaceFocus } from './workspaceFocus.js'
import { transitionPage } from './design-system/motion.js'
const props = defineProps({ account: { type: Object, default: null }, preview: { type: Boolean, default: false }, mapPoint: { type: Object, default: null }, csrfToken: { type: String, default: '' }, stage: { type: String, default: 'input' }, context: { type: Object, default: null }, draft: { type: String, default: '' } })
const emit=defineEmits(['update:stage', 'context-change', 'update:draft', 'navigate', 'open-assistant'])
const runState=ref(null)
const submission=ref(null), runVersion=ref(0), runActive=ref(new URLSearchParams(location.search).has('assessmentSession') || (import.meta.env.DEV && props.preview && new URLSearchParams(location.search).has('assessmentDemo')))
const showAssessmentRun=computed(()=>runActive.value || !props.context?.sample)
function startAnalysis(snapshot){ submission.value=snapshot;runVersion.value++;runActive.value=true;const url=new URL(location.href);for(const key of ['assessmentSession','assessmentTask','assessmentDemo'])url.searchParams.delete(key);history.replaceState(history.state,'',url.pathname+url.search);emit('update:stage','analysis') }
function startDemo(scenario){ if(!import.meta.env.DEV || !props.preview)return;submission.value=null;runVersion.value++;runActive.value=true;const url=new URL(location.href);url.searchParams.set('assessmentDemo',scenario);for(const key of ['assessmentSession','assessmentTask'])url.searchParams.delete(key);history.replaceState(history.state,'',url.pathname+url.search);emit('update:stage','analysis') }
const assistantOpen = ref(typeof window === 'undefined' || window.matchMedia('(min-width: 851px)').matches)
function changeAssistant(open) { return transitionPage(() => { assistantOpen.value = open }, nextTick) }
const assistantMedia = window.matchMedia('(min-width: 851px)')
const compact = ref(!assistantMedia.matches)
function closeOnCompact(event) { compact.value = !event.matches; if (!event.matches) assistantOpen.value = false }
onMounted(() => assistantMedia.addEventListener('change', closeOnCompact))
onBeforeUnmount(() => assistantMedia.removeEventListener('change', closeOnCompact))
watch(assistantOpen, async open => { if (!compact.value) return; await nextTick(); document.querySelector(open ? '.expert-head-actions button:last-child' : '.health-ai-reopen')?.focus() })
const stages = [{ id: 'input', number: '01', label: '录入与核验' }, { id: 'analysis', number: '02', label: '结果与分析' }, { id: 'evidence', number: '03', label: '依据与版本' }, { id: 'report', number: '04', label: '报告与记录' }]
const stageDescription = computed(() => ({ input: '整理检测数据，核对每一项指标。', analysis: '围绕当前样本，查看结果与已知限制。', evidence: '从分析结论回到数据来源与运行版本。', report: '汇集分析任务、研究行动与报告版本。' })[props.stage])
</script>
