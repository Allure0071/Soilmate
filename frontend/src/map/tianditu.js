export const tiandituAttribution = '底图 © <a href="https://www.tianditu.gov.cn/" target="_blank" rel="noopener noreferrer">天地图</a>'

// Use the official Web Mercator tile matrix. Soil tiles and point APIs keep
// their existing coordinates; GCJ-02 tiles must not be substituted here.
export function createTiandituBasemap(leaflet, map, key, onState) {
  const token = key.trim()
  const labels = map.getPane('basemap-labels') || map.createPane('basemap-labels')
  labels.style.zIndex = '450'
  labels.style.pointerEvents = 'none'
  let layers = [], revision = 0
  const clear = () => {
    for (const layer of layers) { layer.off(); map.removeLayer(layer) }
    layers = []
  }
  const switchTo = mode => {
    if (!['vector', 'satellite'].includes(mode)) throw new Error('Unknown basemap mode')
    const current = ++revision
    clear()
    if (!token) { onState('unconfigured'); return }
    const names = mode === 'satellite' ? ['img', 'cia'] : ['vec', 'cva']
    const states = ['loading', 'loading']
    const report = () => {
      if (current !== revision) return
      onState(states.includes('error') ? 'error' : states.every(state => state === 'ready') ? 'ready' : 'loading')
    }
    onState('loading')
    layers = names.map((name, index) => {
      const url = `https://t{s}.tianditu.gov.cn/${name}_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${name}&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${encodeURIComponent(token)}`
      const layer = leaflet.tileLayer(url, {
        subdomains: '01234567', minZoom: 3, maxZoom: 18,
        pane: index ? 'basemap-labels' : 'tilePane',
        className: index ? 'soil-basemap-labels' : 'soil-basemap-tiles',
        attribution: index ? '' : tiandituAttribution,
        // Provider coverage limits do not change the scientific map's zoom.
        zIndex: 0,
      })
      layer.on('loading', () => { states[index] = 'loading'; report() })
      layer.on('tileerror', () => { states[index] = 'error'; report() })
      layer.on('load', () => { if (states[index] !== 'error') states[index] = 'ready'; report() })
      return layer
    })
    for (const layer of layers) layer.addTo(map)
  }
  return {
    switchTo,
    destroy() { revision++; clear() },
  }
}
