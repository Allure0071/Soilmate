import test from 'node:test'
import assert from 'node:assert/strict'
import { buildImport, discardPendingImport, inspectImport, readPendingImport, restoreImportSource, stageImport, suggestMapping } from './measurementImport.js'
import { parseDelimited } from '../tools/research/tables.js'
import { inspectRows, restoreRows } from './measurementDraft.js'
const table = () => parseDelimited('sample_id,pH,SOC(g/kg),备注\nS01,0,12.500,表层\nS01,6.8,NA,复测\nS03,错误,900 mg/kg,待核对')
function memoryStore() { const values = new Map(); return { getItem: key => values.get(key) ?? null, setItem: (key,value) => values.set(key,value), removeItem: key => values.delete(key), values } }
const payload = () => { const data=table();return buildImport(data,suggestMapping(data.headers),0,0,{fileName:'检测.xlsx',sheetName:'工作表一'}) }

test('suggest exact indicator names only; preserve unit case and leave uncertain units for confirmation', () => {
  const mapping=suggestMapping(['sample_id','pH','全氮(%)','SOC(g/kg)','EC','SOC(Mg/kg)','砂粒含量(%)','总磷','pH备注'])
  assert.deepEqual(mapping.map(item=>item.code),['','soil_ph','TN','SOC','EC','SOC','Sand','',''])
  assert.equal(mapping[2].unit,'%');assert.equal(mapping[4].unit,'');assert.equal(mapping[5].unit,'')
})
test('selected row stays independent with duplicate IDs; keep zero, numeric text, raw source and sheet', () => {
  const data=table(), before=JSON.stringify(data), mapping=suggestMapping(data.headers)
  const first=buildImport(data,mapping,0,0,{fileName:'检测.xlsx',sheetName:'表层'})
  assert.equal(first.rows[0].value,'0');assert.equal(first.rows[1].value,'12.500')
  assert.equal(first.source.table_row,2);assert.equal(first.source.sheet_name,'表层')
  assert.equal(first.source.original[3].value,'表层');assert.equal(first.source.fields[1].raw_value,'12.500')
  const second=buildImport(data,mapping,1,0,{})
  assert.equal(second.source.sample_id,first.source.sample_id);assert.equal(second.source.table_row,3)
  assert.equal(second.rows.length,1);assert.equal(second.rows[0].value,'6.8')
  assert.equal(JSON.stringify(data),before);assert.equal(inspectRows(first.rows).valid,true)
  assert.equal(restoreRows(first.rows)[1].value,'12.500')
})
test('block conflicting cell/header units and duplicate mappings; never convert or silently drop invalid filled values', () => {
  const data=table(), mapping=suggestMapping(data.headers), invalid=inspectImport(data,mapping,2,0)
  assert.ok(invalid.errors.length>=2);assert.match(invalid.errors.join(' '),/无法作为检测数值/);assert.match(invalid.errors.join(' '),/不会自动换算/)
  mapping[3]={code:'SOC',unit:'g/kg'}
  assert.match(inspectImport(data,mapping,0).errors.join(' '),/映射了多列/)
  const units=parseDelimited('EC,SOC(Mg/kg)\n20,2'), rules=suggestMapping(units.headers)
  assert.match(inspectImport(units,rules,0).errors.join(' '),/请选择报告单位/)
  rules[0].unit='μS/cm';rules[1].unit='g/kg'
  assert.match(inspectImport(units,rules,0).errors.join(' '),/单位.*不一致/)
  rules[1].code='';assert.equal(inspectImport(units,rules,0).errors.length,0)
})
test('skip unmapped and missing fields only, reject empty selections and built-in synthetic data transfer', () => {
  const data=table(), mapping=suggestMapping(data.headers)
  assert.match(inspectImport(data,mapping,-1).errors[0],/请选择/)
  assert.match(inspectImport(data,mapping.map(()=>({code:'',unit:''})),0).errors[0],/没有可带入/)
  assert.throws(()=>buildImport(data,mapping,0,0,{demo:true}),/合成问题示例/)
  assert.equal(restoreImportSource({}),null)
  const source=payload().source;assert.deepEqual(restoreImportSource(source),source)
})
test('tab handoff survives reads/login, expires, rejects wrong tokens, and removes only the confirmed token', () => {
  const store=memoryStore(), incoming=payload(), token=stageImport(incoming,store,1000)
  assert.equal(readPendingImport(token,store,2000).rows[1].value,'12.500')
  assert.equal(readPendingImport(token,store,3000).source.file_name,'检测.xlsx')
  assert.throws(()=>readPendingImport('unknown',store,3000),/失效/)
  assert.throws(()=>readPendingImport(token,store,1000+30*60*1000),/失效/)
  discardPendingImport('unknown',store);assert.equal(readPendingImport(token,store,4000).source.table_row,2)
  discardPendingImport(token,store);assert.throws(()=>readPendingImport(token,store,4000),/失效/)
  assert.equal(readPendingImport('',store),null)
})
test('storage failures are actionable; restored source keeps only known fields', () => {
  assert.throws(()=>stageImport({...payload(),rows:[null]},memoryStore()),/无效/)
  assert.throws(()=>stageImport({...payload(),rows:[{value:'6.5'}]},memoryStore()),/无效/)
  assert.throws(()=>stageImport(payload(),{setItem(){throw new Error('quota')}}),/无法暂存/)
  assert.throws(()=>readPendingImport('token',{getItem(){throw new Error('blocked')}}),/无法读取/)
  const source={...payload().source,injected:true}
  assert.equal('injected' in restoreImportSource(source),false)
  assert.equal(restoreImportSource({...source,original:[null]}),null)
})
