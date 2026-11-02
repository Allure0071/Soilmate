async (page) => {
  await page.route('**/api/indicators?*', route => route.fulfill({ json: { res: 5, count: 1, indicators: [{ col_name: 'soil_ph', cname: '土壤酸碱度', min: 0, max: 1400 }] } }))
  await page.route('**/api/data?*', route => {
    const params = new URL(route.request().url()).searchParams
    const table = params.get('table')
    const res = params.get('res')
    const pageNumber = Number(params.get('page'))
    return route.fulfill({ json: {
      total: table === 'points' ? 101 : 2,
      columns: [{ col: 'source' }, { col: 'row' }, { col: 'col' }],
      rows: [[`${res} km / ${table}`, pageNumber, 7]],
    } })
  })
  await page.reload()
  await page.getByRole('button', { name: '数据浏览' }).first().click()
  await page.getByRole('button', { name: 'points' }).click()
  await page.getByText('5 km / points').waitFor()
  await page.getByRole('button', { name: '下一页' }).click()
  await page.getByText('5 km / points').waitFor()
  await page.getByRole('button', { name: '1 km 数据库' }).click()
  await page.getByRole('button', { name: 'meta' }).click()
  await page.getByText('1 km / meta').waitFor()
  await page.getByRole('button', { name: '返回地图' }).click()
  await page.getByRole('region', { name: '土壤指标地图' }).waitFor()
}
