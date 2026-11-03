import test from 'node:test'
import assert from 'node:assert/strict'
import { calculate, calculators } from './calculators.js'
import { filterTools, toolTarget, tools } from './catalog.js'
const values = result => result.items.map(item => item.value)
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`)

test('known physical and carbon reference cases give dimensionally consistent results', () => {
  const d = values(calculate('density', { mass: '130', volume: '100', particle: '2.65' }))
  near(d[0], 1.3); near(d[1], 50.9433962264151)
  near(values(calculate('carbon', { carbon: '15', density: '1.3', depth: '20', fragments: '10' }))[0], 35.1)
  near(values(calculate('carbon', { carbon: '15', density: '1.3', depth: '20', fragments: '10' }))[1], 3.51)
})
test('moisture conversions round-trip between dry, wet and volume bases', () => {
  for (const [basis, water] of [['dry', '20'], ['wet', String(100 / 6)], ['volume', '26']]) {
    const v = values(calculate('moisture', { basis, water, density: '1.3' }))
    near(v[0], 20); near(v[1], 100 / 6); near(v[2], 26)
  }
})
test('unit conversions preserve mass, density, conductivity and area dimensions', () => {
  for (const [quantity, from, to, value, expected] of [['mass', '%', 'mg/kg', '1', 10000], ['ec', 'μS/cm', 'dS/m', '1000', 1], ['density', 'kg/m³', 'g/cm³', '1300', 1.3], ['area', 'ha', '亩', '1', 15]]) {
    near(values(calculate('units', { quantity, from, to, value }))[0], expected)
  }
  assert.throws(() => calculate('units', { quantity: 'mass', from: 'mg/L', to: 'g/kg', value: '1' }))
  assert.throws(() => calculate('units', { quantity: '__proto__', from: 'x', to: 'y', value: '1' }), /有效单位/)
})
test('dilution uses the final volume and refuses concentration by dilution', () => {
  assert.deepEqual(values(calculate('dilution', { unit: 'mg/L', stock: '1000', target: '10', volume: '100' })), [1, 100, 100])
  assert.throws(() => calculate('dilution', { unit: 'mg/L', stock: '1', target: '10', volume: '100' }))
})
test('linear calibration fits slope/intercept, inverse prediction, and dilution separately', () => {
  const r = values(calculate('curve', calculators.curve.example))
  for (const [i, expected] of [0.1, 0.02, 1, 1.5, 7.5].entries()) near(r[i], expected)
  assert.throws(() => calculate('curve', { ...calculators.curve.example, response: '4' }), /范围/)
  assert.throws(() => calculate('curve', { ...calculators.curve.example, pairs: '1,2\n1,3\n1,4' }), /不能全部相同/)
  assert.throws(() => calculate('curve', { ...calculators.curve.example, pairs: '0,1\n1,1\n2,1' }), /斜率/)
  assert.equal(calculate('curve', { pairs: '0,0\n1,2\n2,4', response: '', factor: '' }).items.length, 3)
})
test('statistics use sample SD and do not report CV for nonpositive observations', () => {
  const r = calculate('statistics', { values: '10,12;14\n16 18' })
  near(r.items.find(item => item.label === '均值').value, 14)
  near(r.items.find(item => item.label === '样本标准差').value, Math.sqrt(10))
  assert.ok(!calculate('statistics', { values: '-1,0,1' }).items.some(item => item.label.includes('CV')))
})
test('blank, nonfinite, impossible and overflowing inputs are never interpreted as valid zero', () => {
  for (const mass of ['', ' ', 'Infinity', 'NaN', '1.2abc', '1e999', '-1']) assert.throws(() => calculate('density', { mass, volume: '100', particle: '2.65' }))
  assert.throws(() => calculate('density', { mass: '300', volume: '100', particle: '2.65' }))
  assert.throws(() => calculate('moisture', { basis: 'wet', water: '100', density: '1' }))
  assert.throws(() => calculate('moisture', { basis: 'dry', water: '90', density: '1.5' }))
  assert.throws(() => calculate('statistics', { values: '1e308,1e308' }))
  assert.equal(values(calculate('units', { quantity: 'mass', from: 'g/kg', to: 'mg/kg', value: '0' }))[0], 0)
})
test('tool routing, filters and unpublished tools remain truthful', () => {
  assert.equal(new Set(tools.map(tool => tool.id)).size, tools.length)
  assert.equal(filterTools('SOC')[0].id, 'carbon')
  assert.ok(filterTools('', 'common', '物理').every(tool => tool.category === 'common' && tool.domain === '物理'))
  assert.equal(toolTarget('pollution'), null)
  assert.equal(toolTarget('unknown'), null)
  const url = new URL(toolTarget('deep-assessment'), 'https://soilmate.local')
  assert.equal(url.pathname, '/research'); assert.equal(url.searchParams.get('mode'), 'deep'); assert.equal(url.searchParams.get('from'), 'tools')
  assert.match(toolTarget('database-browser'), /tab=database/)
  const scoped = new URL(toolTarget('database-browser', '/tools?category=database&q=原始'), 'https://soilmate.local')
  const returnUrl = new URL(scoped.searchParams.get('returnTo'), 'https://soilmate.local')
  assert.equal(returnUrl.pathname, '/tools')
  assert.equal(returnUrl.searchParams.get('q'), '原始')
  assert.equal(returnUrl.searchParams.get('category'), 'database')
  assert.equal(new URL(toolTarget('database-browser', 'https://evil.test/tools?q=x'), 'https://soilmate.local').searchParams.get('returnTo'), null)
})
