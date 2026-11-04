<template>
  <main class="tools-workspace" aria-labelledby="tools-title">
    <header class="tools-header">
      <div>
        <a v-if="selectedId" class="tool-back-link" :href="directoryHref" @click.prevent="backToDirectory"><WorkspaceIcon name="back" />返回工具目录</a>
        <h1 id="tools-title" tabindex="-1">{{ selectedId ? selectedTool?.name || '工具未找到' : '工具中心' }}</h1>
        <p>{{ selectedId ? selectedTool?.description || '这个工具入口不存在，请返回目录选择。' : '土壤理化计算、数据查询与研究工具。' }}</p>
      </div>
      <label v-if="!selectedId" class="tools-search">
        <WorkspaceIcon name="search" /><span class="visually-hidden">搜索工具</span>
        <input ref="searchInputRef" v-model="query" type="search" aria-label="搜索工具" placeholder="搜索工具，如含水率、SOC、换算" maxlength="200" />
        <button v-if="query" type="button" aria-label="清空搜索" @click="clearSearch"><WorkspaceIcon name="close" /></button>
      </label>
      <span v-else-if="selectedTool" class="tool-status" :class="selectedTool.status">{{ statusLabel(selectedTool) }}</span>
    </header>
    <template v-if="!selectedId">
      <div class="tools-layout">
        <aside class="tools-sidebar">
          <h2>工具分类</h2>
          <HoverSwitch as="nav" class="tools-categories" aria-label="工具分类">
            <button v-for="category in toolCategories" :key="category.id" type="button" :class="{ active: category.id === selectedCategory }" :aria-pressed="category.id === selectedCategory" @click="selectedCategory = category.id">
              {{ category.label }}<span>{{ filterTools('', category.id).length }}</span>
            </button>
          </HoverSwitch>
          <p class="tools-sidebar-note">本地计算 · 无需登录</p>
        </aside>
        <div class="tools-directory">
          <div class="tools-directory-toolbar">
            <p role="status">{{ availableTools.length }} 个可用工具</p>
            <button v-if="visibleTools.length && (query || selectedCategory !== 'all' || domain !== 'all')" type="button" class="tools-reset-filters" @click="clearFilters">清空筛选</button>
          </div>
          <p v-if="domain !== 'all'" class="tools-restored-filter">当前方向：{{ domain }}<button type="button" @click="domain = 'all'">移除方向筛选</button></p>
          <section v-for="group in visibleGroups" :key="group.id" class="tools-group" :aria-labelledby="'tools-group-' + group.id">
            <div class="tools-group-heading"><h2 :id="'tools-group-' + group.id">{{ group.title }}</h2><p>{{ group.note }}</p></div>
            <ul class="tools-list">
              <li v-for="tool in group.tools" :key="tool.id">
                <a class="tool-entry" :href="href(tool)" @click="activate($event, tool)">
                  <ToolIcon :tool-id="tool.id" />
                  <div class="tool-entry-copy"><h3>{{ tool.name }}</h3><p>{{ tool.description }}</p></div>
                  <WorkspaceIcon name="arrow" class="tool-entry-arrow" />
                </a>
              </li>
            </ul>
          </section>

          <div v-if="!visibleTools.length" class="tools-empty"><WorkspaceIcon name="search" /><h2>没有找到匹配的工具</h2><p>试试“含水”“SOC”或“换算”，也可以清空筛选查看全部。</p><button type="button" class="tool-primary-button" @click="clearFilters">清空筛选</button></div>
        </div>
      </div>
    </template>
    <DataAuditWorkbench v-else-if="selectedTool?.workbench === 'data-audit'" @open-research="token => emit('import-research', { token, directory: directoryUrl() })" />
    <TextureWorkbench v-else-if="selectedTool?.workbench === 'texture'" />
    <CalculatorWorkbench v-else-if="selectedTool?.calculator" :key="selectedTool.id" :tool-id="selectedTool.id" />
    <section v-else class="tool-description"><WorkspaceIcon :name="selectedTool?.icon || 'panel'" /><h2>{{ selectedTool ? '使用说明' : '请重新选择工具' }}</h2><p>{{ selectedTool?.note || '工具目录保留了所有可用入口，可返回后重新选择。' }}</p><a v-if="selectedTool?.path" class="tool-primary-button" :href="href(selectedTool)" @click="activate($event, selectedTool)">打开工具<WorkspaceIcon name="expand" /></a><button v-else type="button" class="tool-primary-button" @click="backToDirectory">返回工具目录<WorkspaceIcon name="back" /></button></section>
  </main>
</template>

<script setup>
import HoverSwitch from '../design-system/HoverSwitch.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import WorkspaceIcon from '../WorkspaceIcon.vue'
import ToolIcon from './ToolIcon.vue'
import { transitionPage } from '../design-system/motion.js'
import CalculatorWorkbench from './CalculatorWorkbench.vue'
import DataAuditWorkbench from './research/DataAuditWorkbench.vue'
import TextureWorkbench from './research/TextureWorkbench.vue'
import { filterTools, getTool, statusLabel, toolCategories, tools, toolTarget } from './catalog.js'
import './directory.css'
import './tools.css'
const props = defineProps({ account: { type: Object, default: null }, active: { type: Boolean, default: false } })
const emit = defineEmits(['open-tool', 'import-research'])
const domains = [...new Set(tools.map(tool => tool.domain))]
const searchInputRef = ref(null)
const query = ref(''), selectedCategory = ref('all'), domain = ref('all'), selectedId = ref('')
const selectedTool = computed(() => getTool(selectedId.value))
const visibleTools = computed(() => filterTools(query.value, selectedCategory.value, domain.value))
const availableTools = computed(() => visibleTools.value)
const directoryGroups = [
  { id: 'lab', title: '土壤理化计算', note: '物理性质、有机碳与实验配液', ids: ['density', 'moisture', 'carbon', 'texture', 'dilution'] },
  { id: 'numbers', title: '数据检查与统计', note: '批量质控、实验结果与单位换算', ids: ['data-audit', 'units', 'curve', 'statistics'] },
  { id: 'data', title: '地图与数据查询', note: '进入空间探索和数据资源', ids: ['map-layers', 'indicator-catalog', 'database-browser'] },
  { id: 'assessment', title: '健康评价', note: '需登录，支持录入、评价与报告', ids: ['quick-assessment', 'deep-assessment'] },
]
const visibleGroups = computed(() => directoryGroups.map(group => ({ ...group, tools: group.ids.map(id => availableTools.value.find(tool => tool.id === id)).filter(Boolean) })).filter(group => group.tools.length))
function directoryUrl() { const params = new URLSearchParams(); if (query.value) params.set('q', query.value); if (selectedCategory.value !== 'all') params.set('category', selectedCategory.value); if (domain.value !== 'all') params.set('domain', domain.value); return '/tools' + (params.size ? '?' + params.toString() : '') }
const directoryHref = computed(directoryUrl)
function href(tool) { const target = toolTarget(tool.id, directoryUrl()); if (target) return tool.login && !props.account ? '/account/index.html?next=' + encodeURIComponent(target) : target; const url = new URL(directoryUrl(), location.origin); url.searchParams.set('tool', tool.id); return url.pathname + url.search }
function readLocation() {
  if (location.pathname !== '/tools') return
  const params = new URLSearchParams(location.search)
  query.value = (params.get('q') || '').slice(0, 200)
  selectedCategory.value = toolCategories.some(category => category.id === params.get('category')) ? params.get('category') : 'all'
  domain.value = domains.includes(params.get('domain')) ? params.get('domain') : 'all'
  selectedId.value = params.get('tool') || ''
}
function activate(event, tool) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return
  event.preventDefault()
  if (tool.path) { emit('open-tool', { id: tool.id, directory: directoryUrl() }); return }
  transitionPage(() => { history.pushState({}, '', href(tool)); selectedId.value = tool.id }, focusTitle)
}
async function focusTitle() {
  await nextTick()
  const workspace = document.querySelector('.tools-workspace')
  ;(workspace?.closest('.site-content-tools') || workspace)?.scrollTo({ top: 0 })
  document.getElementById('tools-title')?.focus({ preventScroll: true })
}
function backToDirectory() { transitionPage(() => { history.pushState({}, '', directoryUrl()); selectedId.value = '' }, focusTitle) }
function clearFilters() { query.value = ''; selectedCategory.value = 'all'; domain.value = 'all' }
async function clearSearch() { query.value = ''; await nextTick(); searchInputRef.value?.focus() }
defineExpose({ readLocation })
watch([query, selectedCategory, domain], () => { if (props.active && !selectedId.value) history.replaceState(history.state, '', directoryUrl()) })
watch(() => props.active, active => { if (active) readLocation() })
onMounted(() => { readLocation(); window.addEventListener('popstate', readLocation) })
onBeforeUnmount(() => window.removeEventListener('popstate', readLocation))
</script>
