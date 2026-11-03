// Fictional interface examples. Not agronomic references or real model output.
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
const dir = dirname(fileURLToPath(import.meta.url));
const at = '2026-11-02T04:00:00Z';
const clone = value => JSON.parse(JSON.stringify(value));
const examples = [];
const envelope = data => ({ data, request_id: 'mock-request', data_origin: 'mock' });
const add = (name, operationId, request, status, data, options = {}) => examples.push({ name, operationId, request, response: { status, body: envelope(data) }, ...options });
const problem = code => ({ code, message: '接口开发演示状态，不是真实服务或模型故障。', fields: [], retryable: true });
const value = { indicator_code: 'soil_ph', value: 6.2, unit: null, method: null, source_type: 'user_measurement' };
const input = { session_id: 'mock-session', field_id: null, cycle_id: null, checkpoint_id: null, sample_alias: 'mock-sample-A', sampling_date: '2026-11-02', depth_top_cm: null, depth_bottom_cm: null, values: [value] };
const measurement = { ...clone(input), id: 'mock-measurement-1', values: [{ ...value, normalized_value: null, normalized_unit: null, quality_flags: ['method_unconfirmed'] }], warnings: ['演示数据；检测方法未提供，判读范围应受限。'], created_at: at };
const session = { id: 'mock-session', mode: 'quick', field_id: null, cycle_id: null, crop_name: null, background: '', map_context: null, current_step: 'input', current_checkpoint_id: null, measurement_ids: [], current_plan_id: null, latest_task_id: null, created_at: at, updated_at: at };
const evidence = { source_type: 'measurement', source_id: measurement.id, indicator_code: 'soil_ph', label: 'Mock 单项录入；不是实际地块实测资料' };
const analysis = { id: 'mock-analysis-quick', mode: 'quick', measurement_ids: [measurement.id], input_snapshot: [evidence], coverage: { recommended_codes: [], measured_codes: ['soil_ph'], missing_codes: [], extra_codes: ['soil_ph'] }, assessment: { summary: '界面示例：收到一项指标，可以展示对应范围的说明。', scope: 'single_indicator', composite_score: null, score_explanation: '未计算综合分数；此内容为接口演示，不是科学评价。', indicator_assessments: [{ indicator_code: 'soil_ph', status: 'descriptive_only', explanation: '原值为6.2；本示例不配置评价阈值。', evidence: [evidence] }] }, problems: [{ id: 'mock-problem', title: '检测背景仍需核对', observation: '当前仅提供一项指标，缺少检测方法和地块背景。', possible_causes: [], priority: 'undetermined', evidence: [evidence], verification_needed: ['核对检测方法与采样条件'] }], decisions: [{ id: 'mock-decision', action: '先核对检测记录和管理背景', reason: '示例只支持有限范围的说明。', conditions: ['此建议仅用于前端展示结构'], timing: null, verification_goal: '使下一次判读有明确输入依据', evidence: [evidence] }], gaps: ['方法、土层和作物信息未确认'], optional_tests: [], next_plan_id: null, model_info: { model_name: 'mock-placeholder-not-a-deployed-model', model_version: null, is_fine_tuned: false, rule_version: null }, limitations: ['所有内容均为Mock，不代表实际模型能力或正式健康结论。'], created_at: at };
const accepted = (type = 'quick_analysis', task_id = 'mock-task-quick') => ({ task_id, type, status: 'queued' });
const task = (type = 'quick_analysis', status = 'queued', task_id = 'mock-task-quick') => ({ task_id, type, session_id: session.id, status, current_stage: status === 'queued' ? null : 'mock-stage', agent_tasks: [], result: ['completed','partial'].includes(status) ? { kind: 'analysis', analysis: clone(analysis) } : null, error: ['failed','interrupted'].includes(status) ? problem(status === 'failed' ? 'TASK_FAILED' : 'TASK_INTERRUPTED') : null, created_at: at, updated_at: at });
add('P0 指标字典示例', 'listAssessmentIndicators', {}, 200, { dictionary_version: 'mock-dictionary-1', items: [{ code: 'soil_ph', name: 'pH（演示字段）', aliases: ['pH'], units: [], default_unit: null, methods: [], input_hint: '示例字段；正式方法和字典由后端确认', unit_required: false }, { code: 'cec', name: 'CEC（演示字段）', aliases: ['CEC'], units: ['cmol/kg'], default_unit: 'cmol/kg', methods: [], input_hint: '接口示例，不是正式指标标准', unit_required: true }] });
examples.push({ name: '已有登录接口保持原格式', operationId: 'getAccount', request: {}, response: { status: 200, body: { user: { id: 'mock-user', email: 'frontend@example.test' }, csrf_token: 'placeholder-not-a-real-token' } } });
add('P0 创建快速会话', 'createAssessmentSession', { body: { mode: 'quick' } }, 201, session);
add('P0 只提交一项有效指标', 'createAssessmentMeasurement', { body: input }, 201, measurement);
add('P0 恢复已保存实测', 'getAssessmentMeasurement', { path_params: { measurement_id: measurement.id } }, 200, measurement);
const quickInput = { type: 'quick_analysis', session_id: session.id, measurement_ids: [measurement.id] };
add('P0 创建异步分析任务', 'createAssessmentTask', { body: quickInput }, 202, accepted());
add('P0 排队中无分析结果', 'getAssessmentTask', { path_params: { task_id: 'mock-task-quick' } }, 200, task());
add('P0 运行中不冒充完成', 'getAssessmentTask', { path_params: { task_id: 'mock-task-quick' } }, 200, task('quick_analysis','running'));
add('P0 单指标分析完成且无综合分数', 'getAssessmentTask', { path_params: { task_id: 'mock-task-quick' } }, 200, task('quick_analysis','completed'));
const restored = { ...clone(session), current_step: 'results', measurement_ids: [measurement.id], latest_task_id: 'mock-task-quick' };
add('P0 刷新恢复会话', 'getAssessmentSession', { path_params: { session_id: session.id } }, 200, restored);
add('P0 有限证据结果可标记partial', 'getAssessmentTask', { path_params: { task_id: 'mock-task-partial' } }, 200, task('quick_analysis','partial','mock-task-partial'));
add('P0 发送追问获得任务ID', 'sendAssessmentMessage', { path_params: { session_id: session.id }, body: { content: '这个结论有哪些输入依据？', measurement_ids: [], analysis_id: analysis.id } }, 202, { message_id: 'mock-message-user', task_id: 'mock-task-followup', status: 'queued' });
const userMessage = { id: 'mock-message-user', session_id: session.id, role: 'user', content: '这个结论有哪些输入依据？', sequence: 1, measurement_ids: [], analysis_id: analysis.id, task_id: 'mock-task-followup', created_at: at };
const assistantMessage = { ...clone(userMessage), id: 'mock-message-assistant', role: 'assistant', sequence: 2, content: 'Mock答复：当前引用一项输入，缺少的信息不能推断。' };
const followup = task('followup','completed','mock-task-followup');
followup.result = { kind: 'message', message: assistantMessage, analysis: null };
add('P0 追问沿用同一会话', 'getAssessmentTask', { path_params: { task_id: followup.task_id } }, 200, followup);
add('P0 对话按sequence升序返回', 'listAssessmentMessages', { path_params: { session_id: session.id } }, 200, { items: [userMessage, assistantMessage], next_cursor: null });
const fieldInput = { name: 'Mock地块A', location: { longitude: 117, latitude: 32, crs: 'EPSG:4326' }, background: '仅用于接口示例；并非实际地块资料。' };
const field = { ...clone(fieldInput), id: 'mock-field', map_context: null, current_cycle_id: null, created_at: at, updated_at: at };
const cycleInput = { crop_name: '示例作物', start_date: null, growth_stage: null, management_background: '尚未提供实际管理记录' };
const cycle = { ...clone(cycleInput), id: 'mock-cycle', field_id: field.id, created_at: at };
add('P1 创建地块', 'createAssessmentField', { body: fieldInput }, 201, field);
add('P1 地块列表为空也合法', 'listAssessmentFields', {}, 200, { items: [], next_cursor: null });
add('P1 创建种植周期', 'createAssessmentCycle', { path_params: { field_id: field.id }, body: cycleInput }, 201, cycle);
const deepSession = { ...clone(restored), mode: 'deep', field_id: field.id, cycle_id: cycle.id };
add('P1 快速升级保留同一会话', 'upgradeAssessmentSession', { path_params: { session_id: session.id }, body: { field_id: field.id, cycle_id: cycle.id, attach_measurement_ids: [measurement.id] } }, 200, deepSession);
const plan = { id: 'mock-plan-1', field_id: field.id, cycle_id: cycle.id, version: 1, base_plan_id: null, status: 'draft', source: { type: 'mock', version: null, region_code: 'mock-region-not-real-nx-zone', applicability: '仅为时间线界面示例，不代表真实N+X输出' }, checkpoints: [{ id: 'mock-checkpoint-1', title: '示例基线时点', sequence: 1, stage: 'mock_baseline', planned_date: null, trigger: '建立基线时', purpose: '界面演示', recommended_indicators: [{ indicator_code: 'soil_ph', reason: '演示推荐项', priority: 'recommended', unit: null, method: null }, { indicator_code: 'cec', reason: '演示可未测项', priority: 'optional', unit: 'cmol/kg', method: null }], sampling_guidance: '实际采样方案应由后端结合适用依据生成', estimated_cost: null, currency: 'CNY' }, { id: 'mock-checkpoint-2', title: '示例措施复核时点', sequence: 2, stage: 'mock_management_review', planned_date: null, trigger: '管理措施后满足适用复核条件时', purpose: '演示第二时点', recommended_indicators: [{ indicator_code: 'soil_ph', reason: '演示相同时点指标的追踪', priority: 'recommended', unit: null, method: null }], sampling_guidance: '与历史记录核对方法和条件', estimated_cost: null, currency: 'CNY' }], change_reasons: [], limitations: ['不是科学检测方案；不得作为真实采样建议。'], created_at: at, confirmed_at: null };
const planInput = { type: 'plan_generation', session_id: session.id, field_id: field.id, cycle_id: cycle.id };
add('P1 生成多时点建议任务', 'createAssessmentTask', { body: planInput }, 202, accepted('plan_generation','mock-task-plan'));
const planTask = task('plan_generation','completed','mock-task-plan');
planTask.result = { kind: 'plan', plan };
add('P1 计划任务返回plan而非analysis', 'getAssessmentTask', { path_params: { task_id: planTask.task_id } }, 200, planTask);
add('P1 方案确认后才采用', 'confirmAssessmentPlan', { path_params: { plan_id: plan.id }, body: { expected_version: 1 } }, 200, { ...clone(plan), status: 'confirmed', confirmed_at: at });
const deepInput = { type: 'deep_analysis', session_id: session.id, field_id: field.id, cycle_id: cycle.id, plan_id: plan.id, measurement_ids: [measurement.id] };
add('P1 少于建议集合仍启动深度任务', 'createAssessmentTask', { body: deepInput }, 202, accepted('deep_analysis','mock-task-deep'));
const deepTask = task('deep_analysis','partial','mock-task-deep');
deepTask.agent_tasks = ['manager','data_check','diagnosis','agronomy','process_testing','review'].map((role,index) => ({ id: `mock-worker-${index}`, role, status: 'completed', summary: '模拟完成；不是实际模型调用', error: null }));
deepTask.result.analysis = { ...clone(analysis), id: 'mock-analysis-deep', mode: 'deep', coverage: { recommended_codes: ['soil_ph','cec'], measured_codes: ['soil_ph'], missing_codes: ['cec'], extra_codes: [] }, optional_tests: [{ indicator_code: 'cec', reason: '模拟建议清单中的未测项', intended_question: '演示如何说明补测的用途', timing: null }] };
add('P1 各Agent完成但整体证据仍可partial', 'getAssessmentTask', { path_params: { task_id: deepTask.task_id } }, 200, deepTask);
const feedbackInput = { session_id: session.id, field_id: field.id, cycle_id: cycle.id, analysis_id: deepTask.result.analysis.id, decision_id: 'mock-decision', adoption: 'not_adopted', performed_at: null, actual_action: '', amount_text: null, notes: '', not_adopted_reason: '演示未采用状态' };
add('P1 未采用也能保存真实反馈', 'createManagementEvent', { body: feedbackInput }, 201, { ...feedbackInput, id: 'mock-event', created_at: at });
add('P1 调整计划关联旧版与反馈', 'createAssessmentTask', { body: { type: 'replan', session_id: session.id, field_id: field.id, cycle_id: cycle.id, plan_id: plan.id, management_event_ids: ['mock-event'] } }, 202, accepted('replan','mock-task-replan'));
const preview = { import_id: 'mock-import', filename: 'mock-samples.csv', expires_at: '2026-11-03T04:00:00Z', columns: [{ name: '样本', candidate_indicator_codes: [], candidate_unit: null }, { name: 'pH', candidate_indicator_codes: ['soil_ph'], candidate_unit: null }], rows: [{ row_number: 2, cells: ['A','6.2'], issues: [] }, { row_number: 3, cells: ['B','6.5'], issues: [] }], total_rows: 2, warnings: ['仅为文件预览协议示例，未上传文件'] };
add('P1 文件导入只预览不保存', 'previewAssessmentImport', { content_type: 'multipart/form-data', body: { file: '<file-placeholder-not-a-real-upload>' } }, 201, preview);
add('P1 确认导入拆分多个样本', 'confirmAssessmentImport', { path_params: { import_id: preview.import_id }, body: { session_id: session.id, mappings: [{ column: '样本', target: 'sample_alias', indicator_code: null, unit: null, method: null }, { column: 'pH', target: 'indicator', indicator_code: 'soil_ph', unit: null, method: null }] } }, 201, { import_id: preview.import_id, measurement_ids: ['mock-import-A','mock-import-B'], warnings: [] });
for (const [status,code,operationId,request] of [
  [401,'AUTH_REQUIRED','createAssessmentTask',{body:quickInput}],
  [403,'FORBIDDEN','getAssessmentSession',{path_params:{session_id:'mock-other-owner-session'}}],
  [409,'CONFLICT','confirmAssessmentPlan',{path_params:{plan_id:plan.id},body:{expected_version:1}}],
  [422,'VALIDATION_FAILED','createAssessmentMeasurement',{body:{...clone(input),values:[]}}],
  [429,'RATE_LIMITED','createAssessmentTask',{body:quickInput}],
  [503,'MODEL_UNAVAILABLE','createAssessmentTask',{body:quickInput}]
]) {
  const error = { ...problem(code), retryable: [429,503].includes(status) };
  if (status===422) error.fields=[{path:'/values',code:'min_items',message:'至少一项有效指标'}];
  examples.push({name:`异常：${code}`,operationId,request,request_valid:status!==422,response:{status,body:{error,request_id:'mock-request-error',data_origin:'mock'}}});
}
for (const status of ['failed','interrupted']) add(`异步终态：${status}`, 'getAssessmentTask', {path_params:{task_id:`mock-task-${status}`}}, 200, task('deep_analysis',status,`mock-task-${status}`));
writeFileSync(resolve(dir,'examples.json'), JSON.stringify({ notice:'All examples are fictional Mock interface fixtures, not measured data, agronomic rules or actual model results.', examples },null,2)+'\n');
console.log(`Generated ${examples.length} HTTP examples.`);
