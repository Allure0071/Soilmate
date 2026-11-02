<template>
  <section class="edge-workbench" aria-labelledby="edge-title">
    <header class="edge-header">
      <div><span class="section-kicker">SOILEDGE / FIELD ASSESSMENT</span><h1 id="edge-title">检测数据评估</h1><p>录入实验室检测值，复现 Soiledge 小程序的本地 SHI 估算。</p></div>
      <button type="button" class="edge-back" @click="$emit('close')">返回地图 ×</button>
    </header>
    <div class="edge-body">
      <div class="edge-layout">
        <form class="edge-form" @submit.prevent="calculate">
          <div class="edge-section-heading"><div><span class="section-kicker">INPUT / 样本信息</span><h2>输入检测数据</h2></div><button type="button" @click="fillSample">填入示例</button></div>
          <div class="edge-controls"><label>作物类型<select v-model="crop"><option v-for="item in crops" :key="item" :value="item">{{ item }}</option></select></label><label>评估深度<select v-model="mode"><option value="basic">基础 · 6 项</option><option value="full">专业 · 11 项</option></select></label></div>
          <div class="edge-fields"><label v-for="item in visibleFields" :key="item.key" class="edge-field"><span>{{ item.label }} <small>{{ item.unit }}</small></span><input v-model="values[item.key]" type="number" inputmode="decimal" step="any" :placeholder="item.placeholder" :aria-describedby="`edge-hint-${item.key}`"/><small :id="`edge-hint-${item.key}`">{{ item.hint }}</small></label></div>
          <label class="edge-texture">土壤质地 <small>选填，仅用于记录</small><input v-model.trim="texture" type="text" placeholder="例如：壤土、黏土或砂土"/></label>
          <p v-if="error" class="edge-error" role="alert">{{ error }}</p>
          <div class="edge-actions"><button type="button" @click="clear">清空数据</button><button type="submit">计算研究估算</button></div>
        </form>
        <aside class="edge-result" aria-label="估算结果" aria-live="polite">
          <span class="section-kicker">RESULT / SHI ESTIMATE</span>
          <template v-if="result"><h2>估算结果</h2><div class="edge-score"><strong>{{ result.score.toFixed(2) }}</strong><span>/ 100</span></div><p class="edge-threshold">{{ crop }}参照阈值 {{ result.threshold }} · {{ mode === 'basic' ? '6 项核心' : '11 项完整' }}</p><p class="edge-result-note">{{ result.score >= result.threshold ? '达到该小程序的参照阈值' : '低于该小程序的参照阈值' }}。此结论仅用于研究演示。</p><h3>指标标准化值</h3><div v-for="item in result.details" :key="item.key" class="edge-diagnostic"><div><span>{{ item.label }}</span><strong>{{ item.score.toFixed(2) }} / 100</strong></div><small>输入 {{ item.raw }} {{ item.unit }} · 权重 {{ (item.weight * 100).toFixed(1) }}%</small><div class="edge-track"><i :style="{ width: `${Math.min(100, item.score)}%` }"></i></div></div><p class="edge-method">算法：各指标按小程序的固定范围归一化，按权重加总并除以当前模式的权重和。超出参考范围的值截断至 0–1；须填写当前模式全部指标才能计算。</p><details class="edge-advice"><summary>查看原小程序的改良建议（未经核验）</summary><p v-for="item in result.recommendations" :key="item.key"><strong>{{ item.label }}</strong><br/>{{ item.advice }}</p><p v-if="!result.recommendations.length">当前没有标准化值低于 50 的指标；建议持续监测。</p></details><div class="edge-ai"><button type="button" :disabled="aiLoading" @click="requestAi">{{ aiLoading ? '正在生成…' : '用本机 Ollama 生成说明' }}</button><p v-if="aiMessage" role="status">{{ aiMessage }}</p></div></template>
          <template v-else><h2>等待检测数据</h2><p>填写当前模式的全部指标后计算。示例按钮可体验输入与结果流程。</p><div class="edge-placeholder">06 <span>核心检测指标</span></div></template>
        </aside>
      </div>
      <section class="edge-batch" aria-labelledby="edge-batch-title"><div><span class="section-kicker">BATCH / Excel</span><h2 id="edge-batch-title">批量评估</h2><p>上传 Soiledge 原格式 .xlsx。批量算法会按本批次中位数填补缺失值，再按本批次最小值和最大值标准化；同一站点在不同批次中的估算可能不同。</p></div><div class="edge-batch-controls"><label>Excel 文件<input type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" @change="onFileChange"/></label><label>作物阈值<select v-model="batchCrop"><option value="">按原表样点名称推断</option><option v-for="item in crops" :key="item" :value="item">全部按{{ item }}</option></select></label><button type="button" :disabled="!batchFile || batchLoading" @click="uploadBatch">{{ batchLoading ? '正在计算…' : '上传并计算' }}</button></div><p v-if="batchError" class="edge-error" role="alert">{{ batchError }}</p><div v-if="batchResult" class="edge-batch-result"><div><strong>{{ batchResult.total }} 个样点</strong><span>达到参照阈值 {{ batchResult.above }} · 低于阈值 {{ batchResult.below }} · 中位数填补 {{ batchResult.imputed_cells }} 处</span><button type="button" @click="downloadCsv">下载结果 CSV</button></div><div class="edge-batch-scroll"><table><thead><tr><th scope="col">采样点编号</th><th scope="col">样品编号</th><th scope="col">作物</th><th scope="col">SHI 估算</th><th scope="col">阈值</th><th scope="col">参照判断</th></tr></thead><tbody><tr v-for="(row,index) in batchResult.rows" :key="`${row.site}-${index}`"><td>{{ row.site }}</td><td>{{ row.sample }}</td><td>{{ row.crop }}</td><td>{{ row.score.toFixed(2) }}</td><td>{{ row.threshold }}</td><td>{{ row.level }}</td></tr></tbody></table></div></div></section>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import advice from './soiledgeAdvice.json'
defineEmits(['close'])
const crops = ['设施蔬菜', '水稻', '玉米', '大豆', '中药', '大田']
const thresholds = { 设施蔬菜: 35, 水稻: 14.5, 玉米: 16, 大豆: 20, 中药: 35, 大田: 30 }
// Reproduced from D:/Soil/Soiledge/pages/params/index.js; unvalidated research parameters.
const fields = [
  { key: 'phosphorus', label: '有效磷 AP', unit: 'mg/kg', placeholder: '如 3.076', hint: '检测报告中的有效磷', min: .309, max: 229.056, median: 5.704, direction: 'pos', weight: .4213164150665329 },
  { key: 'clay', label: '黏粒含量', unit: '%', placeholder: '如 23', hint: '粒径小于 0.002 mm 的比例', min: 23, max: 25, median: 23, direction: 'mid', weight: .19248094275775507 },
  { key: 'total_phosphorus', label: '全磷 TP', unit: 'g/kg', placeholder: '如 1.106', hint: '土壤全磷检测值', min: .694048277132854, max: 2.34670073715717, median: .952502979237243, direction: 'pos', weight: .10431811070099721 },
  { key: 'potassium', label: '速效钾 AK', unit: 'mg/kg', placeholder: '如 300.076', hint: '土壤速效钾检测值', min: 99.22786419, max: 412.8045695, median: 208.3420424, direction: 'pos', weight: .056098450142179734 },
  { key: 'total_nitrogen', label: '全氮 TN', unit: '%', placeholder: '如 0.308', hint: '风干基全氮含量', min: .06, max: .532, median: .23625, direction: 'pos', weight: .05514315547644704 },
  { key: 'cec', label: '阳离子交换量 CEC', unit: 'cmol/kg', placeholder: '如 40', hint: '反映土壤保肥能力', min: 17, max: 42, median: 30, direction: 'pos', weight: .04841754508441493 },
  { key: 'total_potassium', label: '全钾 TK', unit: 'g/kg', placeholder: '如 22.45', hint: '土壤全钾检测值', min: 16.1559139784946, max: 28.0321285140562, median: 20.590690471993, direction: 'pos', weight: .033938362849110976 },
  { key: 'bulk_density', label: '土壤容重 BD', unit: 'g/cm³', placeholder: '如 1.10', hint: '反映土壤紧实程度', min: 1, max: 1.3, median: 1.1, direction: 'neg', weight: .028732684270872107 },
  { key: 'organic_carbon', label: '有机碳 SOC', unit: '%', placeholder: '如 2.5752', hint: '填写有机碳，不是有机质', min: .9106, max: 4.9532, median: 2.5114, direction: 'pos', weight: .025493095081457095 },
  { key: 'nitrogen', label: '碱解氮 AN', unit: 'mg/kg', placeholder: '如 200', hint: '反映土壤有效氮供应', min: 60, max: 235.66, median: 190, direction: 'pos', weight: .020388487586283147 },
  { key: 'ph', label: '土壤 pH', unit: 'pH', placeholder: '如 5.24', hint: '土壤酸碱度检测值', min: 4.95, max: 7.83, median: 5.64, direction: 'mid', weight: .01367275098394983 },
]
const sample = { phosphorus: 3.08, clay: 23, total_phosphorus: 1.11, potassium: 300.08, total_nitrogen: .31, cec: 40, total_potassium: 20.35, bulk_density: 1.10, organic_carbon: 2.58, nitrogen: 200, ph: 5.24 }
const values = reactive(Object.fromEntries(fields.map(item => [item.key, ''])))
const crop = ref('设施蔬菜')
const mode = ref('basic')
const texture = ref('')
const error = ref('')
const result = ref(null)
const aiLoading = ref(false)
const aiMessage = ref('')
const batchFile = ref(null)
const batchCrop = ref('')
const batchLoading = ref(false)
const batchError = ref('')
const batchResult = ref(null)
const visibleFields = computed(() => mode.value === 'basic' ? fields.slice(0, 6) : fields)
watch([crop, mode, values], () => { result.value = null; error.value = ''; aiMessage.value = '' }, { deep: true })
function fillSample() { for (const item of fields) values[item.key] = String(sample[item.key]); error.value = ''; result.value = null }
function clear() { for (const item of fields) values[item.key] = ''; texture.value = ''; error.value = ''; result.value = null }
function calculate() {
  result.value = null
  for (const item of visibleFields.value) {
    if (values[item.key] === '' || !Number.isFinite(Number(values[item.key]))) { error.value = `请填写有效的${item.label}数值。`; return }
  }
  error.value = ''
  const details = visibleFields.value.map(item => {
    const raw = Number(values[item.key])
    const range = item.max - item.min
    const deviation = Math.max(Math.abs(item.max - item.median), Math.abs(item.min - item.median))
    const base = item.direction === 'neg' ? (item.max - raw) / range : item.direction === 'mid' ? 1 - Math.abs(raw - item.median) / deviation : (raw - item.min) / range
    const normalized = Math.min(1, Math.max(0, base)) + .0001
    return { ...item, raw, score: normalized * 100, normalized }
  })
  const totalWeight = details.reduce((sum, item) => sum + item.weight, 0)
  const score = details.reduce((sum, item) => sum + item.normalized * item.weight, 0) / totalWeight * 100
  const recommendations = details.filter(item => item.normalized < .5).sort((a, b) => (1.0001 - b.normalized) * b.weight - (1.0001 - a.normalized) * a.weight).slice(0, 6).map(item => ({ key: item.key, label: item.label, advice: item.normalized < .3 ? advice[item.key].severe : advice[item.key].mild }))
  result.value = { score, threshold: thresholds[crop.value], details, recommendations }
}
function onFileChange(event) { batchFile.value = event.target.files?.[0] || null; batchError.value = ''; batchResult.value = null }
async function uploadBatch() {
  if (!batchFile.value) return
  if (!batchFile.value.name.toLowerCase().endsWith('.xlsx') || batchFile.value.size > 12_000_000) { batchError.value = '请选择不超过 12 MB 的 .xlsx 文件。'; return }
  batchLoading.value = true; batchError.value = ''; batchResult.value = null
  try {
    const response = await fetch(`/api/soiledge/upload?crop=${encodeURIComponent(batchCrop.value)}`, { method: 'POST', headers: { 'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }, body: batchFile.value })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.detail || `上传失败（${response.status}）`)
    batchResult.value = payload
  } catch (failure) { batchError.value = failure.message || '上传失败，请检查本地后端。' }
  finally { batchLoading.value = false }
}
function downloadCsv() {
  if (!batchResult.value) return
  const columns = ['site', 'location', 'sample', 'crop', 'score', 'threshold', 'level']
  const names = ['采样点编号', '企业/地点', '样品编号', '作物类型', 'SHI估算', '参照阈值', '参照判断']
  const escape = value => `"${String(value ?? '').replaceAll('"', '""')}"`
  const content = '\ufeff' + [names, ...batchResult.value.rows.map(row => columns.map(key => row[key]))].map(row => row.map(escape).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a'); link.href = url; link.download = 'soiledge-research-estimates.csv'; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
async function requestAi() {
  if (!result.value || aiLoading.value) return
  aiLoading.value = true; aiMessage.value = ''
  try {
    const response = await fetch('/api/soiledge/ai', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ crop: crop.value, score: result.value.score, threshold: result.value.threshold, diagnostics: result.value.details.map(item => ({ label: item.label, raw: item.raw, score: item.score })) }) })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.detail || `生成失败（${response.status}）`)
    aiMessage.value = payload.evaluation || 'Ollama 没有返回内容。'
  } catch (failure) { aiMessage.value = failure.message || '本机 Ollama 暂不可用。' }
  finally { aiLoading.value = false }
}
</script>
