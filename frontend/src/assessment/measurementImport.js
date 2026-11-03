import { createRow, inspectRows, reviewIndicators } from './measurementDraft.js'
import { missing } from '../tools/research/tables.js'

const storageKey = 'soilmate.assessment.pending-import.v1'
const lifetime = 30 * 60 * 1000
const unitKey = value => String(value).trim().replace(/µ/g, 'μ').replace(/\s/g, '').replace(/3/g, '³')
const aliases = { soil_ph: ['ph', '酸碱度', '土壤ph'], EC: ['电导率'], TN: ['全氮'], AN: ['碱解氮'], AP: ['有效磷'], AK: ['速效钾'], cec: ['阳离子交换量'], BD: ['容重', '土壤容重'], SOC: ['有机碳', '土壤有机碳'], SOM: ['有机质'], Sand: ['砂粒', '砂粒含量'], Clay: ['黏粒', '粘粒', '黏粒含量', '粘粒含量'] }
export const headerUnit = header => header.match(/[（(\[]([^()（）\[\]]+)[）)\]]\s*$/)?.[1]?.trim() || ''
export function suggestMapping(headers) {
  return headers.map(header => {
    const name = header.replace(/[（(\[].*$/, '').trim().toLowerCase()
    const indicator = reviewIndicators.find(item => [item.code, ...(aliases[item.code] || [])].some(alias => alias.toLowerCase() === name))
    const unit = headerUnit(header)
    return { code: indicator?.code || '', unit: indicator?.units.find(candidate => unitKey(candidate) === unitKey(unit)) || '' }
  })
}

// One table row is one detection. Duplicate IDs, depths and dates are never merged.
export function inspectImport(table, mapping, index, idColumn = -1) {
  const errors = [], rows = [], fields = [], used = new Set()
  const original = table?.rows[index]
  if (!original) return { errors: ['请选择一行样本。'], rows, fields }
  mapping.forEach((item, column) => {
    if (!item.code) return
    const indicator = reviewIndicators.find(candidate => candidate.code === item.code)
    if (!indicator) { errors.push('存在不支持的指标映射。'); return }
    if (used.has(item.code)) errors.push(`${indicator.name} 映射了多列，请只保留一列。`)
    used.add(item.code)
    const raw = original[column]
    if (missing(raw)) return
    if (indicator.units.length && !indicator.units.includes(item.unit)) { errors.push(`${table.headers[column]}：请选择报告单位。`); return }
    const match = String(raw).trim().match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*(.*)$/i)
    if (!match || !Number.isFinite(Number(match[1])) || match[1].length > 100) { errors.push(`${table.headers[column]}：原值“${String(raw).slice(0, 60)}”无法作为检测数值，请修正数据或跳过此列。`); return }
    const expected = indicator.units.length ? item.unit : ''
    const fromHeader = headerUnit(table.headers[column])
    const fromCell = match[2]
    if ([fromHeader, fromCell].some(unit => unit && unitKey(unit) !== unitKey(expected))) { errors.push(`${table.headers[column]}：表头或单元格单位与所选单位不一致，请修正原表或跳过此列；不会自动换算。`); return }
    rows.push({ ...createRow(item.code), value: match[1], unit: expected })
    fields.push({ column: table.headers[column], indicator_code: item.code, raw_value: raw, unit: expected })
  })
  if (!rows.length) errors.push('本行没有可带入的检测值，请选择指标列和样本；缺失项不填补。')
  const sample = idColumn >= 0 && !missing(original[idColumn]) ? original[idColumn].trim() : `表格第 ${index + 2} 行`
  return { errors, rows, fields, sample }
}

export function buildImport(table, mapping, index, idColumn, metadata) {
  if (metadata.demo) throw new Error('合成问题示例不能带入实测录入，请导入自己的检测表。')
  const result = inspectImport(table, mapping, index, idColumn)
  if (result.errors.length) throw new Error(result.errors.join('；'))
  return {
    rows: result.rows,
    source: { file_name: metadata.fileName || '粘贴内容', sheet_name: metadata.sheetName || '', table_row: index + 2, sample_id: result.sample, imported_at: new Date().toISOString(), fields: result.fields, original: table.headers.map((column, i) => ({ column, value: table.rows[index][i] })) },
  }
}

export function restoreImportSource(value) {
  if (!value || typeof value.file_name !== 'string' || typeof value.sample_id !== 'string' || !Number.isInteger(value.table_row) || value.table_row < 2 || value.table_row > 5001 || !Array.isArray(value.fields) || !Array.isArray(value.original)) return null
  if (value.fields.length > reviewIndicators.length || value.original.length > 60) return null
  if (!value.fields.every(item => item && typeof item.column === 'string' && typeof item.raw_value === 'string' && typeof item.unit === 'string' && reviewIndicators.some(indicator => indicator.code === item.indicator_code))) return null
  if (!value.original.every(item => item && typeof item.column === 'string' && typeof item.value === 'string')) return null
  return { file_name: value.file_name, sample_id: value.sample_id, sheet_name: typeof value.sheet_name === 'string' ? value.sheet_name : '', table_row: value.table_row, imported_at: typeof value.imported_at === 'string' ? value.imported_at : '', fields: value.fields.map(({ column, indicator_code, raw_value, unit }) => ({ column, indicator_code, raw_value, unit })), original: value.original.map(({ column, value }) => ({ column, value })) }
}

// Tab-scoped handoff survives same-tab login. Never put measurements in URLs.
function validPayload(payload) {
  return Boolean(restoreImportSource(payload?.source) && Array.isArray(payload.rows) && payload.rows.length > 0 && payload.rows.length <= reviewIndicators.length && payload.rows.every(row => row && typeof row.value === 'string' && row.value.trim() && row.value.length <= 100 && typeof row.method === 'string' && typeof row.unit === 'string') && inspectRows(payload.rows).valid)
}
export function stageImport(payload, storage = sessionStorage, now = Date.now()) {
  if (!validPayload(payload)) throw new Error('导入内容无效，请重新核对。')
  const token = globalThis.crypto.randomUUID()
  try { storage.setItem(storageKey, JSON.stringify({ token, expires: now + lifetime, payload })) }
  catch { throw new Error('浏览器无法暂存这条样本，请允许会话存储或手动录入。') }
  return token
}
export function readPendingImport(token, storage = sessionStorage, now = Date.now()) {
  if (!token) return null
  let record
  try { record = JSON.parse(storage.getItem(storageKey) || 'null') } catch { throw new Error('无法读取待导入样本，请返回数据体检重新选择。') }
  if (!record || record.token !== token || record.expires <= now || !Number.isFinite(record.expires) || !validPayload(record.payload)) throw new Error('待导入样本已失效，请返回数据体检重新选择（有效期 30 分钟）。')
  return { rows: record.payload.rows, source: restoreImportSource(record.payload.source) }
}
export function discardPendingImport(token, storage = sessionStorage) {
  try { const record = JSON.parse(storage.getItem(storageKey) || 'null'); if (record?.token === token) storage.removeItem(storageKey) } catch { /* Unavailable storage must not block editing. */ }
}
