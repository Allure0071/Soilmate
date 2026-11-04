/**
 * 答辩演示模式 · 公开数据案例 + 演示规则计算
 *
 * 数据：ISRIC SoilGrids 2.0（250 m 全球土壤属性栅格）REST 查询结果，
 *       查询时间 2026-11-04，属性 phh2o / soc / nitrogen / cec / bdod / clay / sand / silt，
 *       深度 0–5 cm，value=mean。为区域预测值，不是本地实测。
 * 计算：SMAF 型评分曲线 + 三套演示规则集，全部在浏览器内确定性计算。
 * 边界：规则集为演示参数，未经独立验证；不构成健康等级诊断或农艺处方。
 */

export const DEMO_VERSION = 'demo-2026-11-04'

export const dataSource = {
  name: 'ISRIC SoilGrids 2.0',
  description: '全球土壤属性栅格产品（250 m 分辨率）',
  provider: 'ISRIC — World Soil Information',
  license: 'CC BY 4.0',
  doi: '10.5194/soil-7-217-2021',
  site: 'https://soilgrids.org',
  api: 'https://rest.isric.org/soilgrids/v2.0/properties/query',
  accessed: '2026-11-04 04:55 CST',
  query: 'property=phh2o,soc,nitrogen,cec,bdod,clay,sand,silt；depth=0-5cm；value=mean',
  type: '区域预测值（模型输出，不是本地实测）',
  citation: 'Poggio, L., de Sousa, L. M., Batjes, N. H., Heuvelink, G. B. M., Kempen, B., Riberio, E., Rossiter, D. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL, 7, 217–240.',
}

const plots = {
  A: {
    id: 'A-07',
    name: '雷州半岛水稻田 A-07（公开数据案例）',
    short: 'A-07',
    region: '广东 · 湛江雷州',
    lon: 110.0,
    lat: 21.4,
    crop: '水稻',
    depth: '0–5 cm 表层',
    values: { ph: 6.0, soc: 19.7, tn: 2.54, cec: 18.2, bd: 1.21, clay: 30.8, sand: 44.4, silt: 24.8 },
  },
  B: {
    id: 'B-02',
    name: '惠州台地稻田 B-02（公开数据案例）',
    short: 'B-02',
    region: '广东 · 惠州',
    lon: 114.3,
    lat: 23.1,
    crop: '水稻',
    depth: '0–5 cm 表层',
    values: { ph: 5.2, soc: 32.8, tn: 2.67, cec: 18.3, bd: 1.16, clay: 24.4, sand: 41.4, silt: 34.2 },
  },
}

const INDICATOR_META = [
  { code: 'ph', label: 'pH（H₂O）', unit: '无量纲', sg: 'phh2o', factor: 10 },
  { code: 'soc', label: '有机碳 SOC', unit: 'g/kg', sg: 'soc', factor: 10 },
  { code: 'tn', label: '全氮 TN', unit: 'g/kg', sg: 'nitrogen', factor: 100 },
  { code: 'cec', label: '阳离子交换量 CEC', unit: 'cmol(c)/kg', sg: 'cec', factor: 10 },
  { code: 'bd', label: '容重 BD', unit: 'g/cm³', sg: 'bdod', factor: 100 },
  { code: 'clay', label: '黏粒含量 Clay', unit: '%', sg: 'clay', factor: 10 },
]

const FUNCTION_META = [
  { id: 'production', label: '生产支持' },
  { id: 'nutrition', label: '养分供给' },
  { id: 'structure', label: '土壤结构' },
  { id: 'water', label: '水分调节' },
]

const FUNCTION_WEIGHTS = {
  production: { soc: 0.35, tn: 0.3, ph: 0.2, bd: 0.15 },
  nutrition: { tn: 0.4, soc: 0.35, cec: 0.25 },
  structure: { bd: 0.45, clay: 0.35, soc: 0.2 },
  water: { clay: 0.4, bd: 0.35, soc: 0.25 },
}

const RULE_SETS = [
  {
    id: 'A',
    name: '规则集 A · SMAF 型曲线',
    basis: '文献最适区间 + 连续评分曲线',
    curves: {
      ph: { type: 'opt', low: 4.0, optLow: 5.5, optHigh: 6.5, high: 8.0 },
      soc: { type: 'up', low: 8, high: 25 },
      tn: { type: 'up', low: 0.8, high: 2.5 },
      cec: { type: 'up', low: 5, high: 25 },
      bd: { type: 'down', low: 1.15, high: 1.45 },
      clay: { type: 'opt', low: 12, optLow: 20, optHigh: 35, high: 45 },
    },
    compositeWeights: { production: 0.3, nutrition: 0.3, structure: 0.2, water: 0.2 },
    aggregate: 'weighted',
  },
  {
    id: 'B',
    name: '规则集 B · 区域参照分位',
    basis: '区域参照组 25/50/75 分位（演示参数）',
    curves: {
      ph: { type: 'opt', low: 4.2, optLow: 5.3, optHigh: 6.8, high: 8.2 },
      soc: { type: 'up', low: 10, high: 30 },
      tn: { type: 'up', low: 1.0, high: 2.8 },
      cec: { type: 'up', low: 6, high: 28 },
      bd: { type: 'down', low: 1.2, high: 1.5 },
      clay: { type: 'opt', low: 10, optLow: 17, optHigh: 38, high: 50 },
    },
    compositeWeights: { production: 0.25, nutrition: 0.3, structure: 0.25, water: 0.2 },
    aggregate: 'weighted',
  },
  {
    id: 'C',
    name: '规则集 C · 保守阈值（短板优先）',
    basis: '更严阈值 + 关键功能短板约束',
    curves: {
      ph: { type: 'opt', low: 4.5, optLow: 5.8, optHigh: 6.8, high: 8.0 },
      soc: { type: 'up', low: 12, high: 28 },
      tn: { type: 'up', low: 1.1, high: 2.8 },
      cec: { type: 'up', low: 8, high: 30 },
      bd: { type: 'down', low: 1.1, high: 1.38 },
      clay: { type: 'opt', low: 15, optLow: 20, optHigh: 35, high: 42 },
    },
    compositeWeights: { production: 0.3, nutrition: 0.3, structure: 0.2, water: 0.2 },
    aggregate: 'shortboard',
  },
]

const GRADES = [
  { min: 80, label: '较好' },
  { min: 65, label: '中等' },
  { min: 0, label: '偏低' },
]
const gradeOf = score => (GRADES.find(item => score >= item.min) || GRADES[GRADES.length - 1]).label
const round1 = value => Math.round(value * 10) / 10
const clamp = value => Math.max(0, Math.min(100, value))

function scoreCurve(value, curve) {
  if (value == null || Number.isNaN(value)) return null
  if (curve.type === 'up') return clamp(((value - curve.low) / (curve.high - curve.low)) * 100)
  if (curve.type === 'down') return clamp(((curve.high - value) / (curve.high - curve.low)) * 100)
  if (value >= curve.optLow && value <= curve.optHigh) return 100
  if (value < curve.optLow) return clamp(((value - curve.low) / (curve.optLow - curve.low)) * 100)
  return clamp(((curve.high - value) / (curve.high - curve.optHigh)) * 100)
}

function weightedMean(scores, weights) {
  let total = 0
  let weight = 0
  for (const [code, w] of Object.entries(weights)) {
    if (scores[code] == null) continue
    total += scores[code] * w
    weight += w
  }
  return weight ? total / weight : null
}

function evaluate(values, ruleSet) {
  const indicatorScores = {}
  for (const meta of INDICATOR_META) indicatorScores[meta.code] = scoreCurve(values[meta.code], ruleSet.curves[meta.code])
  const functionScores = {}
  for (const fn of FUNCTION_META) functionScores[fn.id] = weightedMean(indicatorScores, FUNCTION_WEIGHTS[fn.id])
  const valuesList = Object.values(functionScores).filter(v => v != null)
  const mean = valuesList.reduce((sum, v) => sum + v, 0) / valuesList.length
  let composite = mean
  if (ruleSet.aggregate === 'shortboard') {
    const lowest = Math.min(...valuesList)
    composite = mean * 0.6 + lowest * 0.4
  } else {
    let total = 0
    let weight = 0
    for (const [id, w] of Object.entries(ruleSet.compositeWeights)) {
      if (functionScores[id] == null) continue
      total += functionScores[id] * w
      weight += w
    }
    composite = weight ? total / weight : mean
  }
  return { indicatorScores, functionScores, composite: round1(composite), grade: gradeOf(composite) }
}

const caseA = plots.A
const caseB = plots.B
const evaluations = Object.fromEntries(RULE_SETS.map(rule => [rule.id, evaluate(caseA.values, rule)]))
const compositeValues = RULE_SETS.map(rule => evaluations[rule.id].composite)
export const rules = RULE_SETS.map(rule => ({
  id: rule.id,
  name: rule.name,
  basis: rule.basis,
  grade: evaluations[rule.id].grade,
  score: evaluations[rule.id].composite,
  note: describeRuleNote(rule.id),
}))
const minComposite = Math.min(...compositeValues)
const maxComposite = Math.max(...compositeValues)
const sortedComposite = [...compositeValues].sort((a, b) => a - b)
const medianComposite = round1(sortedComposite[Math.floor(sortedComposite.length / 2)])
const grades = [...new Set(compositeValues.map(gradeOf))]
const flips = grades.length - 1
const rangeLow = Math.floor(minComposite)
const rangeHigh = Math.ceil(maxComposite)

function describeRuleNote(id) {
  if (id === 'A') return 'pH 处于最适区间；SOC、CEC 得分偏低'
  if (id === 'B') return '区域参照下 SOC、CEC 均偏低'
  return '保守阈值同时压低 SOC、CEC 与容重得分'
}

/* 指标在各规则下的得分范围，用于识别稳定短板与敏感项 */
const indicatorStats = Object.fromEntries(INDICATOR_META.map(meta => {
  const scores = RULE_SETS.map(rule => evaluations[rule.id].indicatorScores[meta.code]).filter(v => v != null)
  return [meta.code, {
    min: round1(Math.min(...scores)),
    max: round1(Math.max(...scores)),
    avg: round1(scores.reduce((a, b) => a + b, 0) / scores.length),
  }]
}))

/* 演示边际贡献：规则集 A 下，把该指标得分置 0 后综合分的下降量 */
function compositeWhenZero(code) {
  const rule = RULE_SETS[0]
  const scores = { ...evaluations[rule.id].indicatorScores, [code]: 0 }
  const functions = {}
  for (const fn of FUNCTION_META) functions[fn.id] = weightedMean(scores, FUNCTION_WEIGHTS[fn.id])
  let total = 0
  let weight = 0
  for (const [id, w] of Object.entries(rule.compositeWeights)) {
    if (functions[id] == null) continue
    total += functions[id] * w
    weight += w
  }
  return weight ? total / weight : 0
}
const baseCompositeA = evaluations.A.composite
const contributions = Object.fromEntries(INDICATOR_META.map(meta => [meta.code, round1(baseCompositeA - compositeWhenZero(meta.code))]))

/* N+X 演示选测：N 固定为共享候选，X 按演示边际贡献取前二，其余记为预算外 */
const N_POOL = ['ph', 'soc', 'tn']
const X_POOL = ['cec', 'bd', 'clay']
const sortedX = [...X_POOL].sort((a, b) => contributions[b] - contributions[a])
const selectedX = sortedX.slice(0, 2)
const extraCode = sortedX[2]
const COSTS = { ph: 8, soc: 18, tn: 25, cec: 20, bd: 10, clay: 15 }

const ROLE_BY_CODE = Object.fromEntries([
  ...N_POOL.map(code => [code, 'N']),
  ...selectedX.map(code => [code, 'X']),
  [extraCode, 'extra'],
])

export const scenario = {
  field: caseA.id,
  fieldName: caseA.name,
  region: caseA.region,
  crop: caseA.crop,
  depth: caseA.depth,
  sampledAt: '2020 版',
  accessedAt: dataSource.accessed,
  lab: dataSource.name + '（REST 查询）',
  runId: 'CASE-SG-20261104-A07',
  rulesVersion: 'SMAF-style demo rules v0.2',
  modelLabel: '规则解释模板（演示；领域模型未接入）',
  budget: 5,
  budgetUnit: '项检测名额',
  totalCost: N_POOL.reduce((sum, code) => sum + COSTS[code], 0) + selectedX.reduce((sum, code) => sum + COSTS[code], 0),
}

export const indicators = INDICATOR_META.map(meta => ({
  code: meta.code,
  label: meta.label,
  value: Number(caseA.values[meta.code].toFixed(meta.code === 'tn' || meta.code === 'bd' ? 2 : 1)),
  unit: meta.unit,
  method: 'SoilGrids 2.0 预测值 · depth 0–5 cm · mean',
  source: `${dataSource.name} · ${meta.sg}`,
  role: ROLE_BY_CODE[meta.code],
  selected: ROLE_BY_CODE[meta.code] !== 'extra',
  note: describeIndicatorNote(meta.code),
}))

function describeIndicatorNote(code) {
  const notes = {
    ph: '接近水稻适宜区间（5.5–6.5）',
    soc: '三套规则下指标得分均偏低',
    tn: '全氮水平较高，但供应速率仍需速效氮验证',
    cec: '保肥能力偏低，且被预算挤出',
    bd: '容重随规则变化敏感（阈值差异大）',
    clay: '黏粒比例适合水稻土结构',
  }
  return notes[code]
}

export const auditChecks = [
  { title: '地块坐标与查询参数', detail: `${caseA.region} · ${caseA.lon.toFixed(2)}°E, ${caseA.lat.toFixed(2)}°N · 250 m 栅格`, ok: true },
  { title: '单位与换算', detail: 'pH×10、SOC dg/kg、N cg/kg、CEC mmol(c)/kg、容重 cg/cm³、黏粒 g/kg，已统一换算', ok: true },
  { title: '数据版本与深度', detail: `SoilGrids 2.0（2020 版）· 0–5 cm 表层 · 查询 ${dataSource.accessed}`, ok: true },
  { title: '来源与许可', detail: 'ISRIC SoilGrids 2.0 · CC BY 4.0 · 可复现 REST 查询', ok: true },
  { title: '证据缺口', detail: '区域预测不是本地实测；深度仅 0–5 cm；缺有效磷与速效氮；未做样本身份核验', ok: false },
]

export const selection = {
  n: N_POOL,
  x: selectedX,
  extra: [extraCode],
  rationale: [
    ...N_POOL.map(code => makeRationale(code, 'N · 跨区共享')),
    ...selectedX.map(code => makeRationale(code, 'X · 区域增补')),
    makeRationale(extraCode, '预算外（被挤出）'),
  ],
  tradeoff: `在 ${scenario.budget} 项预算下，${labelOf(extraCode)}（${indicatorValueText(extraCode)}）的演示边际贡献最低（+${contributions[extraCode].toFixed(1)} 分），被挤出并保留为补测候选；它同时是稳定短板，因此补测优先级高于其他预算外指标。`,
}

function makeRationale(code, role) {
  return {
    code,
    role,
    gain: `+${contributions[code].toFixed(1)}`,
    cost: COSTS[code],
    reason: describeRationale(code),
  }
}
function describeRationale(code) {
  const reasons = {
    ph: '跨区判别力稳定、检测成本低，共享核心',
    soc: '与生产支持、养分供给均相关，跨区可比',
    tn: '氮循环重点场景的核心指标，共享',
    cec: '预算外：边际贡献最低，但属于稳定短板，保留补测',
    bd: '区域结构限制常见，边际贡献较高，优先增补',
    clay: '质地信息与结构功能相关，按区域预算增补',
  }
  return reasons[code]
}
function labelOf(code) {
  return INDICATOR_META.find(item => item.code === code)?.label || code
}
function indicatorValueText(code) {
  const meta = INDICATOR_META.find(item => item.code === code)
  return `${caseA.values[code]} ${meta.unit}`
}

export const functions = FUNCTION_META.map(fn => ({
  id: fn.id,
  label: fn.label,
  score: round1(evaluations.A.functionScores[fn.id]),
}))

export const scoreSummary = {
  rangeLow,
  rangeHigh,
  median: medianComposite,
  grade: `${gradeOf(medianComposite)}（三套规则覆盖 ${grades.join(' / ')}）`,
  explanation: '综合分以区间呈现：三套演示规则下的结果不同，说明结论对阈值与权重敏感；同时识别在全部规则下都成立的稳定短板。',
}

export const stability = {
  flips,
  sensitive: `等级翻转 ${flips} 处，主要依赖 SOC 与容重的阈值选择；容重指标得分在 ${indicatorStats.bd.min}–${indicatorStats.bd.max} 之间波动。`,
  conclusion: `三套规则下综合分为 ${compositeValues.map(v => v.toFixed(1)).join(' / ')}，等级覆盖 ${grades.join('、')}；因此报告只给区间与敏感项，不给单一等级结论。`,
}

export const shortboards = [
  {
    id: 'soc',
    title: '有机碳偏低（稳定短板）',
    level: '稳定',
    detail: `SOC ${caseA.values.soc} g/kg，三套规则下指标得分 ${indicatorStats.soc.min}–${indicatorStats.soc.max}，均低于 70。`,
    evidence: 'SG-A07-20261104 · soc · rule v0.2-demo',
  },
  {
    id: 'cec',
    title: '保肥能力偏低（稳定短板）',
    level: '稳定',
    detail: `CEC ${caseA.values.cec} cmol(c)/kg，指标得分 ${indicatorStats.cec.min}–${indicatorStats.cec.max}，且被预算挤出，建议优先补测。`,
    evidence: 'SG-A07-20261104 · cec · rule v0.2-demo',
  },
  {
    id: 'bd',
    title: '容重等级敏感项',
    level: '敏感',
    detail: `BD ${caseA.values.bd} g/cm³，得分随规则在 ${indicatorStats.bd.min}–${indicatorStats.bd.max} 之间变化，是等级翻转的主要来源之一。`,
    evidence: 'SG-A07-20261104 · bdod · 规则差异追踪',
  },
]

export const evidenceItems = [
  {
    id: 'E1',
    type: '事实',
    claim: `有机碳 ${caseA.values.soc} g/kg：三套规则下指标得分 ${indicatorStats.soc.min}–${indicatorStats.soc.max}，属稳定短板。`,
    refs: ['SG-A07-20261104 · soc', 'rule soc v0.2-demo', dataSource.name],
    caveat: '区域预测值，未经本地实测核验。',
  },
  {
    id: 'E2',
    type: '事实',
    claim: `阳离子交换量 ${caseA.values.cec} cmol(c)/kg：指标得分 ${indicatorStats.cec.min}–${indicatorStats.cec.max}，保肥能力偏低。`,
    refs: ['SG-A07-20261104 · cec', 'rule cec v0.2-demo', dataSource.name],
    caveat: '该指标被检测预算挤出，补测优先级应高于预算外其他指标。',
  },
  {
    id: 'E3',
    type: '推断',
    claim: `容重 ${caseA.values.bd} g/cm³ 的得分对阈值敏感（${indicatorStats.bd.min}–${indicatorStats.bd.max}），是等级翻转的重要来源。`,
    refs: ['SG-A07-20261104 · bdod', 'rule bd v0.2-demo'],
    caveat: '0–5 cm 表层容重不能代表耕作层与犁底层结构。',
  },
  {
    id: 'E4',
    type: '证据缺口',
    claim: '数据为 250 m 区域预测值（0–5 cm），不是本地实测；缺有效磷、速效氮与样本身份核验。',
    refs: [dataSource.name, 'query 2026-11-04', '缺口清单'],
    caveat: '正式评价需按 0–20 cm 采样并登记实验室报告号。',
  },
  {
    id: 'E5',
    type: '建议（示例）',
    claim: '优先补测：CEC、有效磷、碱解氮，并按 0–20 cm 重新采样；对 SOC 采取秸秆还田/有机肥等措施需结合轮作与机械条件。',
    refs: ['证据 E1–E4', '规则集 C 约束'],
    caveat: '不提供具体施用剂量；需农技人员现场复核。',
  },
]

export const modelInfo = {
  label: '解释生成：确定性规则模板（演示）',
  status: '未调用模型服务；正式版本接入领域模型与证据约束链路',
  promptVersion: 'rule-template-demo-v0.2',
  note: '解释文字由规则模板与证据模板生成，数值全部来自同一套规则计算；模型不允许修改数值或阈值。',
}

export const agents = [
  { id: 'audit', role: '数据核验', status: 'done', output: `6 项指标 · 单位换算通过 · ${auditChecks.filter(item => !item.ok).length} 项证据缺口`, fp: 'sha256:4f1c…a9' },
  { id: 'select', role: '指标筛选', status: 'done', output: `N=${N_POOL.length} · X=${selectedX.length} · 预算 ${scenario.budget} · ${labelOf(extraCode)} 被挤出并记录`, fp: 'sha256:8b27…d1' },
  { id: 'score', role: '规则计算', status: 'done', output: `区间 ${rangeLow}–${rangeHigh} · 等级翻转 ${flips} 处 · 稳定短板 2 项`, fp: 'sha256:c093…7e' },
  { id: 'explain', role: '解释生成', status: 'reworked', output: '解释稿 v1 引用规则 v0.1 的 SOC 阈值，与当前 v0.2 不一致，被复核退回', fp: 'sha256:12ab…44' },
  { id: 'review', role: '独立复核', status: 'reviewed', output: '检出规则版本引用冲突 · 回退重算 · 报告 v2 通过', fp: 'sha256:9d54…b2' },
]

export const agentTimeline = [
  { at: '10:24:03', text: '任务 CASE-20261104-A07 创建，5 个角色按依赖图分派。' },
  { at: '10:24:05', text: '数据核验通过，写入不可变结果文件（含查询参数与数据版本指纹）。' },
  { at: '10:24:06', text: `选测与评分完成：区间 ${rangeLow}–${rangeHigh}，规则版本 v0.2。` },
  { at: '10:24:08', text: '解释稿 v1 生成，但引用规则 v0.1 的 SOC 阈值文字。' },
  { at: '10:24:09', text: '独立复核角色不参与生成，检出引用版本不一致 → 阻止报告发布并退回。' },
  { at: '10:24:11', text: '回退评分步骤重算，解释稿 v2 重新生成，复核通过。' },
]

export const report = {
  version: 'v2',
  generatedAt: '2026-11-04 10:24',
  status: '独立复核通过（流程演示）',
  sections: [
    '数据来源与类型',
    '案例地块与查询参数',
    '指标值与规则得分',
    '功能评分与总分区间',
    '稳定短板与等级敏感项',
    '证据缺口与补测建议',
    '复核记录与版本',
    '适用范围与限制声明',
  ],
  limits: [
    '数据来自 ISRIC SoilGrids 2.0（250 m 区域预测值，0–5 cm），不是本地实测，不能当作地块化验单。',
    '评分为演示规则集计算，规则参数未经独立验证，不构成健康等级诊断或科研结论。',
    '报告不含施肥剂量；任何田间措施需农技人员结合本地采样与现场条件复核。',
    '区域预测值与地块实测不可混用；0–5 cm 表层数据不能外推到根区。',
  ],
}

export const retest = {
  sampledAt: '对照地块 B-02（同一数据版本）',
  values: INDICATOR_META.map(meta => ({
    code: meta.code,
    label: meta.label,
    before: Number(caseA.values[meta.code].toFixed(meta.code === 'tn' || meta.code === 'bd' ? 2 : 1)),
    after: Number(caseB.values[meta.code].toFixed(meta.code === 'tn' || meta.code === 'bd' ? 2 : 1)),
    unit: meta.unit,
  })),
  checks: [
    { label: '同一数据源（SoilGrids 2.0）', ok: true },
    { label: '同一深度（0–5 cm）', ok: true },
    { label: '同一空间分辨率（250 m）', ok: true },
    { label: '不同地块（A-07 vs B-02）', ok: false },
    { label: '非配对实测，不能做复测', ok: false },
  ],
  verdict: '同源可横向比较，但不是复测',
  note: '两块地都是区域预测值；横向比较只反映同一数据版本下的差异，不能当作复测、改善或管理效果证据。',
}

export const steps = [
  { id: 'scene', no: '01', label: '案例与来源', short: '来源', tip: '先讲清数据来源与类型：公开土壤属性数据、250 m 区域预测值，不是本地实测。' },
  { id: 'input', no: '02', label: '数据接入与核验', short: '核验', tip: '强调单位换算、深度与版本；系统主动暴露证据缺口，不把预测值伪装成化验结果。' },
  { id: 'select', no: '03', label: 'N+X 选测', short: 'N+X', tip: '创新一：共享指标保跨区可比，区域增补按预算分配，并解释被挤出的信息。' },
  { id: 'score', no: '04', label: '稳健评分', short: '评分', tip: '创新二：三套规则计算后输出区间与等级稳定性，而不是一个看似精确的分数。' },
  { id: 'explain', no: '05', label: '证据化解释', short: '解释', tip: '创新三：结论逐条挂数据查询、规则版本与缺口；规则模板生成解释，不改数值。' },
  { id: 'agents', no: '06', label: '多 Agent 复核', short: '复核', tip: '创新四：生成者不能验收自己的结论；版本冲突自动回退。' },
  { id: 'report', no: '07', label: '报告与版本', short: '报告', tip: '可下载报告带数据来源、查询参数、规则版本、限制声明与水印。' },
  { id: 'retest', no: '08', label: '对照地块与可比性', short: '对照', tip: '先判断可比性：同源同深度可横向比较，但不同地块不是复测，不能算改善。' },
]

function esc(value) {
  return String(value).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]))
}

export function buildReportHtml() {
  const indicatorRows = indicators.map(item => `<tr><td>${esc(item.label)}</td><td>${esc(item.value)} ${esc(item.unit)}</td><td>${esc(indicatorStats[item.code].avg)}</td><td>${esc(item.role === 'N' ? 'N 共享' : item.role === 'X' ? 'X 区域' : '预算外')}</td></tr>`).join('')
  const functionRows = functions.map(item => `<tr><td>${esc(item.label)}</td><td>${item.score}</td><td>${esc(item.score >= 80 ? '较好' : item.score >= 65 ? '中等' : '偏低')}</td></tr>`).join('')
  const ruleRows = rules.map(item => `<tr><td>${esc(item.name)}</td><td>${esc(item.basis)}</td><td>${item.score}</td><td>${esc(item.grade)}</td></tr>`).join('')
  const sectionList = report.sections.map(item => `<li>${esc(item)}</li>`).join('')
  const limits = report.limits.map(item => `<li>${esc(item)}</li>`).join('')
  const shortboardList = shortboards.map(item => `<li><b>${esc(item.title)}</b>：${esc(item.detail)}（${esc(item.evidence)}）</li>`).join('')
  return `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>沃壤知行 · 案例评价报告 ${esc(caseA.id)}</title>
<style>
  body{margin:0;background:#eef1e9;font-family:"HarmonyOS Sans SC","Microsoft YaHei UI",sans-serif;color:#23382d;line-height:1.7}
  .paper{max-width:880px;margin:30px auto;padding:56px 64px;background:#fff;box-shadow:0 18px 60px rgba(20,45,30,.12);position:relative;overflow:hidden}
  .paper:before{content:"DEMO · 案例计算";position:absolute;right:-46px;top:42px;transform:rotate(24deg);font-size:20px;letter-spacing:.24em;color:rgba(180,60,40,.10);font-weight:700;white-space:nowrap}
  h1{margin:0 0 6px;font-size:26px;font-weight:600;color:#1c3a28}
  .sub{color:#5d7264;font-size:13px;margin:0 0 4px}
  .badge{display:inline-block;margin:14px 0 22px;padding:4px 12px;border:1px solid #b7c9b2;border-radius:999px;color:#3f6a4c;font-size:12px;letter-spacing:.04em}
  h2{font-size:16px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid #dfe6dc;color:#2b4c34}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:8px 6px;border-bottom:1px solid #edf0eb;vertical-align:top}
  th{color:#6f8373;font-weight:600;background:#f7f9f3}
  ul{margin:8px 0 0;padding-left:20px;font-size:13px}
  .meta{display:grid;grid-template-columns:1fr 1fr;gap:6px 24px;font-size:13px;color:#3d5345}
  .warn{background:#fdf6ee;border:1px solid #f0dcc4;border-radius:8px;padding:14px 18px;font-size:13px;color:#7c5a35;margin-top:22px}
  .src{background:#f4f8ef;border:1px solid #d8e5d2;border-radius:8px;padding:14px 18px;font-size:12.5px;color:#456352;margin-top:14px}
  .foot{margin-top:30px;padding-top:14px;border-top:1px solid #dfe6dc;color:#839586;font-size:11px}
  code{font-size:11px;color:#5c7565}
  @media print{body{background:#fff}.paper{box-shadow:none;margin:0;padding:28px 34px}}
</style></head>
<body><div class="paper">
  <h1>农田土壤健康评价 · 案例计算报告</h1>
  <p class="sub">${esc(caseA.name)} · ${esc(caseA.crop)} · ${esc(caseA.depth)} · ${esc(caseA.region)}</p>
  <span class="badge">公开数据案例 · 演示规则计算 · 不构成健康诊断或农艺处方</span>
  <div class="meta">
    <div>报告版本：${esc(report.version)}（${esc(report.status)}）</div>
    <div>生成时间：${esc(report.generatedAt)}</div>
    <div>运行标识：${esc(scenario.runId)}</div>
    <div>规则版本：${esc(scenario.rulesVersion)}</div>
    <div>数据来源：${esc(dataSource.name)}（${esc(dataSource.license)}）</div>
    <div>查询时间：${esc(dataSource.accessed)}</div>
  </div>
  <div class="src">
    <b>数据来源与类型</b><br>
    数据：${esc(dataSource.name)}，${esc(dataSource.description)}，${esc(dataSource.type)}。<br>
    查询：坐标 ${esc(caseA.lon)}°E, ${esc(caseA.lat)}°N；${esc(dataSource.query)}；接口 <code>${esc(dataSource.api)}</code>。<br>
    引用：${esc(dataSource.citation)}<br>
    许可：${esc(dataSource.license)}；数据为区域预测值，非本地实测。
  </div>
  <h2>一、指标值与规则得分</h2>
  <table><thead><tr><th>指标</th><th>查询值</th><th>三套规则平均得分</th><th>选测角色</th></tr></thead><tbody>${indicatorRows}</tbody></table>
  <h2>二、N+X 选测清单（预算 ${scenario.budget} 项）</h2>
  <ul>
    <li>共享指标 N：${N_POOL.map(code => labelOf(code)).join('、')}</li>
    <li>区域增补 X：${selectedX.map(code => labelOf(code)).join('、')}</li>
    <li>预算外：${labelOf(extraCode)}（保留为补测候选，未纳入评分）</li>
    <li>取舍说明：${esc(selection.tradeoff)}</li>
  </ul>
  <h2>三、功能评分与总分区间</h2>
  <table><thead><tr><th>功能</th><th>评分（0–100）</th><th>等级</th></tr></thead><tbody>${functionRows}</tbody></table>
  <p>三套规则综合分：${compositeValues.map(v => v.toFixed(1)).join(' / ')}；区间 ${rangeLow}–${rangeHigh}（中值 ${medianComposite}）。${esc(scoreSummary.explanation)}</p>
  <h2>四、规则敏感性</h2>
  <table><thead><tr><th>规则集</th><th>依据</th><th>综合分</th><th>等级</th></tr></thead><tbody>${ruleRows}</tbody></table>
  <p>${esc(stability.conclusion)}</p>
  <h2>五、稳定短板与敏感项</h2>
  <ul>${shortboardList}</ul>
  <h2>六、证据缺口与补测建议</h2>
  <ul>
    <li>区域预测值不是本地实测：需按 0–20 cm 采样并登记实验室报告号、检测方法与质控样。</li>
    <li>缺有效磷与速效氮：无法判断磷限制与氮供应速率。</li>
    <li>${labelOf(extraCode)} 被检测预算挤出，但属稳定短板，建议优先补测。</li>
  </ul>
  <h2>七、复核记录与版本</h2>
  <ul>
    <li>独立复核角色检出：解释稿 v1 引用规则 v0.1，与当前激活的 v0.2 不一致。</li>
    <li>处理：阻止报告发布 → 退回计算步骤重算 → 解释稿 v2 → 复核通过。</li>
    <li>${esc(report.status)}；结果文件指纹：sha256:9d54…b2（演示占位）。</li>
  </ul>
  <h2>八、报告目录</h2>
  <ul>${sectionList}</ul>
  <div class="warn"><b>适用范围与限制</b><ul>${limits}</ul></div>
  <div class="foot">沃壤知行 · 土壤健康智能决策平台 · 答辩演示模式（${DEMO_VERSION}）· 报告由公开数据案例与演示规则计算生成，可打印或另存为 PDF。</div>
</div></body></html>`
}

export function getScenarioSummary() {
  return {
    field: caseA.name,
    crop: caseA.crop,
    depth: caseA.depth,
    indicatorCount: indicators.length,
    selectedCount: N_POOL.length + selectedX.length,
    budget: scenario.budget,
    source: dataSource.name,
  }
}
