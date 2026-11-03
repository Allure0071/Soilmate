export const MAX_ROWS = 5000
export const MAX_COLUMNS = 60
export const missing = value => /^(?:|na|n\/a|null|nan|—|-)$/i.test(String(value ?? '').trim())

// RFC 4180-style quoting, including embedded newlines and escaped quotes.
export function parseDelimited(text) {
  text = String(text).replace(/^\uFEFF/, '')
  if (text.length > 2_000_000) throw new Error('文本过大，请控制在 200 万字符以内。')
  let inQuote=false, tabs=0, commas=0
  for (let i=0;i<text.length;i++) {
    if (text[i]==='"') { if(inQuote&&text[i+1]==='"') i++; else inQuote=!inQuote }
    else if (!inQuote) { if(/[\r\n]/.test(text[i])) break; if(text[i]==='\t') tabs++; if(text[i]===',') commas++ }
  }
  const delimiter = tabs > commas ? '\t' : ','
  const rows = [], row = []
  let cell = '', quoted = false, closed = false
  function pushCell() { row.push(cell); cell = ''; closed = false }
  function pushRow() { pushCell(); rows.push(row.splice(0)); if (rows.length > MAX_ROWS + 1) throw new Error(`最多读取 ${MAX_ROWS} 行数据。`) }
  for (let i=0;i<text.length;i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i+1] === '"') { cell += '"'; i++ }
      else if (c === '"') { quoted = false; closed = true }
      else cell += c
    } else if (c === '"' && !cell && !closed) quoted = true
    else if (c === delimiter) pushCell()
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i+1] === '\n') i++; pushRow() }
    else if (closed || c === '"') throw new Error(`第 ${rows.length+1} 行的引号格式不正确。`)
    else cell += c
    if (row.length > MAX_COLUMNS) throw new Error(`最多读取 ${MAX_COLUMNS} 列。`)
  }
  if (quoted) throw new Error('存在未闭合的引号，请检查文件格式。')
  if (cell || row.length || closed) pushRow()
  return prepareTable(rows)
}

export function prepareTable(input) {
  const rows = input.map(row => row.map(value => value == null ? '' : value instanceof Date ? value.toISOString() : String(value)))
  while (rows.length && rows.at(-1).every(value => value.trim() === '')) rows.pop()
  if (rows.length < 2) throw new Error('需要一行表头和至少一行数据。')
  const headers = rows[0].map(value => value.trim())
  if (headers.length > MAX_COLUMNS || rows.length-1 > MAX_ROWS) throw new Error(`最多支持 ${MAX_ROWS} 行、${MAX_COLUMNS} 列。`)
  if (headers.some(value => !value)) throw new Error('表头存在空列名，请补齐列名。')
  if (new Set(headers).size !== headers.length) throw new Error('表头存在重复列名，请先区分各列。')
  const data = rows.slice(1).map((row,index) => {
    if (row.length > headers.length && row.slice(headers.length).some(value => value !== '')) throw new Error(`第 ${index+2} 行的列数多于表头，请检查分隔符或引号。`)
    return headers.map((_,i) => row[i] ?? '')
  })
  return { headers, rows: data }
}

export function numericCell(value) {
  const match = String(value).trim().match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*([^\d\s].*)?$/i)
  if (!match || !Number.isFinite(Number(match[1]))) return null
  return { value: Number(match[1]), unit: (match[2] || '').trim() }
}
// SI prefixes are case-sensitive: mg and Mg must remain distinct.
const unitKey = unit => String(unit).trim().replace(/µ/g,'μ').replace(/\s+/g,'')
export function defaultRules(table) {
  return table.headers.map((header,index) => {
    const observed = table.rows.map(row => row[index]).filter(value => !missing(value))
    const id = /^(?:id|sample[_ -]?id|样本(?:编号|id)|样品(?:编号|id)|编号)$/i.test(header)
    const unit = header.match(/[（(\[]([^()（）\[\]]+)[）)\]]\s*$/)?.[1] || ''
    const numeric = !id && (/^(?:ph|soc|som|ec|tn|tp|an|ap|ak|sand|silt|clay|纬度|经度|容重|砂粒|粉粒|黏粒|粘粒)\b/i.test(header) || observed.length && observed.filter(value => numericCell(value)).length / observed.length >= .6)
    return { kind: numeric ? 'number' : 'text', unit, min: '', max: '' }
  })
}
const quantile = (values,p) => { const i=(values.length-1)*p, a=Math.floor(i); return values[a]+(values[Math.ceil(i)]-values[a])*(i-a) }
export function auditTable(table, rules, idColumn = -1, checkOutliers = true) {
  const issues = [], profiles = [], ids = new Map(), records = new Map()
  const add = (row,column,severity,type,message) => issues.push({ row: row+2, column: column < 0 ? '整行' : table.headers[column], severity, type, value: column < 0 ? '' : table.rows[row][column], message })
  table.rows.forEach((row,i) => {
    const key = JSON.stringify(row)
    if (records.has(key)) add(i,-1,'warning','重复行',`与表格第 ${records.get(key)+2} 行内容完全相同，请核对。`)
    else records.set(key,i)
    if (idColumn >= 0 && !missing(row[idColumn])) { const id=row[idColumn].trim(); if (!ids.has(id)) ids.set(id,[]); ids.get(id).push(i) }
  })
  for (const indices of ids.values()) if (indices.length > 1) for (const i of indices) add(i,idColumn,'warning','重复编号','编号重复，请确认是否为重复测定、不同土层或重复记录。')
  table.headers.forEach((header,col) => {
    const rule = rules[col], numbers = [], units = new Set(), missingRows = []
    const min = String(rule.min).trim() === '' ? null : Number(rule.min), max = String(rule.max).trim() === '' ? null : Number(rule.max)
    if (rule.kind === 'number' && ((min !== null && !Number.isFinite(min)) || (max !== null && !Number.isFinite(max)) || (min !== null && max !== null && min > max))) throw new Error(`${header} 的范围设置无效。`)
    table.rows.forEach((row,i) => {
      if (missing(row[col])) { missingRows.push(i); add(i,col,'warning','缺失值','为空或使用了缺失标记，未填补。'); return }
      if (rule.kind !== 'number') return
      const number = numericCell(row[col])
      if (!number) { add(i,col,'error','非数值','此列设为数值，但单元格无法解析为有限数值。'); return }
      const unit = unitKey(number.unit || rule.unit)
      units.add(unit)
      numbers.push({ row:i, value:number.value, unit })
      if (number.unit && rule.unit && unitKey(number.unit) !== unitKey(rule.unit)) add(i,col,'warning','单位不一致',`单元格单位与设置的 ${rule.unit} 不一致，未自动换算。`)
    })
    if (units.size > 1) for (const item of numbers) add(item.row,col,'warning','混用单位','本列出现多个单位或有单位与无单位混用，未合并统计、未换算。')
    const incomparable = units.size > 1 || Boolean(rule.unit && numbers.some(item=>item.unit!==unitKey(rule.unit)))
    if (!incomparable) for (const item of numbers) if ((min !== null && item.value < min) || (max !== null && item.value > max)) add(item.row,col,'warning','范围核对','超出手动设置的范围；请结合单位和测定方法核对。')
    const sorted = !incomparable ? numbers.map(item => item.value).sort((a,b)=>a-b) : []
    if (checkOutliers && sorted.length >= 4) {
      const q1=quantile(sorted,.25), q3=quantile(sorted,.75), iqr=q3-q1
      if (iqr > 0) for (const item of numbers) if (item.value < q1-1.5*iqr || item.value > q3+1.5*iqr) add(item.row,col,'warning','疑似离群值','超出 Q1−1.5×IQR 或 Q3+1.5×IQR，仅标记、不删除。')
    }
    profiles.push({ header, missing:missingRows.length, numeric:numbers.length, min:sorted.length?sorted[0]:null, max:sorted.length?sorted.at(-1):null, mixed:incomparable })
  })
  return { issues, profiles, rows:table.rows.length, columns:table.headers.length, errors:issues.filter(item=>item.severity==='error').length, warnings:issues.filter(item=>item.severity==='warning').length }
}

export function toCsv(rows) {
  return '\uFEFF' + rows.map(row => row.map(value => {
    let text=String(value ?? '')
    if (/^[\s]*[=+@-]/.test(text)) text="'"+text
    return '"'+text.replace(/"/g,'""')+'"'
  }).join(',')).join('\r\n')
}
export function downloadBlob(content, filename, type = 'text/plain;charset=utf-8') {
  const url=URL.createObjectURL(new Blob([content],{type})), a=document.createElement('a')
  a.href=url; a.download=filename; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000)
}
