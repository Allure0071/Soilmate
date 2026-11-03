import { calculators } from './calculators.js'

export const toolCategories = [
  { id: 'all', label: '全部工具' }, { id: 'map', label: '地图展示' }, { id: 'database', label: '数据库' },
  { id: 'agent', label: 'Agent 分析' }, { id: 'common', label: '常用工具' },
]
const linkedTools = [
  { id: 'map-layers', name: '空间图层与点位', category: 'map', domain: '野外', icon: 'map', description: '打开空间探索，切换指标图层、选取位置并查看点位数据。', path: '/explore', status: 'ready', keywords: '定位 地图 图层 区域 位置 查询' },
  { id: 'indicator-catalog', name: '指标目录查询', category: 'database', domain: '数据', icon: 'database', description: '浏览已登记指标，核对字段、单位、来源与缺失的元数据。', path: '/resources?tab=layers', status: 'ready' },
  { id: 'database-browser', name: '原始数据表浏览', category: 'database', domain: '数据', icon: 'database', description: '按数据库与数据表分页查询记录，复用数据资源中心。', path: '/resources?tab=database', status: 'ready' },
  { id: 'quick-assessment', name: '快速健康评价', category: 'agent', domain: '评价', icon: 'analysis', description: '整理已有检测结果，进入快速录入与核验流程。', path: '/research?stage=input&mode=quick&step=mode', status: 'input', login: true, note: '复用健康研究。当前提供录入、草稿和核验；新评价提交服务尚未接入，不会自动生成健康分数。' },
  { id: 'deep-assessment', name: '深度健康分析', category: 'agent', domain: '评价', icon: 'analysis', description: '结合地块、作物与管理背景，继续深度录入流程。', path: '/research?stage=input&mode=deep&step=mode', status: 'input', login: true, note: '需登录后使用。当前支持地块背景与检测录入，后续分析能力以已接入的研究服务为准。' },
]
const plannedTools = [
  { id: 'field-measurement', name: '地块测量', domain: '野外', icon: 'map', description: '距离、面积与地块边界记录。', note: '需要接入地图绘制、坐标系统和面积计算口径；当前不生成测距或面积结果。' },
  { id: 'sampling-assistant', name: '采样助手', domain: '野外', icon: 'map', description: '采样点定位与采样记录整理。', note: '采样点、天气与文件导出尚未接入；后续需明确采样方案和定位精度。' },
  { id: 'fertilizer-card', name: '施肥卡片', domain: '评价', icon: 'analysis', description: '整理地块与肥料信息，形成管理记录。', note: '需要作物目标、肥料养分含量和经过核验的推荐规则，当前不提供施肥剂量建议。' },
  { id: 'ph-ec', name: 'pH / EC 判读', domain: '化学', icon: 'flask', description: '结合测定方法理解酸碱度与电导率。', note: '需登记浸提方法、土水比、温度与适用阈值；不同测定口径不能直接套用统一等级。电导率的单位换算已可使用。' },
  { id: 'texture', name: '质地判别', domain: '物理', icon: 'analysis', description: '基于砂、粉、黏粒比例识别质地类型。', note: '质地三角图的分类体系和粒径界限待确认，暂不输出质地类别。' },
  { id: 'instruments', name: '仪器分析', domain: '化学', icon: 'flask', description: '测定方法、仪器原理与图谱参考。', note: '需要整理有授权且可追溯的仪器资料与图谱，当前没有已验证的仪器数据库。' },
  { id: 'reagents', name: '试剂配制与酶活', domain: '化学', icon: 'flask', description: '试剂配方、酶活与菌群实验方法。', note: '具体 SOP、试剂纯度和试剂盒说明书尚未整理。通用溶液稀释计算已可使用，但不替代实验操作规程。' },
  { id: 'salinity', name: '盐碱指标', domain: '化学', icon: 'flask', description: 'EC、ESP 与 SAR 的计算与解释。', note: '离子单位、提取方法与指标适用条件待核查，当前不输出盐碱等级。' },
  { id: 'pollution', name: '污染阈值核对', domain: '评价', icon: 'analysis', description: '按用途、pH 与适用标准核对检测值。', note: '需要核实有效标准、土地用途及检测方法；当前不判断达标或超标。' },
].map(tool => ({ ...tool, category: 'common', status: 'planned' }))

export const tools = [
  ...linkedTools,
  ...Object.entries(calculators).map(([id, calculator]) => ({ id, name: calculator.name, category: 'common', domain: calculator.domain, icon: calculator.domain === '物理' ? 'soil' : calculator.domain === '统计' ? 'chart' : calculator.domain === '通用' ? 'convert' : 'flask', description: calculator.description, status: 'ready', calculator: true, keywords: id === 'carbon' ? 'SOC 有机碳 碳储量' : '' })),
  ...plannedTools,
]
export function filterTools(query = '', category = 'all', domain = 'all') {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean)
  return tools.filter(tool => (category === 'all' || tool.category === category) && (domain === 'all' || tool.domain === domain) && terms.every(term => `${tool.name} ${tool.description} ${tool.domain} ${tool.keywords || ''}`.toLocaleLowerCase().includes(term)))
}
export function getTool(id) { return tools.find(tool => tool.id === id) || null }
export function toolTarget(id, directoryPath = '/tools') {
  const tool = getTool(id)
  if (!tool?.path || tool.status === 'planned') return null
  const url = new URL(tool.path, 'https://soilmate.local')
  url.searchParams.set('from', 'tools')
  url.searchParams.set('tool', id)
  const directory = new URL(directoryPath || '/tools', 'https://soilmate.local')
  if (directory.origin === 'https://soilmate.local' && directory.pathname === '/tools' && directory.search) url.searchParams.set('returnTo', directory.pathname + directory.search)
  return url.pathname + url.search
}
export function statusLabel(tool) {
  return tool.status === 'planned' ? '建设中' : tool.status === 'input' ? '录入可用' : '已接入'
}
