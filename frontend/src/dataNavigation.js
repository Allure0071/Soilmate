// Keep shareable navigation state separate from metadata and scientific values.
export function localDataPath(value, pathname) {
  try {
    const url = new URL(value, 'https://soilmate.invalid')
    return url.origin === 'https://soilmate.invalid' && url.pathname === pathname && value?.startsWith('/') && !value.startsWith('//') && value.length < 6000 ? url.pathname + url.search : ''
  } catch { return '' }
}
export function readDataLocation(search) {
  const params = new URLSearchParams(search)
  const center = (params.get('view') || '').split(',').map(Number)
  return { key: (params.get('indicator') || '').slice(0, 160), res: params.get('res') === '1' ? 1 : 5, center: center.length === 3 && center.every(Number.isFinite) && Math.abs(center[0]) <= 85 && Math.abs(center[1]) <= 180 && center[2] >= 3 && center[2] <= 12 ? center : null, resourceReturn: localDataPath(params.get('resourceReturn'), '/resources') }
}
export function mapDataPath(key, res, center, resourceReturn = '') {
  const params = new URLSearchParams({ indicator: key, res: String(res) })
  if (center) params.set('view', center.map(value => Number(value.toFixed(5))).join(','))
  const target = localDataPath(resourceReturn, '/resources')
  if (target) { const url = new URL(target, 'https://soilmate.invalid'); url.searchParams.delete('mapReturn'); params.set('resourceReturn', url.pathname + url.search) }
  return '/explore?' + params
}
export function resourceDataPath(key, res, returnMap = '', catalog = '/resources') {
  const url = new URL(localDataPath(catalog, '/resources') || '/resources', 'https://soilmate.invalid')
  url.searchParams.set('indicator', key); url.searchParams.set('res', String(res))
  const target = localDataPath(returnMap, '/explore')
  if (target) { const map = new URL(target, 'https://soilmate.invalid'); map.searchParams.delete('resourceReturn'); url.searchParams.set('mapReturn', map.pathname + map.search) }
  return url.pathname + url.search
}
