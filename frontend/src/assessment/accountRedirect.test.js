import test from 'node:test'
import assert from 'node:assert/strict'
import { accountDestination } from '../../public/account/redirect.js'

test('login preserves new workspace routes, stages and assessment steps', () => {
  for (const path of ['/assistant', '/research?stage=evidence', '/assessment?mode=deep&step=input', '/analysis', '/evidence', '/explore', '/resources']) {
    assert.equal(accountDestination(path), path)
  }
})

test('login rejects external, malformed and unknown return destinations', () => {
  for (const path of [null, '', 'https://evil.test/research', '//evil.test/research', '/\\evil.test/research', '/unknown', '/account/index.html', '/research/../unknown']) {
    assert.equal(accountDestination(path), '/research')
  }
})
