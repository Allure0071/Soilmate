import test from 'node:test'
import assert from 'node:assert/strict'
import { classifyTexture, textureClasses, texturePoint } from './texture.js'
import { auditTable, defaultRules, parseDelimited, prepareTable, toCsv } from './tables.js'
import { getTool, filterTools, tools } from '../catalog.js'
const classify=(sand,silt,clay,normalize=false)=>classifyTexture({sand,silt,clay},normalize)

test('all twelve USDA classes, pure vertices and shared boundaries classify consistently',()=>{
  const cases=[[95,3,2,'S'],[82,12,6,'LS'],[65,25,10,'SL'],[40,40,20,'L'],[20,65,15,'SIL'],[5,90,5,'SI'],[60,15,25,'SCL'],[35,30,35,'CL'],[10,55,35,'SICL'],[55,5,40,'SC'],[10,45,45,'SIC'],[25,20,55,'C'],[100,0,0,'S'],[0,100,0,'SI'],[0,0,100,'C'],[85,15,0,'LS'],[70,30,0,'SL'],[52,41,7,'L'],[20,40,40,'SIC'],[45,15,40,'C']]
  for(const [sand,silt,clay,id] of cases) assert.equal(classify(sand,silt,clay).id,id,`${sand}/${silt}/${clay}`)
  const found=new Set()
  for(let sand=0;sand<=100;sand++)for(let clay=0;clay<=100-sand;clay++)found.add(classify(sand,100-sand-clay,clay).id)
  assert.equal(found.size,12)
})
test('texture diagram regions cover the simplex and agree with classifications away from borders',()=>{
  const inside=(p,vertices)=>{
    const a=vertices.map(texturePoint)
    let result=false
    for(let i=0,j=a.length-1;i<a.length;j=i++){
      const v=a[j],w=a[i],cross=(w.x-v.x)*(p.y-v.y)-(w.y-v.y)*(p.x-v.x)
      if(Math.abs(cross)<1e-6 && p.x>=Math.min(v.x,w.x)-1e-6 && p.x<=Math.max(v.x,w.x)+1e-6 && p.y>=Math.min(v.y,w.y)-1e-6 && p.y<=Math.max(v.y,w.y)+1e-6)return true
      if((v.y>p.y)!==(w.y>p.y) && p.x<(w.x-v.x)*(p.y-v.y)/(w.y-v.y)+v.x)result=!result
    }
    return result
  }
  for(let sand=0;sand<=100;sand+=2)for(let clay=0;clay<=100-sand;clay+=2){const silt=100-sand-clay,r=classify(sand,silt,clay);assert.ok(inside(texturePoint([sand,silt,clay]),textureClasses.find(c=>c.id===r.id).vertices),`${sand}/${silt}/${clay}: ${r.id}`)}
})
test('texture rejects malformed values and never silently normalizes an incomplete sum',()=>{
  for(const value of ['',-1,101,'1e2','NaN','4%'])assert.throws(()=>classify(value,40,20))
  assert.throws(()=>classify(30,30,30),/100/)
  assert.throws(()=>classify(0,0,0,true))
  const r=classify(30,30,30,true)
  assert.equal(r.normalized,true);assert.deepEqual(r.raw,[30,30,30]);assert.ok(Math.abs(r.sand-100/3)<1e-10)
})
test('CSV and TSV preserve quoted commas, newlines, zero and source line numbers',()=>{
  const table=parseDelimited('\uFEFFid,value,note\r\nA,0,"hello,\nworld"\r\nB,,"a""b"\r\n')
  assert.deepEqual(table.rows,[['A','0','hello,\nworld'],['B','','a"b']])
  assert.deepEqual(parseDelimited('id\tvalue\nA\t1').rows,[['A','1']])
  assert.deepEqual(parseDelimited('"header\tinside",value\nA,1').headers,['header\tinside','value'])
  const out=auditTable(table,defaultRules(table),0)
  assert.equal(out.issues.find(i=>i.type==='缺失值').row,3)
  assert.equal(out.profiles[1].min,0)
  assert.throws(()=>parseDelimited('a,a\n1,2'),/重复列名/)
  assert.throws(()=>parseDelimited('a,b\n"x,1'),/引号/)
  assert.throws(()=>parseDelimited('a,b\n1,2,3'),/列数/)
})
test('audit preserves originals, marks duplicates and excludes mixed units from statistics and ranges',()=>{
  const table=parseDelimited('sample_id,SOC(g/kg)\nA,1\nA,200 mg/kg\nB,3\nB,3')
  const before=JSON.stringify(table),rules=defaultRules(table);rules[1].max='10'
  const out=auditTable(table,rules,0)
  assert.equal(JSON.stringify(table),before)
  assert.equal(out.issues.filter(i=>i.type==='重复编号').length,4)
  assert.ok(out.issues.some(i=>i.type==='重复行'))
  assert.ok(out.issues.some(i=>i.type==='单位不一致'))
  assert.equal(out.profiles[1].mixed,true);assert.equal(out.profiles[1].max,null)
  assert.ok(!out.issues.some(i=>['疑似离群值','范围核对'].includes(i.type)))
  const prefixes=parseDelimited('value\n1 mg/L\n1 Mg/L')
  assert.equal(auditTable(prefixes,defaultRules(prefixes)).profiles[0].mixed,true,'SI prefixes must retain case')
})
test('audit detects nonnumeric cells, manual limits and IQR outliers without deleting data',()=>{
  const table=parseDelimited('sample_id,value\nA,1\nB,2\nC,3\nD,4\nE,100\nF,bad\nG,NA'),rules=defaultRules(table)
  rules[1].min='0';rules[1].max='50'
  const r=auditTable(table,rules,0)
  assert.ok(r.issues.some(i=>i.row===6&&i.type==='疑似离群值'))
  assert.ok(r.issues.some(i=>i.row===7&&i.severity==='error'))
  assert.ok(r.issues.some(i=>i.row===6&&i.type==='范围核对'))
  rules[1].min='80';assert.throws(()=>auditTable(table,rules,0),/范围设置/)
  assert.throws(()=>prepareTable([['a'],...Array.from({length:5001},()=>['x'])]),/最多/)
})
test('exports escape CSV cells and neutralize formula prefixes; tools are ready and searchable',()=>{
  assert.match(toCsv([['=SUM(A1)','hello,"world"']]),/"'=SUM\(A1\)"/)
  assert.match(toCsv([['x"y']]),/"x""y"/)
  for(const id of ['texture','data-audit'])assert.equal(getTool(id).status,'ready')
  assert.equal(filterTools('xlsx')[0].id,'data-audit')
  assert.equal(new Set(tools.map(t=>t.id)).size,tools.length)
})
