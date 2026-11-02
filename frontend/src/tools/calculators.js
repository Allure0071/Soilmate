const numeric = (id, label, unit = '', extra = {}) => ({ id, label, unit, type: 'number', ...extra })
const choice = (id, label, options, value) => ({ id, label, type: 'select', options, value })
const text = (id, label, hint) => ({ id, label, hint, type: 'textarea' })
const source = (title, href) => ({ title, href })
const physicalSource = source('USDA NRCS · Soil Survey Laboratory Information Manual', 'https://www.nrcs.usda.gov/sites/default/files/2022-10/SSIR45.pdf')
const unitSets = {
  mass: { label: '土壤质量分数', units: { 'g/kg': 1, 'mg/kg': 0.001, '%': 10 } },
  density: { label: '容重', units: { 'g/cm³': 1, 'kg/m³': 0.001, 'Mg/m³': 1 } },
  ec: { label: '电导率', units: { 'dS/m': 1, 'mS/cm': 1, 'μS/cm': 0.001, 'mS/m': 0.01 } },
  area: { label: '面积', units: { 'm²': 1, 'ha': 10000, '亩': 2000 / 3 } },
}
export { unitSets }

export const calculators = {
  density: {
    name: '容重与孔隙度', domain: '物理', description: '用干土质量与环刀体积计算容重，估算总孔隙度。',
    fields: [numeric('mass', '干土净质量', 'g'), numeric('volume', '土样总体积', 'cm³'), numeric('particle', '土粒密度', 'g/cm³', { hint: '矿质土常用假设为 2.65；有实测值时请使用实测值。' })],
    example: { mass: '130', volume: '100', particle: '2.65' },
    formula: 'ρb = 干土净质量 / 土样总体积；总孔隙度 = (1 − ρb / ρs) × 100%',
    scope: '质量不包含环刀或容器。适用于体积和干质量口径一致的土样；砾石、根系与土体收缩需要按检测方法修正。孔隙度是基于土粒密度的估算，不是健康等级。',
    sources: [physicalSource],
    run(v) {
      const density = number(v, 'mass', { positive: true }) / number(v, 'volume', { positive: true })
      const particle = number(v, 'particle', { positive: true })
      if (density > particle) fail('particle', '容重大于土粒密度，请核对质量、体积和土粒密度。')
      return result([item('土壤容重', density, 'g/cm³'), item('总孔隙度', (1 - density / particle) * 100, '%')])
    },
  },
  moisture: {
    name: '含水率换算', domain: '物理', description: '在干基、湿基和体积含水率之间换算。',
    fields: [choice('basis', '输入含水率口径', [['dry', '干基质量含水率'], ['wet', '湿基质量含水率'], ['volume', '体积含水率']], 'dry'), numeric('water', '含水率', '%'), numeric('density', '干土容重', 'g/cm³')],
    example: { basis: 'dry', water: '20', density: '1.3' },
    formula: 'wd = 水质量 / 干土质量；ww = wd / (1 + wd)；θv = wd × ρb / ρwater。公式中比例均为小数。',
    scope: '水密度取 1 g/cm³，容重必须是干土容重。干基含水率可以超过 100%；体积含水率不得超过 100%。未校验土样实际孔隙度，不能据此认定饱和或确定灌溉量。',
    sources: [physicalSource, source('USDA NRCS · Soil Quality Test Kit Guide', 'https://www.nrcs.usda.gov/sites/default/files/2022-10/Soil%20Quality%20Test%20Kit%20Guide.pdf')],
    run(v) {
      const density = number(v, 'density', { positive: true }), water = number(v, 'water', { min: 0 }) / 100
      if (!['dry', 'wet', 'volume'].includes(v.basis)) fail('basis', '请选择含水率口径。')
      if (v.basis === 'wet' && water >= 1) fail('water', '湿基含水率必须小于 100%。')
      if (v.basis === 'volume' && water > 1) fail('water', '体积含水率不能超过 100%。')
      const dry = v.basis === 'dry' ? water : v.basis === 'wet' ? water / (1 - water) : water / density
      const volume = dry * density
      if (volume > 1 + 1e-12) fail('water', '换算后的体积含水率超过 100%，请核对含水率口径与容重。')
      return result([item('干基质量含水率', dry * 100, '%'), item('湿基质量含水率', dry / (1 + dry) * 100, '%'), item('体积含水率', volume * 100, '%')])
    },
  },
  carbon: {
    name: 'SOC / 有机碳储量', domain: '化学', description: '按单一土层厚度、细土容重和砾石体积分数估算碳储量。',
    fields: [numeric('carbon', '细土有机碳含量', 'g/kg'), numeric('density', '细土干容重', 'g/cm³'), numeric('depth', '土层厚度', 'cm'), numeric('fragments', '粗颗粒体积分数', '%', { hint: '大于 2 mm 的粗颗粒，以体积占比输入；不能直接填质量占比。' })],
    example: { carbon: '15', density: '1.3', depth: '20', fragments: '10' },
    formula: 'SOC 储量 (t C/ha) = SOC (g/kg) × 细土容重 (g/cm³) × 厚度 (cm) × (1 − 粗颗粒体积分数/100) × 0.1',
    scope: '单层、固定深度估算，细土为小于 2 mm 的部分。输入的是有机碳而不是有机质，容重按细土体积计；不再次使用已经按粗颗粒修正的整土密度。不能用单次储量推断固碳速率或碳汇收益。',
    sources: [source('FAO · Soil organic carbon stock calculation sub-protocol', 'https://www.fao.org/fileadmin/user_upload/GSP/MRV/GSP_MRV_Protocol_A4_EN_002.pdf'), source('SOIL · Proximal sensing for soil carbon accounting', 'https://soil.copernicus.org/articles/4/101/2018/soil-4-101-2018.html')],
    run(v) {
      const carbon = number(v, 'carbon', { min: 0, max: 1000 }), density = number(v, 'density', { positive: true }), depth = number(v, 'depth', { positive: true }), fragments = number(v, 'fragments', { min: 0, max: 100 })
      const stock = carbon * density * depth * (1 - fragments / 100) * 0.1
      return result([item('单层有机碳储量', stock, 't C/ha'), item('单位面积储量', stock / 10, 'kg C/m²')])
    },
  },
  units: {
    name: '土壤单位换算', domain: '通用', description: '质量分数、容重、电导率及面积的同量纲换算。',
    fields: [choice('quantity', '换算类型', Object.entries(unitSets).map(([id, set]) => [id, set.label]), 'mass'), numeric('value', '原始数值'), choice('from', '原始单位', [], 'g/kg'), choice('to', '目标单位', [], 'mg/kg')],
    example: { quantity: 'mass', value: '1.2', from: 'g/kg', to: 'mg/kg' },
    formula: '目标数值 = 原始数值 × 原始单位系数 / 目标单位系数；1% = 10 g/kg = 10,000 mg/kg；1 dS/m = 1 mS/cm。',
    scope: '仅换算相同物理量，不把水溶液 mg/L 直接换为土壤 mg/kg，也不把 EC 直接换为盐含量。质量分数 % 为质量百分数；亩按市亩 2000/3 m² 计算。',
    sources: [source('BIPM · SI Brochure', 'https://www.bipm.org/en/publications/si-brochure')],
    run(v) {
      const set = Object.hasOwn(unitSets, v.quantity) ? unitSets[v.quantity] : null
      if (!set || !Object.hasOwn(set.units, v.from) || !Object.hasOwn(set.units, v.to)) fail('from', '请选择同一种换算类型中的有效单位。')
      const value = number(v, 'value', { min: 0 })
      const massFraction = value * set.units[v.from]
      if (v.quantity === 'mass' && massFraction > 1000) fail('value', '质量分数不能大于 100%。')
      return result([item('换算结果', massFraction / set.units[v.to], v.to)])
    },
  },
  dilution: {
    name: '溶液稀释', domain: '化学', description: '根据母液、目标浓度与最终体积计算移取量。',
    fields: [choice('unit', '统一浓度单位', [['mg/L', 'mg/L'], ['g/L', 'g/L'], ['mol/L', 'mol/L']], 'mg/L'), numeric('stock', '母液浓度 C₁'), numeric('target', '目标浓度 C₂'), numeric('volume', '最终溶液体积 V₂', 'mL')],
    example: { unit: 'mg/L', stock: '1000', target: '10', volume: '100' },
    formula: 'C₁V₁ = C₂V₂；母液移取体积 V₁ = C₂ × V₂ / C₁；稀释倍数 = C₁ / C₂。',
    scope: '母液与目标浓度须使用同一种溶质、同一种浓度单位。输出的是移取量与最终定容体积，不把体积差当作精确加水量；不涉及反应、溶质损失或具体试剂操作规程。',
    sources: [source('Kingston University · Dilution', 'https://sciskills.kingston.ac.uk/concentration_of_solutions/dilution/overview.html')],
    run(v) {
      if (!['mg/L', 'g/L', 'mol/L'].includes(v.unit)) fail('unit', '请选择浓度单位。')
      const stock = number(v, 'stock', { positive: true }), target = number(v, 'target', { positive: true }), volume = number(v, 'volume', { positive: true })
      if (target > stock) fail('target', '目标浓度高于母液浓度，不能通过稀释得到。')
      return result([item('需要移取的母液', target / stock * volume, 'mL'), item('最终定容体积', volume, 'mL'), item('稀释倍数', stock / target, '倍')], ['将母液按相应实验方法移取后定容至最终体积。'])
    },
  },
  curve: {
    name: '线性标准曲线', domain: '统计', description: '拟合浓度与响应的一元线性关系，并反算样品浓度。',
    fields: [text('pairs', '标准点：每行一个“浓度, 响应”', '至少 3 组，使用英文逗号或空格分隔；不带表头，浓度单位自行保持一致。'), numeric('response', '样品响应', '', { optional: true, hint: '选填；留空时仅拟合标准曲线。' }), numeric('factor', '样品稀释倍数', '倍', { value: '1', hint: '未稀释填 1，仅在反算样品浓度时使用。' })],
    example: { pairs: '0, 0.02\n1, 0.12\n2, 0.22\n3, 0.32', response: '0.17', factor: '5' },
    formula: 'y = a + bx；b = Σ[(xi − x̄)(yi − ȳ)] / Σ(xi − x̄)²；a = ȳ − bx̄；原样浓度 = (响应 − a) / b × 稀释倍数。',
    scope: '带截距的普通最小二乘拟合，不强制过原点；只支持一元线性模型。R² 不是方法验证结论，不替代空白、检出限、回收率及残差检查。反算只允许落在标准点浓度范围内，稀释倍数不得小于 1。',
    sources: [source('NIST · Least Squares', 'https://itl.nist.gov/div898/handbook/pmd/section4/pmd431.htm')],
    run(v) {
      const lines = String(v.pairs || '').trim().split(/\r?\n/).filter(line => line.trim())
      if (lines.length < 3 || lines.length > 1000) fail('pairs', '请提供 3～1000 组标准点。')
      const points = lines.map((line, index) => {
        const parts = line.trim().split(/[,，\s]+/)
        if (parts.length !== 2) fail('pairs', `第 ${index + 1} 行需要一组浓度和响应。`)
        const x = number({ pairs: parts[0] }, 'pairs', { min: 0 }), y = number({ pairs: parts[1] }, 'pairs')
        return { x, y }
      })
      const n = points.length, mx = points.reduce((s, p) => s + p.x, 0) / n, my = points.reduce((s, p) => s + p.y, 0) / n
      const xx = points.reduce((s, p) => s + (p.x - mx) ** 2, 0), xy = points.reduce((s, p) => s + (p.x - mx) * (p.y - my), 0)
      if (!(xx > 0)) fail('pairs', '标准点浓度不能全部相同。')
      const b = xy / xx, a = my - b * mx
      if (!Number.isFinite(b) || Math.abs(b) < 1e-15) fail('pairs', '斜率为零或接近零，不能用于浓度反算。')
      const ss = points.reduce((s, p) => s + (p.y - my) ** 2, 0), residual = points.reduce((s, p) => s + (p.y - a - b * p.x) ** 2, 0)
      const items = [item('斜率 b', b), item('截距 a', a), item('决定系数 R²', 1 - residual / ss)]
      const min = Math.min(...points.map(p => p.x)), max = Math.max(...points.map(p => p.x))
      if (String(v.response ?? '').trim() !== '') {
        const factor = number(v, 'factor', { min: 1 })
        const concentration = (number(v, 'response') - a) / b
        const tolerance = 1e-10 * Math.max(1, Math.abs(min), Math.abs(max))
        if (concentration < min - tolerance || concentration > max + tolerance) fail('response', '反算浓度超出标准点范围，请重新稀释或补充标准点。')
        items.push(item('待测液浓度', Math.max(0, concentration), '与标准点同单位'), item('原样浓度', Math.max(0, concentration) * factor, '与标准点同单位'))
      }
      return result(items, [`标准浓度范围：${min}～${max}；反算前使用待测液浓度核验范围。`], { points, slope: b, intercept: a })
    },
  },
  statistics: {
    name: '统计速算', domain: '统计', description: '汇总一组数据的均值、中位数、样本标准差与 CV。',
    fields: [text('values', '数据序列', '使用空格、逗号、分号或换行分隔，2～1000 个有效数值；所有数据应使用同一单位。')],
    example: { values: '10, 12, 14, 16, 18' },
    formula: '均值 x̄ = Σxi / n；样本标准差 s = √[Σ(xi − x̄)² / (n − 1)]；CV = s / x̄ × 100%。',
    scope: '不自动删除缺失值、异常值或重复观测；重复数值作为独立输入计数。CV 仅适用于正值、具有真实零点的比率尺度数据，不适用于 pH 等对数指标或摄氏温度。',
    sources: [source('NIST · Measures of Scale', 'https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm'), source('NIST · Coefficient of Variation', 'https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/coefvari.htm')],
    run(v) {
      const tokens = String(v.values || '').trim().split(/[\s,，;；]+/)
      if (tokens.length < 2 || tokens.length > 1000) fail('values', '请提供 2～1000 个数值。')
      const values = tokens.map(token => number({ values: token }, 'values')), n = values.length
      const mean = values.reduce((s, x) => s + x, 0) / n, sd = Math.sqrt(values.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1))
      const sorted = [...values].sort((a, b) => a - b), median = n % 2 ? sorted[(n - 1) / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2
      const items = [item('数据个数', n, '个'), item('均值', mean), item('中位数', median), item('样本标准差', sd), item('最小值', sorted[0]), item('最大值', sorted[n - 1])]
      const notes = []
      if (values.every(x => x > 0)) items.push(item('变异系数 CV', sd / mean * 100, '%'))
      else notes.push('数据包含零或负值，未给出 CV；均值和标准差仍按全部输入计算。')
      return result(items, notes)
    },
  },
}

export class CalculationError extends Error {
  constructor(field, message) { super(message); this.field = field }
}
function fail(field, message) { throw new CalculationError(field, message) }
function number(values, field, options = {}) {
  const raw = String(values[field] ?? '').trim()
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(raw)) fail(field, '请填写有效数值，不要包含单位、空值或其他文字。')
  const value = Number(raw)
  if (!Number.isFinite(value)) fail(field, '数值过大或不是有限数值，请核对输入。')
  if (options.positive && value <= 0) fail(field, '该数值必须大于 0。')
  if (options.min !== undefined && value < options.min) fail(field, `该数值不能小于 ${options.min}。`)
  if (options.max !== undefined && value > options.max) fail(field, `该数值不能大于 ${options.max}。`)
  return value
}
function item(label, value, unit = '') { return { label, value, unit } }
function result(items, notes = [], chart = null) {
  if (items.some(item => !Number.isFinite(item.value))) fail('', '计算超出可表示范围，请检查输入的数量级。')
  return { items, notes, chart }
}
export function calculate(id, values) {
  if (!Object.hasOwn(calculators, id)) throw new CalculationError('', '这个工具尚未接入计算。')
  return calculators[id].run(values)
}
export function formatNumber(value) {
  return Number.isFinite(value) ? Number(value.toPrecision(7)).toLocaleString('zh-CN', { maximumSignificantDigits: 7 }) : '—'
}
