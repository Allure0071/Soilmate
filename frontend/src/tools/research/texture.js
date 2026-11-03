// USDA fine-earth texture classes. Percent by mass; sand 0.05–2 mm,
// silt 0.002–0.05 mm, clay <0.002 mm. See SOURCES.md for references.
export const textureClasses = [
  ['S', '砂土', 'Sand', [[100,0,0],[90,0,10],[85,15,0]]],
  ['LS', '壤质砂土', 'Loamy sand', [[85,15,0],[70,30,0],[85,0,15],[90,0,10]]],
  ['SL', '砂壤土', 'Sandy loam', [[70,30,0],[50,50,0],[43,50,7],[52,41,7],[52,28,20],[80,0,20],[85,0,15]]],
  ['L', '壤土', 'Loam', [[52,28,20],[45,28,27],[23,50,27],[43,50,7],[52,41,7]]],
  ['SIL', '粉壤土', 'Silt loam', [[50,50,0],[20,80,0],[8,80,12],[0,88,12],[0,73,27],[23,50,27]]],
  ['SI', '粉土', 'Silt', [[20,80,0],[0,100,0],[0,88,12],[8,80,12]]],
  ['SCL', '砂质黏壤土', 'Sandy clay loam', [[80,0,20],[52,28,20],[45,28,27],[45,20,35],[65,0,35]]],
  ['CL', '黏壤土', 'Clay loam', [[45,28,27],[20,53,27],[20,40,40],[45,15,40]]],
  ['SICL', '粉质黏壤土', 'Silty clay loam', [[20,53,27],[0,73,27],[0,60,40],[20,40,40]]],
  ['SC', '砂质黏土', 'Sandy clay', [[65,0,35],[45,20,35],[45,0,55]]],
  ['SIC', '粉质黏土', 'Silty clay', [[20,40,40],[0,60,40],[0,40,60]]],
  ['C', '黏土', 'Clay', [[45,15,40],[20,40,40],[0,40,60],[0,0,100],[45,0,55]]],
].map(([id, name, english, vertices]) => ({ id, name, english, vertices }))

export function classifyTexture(values, normalize = false) {
  const raw = ['sand','silt','clay'].map(key => {
    const value = String(values[key] ?? '').trim()
    if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(value) || !Number.isFinite(Number(value)) || Number(value) > 100) throw new Error('砂、粉、黏粒均须填写 0～100 之间的百分数。')
    return Number(value)
  })
  const total = raw.reduce((a,b) => a+b, 0)
  if (!total) throw new Error('三个组分不能全部为 0。')
  if (!normalize && Math.abs(total - 100) > 1e-6) throw new Error(`当前合计为 ${Number(total.toFixed(6))}%，须为 100%；或明确选择按总量归一化。`)
  const [sand,silt,clay] = Math.abs(total-100) < 1e-12 ? raw : raw.map(value => value / total * 100)
  let id
  if (silt + 1.5*clay < 15) id = 'S'
  else if (silt + 2*clay < 30) id = 'LS'
  else if ((clay >= 7 && clay < 20 && sand > 52) || (clay < 7 && silt < 50)) id = 'SL'
  else if (clay >= 7 && clay < 27 && silt >= 28 && silt < 50 && sand <= 52) id = 'L'
  else if ((silt >= 50 && clay >= 12 && clay < 27) || (silt >= 50 && silt < 80 && clay < 12)) id = 'SIL'
  else if (silt >= 80 && clay < 12) id = 'SI'
  else if (clay >= 20 && clay < 35 && silt < 28 && sand > 45) id = 'SCL'
  else if (clay >= 27 && clay < 40 && sand > 20 && sand <= 45) id = 'CL'
  else if (clay >= 27 && clay < 40 && sand <= 20) id = 'SICL'
  else if (clay >= 35 && sand > 45) id = 'SC'
  else if (clay >= 40 && silt >= 40) id = 'SIC'
  else if (clay >= 40 && sand <= 45 && silt < 40) id = 'C'
  else throw new Error('无法分类，请核对组分比例。')
  return { ...textureClasses.find(item => item.id === id), sand, silt, clay, raw, total, normalized: Math.abs(total - 100) > 1e-6 }
}

export const texturePoint = ([sand,silt,clay]) => ({ x: 60 + 420*(silt + clay/2)/100, y: 405 - 363.73067*clay/100 })
