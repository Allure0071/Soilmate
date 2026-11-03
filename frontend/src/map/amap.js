import { toGcj02 } from './coordinates.js'

let sdkPromise = null
function loadSdk(key, serviceHost) {
  if (window.AMap) return Promise.resolve(window.AMap)
  if (sdkPromise) return sdkPromise
  if (serviceHost) window._AMapSecurityConfig = { serviceHost }
  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    const timeout = window.setTimeout(() => { sdkPromise = null; script.remove(); reject(new Error('Map SDK unavailable')) }, 20000)
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`
    script.async = true
    script.onload = () => {
      window.clearTimeout(timeout)
      if (window.AMap) resolve(window.AMap)
      else { sdkPromise = null; script.remove(); reject(new Error('Map SDK unavailable')) }
    }
    script.onerror = () => { window.clearTimeout(timeout); sdkPromise = null; script.remove(); reject(new Error('Map SDK unavailable')) }
    document.head.append(script)
  })
  return sdkPromise
}

// The official SDK owns the basemap, labels, logo and review attribution.
// Leaflet owns input and scientific overlays, in the same display projection.
export function createAmapBasemap(leafletMap, host, key, onState, serviceHost = '') {
  let sdk = null, providerMap = null, satelliteLayers = null, disposed = false, mode = 'vector', visibleMode = 'vector', deadline = 0
  let state = 'unconfigured'
  const report = value => { state = value; if (!disposed) onState(value) }
  const applyMode = () => {
    if (mode === visibleMode) return
    if (mode === 'satellite') {
      satelliteLayers ||= [new sdk.TileLayer.Satellite(), new sdk.TileLayer.RoadNet()]
      providerMap.add(satelliteLayers)
    } else if (satelliteLayers) providerMap.remove(satelliteLayers)
    visibleMode = mode
  }
  const sync = () => {
    if (disposed || !sdk || !host.clientWidth || !host.clientHeight) return
    const center = leafletMap.getCenter()
    const location = toGcj02([center.lng, center.lat])
    if (!providerMap) {
      providerMap = new sdk.Map(host, { center: location, zoom: leafletMap.getZoom(), viewMode: '2D', resizeEnable: true, animateEnable: false, dragEnable: false, keyboardEnable: false, doubleClickZoom: false, scrollWheel: false, touchZoom: false })
      applyMode()
      deadline = window.setTimeout(() => report('error'), 20000)
      providerMap.on('complete', () => { window.clearTimeout(deadline); report('ready') })
    } else providerMap.setZoomAndCenter(leafletMap.getZoom(), location, true)
  }
  const start = () => {
    if (!key) { report('unconfigured'); return }
    report('loading')
    loadSdk(key, serviceHost).then(value => { if (!disposed) { sdk = value; sync() } }, () => report('error'))
  }
  leafletMap.on('move zoom resize', sync)
  return {
    switchTo(value) {
      mode = value
      if (state === 'error' && providerMap) { providerMap.destroy(); providerMap = null; visibleMode = 'vector'; satelliteLayers = null }
      if (!providerMap) start()
      else { applyMode(); sync(); report('ready') }
    },
    destroy() {
      disposed = true
      window.clearTimeout(deadline)
      leafletMap.off('move zoom resize', sync)
      providerMap?.destroy()
    },
  }
}
