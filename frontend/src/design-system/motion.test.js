import test from 'node:test'
import assert from 'node:assert/strict'
import { attachScrollResponse, revealOnScroll, transitionPage } from './motion.js'

function environment(reduced = false) {
  const media = Object.assign(new EventTarget(), { matches: reduced })
  const document = Object.assign(new EventTarget(), { hidden: false })
  let now = 0, nextFrame = 0
  const frames = new Map()
  globalThis.window = { matchMedia: () => media }
  globalThis.document = document
  globalThis.requestAnimationFrame = callback => { frames.set(++nextFrame, callback); return nextFrame }
  globalThis.cancelAnimationFrame = id => frames.delete(id)
  Object.defineProperty(globalThis, 'performance', { configurable: true, value: { now: () => now } })
  const values = []
  const properties = new Map()
  const style = {
    setProperty(name, value) { properties.set(name, value); values.push(parseFloat(value)) },
    removeProperty(name) { properties.delete(name) },
  }
  const advance = () => {
    now += 16
    const callbacks = [...frames.values()]
    frames.clear()
    callbacks.forEach(callback => callback(now))
  }
  return { media, document, frames, values, properties, style, advance }
}

test('native scroll remains untouched and visual drift settles without a running RAF', () => {
  const env = environment()
  const scroller = Object.assign(new EventTarget(), { scrollTop: 0 })
  const stop = attachScrollResponse(scroller, { style: env.style })
  for (let i = 0; i < 50; i++) {
    scroller.scrollTop += 30
    const event = new Event('scroll', { cancelable: true })
    scroller.dispatchEvent(event)
    assert.equal(event.defaultPrevented, false)
    env.advance()
  }
  assert.equal(scroller.scrollTop, 1500)
  assert.ok(env.values.some(value => Math.abs(value) > 2), 'response must be visible')
  assert.ok(env.values.every(value => Math.abs(value) < 10), 'response must stay restrained')
  for (let i = 0; i < 250; i++) env.advance()
  assert.equal(env.frames.size, 0)
  assert.equal(env.properties.has('--scroll-drift'), false)
  stop()
  scroller.dispatchEvent(new Event('scroll'))
  assert.equal(env.frames.size, 0)
})

test('reduced motion and backgrounding clear the visual response', () => {
  const env = environment()
  const scroller = Object.assign(new EventTarget(), { scrollTop: 0 })
  const stop = attachScrollResponse(scroller, { style: env.style })
  scroller.scrollTop = 100
  scroller.dispatchEvent(new Event('scroll'))
  env.advance()
  env.media.matches = true
  env.media.dispatchEvent(new Event('change'))
  assert.equal(env.frames.size, 0)
  assert.equal(env.properties.size, 0)
  scroller.dispatchEvent(new Event('scroll'))
  assert.equal(env.frames.size, 0)
  env.media.matches = false
  scroller.scrollTop = 300
  scroller.dispatchEvent(new Event('scroll'))
  env.document.hidden = true
  env.document.dispatchEvent(new Event('visibilitychange'))
  assert.equal(env.frames.size, 0)
  assert.equal(env.properties.size, 0)
  stop()
})

test('changing reduced motion reveals pending content without animation', () => {
  const env = environment()
  let disconnected = false
  globalThis.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() { disconnected = true }
  }
  const element = { style: {}, dataset: {}, animate() { assert.fail('pending content must not animate') } }
  const stop = revealOnScroll({ querySelectorAll: () => [element] })
  assert.equal(element.style.opacity, '0')
  env.media.matches = true
  env.media.dispatchEvent(new Event('change'))
  assert.equal(element.style.opacity, '')
  assert.equal(disconnected, true)
  stop()
})


test('page updates immediately without animation support or with reduced motion', async () => {
  const env = environment()
  const calls = []
  await transitionPage(() => calls.push('update'), () => calls.push('render'))
  assert.deepEqual(calls, ['update', 'render'])
  env.document.startViewTransition = () => assert.fail('reduced motion must skip snapshots')
  env.media.matches = true
  await transitionPage(() => calls.push('reduced'))
  assert.equal(calls.at(-1), 'reduced')
})

test('rapid navigation skips old snapshots and only the newest destination commits', async () => {
  const env = environment()
  const transitions = [], calls = []
  env.document.startViewTransition = update => {
    let resolveFinished
    const transition = {
      update,
      ready: Promise.resolve(),
      finished: new Promise(resolve => { resolveFinished = resolve }),
      updateCallbackDone: Promise.resolve(),
      skipped: 0,
      skipTransition() { this.skipped++ },
      finish() { resolveFinished() },
    }
    transitions.push(transition)
    return transition
  }
  transitionPage(() => calls.push('old'))
  transitionPage(() => calls.push('new'), async () => calls.push('rendered'))
  assert.equal(transitions[0].skipped, 1)
  await transitions[0].update()
  await transitions[1].update()
  assert.deepEqual(calls, ['new', 'rendered'])
  transitions[0].finish()
  await Promise.resolve()
  env.media.matches = true
  env.media.dispatchEvent(new Event('change'))
  assert.equal(transitions[1].skipped, 1, 'a preference change must finish the current visual transition')
  transitions[1].finish()
  await Promise.resolve()
  env.media.dispatchEvent(new Event('change'))
  assert.equal(transitions[1].skipped, 1, 'completed transitions must release their listener')
})
