import test from 'node:test';
import assert from 'node:assert/strict';
import { createRow, inspectRows, restoreRows } from './measurementDraft.js';

test('one valid indicator suffices; zero is a value and blank extra rows are optional', () => {
  const row = { ...createRow(), value: '0' };
  const check = inspectRows([row, createRow('TN')]);
  assert.equal(check.valid, true);
  assert.equal(check.values.length, 1);
  assert.equal(check.values[0].value, 0);
  assert.equal(check.emptyCount, 1);
  assert.equal(inspectRows([]).valid, false);
});

test('reject malformed numbers, overflow, duplicate filled indicators and unsupported units', () => {
  for (const value of ['abc', '0x10', 'Infinity', '1e999', '6.2 pH', '1,200']) {
    assert.equal(inspectRows([{ ...createRow(), value }]).valid, false, value);
  }
  assert.equal(inspectRows([{ ...createRow(), value: '6.2' }, { ...createRow(), value: '7' }]).valid, false);
  assert.equal(inspectRows([{ ...createRow('TN'), value: '1.2', unit: 'mg/L' }]).valid, false);
  assert.equal(inspectRows([{ ...createRow('TN'), value: '1.2e-3' }]).valid, true);
});

test('restored browser drafts receive fresh row identities and cannot inject unknown fields', () => {
  const restored = restoreRows([{ id: 'untrusted', indicator_code: 'soil_ph', value: '6.2', unit: '', method: '报告方法', injected: true }, { indicator_code: 'unknown', value: '4' }]);
  assert.equal(restored.length, 1);
  assert.notEqual(restored[0].id, 'untrusted');
  assert.equal(restored[0].value, '6.2');
  assert.equal('injected' in restored[0], false);
});
