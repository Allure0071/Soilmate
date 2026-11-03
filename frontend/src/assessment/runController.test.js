import test from 'node:test'
import assert from 'node:assert/strict'
import { createRunController } from './runController.js'
import { AssessmentError, createAssessmentApi } from './runClient.js'
import { demoRequest, demoSnapshot } from './runDemo.js'
function memory(){const data=new Map();return{getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)}}
function setup(request=demoRequest(),storage=memory()){
 const scheduled=new Map();let i=0
 const controller=createRunController({request,storage,storageKey:'test',schedule:fn=>{scheduled.set(++i,fn);return i},unschedule:key=>scheduled.delete(key)})
 return{controller,scheduled,storage,async tick(){const [key,fn]=scheduled.entries().next().value || [];if(fn){scheduled.delete(key);await fn()}}}
}
test('queued/running/completed use server states and stop polling without inventing a score',async()=>{
 const env=setup();await env.controller.start(demoSnapshot)
 assert.equal(env.controller.state.task.status,'queued');assert.equal(env.scheduled.size,1)
 await env.tick();assert.equal(env.controller.state.task.status,'running')
 await env.tick();assert.equal(env.controller.state.task.status,'completed');assert.equal(env.scheduled.size,0)
 assert.equal(env.controller.state.task.result.analysis.assessment.composite_score,null)
})
test('partial is terminal and failed retry creates a new task key while reusing original measurements',async()=>{
 const partial=setup(demoRequest('partial'));await partial.controller.start(demoSnapshot);await partial.tick();await partial.tick()
 assert.equal(partial.controller.state.task.status,'partial');assert.equal(partial.scheduled.size,0)
 const calls=[],transport=demoRequest('failed'),env=setup(async(...args)=>{calls.push(args);return transport(...args)})
 await env.controller.start(demoSnapshot);await env.tick();await env.tick();assert.equal(env.controller.state.task.status,'failed')
 await env.controller.retry();await env.tick();await env.tick()
 assert.equal(env.controller.state.task.status,'completed')
 assert.equal(calls.filter(([method,path])=>method==='POST'&&path==='/measurements').length,1)
 const tasks=calls.filter(([method,path])=>method==='POST'&&path==='/tasks');assert.equal(tasks.length,2);assert.notEqual(tasks[0][3],tasks[1][3]);assert.deepEqual(tasks[0][2].measurement_ids,tasks[1][2].measurement_ids)
})
test('uncertain POST retries reuse keys across refresh instead of creating a second measurement',async()=>{
 const storage=memory(),calls=[],base=demoRequest(),request=async(...args)=>{calls.push(args);if(args[1]==='/measurements')throw new AssessmentError('network',{retryable:true});return base(...args)}
 const env=setup(request,storage);await env.controller.start(demoSnapshot);assert.equal(env.controller.state.phase,'error')
 const reloaded=setup(request,storage);reloaded.controller.load();await reloaded.controller.resume()
 const writes=calls.filter(([method,path])=>method==='POST'&&path==='/measurements')
 assert.equal(writes.length,2);assert.equal(writes[0][3],writes[1][3]);assert.deepEqual(writes[0][2],writes[1][2])
 assert.equal(calls.filter(([method,path])=>method==='POST'&&path==='/sessions').length,1)
})
test('refresh with a task ID only reads existing task; pause removes the polling timer',async()=>{
 const storage=memory(),base=demoRequest(),calls=[],request=async(...args)=>{calls.push(args);return base(...args)}
 const env=setup(request,storage);await env.controller.start(demoSnapshot);env.controller.pause();assert.equal(env.scheduled.size,0)
 const reload=setup(request,storage);reload.controller.load();const count=calls.length;await reload.controller.resume()
 assert.equal(calls[count][0],'GET');assert.ok(calls.slice(count).every(([method])=>method==='GET'))
 reload.controller.dispose();assert.equal(reload.scheduled.size,0)
})
test('late responses after disposal cannot update another page or schedule polling',async()=>{
 let resolve;const env=setup(()=>new Promise(r=>{resolve=r}));const pending=env.controller.start(demoSnapshot);env.controller.dispose()
 resolve({data:{items:[{code:'soil_ph',units:[],unit_required:false}]},origin:'real'});await pending
 assert.equal(env.controller.state.sessionId,'');assert.equal(env.scheduled.size,0)
})
test('mismatched task identity and false completed payloads are rejected',async()=>{
 for(const bad of [{task_id:'other',session_id:'mock-session',status:'completed'}, {task_id:'mock-task-quick',session_id:'mock-session',type:'quick_analysis',status:'completed',result:null}]){
 const base=demoRequest(),env=setup((...args)=>args[1].startsWith('/tasks/')?Promise.resolve({data:bad,origin:'real'}):base(...args))
 await env.controller.start(demoSnapshot);assert.equal(env.controller.state.phase,'error');assert.equal(env.controller.state.error.retryable,false);assert.equal(env.scheduled.size,0)
 }
})
test('deep mode without service-side field/cycle does not submit fabricated IDs',async()=>{
 const calls=[],env=setup(async(...args)=>{calls.push(args);return demoRequest()(...args)})
 await env.controller.start({...demoSnapshot,session:{mode:'deep'}})
 assert.equal(calls.length,0);assert.match(env.controller.state.error.message,/地块和种植周期/)
})
test('transport handles unavailable/auth/validation states and rejects unmarked or unexpected mock success',async()=>{
 for(const status of [401,403,404,422,503]){
 const request=createAssessmentApi({fetcher:async()=>({ok:false,status,json:async()=>({error:{code:'MODEL_UNAVAILABLE',fields:[{path:'/values/0/unit',message:'单位错误'}]},request_id:'req-test'})})})
 await assert.rejects(()=>request('GET','/tasks/test'),error=>error.status===status&&error.requestId==='req-test'&&error.fields.length===1)
 }
 for(const data_origin of [undefined,'mock']){
 const request=createAssessmentApi({fetcher:async()=>({ok:true,json:async()=>({data:{task_id:'x'},data_origin})})})
 await assert.rejects(()=>request('GET','/tasks/test'),/格式.*不一致/)
 }
 let options
 const request=createAssessmentApi({csrf:()=> 'csrf-test',fetcher:async(url,init)=>{options=init;return{ok:true,json:async()=>({data:{id:'test'},data_origin:'real',request_id:'req'})}}})
 await request('POST','/sessions',{mode:'quick'},'same-key')
 assert.equal(options.headers['Idempotency-Key'],'same-key');assert.equal(options.headers['X-CSRF-Token'],'csrf-test');assert.equal(options.credentials,'same-origin')
})
test('session restoration fetches server inputs and task, and rejects malformed analysis arrays',async()=>{
 const calls=[],base=demoRequest(),request=async(method,path,...rest)=>{
 calls.push([method,path])
 if(path.startsWith('/sessions/'))return{data:{id:'mock-session',mode:'quick',measurement_ids:['mock-measurement-1'],latest_task_id:'mock-task-quick-1'},origin:'real'}
 if(path.startsWith('/measurements/'))return{data:{id:'mock-measurement-1',session_id:'mock-session',values:demoSnapshot.measurement.values},origin:'real'}
 return base(method,path,...rest)
 }
 const env=setup(request);await env.controller.restore('mock-session','mock-task-quick-1')
 assert.deepEqual(calls.slice(0,3),[['GET','/sessions/mock-session'],['GET','/measurements/mock-measurement-1'],['GET','/tasks/mock-task-quick-1']])
 assert.equal(env.controller.state.measurement.values[0].value,6.2)
 const transport=demoRequest(),invalid=setup(async(...args)=>{const response=await transport(...args);if(response.data.result?.analysis)response.data.result.analysis.gaps='invalid';return response})
 await invalid.controller.start(demoSnapshot);await invalid.tick();await invalid.tick()
 assert.equal(invalid.controller.state.phase,'error');assert.equal(invalid.scheduled.size,0)
})
test('corrupted pending submissions are not replayed',async()=>{
 const store=memory();store.setItem('test',JSON.stringify({keys:{},sessionId:'',taskId:'',snapshot:{bad:'shape'}}))
 const env=setup(demoRequest(),store);env.controller.load()
 assert.equal(env.controller.state.phase,'idle');assert.equal(env.controller.state.snapshot,null)
})
