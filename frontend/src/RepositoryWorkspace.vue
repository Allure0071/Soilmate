<template>
  <div class="repository">
    <header class="repository-header">
      <div>
        <p class="repository-eyebrow">SOILMATE · SCIENTIFIC DATA REPOSITORY</p>
        <h1 id="browser-title" tabindex="-1">数据资源库</h1>
        <p class="repository-description">检索土壤与环境变量，核对元数据和质量信息，再进入空间地图查看网格。</p>
      </div>
      <button class="repository-raw-link" type="button" @click="$emit('open-database')">浏览原始数据表 <span aria-hidden="true">↗</span></button>
    </header>

    <section class="repository-overview" aria-label="数据目录概览">
      <div class="repository-overview-head">
        <div><h2>目录概览</h2><span class="repository-overview-status"><i aria-hidden="true"></i>{{ overviewStatus }}</span></div>
        <button type="button" :disabled="overviewLoading" @click="refreshOverview">{{ overviewLoading ? '同步中…' : '刷新目录统计' }}</button>
      </div>
      <div class="repository-overview-body">
        <div class="repository-chart" role="img" :aria-label="chartDescription">
          <div v-for="res in [5, 1]" :key="res" class="repository-chart-row">
            <div class="repository-chart-label"><strong>{{ res }} km</strong><span>{{ countFor(res) }} 项登记指标</span></div>
            <div class="repository-chart-track">
              <span v-for="segment in segmentsFor(res)" :key="segment.id" class="repository-chart-segment" :class="`repository-chart-${segment.id}`" :style="{ width: `${segment.percent}%` }" :title="`${segment.label}：${segment.count} 项`"></span>
            </div>
          </div>
          <div class="repository-chart-legend"><span v-for="item in chartCategories" :key="item.id"><i :class="`repository-chart-${item.id}`" aria-hidden="true"></i>{{ item.label }}</span></div>
        </div>
        <div class="repository-overview-facts">
          <div><strong>2</strong><span>网格分辨率</span></div>
          <div><strong class="repository-fact-pending">待核验</strong><span>农业分区覆盖统计</span></div>
        </div>
      </div>
      <p class="repository-overview-note">图中为当前接口登记指标的类别构成；类别根据变量代码暂归类，并非时间趋势或空间覆盖率。</p>
    </section>

    <template v-if="view === 'catalog'">
      <div class="repository-catalog-layout">
        <button v-if="filtersOpen" class="repository-filter-backdrop" type="button" aria-label="关闭筛选面板" @click="closeFilters"></button>
        <aside class="repository-filter-panel" :class="{ 'is-open': filtersOpen }" :role="filtersOpen ? 'dialog' : undefined" :aria-modal="filtersOpen ? 'true' : undefined" aria-label="筛选数据目录" @keydown="handleFilterKeydown">
          <div class="repository-filter-head"><div><h2>筛选目录</h2><span>按登记字段缩小范围</span></div><button class="repository-filter-close" type="button" aria-label="关闭筛选面板" @click="closeFilters">×</button></div>
          <div class="repository-filter-group"><h3>网格分辨率</h3><button v-for="value in [5, 1]" :key="value" type="button" :aria-pressed="resolution === value" :class="{ active: resolution === value }" @click="$emit('resolution-change', value)"><span>{{ value }} km</span><span>{{ countFor(value) }}</span></button></div>
          <div class="repository-filter-group"><h3>数据类型</h3><button v-for="item in categories" :key="item.id" type="button" :aria-pressed="category === item.id" :class="{ active: category === item.id }" @click="category = item.id"><span>{{ item.label }}</span><span>{{ categoryCount(item.id) }}</span></button></div>
          <div class="repository-filter-group"><h3>来源登记</h3><button v-for="item in sourceOptions" :key="item.id" type="button" :aria-pressed="sourceStatus === item.id" :class="{ active: sourceStatus === item.id }" @click="sourceStatus = item.id"><span>{{ item.label }}</span><span>{{ sourceCount(item.id) }}</span></button></div>
          <div class="repository-filter-actions"><button type="button" @click="resetFilters">重置条件</button><button type="button" @click="closeFilters">查看 {{ filtered.length }} 项结果</button></div>
        </aside>

        <section class="repository-results" aria-label="指标目录">
          <div class="repository-results-head"><div><h2>数据目录</h2><p>当前显示 {{ filtered.length }} / {{ indicators.length }} 项 · {{ resolution }} km 网格</p></div><span class="repository-readonly">只读目录 · 选择指标查看详情</span></div>
          <div class="repository-results-tools"><button class="repository-mobile-filter" type="button" @click="openFilters">筛选条件<span v-if="activeFilterCount">{{ activeFilterCount }}</span></button><label class="repository-search"><span class="sr-only">搜索数据目录</span><input v-model="search" type="search" placeholder="搜索指标、变量代码或来源文件" autocomplete="off"></label></div>
        <div v-if="apiState === 'loading'" class="repository-state" role="status">正在读取指标目录…</div>
        <div v-else-if="apiState === 'error'" class="repository-state" role="alert">{{ error }} <button type="button" @click="$emit('retry')">重新连接</button></div>
        <div v-else-if="!filtered.length" class="repository-state">没有匹配的指标。请更换关键词、类别、来源状态或分辨率。</div>
        <div v-else class="repository-table-scroll"><table class="repository-table"><thead><tr><th scope="col" :aria-sort="sortAria('name')"><button type="button" @click="toggleSort('name')">指标 / 变量 <span aria-hidden="true">{{ sortMark('name') }}</span></button></th><th scope="col" :aria-sort="sortAria('category')"><button type="button" @click="toggleSort('category')">类型 <span aria-hidden="true">{{ sortMark('category') }}</span></button></th><th scope="col">单位</th><th scope="col" :aria-sort="sortAria('valid')"><button type="button" @click="toggleSort('valid')">有效像元 <span aria-hidden="true">{{ sortMark('valid') }}</span></button></th><th scope="col" :aria-sort="sortAria('source')"><button type="button" @click="toggleSort('source')">来源登记 <span aria-hidden="true">{{ sortMark('source') }}</span></button></th><th scope="col"><span class="sr-only">操作</span></th></tr></thead><tbody><tr v-for="item in pageItems" :key="item.col_name"><td><button class="repository-item-link" type="button" @click="openDetail(item.col_name)"><strong>{{ nameOf(item) }}</strong><code>{{ item.col_name }}</code></button></td><td>{{ groupLabel(item.col_name) }}</td><td>{{ unitOf(item) }}</td><td class="repository-number">{{ item.valid_count == null ? '未统计' : Number(item.valid_count).toLocaleString() }}</td><td><span :class="item.source_file ? 'repository-status-ok' : 'repository-status-pending'">{{ item.source_file ? '文件已登记' : '来源待补' }}</span></td><td><button class="repository-row-open" type="button" :aria-label="`查看${nameOf(item)}详情`" @click="openDetail(item.col_name)">查看 ↗</button></td></tr></tbody></table></div>
        <footer v-if="filtered.length" class="repository-pagination"><span>第 {{ page }} / {{ pageCount }} 页 · 每页 {{ pageSize }} 项</span><div><button type="button" :disabled="page <= 1" @click="page--">上一页</button><button type="button" :disabled="page >= pageCount" @click="page++">下一页</button></div></footer>
        </section>
      </div>
      <p class="repository-footnote">类别按变量代码暂归类，使用前请核对。登记指标不等于实测样本；网格值、来源文件与质量审计应分别查看。</p>
    </template>

    <template v-else>
      <nav class="repository-breadcrumb" aria-label="当前位置"><button type="button" @click="backToCatalog">数据目录</button><span aria-hidden="true">/</span><span>指标详情</span></nav>
      <div v-if="selected" class="repository-detail">
        <div class="repository-detail-title"><div><span class="repository-detail-tag">{{ groupLabel(selected.col_name) }} · {{ resolution }} km</span><h2>{{ nameOf(selected) }}</h2><code>{{ selected.col_name }}</code></div><button class="repository-preview-button" type="button" @click="$emit('map-preview', selected.col_name)">打开空间预览 <span aria-hidden="true">↗</span></button></div>
        <div class="repository-detail-grid">
          <section class="repository-detail-section"><header><span>01 / 元数据</span><h3>已登记字段</h3></header><dl><div><dt>单位</dt><dd>{{ unitOf(selected) }}</dd></div><div><dt>空间分辨率</dt><dd>{{ resolution }} km</dd></div><div><dt>原始来源文件</dt><dd>{{ selected.source_file || '未登记' }}</dd></div><div><dt>波段</dt><dd>{{ selected.band ?? '未登记' }}</dd></div><div><dt>数值范围</dt><dd>{{ rangeOf(selected) }}</dd></div><div><dt>平均值</dt><dd>{{ metricOf(selected, selected.mean) }}</dd></div></dl></section>
          <section class="repository-detail-section"><header><span>02 / 质量审计</span><h3>当前可核对的质量信息</h3></header><dl><div><dt>有效像元</dt><dd>{{ selected.valid_count == null ? '未统计' : Number(selected.valid_count).toLocaleString() }}</dd></div><div><dt>缺失率</dt><dd class="repository-pending">未统计</dd></div><div><dt>异常值比例</dt><dd class="repository-pending">未统计</dd></div><div><dt>空间覆盖率</dt><dd class="repository-pending">未统计</dd></div></dl><p class="repository-detail-note">有效像元数不能直接换算为独立样本数；当前目录没有足够信息计算缺失率或覆盖率。</p></section>
          <section class="repository-detail-section repository-provenance"><header><span>03 / 来源与使用条件</span><h3>待补齐的溯源信息</h3></header><dl><div><dt>数据年份</dt><dd class="repository-pending">未登记</dd></div><div><dt>土层深度</dt><dd class="repository-pending">未登记</dd></div><div><dt>论文 DOI / 原始下载地址</dt><dd class="repository-pending">未登记</dd></div><div><dt>处理版本</dt><dd class="repository-pending">未登记</dd></div><div><dt>许可协议</dt><dd class="repository-pending">未登记</dd></div><div><dt>九大农业区覆盖</dt><dd class="repository-pending">尚未核验映射</dd></div></dl></section>
          <section class="repository-detail-section repository-spatial"><header><span>04 / 空间数据</span><h3>地图与网格预览</h3></header><p>在地图工作台查看该变量的空间位置和网格查询结果。{{ tilesAvailable === false ? '当前专题瓦片未发布，仍可查询可用网格值。' : '图层是否可显示取决于当前瓦片服务。' }}</p><button type="button" @click="$emit('map-preview', selected.col_name)">进入地图工作台 <span aria-hidden="true">↗</span></button></section>
        </div>
      </div>
      <div v-else class="repository-state">当前分辨率下找不到该指标。<button type="button" @click="backToCatalog">返回数据目录</button></div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { fetchIndicators } from './api.js'
import { displayName, displayUnit, displayValue } from './dataDisplay.js'

const props = defineProps({ indicators: { type: Array, default: () => [] }, resolution: { type: Number, default: 5 }, apiState: { type: String, default: 'loading' }, error: { type: String, default: '' }, tilesAvailable: { type: Boolean, default: null } })
const emit = defineEmits(['resolution-change', 'map-preview', 'open-database', 'retry'])
const categories = [{ id: 'all', label: '全部' }, { id: 'soil', label: '土壤' }, { id: 'env', label: '环境' }, { id: 'crop', label: '农业' }, { id: 'spatial', label: '空间' }, { id: 'water', label: '水域' }]
const sourceOptions = [{ id: 'all', label: '全部' }, { id: 'registered', label: '文件已登记' }, { id: 'missing', label: '来源待补' }]
const search = ref('')
const category = ref('all')
const sourceStatus = ref('all')
const filtersOpen = ref(false)
const sortKey = ref('category')
const sortDirection = ref('asc')
const page = ref(1)
const pageSize = 25
const view = ref('catalog')
const detailKey = ref('')
const counts = ref({ 5: null, 1: null })
const catalogs = ref({ 5: [], 1: [] })
const overviewLoading = ref(false)
const overviewError = ref(false)
const overviewSynced = ref(false)
const chartCategories = categories.filter(item => item.id !== 'all')
const chartDescription = computed(() => [5, 1].map(res => `${res} 公里：${countFor(res)} 项；${segmentsFor(res).map(item => `${item.label} ${item.count} 项`).join('，') || '类别数据读取中'}`).join('。'))
const overviewStatus = computed(() => overviewLoading.value ? '正在同步目录' : overviewError.value ? '部分统计暂不可用' : overviewSynced.value ? '已从目录接口同步' : '等待目录数据')
const activeFilterCount = computed(() => Number(category.value !== 'all') + Number(sourceStatus.value !== 'all'))
const filtered = computed(() => { const query = search.value.trim().toLocaleLowerCase(); const order = { soil: 0, spatial: 1, env: 2, crop: 3, water: 4 }; return props.indicators.filter(item => (category.value === 'all' || groupOf(item.col_name) === category.value) && (sourceStatus.value === 'all' || (sourceStatus.value === 'registered') === Boolean(item.source_file)) && (!query || `${item.col_name} ${nameOf(item)} ${item.source_file || ''}`.toLocaleLowerCase().includes(query))).sort((a, b) => { let result = 0; if (sortKey.value === 'category') result = (order[groupOf(a.col_name)] ?? 9) - (order[groupOf(b.col_name)] ?? 9); if (sortKey.value === 'name') result = nameOf(a).localeCompare(nameOf(b), 'zh-CN'); if (sortKey.value === 'valid') result = (a.valid_count == null ? -1 : Number(a.valid_count)) - (b.valid_count == null ? -1 : Number(b.valid_count)); if (sortKey.value === 'source') result = Number(Boolean(a.source_file)) - Number(Boolean(b.source_file)); return (sortDirection.value === 'asc' ? result : -result) || nameOf(a).localeCompare(nameOf(b), 'zh-CN') || a.col_name.localeCompare(b.col_name) }) })
const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const pageItems = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const selected = computed(() => props.indicators.find(item => item.col_name === detailKey.value) || null)
watch([search, category, sourceStatus, () => props.resolution, sortKey, sortDirection], () => { page.value = 1 })
watch(() => props.indicators, items => { if (props.apiState === 'ready') { counts.value[props.resolution] = items.length; catalogs.value[props.resolution] = items } })
watch(() => props.apiState, state => { if (state === 'ready') { counts.value[props.resolution] = props.indicators.length; catalogs.value[props.resolution] = props.indicators } })

function groupOf(key) { if (/^(corn|rice|soybean|wheat)(_|$)/.test(key)) return 'crop'; if (key.startsWith('soil_') || key === 'ece') return 'soil'; if (key.startsWith('water_')) return 'water'; if (['dem', 'farm_field', 'landscan', 'waterdist'].includes(key)) return 'spatial'; return 'env' }
function groupLabel(key) { return categories.find(item => item.id === groupOf(key))?.label || '环境' }
function nameOf(item) { return displayName(item.col_name, item.cname || item.name) }
function unitOf(item) { return displayUnit(item.col_name, item.unit) || (item.col_name === 'soil_ph' ? '无量纲' : '单位待核对') }
function metricOf(item, value) { const number = displayValue(item.col_name, value); return number == null || !Number.isFinite(Number(number)) ? '未统计' : Number(number).toLocaleString('zh-CN', { maximumFractionDigits: 3 }) }
function rangeOf(item) { return item.min == null || item.max == null ? '未统计' : `${metricOf(item, item.min)} – ${metricOf(item, item.max)}` }
function countFor(res) { return counts.value[res] == null ? '—' : Number(counts.value[res]).toLocaleString() }
function categoryCount(id) { return id === 'all' ? props.indicators.length : props.indicators.filter(item => groupOf(item.col_name) === id).length }
function sourceCount(id) { return id === 'all' ? props.indicators.length : props.indicators.filter(item => (id === 'registered') === Boolean(item.source_file)).length }
function resetFilters() { search.value = ''; category.value = 'all'; sourceStatus.value = 'all' }
function sortAria(key) { return sortKey.value === key ? (sortDirection.value === 'asc' ? 'ascending' : 'descending') : 'none' }
function sortMark(key) { return sortKey.value === key ? (sortDirection.value === 'asc' ? '↑' : '↓') : '↕' }
function toggleSort(key) { if (sortKey.value === key) sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'; else { sortKey.value = key; sortDirection.value = key === 'valid' ? 'desc' : 'asc' } }
async function openFilters() { filtersOpen.value = true; await nextTick(); document.querySelector('.repository-filter-close')?.focus() }
async function closeFilters() { filtersOpen.value = false; await nextTick(); document.querySelector('.repository-mobile-filter')?.focus() }
function handleFilterKeydown(event) { if (event.key === 'Escape') { closeFilters(); return } if (event.key !== 'Tab') return; const controls = [...event.currentTarget.querySelectorAll('button:not(:disabled)')]; const first = controls[0]; const last = controls[controls.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() } }
function segmentsFor(res) { const items = catalogs.value[res]; if (!items.length) return []; return chartCategories.map(item => { const count = items.filter(row => groupOf(row.col_name) === item.id).length; return { ...item, count, percent: count / items.length * 100 } }).filter(item => item.count > 0) }
async function refreshOverview() { overviewLoading.value = true; overviewError.value = false; const results = await Promise.allSettled([5, 1].map(res => fetchIndicators(res))); results.forEach((result, index) => { if (result.status === 'fulfilled') { const res = [5, 1][index]; const items = result.value.indicators || []; catalogs.value[res] = items; counts.value[res] = items.length } else overviewError.value = true }); overviewSynced.value = results.some(result => result.status === 'fulfilled'); overviewLoading.value = false }
function syncFromLocation() { const params = new URLSearchParams(location.search); detailKey.value = params.get('indicator') || ''; view.value = detailKey.value ? 'detail' : 'catalog'; const requested = Number(params.get('res')); if ([1, 5].includes(requested) && requested !== props.resolution) emit('resolution-change', requested) }
function openDetail(key) { filtersOpen.value = false; detailKey.value = key; view.value = 'detail'; history.pushState({}, '', `/resources?indicator=${encodeURIComponent(key)}&res=${props.resolution}`); document.querySelector('.site-content-resources')?.scrollTo(0, 0); document.querySelector('#browser-title')?.focus({ preventScroll: true }) }
function backToCatalog() { view.value = 'catalog'; detailKey.value = ''; history.pushState({}, '', '/resources'); document.querySelector('.site-content-resources')?.scrollTo(0, 0); document.querySelector('#browser-title')?.focus({ preventScroll: true }) }
onMounted(() => { syncFromLocation(); if (props.apiState === 'ready') { counts.value[props.resolution] = props.indicators.length; catalogs.value[props.resolution] = props.indicators } window.addEventListener('popstate', syncFromLocation); refreshOverview() })
onBeforeUnmount(() => window.removeEventListener('popstate', syncFromLocation))
</script>
