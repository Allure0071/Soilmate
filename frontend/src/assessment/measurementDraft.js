// Frontend input metadata only. No evaluation rules, conversions or model calls.
// The backend-owned dictionary will replace these review-only field definitions.
export const reviewIndicators = [
  { code: 'soil_ph', name: '酸碱度 pH', short: 'pH', units: [] },
  { code: 'EC', name: '电导率 EC', short: 'EC', units: ['dS/m', 'μS/cm'] },
  { code: 'TN', name: '全氮 TN', short: 'TN', units: ['g/kg', '%'] },
  { code: 'AN', name: '碱解氮 AN', short: 'AN', units: ['mg/kg'] },
  { code: 'AP', name: '有效磷 AP', short: 'AP', units: ['mg/kg'] },
  { code: 'AK', name: '速效钾 AK', short: 'AK', units: ['mg/kg'] },
  { code: 'cec', name: '阳离子交换量 CEC', short: 'CEC', units: ['cmol/kg'] },
  { code: 'BD', name: '土壤容重 BD', short: 'BD', units: ['g/cm³', 'kg/m³'] },
  { code: 'SOC', name: '有机碳 SOC', short: 'SOC', units: ['g/kg', '%'] },
  { code: 'SOM', name: '有机质 SOM', short: 'SOM', units: ['g/kg', '%'] },
  { code: 'Sand', name: '砂粒含量', short: 'Sand', units: ['%'] },
  { code: 'Clay', name: '黏粒含量', short: 'Clay', units: ['%'] },
];

export function createRow(indicatorCode = 'soil_ph') {
  const indicator = reviewIndicators.find(item => item.code === indicatorCode) || reviewIndicators[0];
  return {
    id: globalThis.crypto?.randomUUID?.() || `row-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    indicator_code: indicator.code,
    value: '',
    unit: indicator.units[0] || '',
    method: '',
  };
}

export function isNumericValue(value) {
  const text = String(value ?? '').trim();
  return /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(text) && Number.isFinite(Number(text));
}

export function inspectRows(rows) {
  const errors = {};
  const values = [];
  const seen = new Set();
  for (const row of rows) {
    if (String(row.value ?? '').trim() === '') continue;
    const indicator = reviewIndicators.find(item => item.code === row.indicator_code);
    if (!indicator) errors[row.id] = '请重新选择指标。';
    else if (seen.has(row.indicator_code)) errors[row.id] = '本次录入中指标重复，请合并或调整。';
    else if (!isNumericValue(row.value)) errors[row.id] = '请输入有效数字，不要在数值中填写单位。';
    else if (indicator.units.length && !indicator.units.includes(row.unit)) errors[row.id] = '请选择与检测报告一致的单位。';
    else {
      values.push({
        indicator_code: row.indicator_code,
        value: Number(String(row.value).trim()),
        unit: row.unit || null,
        method: row.method.trim() || null,
        source_type: 'user_measurement',
      });
    }
    seen.add(row.indicator_code);
  }
  return {
    errors,
    values,
    valid: values.length > 0 && Object.keys(errors).length === 0,
    emptyCount: rows.filter(row => String(row.value ?? '').trim() === '').length,
  };
}

export function restoreRows(value) {
  if (!Array.isArray(value)) return [createRow()];
  return value.slice(0, reviewIndicators.length).filter(row =>
    row && reviewIndicators.some(item => item.code === row.indicator_code)
  ).map(row => {
    const restored = createRow(row.indicator_code);
    return {
      ...restored,
      value: typeof row.value === 'string' || typeof row.value === 'number' ? String(row.value).slice(0, 100) : '',
      unit: typeof row.unit === 'string' ? row.unit : restored.unit,
      method: typeof row.method === 'string' ? row.method.slice(0, 120) : '',
    };
  });
}
