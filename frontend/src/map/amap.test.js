import test from 'node:test'
import assert from 'node:assert/strict'
import { createAmapBasemap } from './amap.js'
import { toGcj02 } from './coordinates.js'

function environment(width = 900) {
  const providers = [], states = [], timers = new Map(), listeners = new Map()
  let timerId = 0
  class Provider {
    constructor(host, options) { this.options = options; this.center = options.center; this.zoom = options.zoom; this.layers = []; this.events = {}; providers.push(this) }
    on(name, callback) { this.events[name] = callback }
    add(layers) { this.layers.push(...layers) }
    remove(layers) { this.layers = this.layers.filter(layer => !layers.includes(layer)) }
    setZoomAndCenter(zoom, center) { if (this.options.zoomEnable !== false) this.zoom = zoom; this.center = center }
    destroy() { this.destroyed = true }
  }
  globalThis.window = {
    AMap: { Map: Provider, TileLayer: { Satellite: class {}, RoadNet: class {} } },
    setTimeout(callback) { timers.set(++timerId, callback); return timerId },
    clearTimeout(id) { timers.delete(id) },
  }
  const map = {
    zoom: 4, center: { lng: 105, lat: 35 },
    getZoom() { return this.zoom }, getCenter() { return this.center },
    on(names, callback) { for (const name of names.split(' ')) listeners.set(name, callback) },
    off(names, callback) { for (const name of names.split(' ')) if (listeners.get(name) === callback) listeners.delete(name) },
  }
  const host = { clientWidth: width, clientHeight: 600 }
  const control = createAmapBasemap(map, host, 'test-key', state => states.push(state))
  return { map, host, control, providers, states, timers, listeners }
}

test('official basemap follows scientific zoom and center without resetting scientific state', async () => {
  const env = environment()
  env.control.switchTo('vector')
  await Promise.resolve()
  const provider = env.providers[0]
  provider.events.complete()
  env.map.zoom = 8
  env.map.center = { lng: 116.397, lat: 39.908 }
  env.listeners.get('zoom')()
  assert.equal(provider.zoom, 8)
  assert.deepEqual(provider.center, toGcj02([116.397, 39.908]))
  env.control.switchTo('satellite')
  assert.equal(provider.layers.length, 2)
  env.control.switchTo('satellite')
  assert.equal(provider.layers.length, 2, 'repeated selection must not duplicate provider layers')
  env.control.switchTo('vector')
  assert.equal(provider.layers.length, 0)
  assert.deepEqual(env.map.center, { lng: 116.397, lat: 39.908 })
  assert.equal(env.map.zoom, 8)
  env.control.destroy()
  assert.ok(provider.destroyed)
  assert.equal(env.timers.size, 0)
  assert.equal(env.listeners.size, 0)
})

test('hidden homepage defers SDK map creation until the explorer has a viewport', async () => {
  const env = environment(0)
  env.control.switchTo('vector')
  await Promise.resolve()
  assert.equal(env.providers.length, 0)
  env.host.clientWidth = 900
  env.listeners.get('resize')()
  assert.equal(env.providers.length, 1)
  env.control.destroy()
  const count = env.states.length
  env.providers[0].events.complete()
  assert.equal(env.states.length, count, 'disposed maps must not report late completion')
})
