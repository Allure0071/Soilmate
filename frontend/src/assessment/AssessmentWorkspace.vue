<template>
  <component :is="embedded ? 'section' : 'main'" class="assessment-workspace" aria-labelledby="assessment-title">
    <div class="assessment-inner">
      <div class="assessment-breadcrumb"><span>健康评价</span><span aria-hidden="true">/</span><span>{{ steps[pageIndex]?.label }}</span><span class="assessment-review-tag">前端审核预览</span></div>

      <nav v-if="!embedded || page !== 'mode'" class="assessment-progress" aria-label="录入步骤"><ol><li v-for="(item, index) in steps" :key="item.id" :class="{ current: page === item.id, completed: index < pageIndex }" :aria-current="page === item.id ? 'step' : undefined"><button v-if="index < pageIndex" type="button" :aria-label="`返回${item.label}`" @click="goPage(item.id)"><span class="assessment-step-marker"><svg class="assessment-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg></span><b>{{ item.label }}</b></button><span v-else class="assessment-step-label"><span class="assessment-step-marker">{{ index + 1 }}</span><b>{{ item.label }}</b></span></li></ol></nav>
      <header class="assessment-intro">
        <div class="assessment-intro-copy"><component :is="embedded ? 'h2' : 'h1'" id="assessment-title" tabindex="-1">{{ page === 'mode' ? '选择评价方式' : pageTitle }}</component><p v-if="page !== 'mode'">{{ pageDescription }}</p></div>
        <button type="button" class="assessment-map-link" @click="$emit('navigate', 'explore')"><svg class="assessment-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16" /></svg>返回地图</button>
      </header>

      <section v-if="page === 'mode'" class="assessment-mode-section" aria-label="评价方式">
        <div class="assessment-mode-options" role="radiogroup" aria-label="选择评价模式">
          <label :class="{ selected: mode === 'quick' }"><span class="assessment-mode-top"><svg class="assessment-icon assessment-mode-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6M10 3v7l-5 8a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-8V3M8 14h8" /></svg><input v-model="mode" type="radio" name="assessment-mode" value="quick" aria-label="快速试用" /></span><b>快速试用</b><p>已有检测值，直接录入。</p></label>
          <label :class="{ selected: mode === 'deep' }"><span class="assessment-mode-top"><svg class="assessment-icon assessment-mode-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16" /></svg><input v-model="mode" type="radio" name="assessment-mode" value="deep" aria-label="深度分析" /></span><b>深度分析</b><p>记录地块背景与检测数据。</p></label>
        </div>
        <div class="assessment-page-actions"><button type="button" class="assessment-primary-button" @click="goPage(mode === 'deep' ? 'background' : 'input')">{{ mode === 'deep' ? '下一步：地块资料' : '开始录入' }}</button></div>
      </section>

      <div v-if="page !== 'mode'" class="assessment-content">
        <div v-if="page !== 'review'" class="assessment-primary">
          <section v-if="page === 'background'" class="assessment-field-section" aria-labelledby="assessment-field-title">
            <div class="assessment-section-heading"><h2 id="assessment-field-title">地块与作物</h2><span class="assessment-draft-label"><span class="assessment-save-dot" :class="{ unavailable: !storageAvailable }" aria-hidden="true"></span>{{ storageAvailable ? '草稿自动保存' : '草稿未保存' }}</span></div>
            <div class="assessment-context-grid"><label>地块名称<input v-model="context.field_name" placeholder="如：东侧试验田" maxlength="100" /></label><label>种植作物<input v-model="context.crop_name" placeholder="如：水稻、玉米" maxlength="80" /></label></div>
            <label class="assessment-background-field">地块位置<input v-model="context.location_label" placeholder="填写地区或从地图带入位置" maxlength="180" /></label>
            <label class="assessment-background-field">地块管理背景 <span class="assessment-optional">选填</span><textarea v-model="context.background" rows="2" maxlength="1500" placeholder="前茬、施肥历史，或目前关注的问题"></textarea></label>
            <details class="assessment-extra-details"><summary>过程检测方案的后续安排</summary><p>N+X 推荐清单与多个检测时点将在后续接入，当前可以先录入已有指标。</p></details>
            <div class="assessment-form-actions"><button type="button" class="assessment-secondary-button" @click="goPage('mode')">上一步</button><button type="button" class="assessment-primary-button" @click="goPage('input')">下一步：检测录入</button></div>
          </section>

          <section v-if="page === 'input'" class="assessment-entry-section" aria-labelledby="assessment-entry-title">
            <div class="assessment-section-heading"><h2 id="assessment-entry-title">本次检测</h2><span class="assessment-draft-label"><span class="assessment-save-dot" :class="{ unavailable: !storageAvailable }" aria-hidden="true"></span>{{ storageAvailable ? '草稿自动保存' : '草稿未保存' }}</span></div>
            <button type="button" class="assessment-back-link" @click="goPage(mode === 'deep' ? 'background' : 'mode')">{{ mode === 'deep' ? '返回地块资料' : '更换评价方式' }}</button>

            <form novalidate @submit.prevent="checkInput">
              <div class="assessment-context-grid assessment-quick-context"><label>种植作物 <span>选填</span><input v-model="context.crop_name" placeholder="如：水稻、玉米" maxlength="80" /></label><label>样本名称 <span>选填</span><input v-model="context.sample_alias" placeholder="如：地块 A 表层样本" maxlength="100" /></label></div>
              <div v-if="mapLocation" class="assessment-map-context"><svg class="assessment-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/></svg><span>地图参考位置：{{ mapLocation }}<small>仅作为位置背景，不自动填入实测值。</small></span></div>

              <div class="assessment-input-toolbar"><b>检测指标</b><div class="assessment-toolbar-actions"><button class="assessment-text-button" type="button" @click="fillExample">填入示例</button><button class="assessment-import-button" type="button" disabled>文件导入（待接入）</button></div></div>

              <div class="assessment-row-head" aria-hidden="true"><span>检测指标</span><span>检测值</span><span>报告单位</span><span></span></div>
              <div v-if="!rows.length" class="assessment-empty-input"><b>还没有检测指标</b><p>添加一个指标，即可填写本次检测值。</p></div>
              <div v-for="(row, index) in rows" :key="row.id" class="assessment-measurement-row" :class="{ 'has-error': errors[row.id] }">
                <label class="assessment-indicator-field"><span class="assessment-mobile-field-label">检测指标</span><select v-model="row.indicator_code" :aria-label="`第 ${index + 1} 项检测指标`" @change="changeIndicator(row)"><option v-for="indicator in reviewIndicators" :key="indicator.code" :value="indicator.code">{{ indicator.name }}</option></select></label>
                <label class="assessment-value-field"><span class="assessment-mobile-field-label">检测值</span><input v-model="row.value" type="text" inputmode="decimal" placeholder="填写数值" maxlength="100" :aria-label="`第 ${index + 1} 项检测值`" :aria-invalid="Boolean(errors[row.id])" :aria-describedby="errors[row.id] ? `error-${row.id}` : undefined" /></label>
                <label class="assessment-unit-field"><span class="assessment-mobile-field-label">报告单位</span><select v-model="row.unit" :aria-label="`第 ${index + 1} 项报告单位`" :disabled="!indicatorFor(row).units.length"><option v-if="!indicatorFor(row).units.length" value="">无量纲</option><option v-for="unit in indicatorFor(row).units" :key="unit" :value="unit">{{ unit }}</option></select></label>
                <button class="assessment-remove-row" type="button" :aria-label="`删除第 ${index + 1} 项指标`" @click="removeRow(row.id)"><svg class="assessment-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6" /></svg></button>
                <p v-if="errors[row.id]" :id="`error-${row.id}`" class="assessment-row-error">{{ errors[row.id] }}</p>
              </div>

              <button type="button" class="assessment-add-row" :disabled="rows.length >= reviewIndicators.length" @click="addRow"><svg class="assessment-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>添加检测指标</button>
              <details class="assessment-extra-details"><summary>补充采样与检测信息 <span>选填</span></summary><div class="assessment-context-grid"><label>采样日期<input v-model="context.sampling_date" type="date" /></label><label>检测方法说明<input v-model="context.method_note" placeholder="可按报告记录方法或机构" maxlength="200" /></label></div></details>

              <p v-if="formError" class="assessment-form-error" role="alert">{{ formError }}</p>
              <div class="assessment-form-actions"><button type="button" class="assessment-secondary-button" @click="saveDraft(true)">保存草稿</button><button type="submit" class="assessment-primary-button">下一步：确认录入</button></div>
              <p class="assessment-storage-note">{{ storageAvailable ? '草稿自动保留在当前浏览器，尚未提交到服务器。' : '浏览器存储不可用，离开页面前请自行保留输入。' }}</p>
            </form>

          </section>
        </div>

        <section v-if="page === 'review'" class="assessment-entry-section assessment-review-section" aria-label="录入确认">
          <div class="assessment-confirm-banner"><span aria-hidden="true"><svg class="assessment-icon" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg></span><div><h2>已整理 {{ rowInspection.values.length }} 项有效指标</h2><p>请核对检测值与报告单位，当前尚未提交分析。</p></div></div>
          <table class="assessment-review-table"><caption>本次有效检测指标</caption><thead><tr><th scope="col">检测指标</th><th scope="col">检测值</th><th scope="col">报告单位</th></tr></thead><tbody><tr v-for="value in rowInspection.values" :key="value.indicator_code"><th scope="row">{{ indicatorName(value.indicator_code) }}</th><td>{{ value.value }}</td><td>{{ value.unit || '无量纲' }}</td></tr></tbody></table>
          <dl class="assessment-review-meta"><div><dt>评价方式</dt><dd>{{ mode === 'quick' ? '快速试用' : '深度分析' }}</dd></div><div><dt>检测样本</dt><dd>{{ context.sample_alias.trim() || '未命名样本' }}</dd></div><div v-if="context.crop_name.trim()"><dt>种植作物</dt><dd>{{ context.crop_name }}</dd></div><div v-if="mode === 'deep' && context.field_name.trim()"><dt>地块名称</dt><dd>{{ context.field_name }}</dd></div><div v-if="mode === 'deep' && context.location_label.trim()"><dt>地块位置</dt><dd>{{ context.location_label }}</dd></div><div v-if="context.sampling_date"><dt>采样日期</dt><dd>{{ context.sampling_date }}</dd></div><div v-if="context.method_note.trim()"><dt>检测方法</dt><dd>{{ context.method_note }}</dd></div><div v-if="mode === 'deep' && context.background.trim()"><dt>管理背景</dt><dd>{{ context.background }}</dd></div></dl>
          <p v-if="rowInspection.emptyCount" class="assessment-storage-note">{{ rowInspection.emptyCount }} 个空白项不计入本次输入。</p>
          <div class="assessment-analysis-note"><b>下一阶段：评价与决策</b><p>分析服务待接入。接入后将单独展示评价、问题分析与种植建议，并支持继续追问。</p></div>
          <div class="assessment-form-actions"><button type="button" class="assessment-secondary-button" @click="goPage('input')">返回修改</button><button type="button" class="assessment-primary-button" disabled>提交分析（待接入）</button></div>
        </section>
      </div>
      <div class="assessment-feedback" aria-live="polite" role="status"><p v-if="message">{{ message }}</p></div>
      <footer class="assessment-footer"><span>{{ storageAvailable ? '草稿仅存当前浏览器，分析服务尚未接入。' : '浏览器存储不可用，请自行保留当前输入。' }}</span><button type="button" @click="$emit('navigate', 'home')">返回首页</button></footer>
    </div>
  </component>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { createRow, inspectRows, restoreRows, reviewIndicators } from './measurementDraft.js'

const props = defineProps({ account: { type: Object, default: null }, preview: { type: Boolean, default: false }, mapPoint: { type: Object, default: null }, embedded: { type: Boolean, default: false } })
defineEmits(['navigate'])
const storageKey = `soilmate.assessment.input-review.v1.${props.preview ? 'preview' : props.account?.id || 'guest'}`
const storageAvailable = ref(true)
let saved = null
try { saved = JSON.parse(localStorage.getItem(storageKey) || 'null') } catch { storageAvailable.value = false }
const queryMode = new URLSearchParams(location.search).get('mode')
const mode = ref(['quick', 'deep'].includes(queryMode) ? queryMode : saved?.mode === 'deep' ? 'deep' : 'quick')
const context = reactive({ crop_name: '', sample_alias: '', field_name: '', location_label: '', background: '', sampling_date: '', method_note: '' })
if (saved?.context && typeof saved.context === 'object') {
  for (const key of Object.keys(context)) if (typeof saved.context[key] === 'string') context[key] = saved.context[key].slice(0, 1500)
}
const rows = ref(restoreRows(saved?.rows))
const errors = ref({})
const formError = ref('')
const page = ref('mode')
const message = ref('')
let messageTimer
const rowInspection = computed(() => inspectRows(rows.value))
const steps = computed(() => [{ id: 'mode', label: '选择方式' }, ...(mode.value === 'deep' ? [{ id: 'background', label: '地块资料' }] : []), { id: 'input', label: '检测录入' }, { id: 'review', label: '录入确认' }])
const pageIndex = computed(() => steps.value.findIndex(item => item.id === page.value))
const pageTitle = computed(() => ({ mode: '从一次检测，开始了解土地。', background: '先了解这块土地。', input: '填写本次检测结果。', review: '核对输入，准备下一步。' })[page.value])
const pageDescription = computed(() => ({ mode: '选择适合你的方式，每一步都可以返回调整。', background: '记录地块位置、种植作物与管理背景。', input: '一项有效指标也可以开始，按检测报告填写数值与单位。', review: '确认本次录入后，再进入评价与决策。' })[page.value])
function indicatorName(code) { return reviewIndicators.find(item => item.code === code)?.name || code }
const mapLocation = computed(() => {
  const point = props.mapPoint
  if (!point || !Number.isFinite(point.lon) || !Number.isFinite(point.lat)) return ''
  return `${point.lon.toFixed(4)}° E，${point.lat.toFixed(4)}° N`
})
if (!context.location_label && mapLocation.value) context.location_label = mapLocation.value
function indicatorFor(row) { return reviewIndicators.find(item => item.code === row.indicator_code) || reviewIndicators[0] }
function notify(text) { clearTimeout(messageTimer); message.value = text; messageTimer = setTimeout(() => { message.value = '' }, 4000) }
function saveDraft(announce = false) {
  try {
    localStorage.setItem(storageKey, JSON.stringify({ version: 1, mode: mode.value, context: { ...context }, rows: rows.value }))
    storageAvailable.value = true
    if (announce) notify('草稿已保存在当前浏览器。')
  } catch { storageAvailable.value = false; if (announce) notify('浏览器未允许保存草稿，请保留当前页面。') }
}
function syncModeUrl() {
  const url = new URL(location.href)
  url.searchParams.set('mode', mode.value)
  url.searchParams.set('step', page.value)
  history.replaceState(history.state, '', url.pathname + url.search + url.hash)
}
async function focusPage() {
  await nextTick()
  const title = document.getElementById('assessment-title')
  title?.closest('.assessment-workspace')?.scrollTo({ top: 0 })
  title?.focus({ preventScroll: true })
}
function goPage(target) {
  if (target === 'review' && !rowInspection.value.valid) target = 'input'
  if (target === 'background' && mode.value !== 'deep') target = 'input'
  if (page.value === target) return
  page.value = target
  errors.value = {}; formError.value = ''; message.value = ''
  const url = new URL(location.href)
  url.searchParams.set('mode', mode.value)
  url.searchParams.set('step', page.value)
  history.pushState(history.state, '', url.pathname + url.search + url.hash)
  focusPage()
}
function readPageFromUrl(focus = false) {
  if (!['/assessment', '/assessment/preview', '/research'].includes(location.pathname)) return
  const params = new URLSearchParams(location.search)
  if (['quick', 'deep'].includes(params.get('mode'))) mode.value = params.get('mode')
  const requested = params.get('step') || 'mode'
  page.value = steps.value.some(item => item.id === requested) ? requested : 'mode'
  if (page.value === 'review' && !rowInspection.value.valid) {
    page.value = 'input'
    notify('请先完成至少一项有效检测值，再确认录入。')
    syncModeUrl()
  } else if (page.value !== requested) syncModeUrl()
  errors.value = {}; formError.value = ''
  if (focus) focusPage()
}
function onPopState() { readPageFromUrl(true) }
function changeIndicator(row) { row.unit = indicatorFor(row).units[0] || '' }
async function addRow() {
  if (rows.value.length >= reviewIndicators.length) return
  const used = new Set(rows.value.map(row => row.indicator_code))
  rows.value.push(createRow(reviewIndicators.find(item => !used.has(item.code))?.code))
  await nextTick()
  document.querySelector(`[aria-label="第 ${rows.value.length} 项检测值"]`)?.focus()
}
function removeRow(id) { rows.value = rows.value.filter(row => row.id !== id) }
function fillExample() {
  const examples = [{ code: 'soil_ph', value: '6.2' }, { code: 'TN', value: '1.2' }, { code: 'cec', value: '18' }]
  if (!rows.value.some(row => String(row.value).trim())) rows.value = examples.map(item => ({ ...createRow(item.code), value: item.value }))
  else for (const row of rows.value) if (!String(row.value).trim()) row.value = examples.find(item => item.code === row.indicator_code)?.value || ''
  if (!context.sample_alias) context.sample_alias = '前端示例样本'
  notify('已填入界面示例；示例数值不是实际地块记录，已有数值未覆盖。')
}
async function checkInput() {
  const result = inspectRows(rows.value)
  errors.value = result.errors
  formError.value = result.valid ? '' : Object.keys(result.errors).length ? '请核对标出的输入问题。' : '请至少填写一项有效检测值。'
  if (!result.valid) {
    await nextTick()
    const target = document.querySelector('.assessment-measurement-row.has-error input') || document.querySelector('.assessment-value-field input') || document.querySelector('.assessment-add-row')
    target?.focus()
    return
  }
  saveDraft()
  goPage('review')
}
watch([mode, context, rows], () => { errors.value = {}; formError.value = ''; saveDraft() }, { deep: true, flush: 'sync' })
watch(mode, syncModeUrl)
readPageFromUrl()
onMounted(() => window.addEventListener('popstate', onPopState))
onBeforeUnmount(() => { clearTimeout(messageTimer); window.removeEventListener('popstate', onPopState) })
</script>

<style src="./assessment.css"></style>
