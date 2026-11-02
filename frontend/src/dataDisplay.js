// The API returns stored raster values. These layers use integer scale factors;
// convert only the factors supported by the ranges and texture sum in the data.
export function displayScale(colName) {
  if (/(^|_)soil_ph$/.test(colName)) return 100
  if (/(^|_)soil_bd$/.test(colName)) return 1000
  if (/(^|_)soil_(btcly|btslt|btsnd|clay)$/.test(colName)) return 10
  if (/(^|_)soil_(cec|soc|tn|tp|tk)$/.test(colName)) return 100
  return 1
}

export function displayUnit(colName, unit) {
  // The source raster's EC method and unit are unverified; use server metadata only.
  if (colName === 'ece') return unit || ''
  if (/(^|_)soil_ph$/.test(colName)) return ''
  if (/(^|_)soil_bd$/.test(colName)) return 'g/cm³'
  if (/(^|_)soil_(btcly|btslt|btsnd|clay)$/.test(colName)) return '%'
  if (/(^|_)soil_cec$/.test(colName)) return 'cmol(+)/kg'
  if (/(^|_)soil_(soc|tn|tp|tk)$/.test(colName)) return 'g/kg'
  if (/^(corn|rice|soybean|wheat)_tmpmean$/.test(colName)) return '°C'
  if (/^(corn|rice|soybean|wheat)_annual_rain$/.test(colName)) return 'mm'
  return unit || ''
}

const standardNames = {
  ece: '土壤电导率（EC）', ch4: '甲烷排放（CH₄）',
  ndvi: '归一化植被指数（NDVI）', ndsi: '归一化积雪指数（NDSI）',
  soil_awc: '土壤有效含水量（AWC）', soil_bd: '土壤容重（BD）',
  soil_btcly: '土壤黏粒含量（Clay）', soil_clay: '土壤黏粒含量（Clay）',
  soil_btslt: '土壤粉粒含量（Silt）', soil_btsnd: '土壤砂粒含量（Sand）',
  soil_cec: '阳离子交换量（CEC）', soil_ph: '土壤酸碱度（pH）',
  soil_soc: '土壤有机碳含量（SOC）', soil_socd: '土壤有机碳密度（SOCD）',
  soil_tn: '土壤全氮含量（TN）', soil_tp: '土壤全磷含量（TP）',
  soil_tk: '土壤全钾含量（TK）',
  lake_do: '湖泊溶解氧（DO）', lake_doc: '湖泊溶解有机碳（DOC）',
  lake_tn: '湖泊总氮（TN）', lake_tp: '湖泊总磷（TP）',
  lake_ph: '湖泊酸碱度（pH）', lake_cond: '湖泊电导率（EC）',
  water_do: '水体溶解氧（DO）', water_doc: '水体溶解有机碳（DOC）',
  water_tn: '水体总氮（TN）', water_tp: '水体总磷（TP）',
  water_ph: '水体酸碱度（pH）', water_cond: '水体电导率（EC）',
}

export function displayName(colName, name) {
  const cleanName = name?.replace(/（显示值为×100标度）/, '')
  if (standardNames[colName]) return standardNames[colName]
  if (cleanName && cleanName !== colName && !/^(corn|rice|soybean|wheat)_/.test(colName)) return cleanName

  const match = /^(corn|rice|soybean|wheat)_(.+)$/.exec(colName)
  if (!match) return cleanName || colName
  const crop = { corn: '玉米', rice: '水稻', soybean: '大豆', wheat: '小麦' }[match[1]]
  if (standardNames[match[2]]) return `${crop}${standardNames[match[2]]}`
  if (cleanName && cleanName !== colName) return cleanName
  const field = {
    tmpmean: '年均气温', s_deposition: '硫沉降', n_deposition: '氮沉降',
    p_fert: '磷肥施用量', n_fert: '氮肥施用量', farm_field: '农田用地',
    annual_rain: '年降水量', ch4: '甲烷排放', yield: '产量',
    '24d': '2,4-滴除草剂施用量',
    soil_socd: '土壤有机碳密度', soil_soc: '土壤有机碳含量',
    soil_ph: '土壤酸碱度 pH', soil_tp: '土壤全磷含量',
    soil_tn: '土壤全氮含量', soil_tk: '土壤全钾含量',
    soil_texture: '土壤质地类型', soil_cec: '阳离子交换量',
    soil_btsnd: '土壤砂粒含量', soil_clay: '土壤黏粒含量',
    soil_bd: '土壤容重', lake_tur: '湖泊浊度', lake_tp: '湖泊总磷',
    lake_tn: '湖泊总氮', lake_ph: '湖泊 pH', lake_doc: '湖泊溶解有机碳',
    lake_do: '湖泊溶解氧', lake_cond: '湖泊电导率',
  }[match[2]]
  return field ? `${crop}${field}` : colName
}

export function displayValue(colName, value) {
  if (value == null || !Number.isFinite(value)) return null
  // Negative 2,4-D application is physically invalid; the source rasters
  // contain values near -1 that should be treated as missing.
  if (/^(corn|rice|soybean|wheat)_2_4_d$/.test(colName) && value < 0) return null
  return value / displayScale(colName)
}
