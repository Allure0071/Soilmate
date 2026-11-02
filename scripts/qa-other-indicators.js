async (page) => {
  await page.route('**/api/indicators?res=5', route => route.fulfill({ json: { res: 5, count: 2, indicators: [
    { col_name: 'soil_ph', cname: '土壤酸碱度', min: 0, max: 1400 },
    { col_name: 'annual_rain', cname: '年降水量', unit: 'mm', min: 0, max: 3000 },
  ] } }))
  await page.route('**/api/point?*', route => route.fulfill({ json: { found: true, lon: 105, lat: 35, values: {
    ece: { value: 0.4 }, soil_bd: { value: 1320, unit: 'g/cm3' }, soil_btsnd: { value: 420, unit: '%' },
    soil_cec: { value: 2100, unit: 'cmol/kg' }, soil_ph: { value: 685 },
    annual_rain: { value: 607.8, unit: 'mm', cname: '年降水量' }, ch4: { value: null, cname: '甲烷排放' },
  } } }))
  await page.reload()
  await page.getByRole('region', { name: '土壤指标地图' }).click({ position: { x: 420, y: 350 } })
  const disclosure = page.locator('details.other-indicators')
  await disclosure.waitFor()
  if (await disclosure.evaluate(element => element.open)) throw new Error('Other indicators should start collapsed')
  if (await disclosure.getByText('年降水量').isVisible()) throw new Error('Other values should be hidden by default')
  await disclosure.locator('summary').click()
  await disclosure.getByText('年降水量').waitFor()
  await disclosure.getByRole('button', { name: '查看 1 项无数据指标' }).click()
  await disclosure.getByText('甲烷排放').waitFor()
}
