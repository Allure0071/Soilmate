<template>
  <div class="calculator-workbench">
    <div class="calculator-columns">
      <form class="calculator-form" novalidate @submit.prevent="run">
        <div class="calculator-section-heading"><h2>计算参数</h2><button type="button" class="tool-text-button" @click="fillExample">载入示例</button></div>
        <p v-if="exampleLoaded" class="calculator-example-note" role="status">已载入演示参数，不代表实测数据；你可以修改后重新计算。</p>
        <div class="calculator-fields">
          <label v-for="field in definition.fields" :key="field.id" :for="`calc-${field.id}`" :class="{ 'calculator-field-wide': field.type === 'textarea' }">
            <span>{{ field.label }}<small v-if="field.optional">选填</small><small v-else-if="fieldUnit(field)">{{ fieldUnit(field) }}</small></span>
            <select v-if="field.type === 'select'" :id="`calc-${field.id}`" v-model="values[field.id]" :aria-invalid="error?.field === field.id" :aria-describedby="describedBy(field)"><option v-for="option in options(field)" :key="option[0]" :value="option[0]">{{ option[1] }}</option></select>
            <textarea v-else-if="field.type === 'textarea'" :id="`calc-${field.id}`" v-model="values[field.id]" rows="6" maxlength="30000" spellcheck="false" :aria-invalid="error?.field === field.id" :aria-describedby="describedBy(field)"></textarea>
            <input v-else :id="`calc-${field.id}`" v-model="values[field.id]" type="text" inputmode="decimal" maxlength="100" autocomplete="off" :aria-invalid="error?.field === field.id" :aria-describedby="describedBy(field)" />
            <small v-if="field.hint" :id="`calc-${field.id}-hint`" class="calculator-field-hint">{{ field.hint }}</small>
            <small v-if="error?.field === field.id" :id="`calc-${field.id}-error`" class="calculator-field-error">{{ error.message }}</small>
          </label>
        </div>
        <p v-if="error" class="calculator-error" role="alert">{{ error.message }}</p>
        <div class="calculator-form-actions"><button type="submit" class="tool-primary-button">计算结果<WorkspaceIcon name="arrow" /></button><button type="button" class="tool-text-button" @click="reset">清空参数</button></div>
        <p class="calculator-privacy-note">参数仅在当前页面内计算，不上传、不保存到账号。</p>
      </form>
      <section class="calculator-result" aria-labelledby="calculation-result-heading" aria-live="polite">
        <div class="calculator-section-heading"><h2 id="calculation-result-heading">计算结果</h2><button v-if="output" type="button" class="tool-text-button" @click="download">下载结果</button></div>
        <template v-if="output"><dl class="calculator-result-list"><div v-for="item in output.items" :key="item.label"><dt>{{ item.label }}</dt><dd>{{ formatNumber(item.value) }}<small>{{ item.unit }}</small></dd></div></dl><p v-for="note in output.notes" :key="note" class="calculator-result-note">{{ note }}</p><CalibrationPlot v-if="output.chart" :chart="output.chart" /><p class="calculator-result-footnote">结果按输入与所列公式计算，请结合检测方法核对。</p></template>
        <div v-else class="calculator-result-empty"><WorkspaceIcon name="calculator" /><h3>{{ error ? '请先修正输入' : '填写参数后开始计算' }}</h3><p>结果、单位和计算说明将在这里显示。也可载入示例，先了解计算方式。</p></div>
      </section>
    </div>
    <section class="calculator-method" aria-labelledby="calculator-method-title"><h2 id="calculator-method-title">公式与适用说明</h2><p class="calculator-formula">{{ definition.formula }}</p><p>{{ definition.scope }}</p><ul class="tool-sources"><li v-for="source in definition.sources" :key="source.href"><a :href="source.href" target="_blank" rel="noopener noreferrer">{{ source.title }}<WorkspaceIcon name="expand" /></a></li></ul></section>
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import WorkspaceIcon from '../WorkspaceIcon.vue'
import CalibrationPlot from './CalibrationPlot.vue'
import { calculate, calculators, formatNumber, unitSets } from './calculators.js'
const props = defineProps({ toolId: { type: String, required: true } })
const definition = computed(() => calculators[props.toolId])
const defaults = () => Object.fromEntries(definition.value.fields.map(field => [field.id, field.value ?? '']))
const values = reactive(defaults()), output = ref(null), error = ref(null), exampleLoaded = ref(false)
function options(field) { return props.toolId === 'units' && ['from', 'to'].includes(field.id) ? Object.keys(unitSets[values.quantity]?.units || {}).map(unit => [unit, unit]) : field.options }
function fieldUnit(field) { return props.toolId === 'dilution' && ['stock', 'target'].includes(field.id) ? values.unit : field.unit }
function describedBy(field) { return [field.hint ? `calc-${field.id}-hint` : '', error.value?.field === field.id ? `calc-${field.id}-error` : ''].filter(Boolean).join(' ') || undefined }
watch(() => values.quantity, quantity => { if (props.toolId !== 'units') return; const units = Object.keys(unitSets[quantity]?.units || {}); values.from = units[0]; values.to = units[1] || units[0] })
watch(values, () => { output.value = null; error.value = null }, { deep: true, flush: 'sync' })
function fillExample() { Object.assign(values, definition.value.example); exampleLoaded.value = true }
function reset() { Object.assign(values, defaults()); exampleLoaded.value = false; output.value = null; error.value = null }
async function run() {
  output.value = null; error.value = null
  try { output.value = calculate(props.toolId, values) }
  catch (e) { error.value = { field: e.field || '', message: e.message || '计算未完成，请核对参数。' }; await nextTick(); document.getElementById(`calc-${e.field}`)?.focus() }
}
function download() {
  const text = [definition.value.name, exampleLoaded.value ? '含示例来源参数，请核对是否已替换为实测值。' : '', '\n输入参数', ...definition.value.fields.map(field => `${field.label}: ${values[field.id]} ${fieldUnit(field) || ''}`), '\n计算结果', ...output.value.items.map(item => `${item.label}: ${formatNumber(item.value)} ${item.unit}`), ...output.value.notes, '\n公式', definition.value.formula, '\n适用说明', definition.value.scope, '\n来源', ...definition.value.sources.map(source => `${source.title}: ${source.href}`)].join('\n')
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' })), link = document.createElement('a')
  link.href = url; link.download = `soilmate-${props.toolId}.txt`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>
