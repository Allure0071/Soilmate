import test from 'node:test'
import assert from 'node:assert/strict'
import { authErrorMessage } from '../../public/account/errors.js'

test('password validation failures explain input requirements instead of reporting an outage', () => {
  assert.match(authErrorMessage(422, { detail: [{ loc: ['body', 'password'], type: 'string_too_short' }] }), /12～128/)
  assert.match(authErrorMessage(422, { detail: [{ loc: ['body', 'email'] }] }), /邮箱/)
  assert.match(authErrorMessage(422, {}), /格式/)
})
test('authentication failures retain server explanations and service errors have a fallback', () => {
  assert.equal(authErrorMessage(401, { detail: '邮箱或密码不正确' }), '邮箱或密码不正确')
  assert.match(authErrorMessage(500, {}), /暂时不可用/)
})
