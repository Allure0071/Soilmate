async (page) => {
  const indicators = [
    ['ece', '土壤电导率', ''],
    ['soil_bd', '土壤容重', 'g/cm³'],
    ['soil_btsnd', '砂粒含量', '%'],
    ['soil_cec', '阳离子交换量', 'cmol(+)/kg'],
    ['soil_ph', '土壤酸碱度', ''],
  ].map(([col_name, cname, unit]) => ({ col_name, cname, unit, min: 0, max: 100 }))
  await page.route('**/api/indicators?res=5', route => route.fulfill({ json: { res: 5, count: indicators.length, indicators } }))
  await page.route('**/api/point?*', route => {
    const lon = Number(new URL(route.request().url()).searchParams.get('lon'))
    const lat = Number(new URL(route.request().url()).searchParams.get('lat'))
    return route.fulfill({ json: {
      found: true,
      lon, lat, regionName: '黄淮海区', regionId: 'QA-REGION', gridId: 'QA-GRID',
      geometry: { type: 'Polygon', coordinates: [[
        [lon - 0.05, lat - 0.05], [lon + 0.05, lat - 0.05],
        [lon + 0.05, lat + 0.05], [lon - 0.05, lat + 0.05],
        [lon - 0.05, lat - 0.05],
      ]] },
      values: {
        ece: { value: 1.4, unit: '' },
        soil_bd: { value: 1320, unit: 'g/cm³' },
        soil_btsnd: { value: 420, unit: '%' },
        soil_cec: { value: 2100, unit: 'cmol(+)/kg' },
        soil_ph: { value: 685, unit: '' },
      },
    } })
  })
  await page.reload()
  await page.getByRole('region', { name: '土壤指标地图' }).click({ position: { x: 420, y: 350 } })
}
