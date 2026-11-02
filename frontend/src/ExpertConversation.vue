<template>
  <section class="expert-conversation" :class="`expert-${mode}`" aria-label="Soilmate 土壤健康专家">
    <header class="expert-head">
      <div class="expert-ident"><span class="expert-symbol" aria-hidden="true">✳</span><div><span class="expert-kicker">SOILMATE AI</span><h2>土壤健康专家</h2></div></div>
      <div v-if="mode === 'side'" class="expert-head-actions"><button type="button" @click="$emit('expand')" aria-label="打开完整 AI 助手">↗</button><button type="button" @click="$emit('collapse')" aria-label="收起 AI 讨论栏">×</button></div>
    </header>

    <div v-if="showContext && (context?.project || context?.sample)" class="expert-context">
      <div class="expert-context-heading"><span class="expert-context-dot"></span><b>当前研究</b><button v-if="mode === 'full'" type="button" @click="$emit('unlink')">解除关联</button></div>
      <strong>{{ context.project || '当前项目' }}<template v-if="context.sample"> · {{ context.sample }}</template></strong>
      <p>{{ context.runId ? `${runLabel} · ${context.dataVersion || '版本待确认'}` : '分析结果尚未生成' }}</p>
    </div>
    <div v-else-if="showContext" class="expert-context expert-context-unbound"><div class="expert-context-heading"><span class="expert-context-dot"></span><b>{{ mode === 'side' ? '录入草稿' : '独立问答' }}</b></div><p>{{ mode === 'side' ? '数据尚未提交，暂不关联评价结果。' : '未关联研究任务。' }}</p></div>

    <div class="expert-body">
      <div class="expert-intro"><span>研究讨论</span><h3>{{ context?.sample ? '关于这次研究，\n你想知道什么？' : '从一个问题开始。' }}</h3><p>土壤科学、指标选择与评价方法。</p></div>
      <div class="expert-prompts" aria-label="问题示例">
        <button v-for="question in prompts" :key="question" type="button" @click="$emit('update:draft', question)">{{ question }} <span aria-hidden="true">↗</span></button>
      </div>
    </div>

    <div class="expert-compose"><label for="expert-question" class="sr-only">向土壤健康专家提问</label><textarea id="expert-question" :value="draft" rows="3" placeholder="写下你的问题…" @input="$emit('update:draft', $event.target.value)"></textarea><div><span>对话服务待接入</span><button type="button" disabled title="对话服务尚未接入">发送 ↗</button></div></div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ mode: { type: String, default: 'side' }, context: { type: Object, default: null }, draft: { type: String, default: '' }, showContext: { type: Boolean, default: true } })
defineEmits(['expand', 'collapse', 'unlink', 'update:draft'])
const runLabel = computed(() => ({ raw_data: '仅有原始数据', exploratory_assessment: '探索性结果', validated_assessment: '经验证结果', insufficient_data: '数据不足' })[props.context?.runStatus] || '已有关联运行')
const prompts = computed(() => props.context?.sample ? ['当前还缺少哪些证据？', '为什么保留这个指标？'] : ['土壤健康包含哪些维度？', '什么是最小数据集 MDS？'])
</script>
