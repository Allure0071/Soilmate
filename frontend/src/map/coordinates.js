import gcoord from 'gcoord'

export const toGcj02 = point => gcoord.transform(point, gcoord.WGS84, gcoord.GCJ02)
export const toWgs84 = point => gcoord.transform(point, gcoord.GCJ02, gcoord.WGS84)

// Public Leaflet LatLngs stay WGS84; only the display projection is GCJ-02.
export function createGcj02Crs(L) {
  const mercator = L.Projection.SphericalMercator
  return L.extend({}, L.CRS.EPSG3857, {
    code: 'GCJ02:3857',
    projection: {
      bounds: mercator.bounds,
      project(latlng) { const [lng, lat] = toGcj02([latlng.lng, latlng.lat]); return mercator.project(L.latLng(lat, lng)) },
      unproject(point) { const value = mercator.unproject(point); const [lng, lat] = toWgs84([value.lng, value.lat]); return L.latLng(lat, lng) },
    },
  })
}

// A small mesh reprojects scientific WGS84 tiles into the display grid.
// Source tile resolution is unchanged; no scientific values are recomputed.
export function tileWarpGrid(coords, step = 32) {
  const size = 256 * 2 ** coords.z
  const points = []
  for (let y = 0; y <= 256; y += step) {
    const row = []
    for (let x = 0; x <= 256; x += step) {
      const lng = (coords.x * 256 + x) / size * 360 - 180
      const lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * (coords.y * 256 + y) / size))) * 180 / Math.PI
      const [lon, latitude] = toWgs84([lng, lat])
      const sourceX = (lon + 180) / 360 * size
      const radians = Math.max(-85.05112878, Math.min(85.05112878, latitude)) * Math.PI / 180
      const sourceY = (1 - Math.log(Math.tan(Math.PI / 4 + radians / 2)) / Math.PI) / 2 * size
      row.push({ x, y, sourceX, sourceY })
    }
    points.push(row)
  }
  return points
}
