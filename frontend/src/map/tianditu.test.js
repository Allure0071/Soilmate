import test from 'node:test'
import assert from 'node:assert/strict'
import { createTiandituBasemap } from './tianditu.js'

function environment(key = 'test-key') {
  const created = [], removed = [], states = [], panes = new Map()
  const soilLayer = { id: 'scientific-overlay' }
  const map = {
    center: [35, 105], zoom: 4, layers: [soilLayer],
    getPane(name) { return panes.get(name) },
    createPane(name) { const pane = { style: {} }; panes.set(name, pane); return pane },
    removeLayer(layer) { removed.push(layer); this.layers = this.layers.filter(item => item !== layer) },
  }
  const leaflet = {
    tileLayer(url, options) {
      const handlers = new Map()
      const layer = {
        url, options, handlers,
        on(name, callback) { handlers.set(name, callback) },
        off() { handlers.clear() },
        addTo(target) { target.layers.push(this) },
        emit(name) { handlers.get(name)?.() },
      }
      created.push(layer)
      return layer
    },
  }
  const control = createTiandituBasemap(leaflet, map, key, state => states.push(state))
  return { control, created, removed, states, panes, map, soilLayer }
}

test('without a project key no map requests or foreign fallback are created', () => {
  const env = environment('  ')
  env.control.switchTo('vector')
  env.control.switchTo('satellite')
  assert.deepEqual(env.states, ['unconfigured', 'unconfigured'])
  assert.equal(env.created.length, 0)
  assert.deepEqual(env.map.layers, [env.soilLayer])
  env.control.destroy()
})

test('switching standard and satellite basemaps preserves scientific overlays and view', () => {
  const env = environment('test & key')
  env.control.switchTo('vector')
  assert.equal(env.map.layers.length, 3)
  const [base, labels] = env.created
  const url = new URL(base.url.replace('{s}', '0'))
  assert.equal(url.hostname, 't0.tianditu.gov.cn')
  assert.equal(url.pathname, '/vec_w/wmts')
  assert.equal(url.searchParams.get('tk'), 'test & key')
  assert.equal(url.searchParams.get('TILEMATRIXSET'), 'w')
  assert.equal(url.searchParams.get('TILEROW'), '{y}')
  assert.equal(url.searchParams.get('TILECOL'), '{x}')
  assert.equal(labels.options.pane, 'basemap-labels')
  assert.equal(env.panes.get('basemap-labels').style.zIndex, '450')
  assert.equal(env.panes.get('basemap-labels').style.pointerEvents, 'none')
  base.emit('load')
  assert.equal(env.states.at(-1), 'loading', 'both base and annotation must finish')
  labels.emit('load')
  assert.equal(env.states.at(-1), 'ready')
  const staleError = base.handlers.get('tileerror')
  env.control.switchTo('satellite')
  assert.deepEqual(env.removed, [base, labels])
  assert.ok(env.created[2].url.includes('/img_w/'))
  assert.ok(env.created[3].url.includes('/cia_w/'))
  staleError()
  assert.equal(env.states.at(-1), 'loading', 'an obsolete tile cannot change the new map status')
  assert.ok(env.map.layers.includes(env.soilLayer))
  assert.deepEqual(env.map.center, [35, 105])
  assert.equal(env.map.zoom, 4)
  env.control.destroy()
  assert.deepEqual(env.map.layers, [env.soilLayer])
  assert.ok(env.created.every(layer => layer.handlers.size === 0))
})

test('tile errors remain visible until a new load succeeds; retry releases old layers', () => {
  const env = environment()
  env.control.switchTo('vector')
  env.created[0].emit('tileerror')
  env.created[0].emit('load')
  env.created[1].emit('load')
  assert.equal(env.states.at(-1), 'error')
  env.control.switchTo('vector')
  assert.equal(env.removed.length, 2)
  env.created[2].emit('load')
  env.created[3].emit('load')
  assert.equal(env.states.at(-1), 'ready')
  env.control.destroy()
})
