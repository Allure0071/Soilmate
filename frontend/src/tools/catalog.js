import { calculators } from './calculators.js'

export const toolCategories = [
  { id: 'all', label: '全部工具' }, { id: 'map', label: '地图展示' }, { id: 'database', label: '数据库' },
  { id: 'agent', label: 'Agent 分析' }, { id: 'common', label: '常用工具' },
]
const linkedTools = [
  { id: 'map-layers', name: '空间图层与点位', category: 'map', domain: '野外', icon: 'map', description: '打开空间探索，切换指标图层、选取位置并查看点位数据。', path: '/explore', status: 'ready', keywords: '定位 地图 图层 区域 位置 查询' },
  { id: 'indicator-catalog', name: '指标目录查询', category: 'database', domain: '数据', icon: 'database', description: '浏览已登记指标，核对字段、单位、来源与缺失的元数据。', path: '/resources?tab=layers', status: 'ready' },
  { id: 'database-browser', name: '原始数据表浏览', category: 'database', domain: '数据', icon: 'database', description: '按数据库与数据表分页查询记录，复用数据资源中心。', path: '/resources?tab=database', status: 'ready' },
  { id: 'quick-assessment', name: '快速健康评价', category: 'agent', domain: '评价', icon: 'analysis', description: '整理已有检测结果，进入快速录入与核验流程。', path: '/research?stage=input&mode=quick&step=mode', status: 'input', login: true, note: '复用健康研究。已接入录入、快速评价与报告：提交后生成评价结果、依据与可下载报告。' },
  { id: 'deep-assessment', name: '深度健康分析', category: 'agent', domain: '评价', icon: 'analysis', description: '结合地块、作物与管理背景，继续深度录入流程。', path: '/research?stage=input&mode=deep&step=mode', status: 'input', login: true, note: '需登录后使用。支持地块背景、检测录入与深度健康分析，结果与报告在同一任务中查看。' },
]


export const tools = [
  ...linkedTools,
  ...Object.entries(calculators).map(([id, calculator]) => ({ id, name: calculator.name, category: 'common', domain: calculator.domain, icon: calculator.domain === '物理' ? 'soil' : calculator.domain === '统计' ? 'chart' : calculator.domain === '通用' ? 'convert' : 'flask', description: calculator.description, status: 'ready', calculator: true, keywords: id === 'carbon' ? 'SOC 有机碳 碳储量' : '' })),
  { id: 'data-audit', name: '批量数据体检', category: 'common', domain: '数据', icon: 'database', description: '导入表格，检查缺失、重复、单位与异常值，导出问题清单。', status: 'ready', workbench: 'data-audit', keywords: 'CSV TSV Excel xlsx 表格 质控 数据质量 导入 批量 检查' },
  { id: 'texture', name: '土壤质地三角图', category: 'common', domain: '物理', icon: 'analysis', description: '按砂、粉、黏粒比例判别 USDA 质地类型，绘制样点并导出图表。', status: 'ready', workbench: 'texture', keywords: '砂粒 粉粒 黏粒 粘粒 质地判别 USDA 三角图' },
]
export function filterTools(query = '', category = 'all', domain = 'all') {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean)
  return tools.filter(tool => (category === 'all' || tool.category === category) && (domain === 'all' || tool.domain === domain) && terms.every(term => `${tool.name} ${tool.description} ${tool.domain} ${tool.keywords || ''}`.toLocaleLowerCase().includes(term)))
}
export function getTool(id) { return tools.find(tool => tool.id === id) || null }
export function toolTarget(id, directoryPath = '/tools') {
  const tool = getTool(id)
  if (!tool?.path) return null
  const url = new URL(tool.path, 'https://soilmate.local')
  url.searchParams.set('from', 'tools')
  url.searchParams.set('tool', id)
  const directory = new URL(directoryPath || '/tools', 'https://soilmate.local')
  if (directory.origin === 'https://soilmate.local' && directory.pathname === '/tools' && directory.search) url.searchParams.set('returnTo', directory.pathname + directory.search)
  return url.pathname + url.search
}
export function statusLabel(tool) {
  return tool.status === 'input' ? '录入可用' : '已接入'
}
