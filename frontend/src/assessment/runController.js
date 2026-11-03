import { validAnalysis } from './runValidation.js'
import { AssessmentError } from './runClient.js'
const terminal = new Set(['completed', 'partial', 'failed', 'interrupted'])
const id = value => typeof value === 'string' && value.length > 0
const clone = value => JSON.parse(JSON.stringify(value))
const newKey = () => globalThis.crypto?.randomUUID?.() || `request-${Date.now()}-${Math.random()}`
export function createRunController({ request, storage, storageKey, onChange = () => {}, pollMs = 2000, schedule = setTimeout, unschedule = clearTimeout }) {
  let state = { phase: 'idle', sessionId: '', measurementId: '', taskId: '', task: null, measurement: null, session: null, snapshot: null, inputError: '', keys: {}, error: null, origin: 'real', requestId: '', stage: '', storageFailed: false }
  let timer, controller, generation = 0
  function publish() {
    try { storage?.setItem(storageKey, JSON.stringify({ ...state, task: null, measurement: null, error: null })) } catch { state.storageFailed = true }
    onChange({ ...state })
  }
  function stop() { generation++; unschedule(timer); timer = null; controller?.abort() }
  function errorState(error) { state.phase = 'error'; state.error = { message: error.message, status: error.status, code: error.code, requestId: error.requestId, fields: error.fields || [], retryable: error.retryable ?? true }; publish() }
  function accept(envelope) { state.origin = envelope.origin; state.requestId = envelope.requestId }
  async function submit() {
    stop(); const version = generation; controller = new AbortController(); state.phase = 'submitting'; state.error = null; publish()
    const call = async (method, path, body, key) => {
      const result = await request(method, path, body, key, controller.signal)
      if (generation !== version) throw new DOMException('Stopped', 'AbortError')
      accept(result); return result.data
    }
    try {
      const input = state.snapshot
      if ((!state.sessionId || !state.measurementId) && !input) throw new AssessmentError('缺少原提交内容，请返回录入页重新确认。', { retryable: false })
      if (input?.session.mode === 'deep' && (!input.session.field_id || !input.session.cycle_id)) throw new AssessmentError('深度分析需要服务端地块和种植周期，请先完成地块对接，或返回选择快速试用。', { retryable: false })
      if (!state.sessionId) {
        state.stage = '核对指标字典'; publish()
        const dictionary = await call('GET', '/indicators')
        for (const value of input.measurement.values) {
          const entry = dictionary.items?.find(item => item.code === value.indicator_code)
          if (!entry || (value.unit && !entry.units.includes(value.unit)) || (!value.unit && entry.unit_required)) throw new AssessmentError('录入指标或单位与服务端字典不一致，请返回录入页核对：' + value.indicator_code, { status: 422, retryable: false })
        }
      }
      if (!state.sessionId) {
        state.stage = '保存研究会话'; publish()
        const session = await call('POST', '/sessions', input.session, state.keys.session)
        if (!id(session.id)) throw new AssessmentError('会话响应缺少标识，无法继续提交。', { retryable: false })
        state.sessionId = session.id; state.session = session; publish()
      }
      if (!state.measurementId) {
        state.stage = '保存检测记录'; publish()
        const measurement = await call('POST', '/measurements', { ...input.measurement, session_id: state.sessionId }, state.keys.measurement)
        if (!id(measurement.id) || measurement.session_id !== state.sessionId) throw new AssessmentError('检测记录与当前会话不匹配。', { retryable: false })
        state.measurementId = measurement.id; state.measurement = measurement; publish()
      }
      state.stage = '提交分析任务'; publish()
      const session = state.session
      const body = { type: session?.mode === 'deep' ? 'deep_analysis' : 'quick_analysis', session_id: state.sessionId, measurement_ids: [state.measurementId] }
      if (body.type === 'deep_analysis') {
        if (!session.field_id || !session.cycle_id) throw new AssessmentError('深度分析需要服务端地块和种植周期。请先完成地块对接，或返回选择快速试用。', { retryable: false })
        body.field_id = session.field_id; body.cycle_id = session.cycle_id
      }
      const task = await call('POST', '/tasks', body, state.keys.task)
      if (!id(task.task_id)) throw new AssessmentError('任务响应缺少标识，请核对服务端状态。', { retryable: false })
      state.taskId = task.task_id; state.phase = 'polling'; state.stage = ''; publish()
      await poll()
    } catch (error) { if (version === generation) errorState(error) }
  }
  async function poll() {
    stop(); const version = generation; controller = new AbortController(); state.phase = 'polling'; state.error = null; publish()
    try {
      const response = await request('GET', '/tasks/' + encodeURIComponent(state.taskId), null, null, controller.signal)
      if (version !== generation) return
      const task = response.data
      if (task.task_id !== state.taskId || task.session_id !== state.sessionId || !['queued', 'running', ...terminal].includes(task.status) || !['quick_analysis', 'deep_analysis'].includes(task.type) || (['completed', 'partial'].includes(task.status) && (task.result?.kind !== 'analysis' || !validAnalysis(task.result.analysis)))) throw new AssessmentError('分析任务的状态或结果结构不符合契约，未作为有效结果展示。', { retryable: false })
      accept(response); state.task = task; state.phase = terminal.has(task.status) ? 'settled' : 'polling'; publish()
      if (!terminal.has(task.status)) timer = schedule(poll, pollMs)
    } catch (error) { if (version === generation) errorState(error) }
  }
  async function restore(sessionId, taskId = '') {
    stop(); const version = generation; controller = new AbortController(); state.phase = 'polling'; state.error = null; state.sessionId = sessionId; state.taskId = taskId; state.task = null; state.snapshot = null; state.measurement = null; state.inputError = ''; publish()
    try {
      const response = await request('GET', '/sessions/' + encodeURIComponent(sessionId), null, null, controller.signal)
      if (version !== generation) return
      if (response.data.id !== sessionId) throw new AssessmentError('服务返回的研究会话不匹配。', { retryable: false })
      accept(response); state.session = response.data; state.taskId = taskId || response.data.latest_task_id || ''; state.measurementId = taskId && taskId !== response.data.latest_task_id ? '' : response.data.measurement_ids?.at(-1) || ''
      if (!state.taskId) { state.phase = 'paused'; publish(); return }
      if (state.measurementId) {
        try {
          const measurement=await request('GET','/measurements/'+encodeURIComponent(state.measurementId),null,null,controller.signal)
          if (version !== generation) return
          if(measurement.data.id!==state.measurementId || measurement.data.session_id!==sessionId) throw new AssessmentError('检测记录与会话不匹配。',{retryable:false})
          state.measurement=measurement.data
        } catch(error){ if(version!==generation)return; if([401,403].includes(error.status))throw error;state.inputError='暂未读取到原始检测记录，可稍后重新打开任务。' }
      }
      publish(); await poll()
    } catch (error) { if (version === generation) errorState(error) }
  }
  return {
    get state() { return state },
    start(snapshot) { stop(); state = { ...state, phase: 'idle', sessionId: '', measurementId: '', taskId: '', task: null, measurement: null, session: null, snapshot: clone(snapshot), keys: { session: newKey(), measurement: newKey(), task: newKey() }, error: null, stage: '' }; publish(); return submit() },
    load() { try { const saved = JSON.parse(storage?.getItem(storageKey) || 'null'); if (saved?.keys && typeof saved.sessionId === 'string' && typeof saved.taskId === 'string' && (!saved.snapshot || (['quick','deep'].includes(saved.snapshot.session?.mode) && Array.isArray(saved.snapshot.measurement?.values) && saved.snapshot.measurement.values.length))) state = { ...state, ...saved, phase: saved.taskId ? 'paused' : saved.snapshot ? 'paused' : 'idle', error: null }; } catch { state.storageFailed = true } onChange({ ...state }); return state },
    resume() { return state.taskId ? poll() : state.snapshot ? submit() : state.sessionId ? restore(state.sessionId) : Promise.resolve() },
    retry() { if (state.task && ['failed', 'interrupted'].includes(state.task.status)) { state.taskId = ''; state.task = null; state.keys.task = newKey(); publish(); return submit() } return state.taskId ? poll() : submit() },
    restore,
    pause() { stop(); state.phase = 'paused'; publish() },
    dispose: stop,
  }
}
