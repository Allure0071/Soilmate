import fixtures from './runDemoFixtures.js'
export const demoSnapshot = { session: { mode: 'quick', crop_name: null, background: '' }, measurement: { sample_alias: '流程审核示例（非实测）', values: [{ indicator_code: 'soil_ph', value: 6.2, unit: null, method: null, source_type: 'user_measurement' }] } }
export function demoRequest(scenario = 'completed') {
  let reads = 0, tasks = 0
  return async (method, path, body) => {
    const wrap = data => ({ data: structuredClone(data), origin: 'mock', requestId: 'mock-ui-review' })
    if (path === '/indicators') return wrap({ items: [{ code: 'soil_ph', units: [], unit_required: false }] })
    if (path === '/sessions' && method === 'POST') return wrap({ id: 'mock-session', mode: 'quick', measurement_ids: [], latest_task_id: null })
    if (path.startsWith('/sessions/')) return wrap({ id: 'mock-session', mode: 'quick', measurement_ids: ['mock-measurement-1'], latest_task_id: 'mock-task-quick' })
    if (path === '/measurements') return wrap({ ...body, id: 'mock-measurement-1' })
    if (path === '/tasks') { reads = 0; tasks++; return wrap({ task_id: 'mock-task-quick-'+tasks, type: 'quick_analysis', status: 'queued' }) }
    if (path.startsWith('/tasks/')) {
      reads++
      const stage = reads === 1 ? 'queued' : reads === 2 ? 'running' : scenario === 'failed' && tasks > 1 ? 'completed' : scenario
      const task = structuredClone(fixtures[stage] || fixtures.running)
      if (stage === 'queued') { task.status = 'queued'; task.result = null; task.error = null }
      task.task_id = path.split('/').at(-1); task.session_id = 'mock-session'
      return wrap(task)
    }
    throw new Error('审核示例不支持此操作。')
  }
}
