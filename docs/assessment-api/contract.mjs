// Contract source only. Generates documentation/types; does not run a backend.
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const dir = dirname(fileURLToPath(import.meta.url));
const version = '0.1.0-draft';
const ref = name => ({ $ref: `#/components/schemas/${name}` });
const str = (description = '') => ({ type: 'string', ...(description && { description }) });
const nonempty = description => ({ ...str(description), minLength: 1 });
const id = () => nonempty('Opaque server-generated identifier; do not infer format or owner.');
const en = (...values) => ({ type: 'string', enum: values });
const num = extra => ({ type: 'number', ...extra });
const integer = extra => ({ type: 'integer', ...extra });
const bool = () => ({ type: 'boolean' });
const nullable = schema => ({ anyOf: [schema, { type: 'null' }] });
const arr = (items, minItems = 0) => ({ type: 'array', items, minItems });
const ids = (min = 0) => ({ ...arr(id(), min), uniqueItems: true });
const obj = (properties, required = Object.keys(properties), description) => ({
  type: 'object', properties, required, additionalProperties: false,
  ...(description && { description })
});
const timestamp = () => ({ type: 'string', format: 'date-time' });
const date = () => ({ type: 'string', format: 'date' });
const S = {};
S.Mode = en('quick', 'deep');
S.TaskType = en('quick_analysis', 'deep_analysis', 'plan_generation', 'replan', 'followup');
S.TaskStatus = en('queued', 'running', 'completed', 'partial', 'failed', 'interrupted');
S.Location = obj({ longitude: num({ minimum: -180, maximum: 180 }), latitude: num({ minimum: -90, maximum: 90 }), crs: { const: 'EPSG:4326', type: 'string' } });
S.FieldError = obj({ path: nonempty('JSON Pointer, e.g. /values/0/unit'), code: nonempty(), message: nonempty() });
S.ErrorDetail = obj({ code: en('VALIDATION_FAILED', 'AUTH_REQUIRED', 'FORBIDDEN', 'NOT_FOUND', 'CONFLICT', 'RATE_LIMITED', 'MODEL_UNAVAILABLE', 'NX_UNSUPPORTED', 'TASK_FAILED', 'TASK_INTERRUPTED', 'IMPORT_EXPIRED', 'INTERNAL_ERROR'), message: nonempty(), fields: arr(ref('FieldError')), retryable: bool() });
S.ApiError = obj({ error: ref('ErrorDetail'), request_id: id(), data_origin: en('real', 'mock') });
S.AuthMe = obj({ user: obj({ id: id(), email: { type: 'string', format: 'email' } }), csrf_token: nonempty() });
S.LegacyAuthError = obj({ detail: str() });
S.Indicator = obj({ code: nonempty(), name: nonempty(), aliases: arr(str()), units: arr(str()), default_unit: nullable(str()), methods: arr(str()), input_hint: str(), unit_required: bool() });
S.IndicatorList = obj({ items: arr(ref('Indicator')), dictionary_version: nonempty() });
S.BackgroundValue = obj({ indicator_code: nonempty(), value: nullable(num()), unit: nullable(str()), source_label: nonempty(), year: nullable(integer({ minimum: 1900 })), depth_label: nullable(str()) });
S.MapContext = obj({ source_type: { const: 'map_reference', type: 'string' }, location: ref('Location'), resolution_km: { type: 'integer', enum: [1, 5] }, region_reference: nullable(str()), layer_values: arr(ref('BackgroundValue')) }, undefined, 'Background only; never copied automatically into measured values or verified N+X region identity.');
S.SessionCreate = obj({ mode: ref('Mode'), crop_name: nullable(str()), background: str(), field_id: nullable(id()), cycle_id: nullable(id()), map_context: nullable(ref('MapContext')) }, ['mode']);
S.Session = obj({ id: id(), mode: ref('Mode'), field_id: nullable(id()), cycle_id: nullable(id()), crop_name: nullable(str()), background: str(), map_context: nullable(ref('MapContext')), current_step: en('input', 'field_setup', 'timeline', 'results', 'feedback'), current_checkpoint_id: nullable(id()), measurement_ids: ids(), current_plan_id: nullable(id()), latest_task_id: nullable(id()), created_at: timestamp(), updated_at: timestamp() });
S.SessionUpgrade = obj({ field_id: id(), cycle_id: id(), attach_measurement_ids: ids() }, undefined, 'User-confirmed association only; keep original measurement provenance and previous quick results.');
S.FieldCreate = obj({ name: nonempty(), location: ref('Location'), background: str(), map_context: nullable(ref('MapContext')) }, ['name', 'location']);
S.FieldPatch = { ...obj({ name: nonempty(), location: ref('Location'), background: str() }, []), minProperties: 1 };
S.Field = obj({ id: id(), name: nonempty(), location: ref('Location'), background: str(), map_context: nullable(ref('MapContext')), current_cycle_id: nullable(id()), created_at: timestamp(), updated_at: timestamp() });
S.FieldList = obj({ items: arr(ref('Field')), next_cursor: nullable(str()) });
S.CycleCreate = obj({ crop_name: nonempty(), start_date: nullable(date()), growth_stage: nullable(str()), management_background: str() }, ['crop_name']);
S.Cycle = obj({ id: id(), field_id: id(), crop_name: nonempty(), start_date: nullable(date()), growth_stage: nullable(str()), management_background: str(), created_at: timestamp() });
S.ValueInput = obj({ indicator_code: nonempty(), value: num(), unit: nullable(str()), method: nullable(str()), source_type: { const: 'user_measurement', type: 'string' } }, ['indicator_code', 'value', 'source_type']);
S.MeasurementCreate = obj({ session_id: id(), field_id: nullable(id()), cycle_id: nullable(id()), checkpoint_id: nullable(id()), sample_alias: nonempty(), sampling_date: nullable(date()), depth_top_cm: nullable(num({ minimum: 0 })), depth_bottom_cm: nullable(num({ minimum: 0 })), values: arr(ref('ValueInput'), 1) }, ['session_id', 'sample_alias', 'values'], 'At least one measured value; recommended-count coverage never blocks submission. Unit/method issues narrow numerical interpretation instead of fabricating values.');
S.MeasuredValue = obj({ indicator_code: nonempty(), value: num(), unit: nullable(str()), method: nullable(str()), source_type: { const: 'user_measurement', type: 'string' }, normalized_value: nullable(num()), normalized_unit: nullable(str()), quality_flags: arr(str()) });
S.Measurement = obj({ id: id(), session_id: id(), field_id: nullable(id()), cycle_id: nullable(id()), checkpoint_id: nullable(id()), sample_alias: nonempty(), sampling_date: nullable(date()), depth_top_cm: nullable(num({ minimum: 0 })), depth_bottom_cm: nullable(num({ minimum: 0 })), values: arr(ref('MeasuredValue'), 1), warnings: arr(str()), created_at: timestamp() });
S.EvidenceRef = obj({ source_type: en('measurement', 'historical_measurement', 'map_reference', 'rule', 'user_statement'), source_id: nonempty(), indicator_code: nullable(str()), label: nonempty() });
S.Assessment = obj({ summary: nonempty(), scope: en('single_indicator', 'partial_indicators', 'recommended_set'), composite_score: nullable(num()), score_explanation: str(), indicator_assessments: arr(obj({ indicator_code: nonempty(), status: en('needs_attention', 'within_reference', 'uncertain', 'descriptive_only'), explanation: nonempty(), evidence: arr(ref('EvidenceRef')) })) });
S.Problem = obj({ id: id(), title: nonempty(), observation: nonempty(), possible_causes: arr(str()), priority: en('high', 'medium', 'low', 'undetermined'), evidence: arr(ref('EvidenceRef')), verification_needed: arr(str()) });
S.Decision = obj({ id: id(), action: nonempty(), reason: nonempty(), conditions: arr(str()), timing: nullable(str()), verification_goal: nullable(str()), evidence: arr(ref('EvidenceRef')) });
S.OptionalTest = obj({ indicator_code: nonempty(), reason: nonempty(), intended_question: nonempty(), timing: nullable(str()) });
S.Coverage = obj({ recommended_codes: ids(), measured_codes: ids(1), missing_codes: ids(), extra_codes: ids() }, undefined, 'Count distinct indicator codes, not file rows, sample count or repeated timepoints.');
S.ModelInfo = obj({ model_name: nonempty(), model_version: nullable(str()), is_fine_tuned: bool(), rule_version: nullable(str()) });
S.AnalysisResult = obj({ id: id(), mode: ref('Mode'), measurement_ids: ids(1), input_snapshot: arr(ref('EvidenceRef')), coverage: ref('Coverage'), assessment: ref('Assessment'), problems: arr(ref('Problem')), decisions: arr(ref('Decision')), gaps: arr(str()), optional_tests: arr(ref('OptionalTest')), next_plan_id: nullable(id()), model_info: ref('ModelInfo'), limitations: arr(str()), created_at: timestamp() });
S.RecommendedIndicator = obj({ indicator_code: nonempty(), reason: nonempty(), priority: en('essential', 'recommended', 'optional'), unit: nullable(str()), method: nullable(str()) });
S.Checkpoint = obj({ id: id(), title: nonempty(), sequence: integer({ minimum: 1 }), stage: nonempty(), planned_date: nullable(date()), trigger: nullable(str()), purpose: nonempty(), recommended_indicators: arr(ref('RecommendedIndicator'), 1), sampling_guidance: str(), estimated_cost: nullable(num({ minimum: 0 })), currency: { const: 'CNY', type: 'string' } }, undefined, 'Suggested, non-binding checklist. Date may be null when stage/trigger determines timing.');
S.Plan = obj({ id: id(), field_id: id(), cycle_id: id(), version: integer({ minimum: 1 }), base_plan_id: nullable(id()), status: en('draft', 'confirmed', 'superseded'), source: obj({ type: en('nx_model', 'verified_configuration', 'manual', 'mock'), version: nullable(str()), region_code: nullable(str()), applicability: str() }), checkpoints: arr(ref('Checkpoint'), 1), change_reasons: arr(str()), limitations: arr(str()), created_at: timestamp(), confirmed_at: nullable(timestamp()) });
S.PlanConfirm = obj({ expected_version: integer({ minimum: 1 }) });
S.ManagementCreate = obj({ session_id: id(), field_id: id(), cycle_id: id(), analysis_id: id(), decision_id: nullable(id()), adoption: en('adopted', 'partially_adopted', 'not_adopted'), performed_at: nullable(timestamp()), actual_action: str(), amount_text: nullable(str()), notes: str(), not_adopted_reason: nullable(str()) }, ['session_id', 'field_id', 'cycle_id', 'analysis_id', 'adoption', 'actual_action'], 'Record actual execution independently of suggested action; do not mark a recommendation executed automatically.');
S.ManagementEvent = obj({ id: id(), session_id: id(), field_id: id(), cycle_id: id(), analysis_id: id(), decision_id: nullable(id()), adoption: en('adopted', 'partially_adopted', 'not_adopted'), performed_at: nullable(timestamp()), actual_action: str(), amount_text: nullable(str()), notes: str(), not_adopted_reason: nullable(str()), created_at: timestamp() });
const taskBase = { session_id: id(), field_id: nullable(id()), cycle_id: nullable(id()), measurement_ids: ids(), plan_id: nullable(id()), management_event_ids: ids() };
S.QuickTaskCreate = obj({ type: { const: 'quick_analysis', type: 'string' }, ...taskBase, measurement_ids: ids(1) }, ['type', 'session_id', 'measurement_ids']);
S.DeepTaskCreate = obj({ type: { const: 'deep_analysis', type: 'string' }, ...taskBase, field_id: id(), cycle_id: id(), measurement_ids: ids(1) }, ['type', 'session_id', 'field_id', 'cycle_id', 'measurement_ids']);
S.PlanTaskCreate = obj({ type: { const: 'plan_generation', type: 'string' }, ...taskBase, field_id: id(), cycle_id: id() }, ['type', 'session_id', 'field_id', 'cycle_id']);
S.ReplanTaskCreate = obj({ type: { const: 'replan', type: 'string' }, ...taskBase, field_id: id(), cycle_id: id(), plan_id: id() }, ['type', 'session_id', 'field_id', 'cycle_id', 'plan_id']);
S.TaskCreate = { oneOf: ['QuickTaskCreate', 'DeepTaskCreate', 'PlanTaskCreate', 'ReplanTaskCreate'].map(ref), discriminator: { propertyName: 'type', mapping: Object.fromEntries([['quick_analysis','QuickTaskCreate'],['deep_analysis','DeepTaskCreate'],['plan_generation','PlanTaskCreate'],['replan','ReplanTaskCreate']].map(([key,value]) => [key, `#/components/schemas/${value}`])) } };
S.AgentTask = obj({ id: id(), role: en('manager', 'data_check', 'diagnosis', 'agronomy', 'process_testing', 'review'), status: ref('TaskStatus'), summary: str(), error: nullable(ref('ErrorDetail')) });
S.MessageCreate = obj({ content: nonempty(), measurement_ids: ids(), analysis_id: nullable(id()) }, ['content'], 'New measurements must first be saved; followup references their IDs. Do not treat free-text guessed values as lab records.');
S.Message = obj({ id: id(), session_id: id(), role: en('user', 'assistant'), content: str(), sequence: integer({ minimum: 1 }), measurement_ids: ids(), analysis_id: nullable(id()), task_id: nullable(id()), created_at: timestamp() });
S.MessageList = obj({ items: arr(ref('Message')), next_cursor: nullable(str()) });
S.MessageAccepted = obj({ message_id: id(), task_id: id(), status: { const: 'queued', type: 'string' } });
S.TaskAccepted = obj({ task_id: id(), type: ref('TaskType'), status: { const: 'queued', type: 'string' } });
S.TaskResult = { oneOf: [obj({ kind: { const: 'analysis', type: 'string' }, analysis: ref('AnalysisResult') }), obj({ kind: { const: 'plan', type: 'string' }, plan: ref('Plan') }), obj({ kind: { const: 'message', type: 'string' }, message: ref('Message'), analysis: nullable(ref('AnalysisResult')) })], discriminator: { propertyName: 'kind' } };
S.Task = obj({ task_id: id(), type: ref('TaskType'), session_id: id(), status: ref('TaskStatus'), current_stage: nullable(str()), agent_tasks: arr(ref('AgentTask')), result: nullable(ref('TaskResult')), error: nullable(ref('ErrorDetail')), created_at: timestamp(), updated_at: timestamp() });
S.Task.allOf = [
  { if: { properties: { status: { enum: ['queued', 'running'] } }, required: ['status'] }, then: { properties: { result: { type: 'null' }, error: { type: 'null' } } } },
  { if: { properties: { status: { enum: ['completed', 'partial'] } }, required: ['status'] }, then: { properties: { result: ref('TaskResult') } } },
  { if: { properties: { status: { const: 'completed' } }, required: ['status'] }, then: { properties: { error: { type: 'null' } } } },
  { if: { properties: { status: { enum: ['failed', 'interrupted'] } }, required: ['status'] }, then: { properties: { result: { type: 'null' }, error: ref('ErrorDetail') } } },
  { if: { properties: { type: { enum: ['quick_analysis','deep_analysis'] }, status: { enum: ['completed','partial'] } }, required: ['type','status'] }, then: { properties: { result: { properties: { kind: { const: 'analysis' } } } } } },
  { if: { properties: { type: { enum: ['plan_generation','replan'] }, status: { enum: ['completed','partial'] } }, required: ['type','status'] }, then: { properties: { result: { properties: { kind: { const: 'plan' } } } } } },
  { if: { properties: { type: { const: 'followup' }, status: { enum: ['completed','partial'] } }, required: ['type','status'] }, then: { properties: { result: { properties: { kind: { const: 'message' } } } } } }
];
S.ImportColumn = obj({ name: nonempty(), candidate_indicator_codes: arr(str()), candidate_unit: nullable(str()) });
S.ImportRow = obj({ row_number: integer({ minimum: 1 }), cells: arr(nullable(str())), issues: arr(ref('FieldError')) });
S.ImportPreview = obj({ import_id: id(), filename: nonempty(), expires_at: timestamp(), columns: arr(ref('ImportColumn')), rows: arr(ref('ImportRow')), total_rows: integer({ minimum: 0 }), warnings: arr(str()) });
S.ImportMapping = obj({ column: nonempty(), target: en('sample_alias','sampling_date','depth_top_cm','depth_bottom_cm','indicator'), indicator_code: nullable(str()), unit: nullable(str()), method: nullable(str()) });
S.ImportMapping.allOf = [{ if: { properties: { target: { const: 'indicator' } }, required: ['target'] }, then: { properties: { indicator_code: nonempty() }, required: ['indicator_code'] } }];
S.ImportConfirm = obj({ session_id: id(), field_id: nullable(id()), cycle_id: nullable(id()), checkpoint_id: nullable(id()), mappings: arr(ref('ImportMapping'), 1) }, ['session_id','mappings']);
S.ImportConfirmed = obj({ import_id: id(), measurement_ids: ids(1), warnings: arr(str()) }, undefined, 'Atomic commit: validation errors return 422 and persist no imported measurement rows. Distinct samples are returned as separate measurements.');
const wrapped = name => {
  const key = `${name}Response`;
  S[key] = obj({ data: ref(name), request_id: id(), data_origin: en('real', 'mock') });
  return ref(key);
};
const responses = schema => ({ description: 'Success. New assessment payloads always declare real/mock origin.', content: { 'application/json': { schema: wrapped(schema) } } });
const errorResponse = code => ({ description: `HTTP ${code}; structured error, no fabricated success.`, content: { 'application/json': { schema: ref('ApiError') } } });
const csrf = { $ref: '#/components/parameters/Csrf' };
const idem = { $ref: '#/components/parameters/IdempotencyKey' };
const paths = {};
const ops = [];
function op(method, path, operationId, summary, output, input, code = '200', extra = {}) {
  const pathParams = [...path.matchAll(/\{([^}]+)\}/g)].map(match => ({ name: match[1], in: 'path', required: true, schema: id() }));
  const write = ['post', 'patch', 'put', 'delete'].includes(method);
  const operation = {
    operationId, summary, tags: [path.includes('/auth/') ? 'Existing account' : 'Assessment draft'],
    'x-implemented': false,
    parameters: [...pathParams, ...(write ? [csrf, idem] : []), ...(extra.parameters || [])],
    responses: { [code]: responses(output), ...Object.fromEntries(['401','403','404','409','422','429','503','500'].map(c => [c, errorResponse(c)])) }
  };
  if (input) operation.requestBody = { required: true, content: { 'application/json': { schema: ref(input) } } };
  if (extra.multipart) operation.requestBody = { required: true, content: { 'multipart/form-data': { schema: obj({ file: { type: 'string', format: 'binary', description: 'CSV or XLSX; proposed maximum 12,000,000 bytes, subject to backend confirmation.' } }) } } };
  paths[path] ||= {};
  paths[path][method] = operation;
  ops.push({ method: method.toUpperCase(), path, operationId, summary, priority: extra.priority || 'P1' });
}
const base = '/api/assessment';
const cursor = [{ name: 'cursor', in: 'query', schema: nonempty() }, { name: 'limit', in: 'query', schema: { type: 'integer', minimum: 1, maximum: 100, default: 20 } }];
op('get','/api/auth/me','getAccount','Reuse current session/user and CSRF token','AuthMe',null,'200',{priority:'P0'});
paths['/api/auth/me'].get['x-implemented'] = true;
paths['/api/auth/me'].get.responses = {
  '200': { description: 'Existing raw response; deliberately not wrapped.', content: { 'application/json': { schema: ref('AuthMe') } } },
  '401': { description: 'Existing FastAPI error format.', content: { 'application/json': { schema: ref('LegacyAuthError') } } }
};
op('get',`${base}/indicators`,'listAssessmentIndicators','Read canonical input dictionary','IndicatorList',null,'200',{priority:'P0'});
op('post',`${base}/sessions`,'createAssessmentSession','Create quick/deep session','Session','SessionCreate','201',{priority:'P0'});
op('get',`${base}/sessions/{session_id}`,'getAssessmentSession','Restore session and its related IDs','Session',null,'200',{priority:'P0'});
op('post',`${base}/sessions/{session_id}/upgrade`,'upgradeAssessmentSession','Upgrade same session to deep without losing quick history','Session','SessionUpgrade');
op('get',`${base}/fields`,'listAssessmentFields','List own plots','FieldList',null,'200',{parameters:cursor});
op('post',`${base}/fields`,'createAssessmentField','Create plot; backend assigns owner','Field','FieldCreate','201');
op('get',`${base}/fields/{field_id}`,'getAssessmentField','Read own plot','Field');
op('patch',`${base}/fields/{field_id}`,'updateAssessmentField','Update plot background','Field','FieldPatch');
op('post',`${base}/fields/{field_id}/cycles`,'createAssessmentCycle','Create crop cycle','Cycle','CycleCreate','201');
op('get',`${base}/cycles/{cycle_id}`,'getAssessmentCycle','Read crop cycle','Cycle');
op('post',`${base}/measurements`,'createAssessmentMeasurement','Save one sample batch with one or more values','Measurement','MeasurementCreate','201',{priority:'P0'});
op('get',`${base}/measurements/{measurement_id}`,'getAssessmentMeasurement','Restore raw and normalized input','Measurement',null,'200',{priority:'P0'});
op('post',`${base}/tasks`,'createAssessmentTask','Enqueue analysis, initial plan or replan','TaskAccepted','TaskCreate','202',{priority:'P0'});
op('get',`${base}/tasks/{task_id}`,'getAssessmentTask','Poll task, role states and typed result','Task',null,'200',{priority:'P0'});
op('get',`${base}/analyses/{analysis_id}`,'getAssessmentAnalysis','Read immutable analysis result for earlier messages/decisions','AnalysisResult');
op('get',`${base}/plans/{plan_id}`,'getAssessmentPlan','Read a plan version','Plan');
op('post',`${base}/plans/{plan_id}/confirm`,'confirmAssessmentPlan','Adopt draft using optimistic version check','Plan','PlanConfirm');
op('post',`${base}/imports`,'previewAssessmentImport','Parse file and preview before saving','ImportPreview',null,'201',{multipart:true});
op('post',`${base}/imports/{import_id}/confirm`,'confirmAssessmentImport','Atomically save mapped sample batches','ImportConfirmed','ImportConfirm','201');
op('get',`${base}/sessions/{session_id}/messages`,'listAssessmentMessages','Latest message page, ascending sequence; cursor fetches older pages','MessageList',null,'200',{parameters:cursor,priority:'P0'});
op('post',`${base}/sessions/{session_id}/messages`,'sendAssessmentMessage','Save question and enqueue followup in current mode','MessageAccepted','MessageCreate','202',{priority:'P0'});
op('post',`${base}/management-events`,'createManagementEvent','Save user-reported actual management','ManagementEvent','ManagementCreate','201');

const api = {
  openapi: '3.1.0', jsonSchemaDialect: 'https://json-schema.org/draft/2020-12/schema',
  info: { title: 'Soilmate 健康评价前后端接口契约', version, description: 'DRAFT: frontend proposal awaiting backend confirmation. Only GET /api/auth/me already exists. No new backend implementation or scientific validation is claimed.' },
  'x-contract-status': 'draft-awaiting-backend-review',
  servers: [{ url: '/' }], security: [{ SessionCookie: [] }], paths,
  components: {
    securitySchemes: { SessionCookie: { type: 'apiKey', in: 'cookie', name: 'soilmate_session', description: 'Reuse existing HttpOnly session cookie; frontend does not handle passwords/model keys here.' } },
    parameters: {
      Csrf: { name: 'X-CSRF-Token', in: 'header', required: true, description: 'From existing GET /api/auth/me; backend must enforce it for new write routes.', schema: nonempty() },
      IdempotencyKey: { name: 'Idempotency-Key', in: 'header', required: true, description: 'Proposed replay protection: same user + method + path + key + body returns original outcome; changed body with same key returns 409. Retention window needs backend sign-off.', schema: nonempty() }
    }, schemas: S
  }
};

function tsType(schema) {
  if (schema.$ref) return schema.$ref.split('/').at(-1);
  if ('const' in schema) return JSON.stringify(schema.const);
  if (schema.enum) return schema.enum.map(value => JSON.stringify(value)).join(' | ');
  if (schema.oneOf || schema.anyOf) return (schema.oneOf || schema.anyOf).map(tsType).join(' | ');
  if (schema.type === 'null') return 'null';
  if (schema.type === 'array') return `Array<${tsType(schema.items)}>`;
  if (schema.type === 'object') return `{\n${Object.entries(schema.properties || {}).map(([key, value]) => `  ${JSON.stringify(key)}${(schema.required || []).includes(key) ? '' : '?'}: ${tsType(value)};`).join('\n')}\n}`;
  if (schema.type === 'integer' || schema.type === 'number') return 'number';
  if (schema.type === 'boolean') return 'boolean';
  return 'string';
}
const dts = [
  '// Generated by docs/assessment-api/contract.mjs. Draft, not backend-confirmed.',
  '// Runtime rules (minItems, status/result relation, ownership) remain in OpenAPI + README.',
  ...Object.entries(S).map(([name, schema]) => `export type ${name} = ${tsType(schema)};`)
].join('\n\n') + '\n';
mkdirSync(resolve(dir, '../../frontend/src/assessment'), { recursive: true });
writeFileSync(resolve(dir, 'openapi.json'), JSON.stringify(api, null, 2) + '\n');
writeFileSync(resolve(dir, '../../frontend/src/assessment/contracts.d.ts'), dts);
writeFileSync(resolve(dir, 'operations.json'), JSON.stringify(ops, null, 2) + '\n');
console.log(`Generated OpenAPI ${version}: ${ops.length} operations, ${Object.keys(S).length} schemas and frontend declarations.`);
