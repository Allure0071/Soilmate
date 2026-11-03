import test from 'node:test'
import assert from 'node:assert/strict'
import { primaryLinks, siteLinks, viewFromPath } from './siteNavigation.js'

test('every navigation destination can be opened directly and restored by browser history', () => {
  for (const link of siteLinks) assert.equal(viewFromPath(link.href), link.id)
  assert.equal(new Set(siteLinks.map(link => link.href)).size, siteLinks.length)
})

test('legacy assessment and research URLs still activate health research', () => {
  for (const path of ['/analysis', '/evidence', '/assessment', '/assessment/preview']) assert.equal(viewFromPath(path), 'research')
  assert.equal(viewFromPath('/unknown'), 'home')
})

test('five functions have separate primary entries and independent active states', () => {
  assert.equal(primaryLinks.length, 5)
  for (const view of ['explore', 'gold', 'research', 'assistant', 'tools']) {
    const link = primaryLinks.find(link => link.id === view)
    assert.deepEqual(link.views, [view])
    assert.equal(viewFromPath(link.href), view)
  }
})
