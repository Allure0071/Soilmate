// Research mapping from docs/n-plus-x-data-gap.md. An id is used only where
// the audit identified an exact existing raster field; other X values remain
// unbound until the backend supplies verified spatial data and metadata.
const entry = (label, id = null) => ({ label, id })

export const regionIndicatorConfig = {
  '东北区': [entry('土壤电导率 EC', 'ece'), entry('含盐量'), entry('年均温 / 积温'), entry('土壤含水量')],
  '内蒙古及长城沿线区': [entry('砂粒含量', 'soil_btsnd'), entry('降水量 / 蒸散量'), entry('土壤电导率 EC', 'ece'), entry('土壤容重', 'soil_bd')],
  '黄淮海区': [entry('土壤电导率 EC', 'ece'), entry('含盐量'), entry('地下水埋深')],
  '黄土高原区': [entry('侵蚀模数'), entry('坡度'), entry('田间持水量'), entry('土壤有机碳 SOC', 'soil_soc')],
  '长江中下游区': [entry('地下水位'), entry('Cd / As / Pb / Cr / Hg 含量及有效态')],
  '西南区': [entry('土壤酸碱度 pH', 'soil_ph'), entry('交换性铝'), entry('砾石含量', 'soil_cf'), entry('侵蚀模数')],
  '华南区': [entry('土壤酸碱度 pH', 'soil_ph'), entry('交换性铝'), entry('侵蚀模数')],
  '甘新区': [entry('降水量 / 蒸散量'), entry('土壤电导率 EC', 'ece'), entry('含盐量'), entry('砂粒含量', 'soil_btsnd')],
  '青藏区': [entry('年均温 / 积温'), entry('地下水位'), entry('砾石含量', 'soil_cf')],
}

export function regionalConfigFor(regionName) {
  return regionIndicatorConfig[regionName] || null
}
