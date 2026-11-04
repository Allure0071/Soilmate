const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function getJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`数据接口返回 ${response.status}`)
  return response.json()
}

export async function fetchIndicators(res = 5) {
  return getJson(`${BASE}/api/indicators?res=${res}`)
}

export async function fetchMeta(res = 5) {
  return getJson(`${BASE}/api/meta?res=${res}`)
}

export async function fetchPreviewLayers() {
  return getJson(`${BASE}/api/preview/layers`)
}

export async function fetchZ01Boundaries() {
  return getJson(`${BASE}/api/zones/z01`)
}

export async function fetchZ01Point(lon, lat) {
  return getJson(`${BASE}/api/zones/z01/point?lon=${encodeURIComponent(lon)}&lat=${encodeURIComponent(lat)}`)
}

export async function fetchPreviewPoint(lon, lat) {
  return getJson(`${BASE}/api/preview/point?lon=${encodeURIComponent(lon)}&lat=${encodeURIComponent(lat)}`)
}

export function previewTileUrl(id) {
  return `${BASE}/api/preview/tiles/${id}/{z}/{x}/{y}.png`
}

export async function fetchPoint(lon, lat, res = 5) {
  const r = await fetch(`${BASE}/api/point?lon=${encodeURIComponent(lon)}&lat=${encodeURIComponent(lat)}&res=${res}`)
  if (r.status === 404) return null
  if (!r.ok) throw new Error(`数据接口返回 ${r.status}`)
  return r.json()
}

export async function fetchData({ res = 5, table = 'points', page = 1, pageSize = 50, bbox = null }) {
  const params = new URLSearchParams({ res, table, page, page_size: pageSize })
  if (bbox) for (const [key, value] of Object.entries(bbox)) params.set(key, value)
  return getJson(`${BASE}/api/data?${params}`)
}

export function tileUrl(colName, res = 5) {
  return `${BASE}/tiles/${res === 1 ? '1km/' : ''}${colName}/{z}/{x}/{y}.png`
}

export async function fetchSoilgridsLayers() {
  return getJson(`${BASE}/api/soilgrids/layers`)
}

export async function fetchSoilgridsPoint(lon, lat) {
  return getJson(`${BASE}/api/soilgrids/point?lon=${encodeURIComponent(lon)}&lat=${encodeURIComponent(lat)}`)
}

export function soilgridsTileUrl(code) {
  return `${BASE}/api/soilgrids/tiles/${code}/{z}/{x}/{y}.png`
}
