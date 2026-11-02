<template>
  <main class="health-hub" aria-labelledby="health-hub-title">
    <header class="health-hub-header"><div><span class="health-eyebrow">SOILMATE / RESEARCH</span><h1 id="health-hub-title">健康研究</h1></div><div class="health-hub-status"><span class="health-status-dot"></span><span>{{ stage === 'input' ? '录入草稿' : context?.sample ? `${context.project} · ${context.sample}` : '尚未选择样本' }}</span></div></header>
    <nav class="health-stages" aria-label="健康研究阶段"><button v-for="item in stages" :key="item.id" type="button" :class="{ active: stage === item.id }" :aria-current="stage === item.id ? 'step' : undefined" @click="$emit('update:stage', item.id)"><span>{{ item.number }}</span><b>{{ item.label }}</b></button></nav>
    <div class="health-hub-columns" :class="{ 'health-hub-ai-hidden': !assistantOpen }">
      <div class="health-hub-content">
        <AssessmentWorkspace v-show="stage === 'input'" :account="account" :preview="preview" :map-point="mapPoint" @navigate="$emit('navigate', $event)" />
        <ResearchWorkspace v-if="account" v-show="stage !== 'input'" embedded :stage="stage" :map-point="mapPoint" :csrf-token="csrfToken" @context-change="$emit('context-change', $event)" @navigate-stage="$emit('update:stage', $event)" @back="$emit('navigate', 'explore')" />
      </div>
      <aside v-if="assistantOpen" class="health-hub-assistant"><ExpertConversation mode="side" :context="stage === 'input' ? null : context" :draft="draft" @update:draft="$emit('update:draft', $event)" @expand="$emit('open-assistant')" @collapse="assistantOpen = false" /></aside>
      <button v-else type="button" class="health-ai-reopen" @click="assistantOpen = true">✳ 研究讨论</button>
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import AssessmentWorkspace from './assessment/AssessmentWorkspace.vue'
import ResearchWorkspace from './ResearchWorkspace.vue'
import ExpertConversation from './ExpertConversation.vue'
defineProps({ account: { type: Object, default: null }, preview: { type: Boolean, default: false }, mapPoint: { type: Object, default: null }, csrfToken: { type: String, default: '' }, stage: { type: String, default: 'input' }, context: { type: Object, default: null }, draft: { type: String, default: '' } })
defineEmits(['update:stage', 'context-change', 'update:draft', 'navigate', 'open-assistant'])
const assistantOpen = ref(typeof window === 'undefined' || window.matchMedia('(min-width: 851px)').matches)
const stages = [{ id: 'input', number: '01', label: '录入与核验' }, { id: 'analysis', number: '02', label: '结果与分析' }, { id: 'evidence', number: '03', label: '依据与版本' }, { id: 'report', number: '04', label: '报告与记录' }]
</script>
