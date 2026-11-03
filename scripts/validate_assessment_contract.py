"""Validate draft OpenAPI and HTTP fixtures without starting or changing backend code.

Install the document-only validator into ignored local tooling:
  python -m pip install --target .local-tools/contract-validator jsonschema==4.23.0 openapi-spec-validator==0.7.2
Run from repository root:
  python scripts/validate_assessment_contract.py
"""
from pathlib import Path
import copy
import json
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local-tools' / 'contract-validator'))
try:
    from jsonschema import Draft202012Validator, FormatChecker
    # RefResolver is retained here to resolve the document's internal component refs
    # without making any network requests or adding app runtime dependencies.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        from jsonschema import RefResolver
    from openapi_spec_validator import validate_spec
except ImportError:
    raise SystemExit('Missing local document validators. See this script header; application dependencies are unchanged.')

doc = json.loads((ROOT / 'docs/assessment-api/openapi.json').read_text(encoding='utf-8'))
fixtures = json.loads((ROOT / 'docs/assessment-api/examples.json').read_text(encoding='utf-8'))['examples']
validate_spec(doc)
resolver = RefResolver.from_schema(doc)
def validator(schema):
    return Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())
def require(condition, message):
    if not condition:
        raise AssertionError(message)

operations = {}
for path, methods in doc['paths'].items():
    for method, operation in methods.items():
        if method not in {'get','post','patch','put','delete'}:
            continue
        key = operation['operationId']
        require(key not in operations, f'Duplicate operationId: {key}')
        operations[key] = (path, method, operation)

for example in fixtures:
    path, method, operation = operations[example['operationId']]
    request = example['request']
    path_params = request.get('path_params', {})
    for parameter in operation.get('parameters', []):
        if '$ref' in parameter:
            parameter = doc['components']['parameters'][parameter['$ref'].rsplit('/',1)[-1]]
        if parameter['in'] == 'path':
            require(parameter['name'] in path_params, f"Missing path parameter: {example['name']}")
            validator(parameter['schema']).validate(path_params[parameter['name']])
    if 'requestBody' in operation:
        content_type = request.get('content_type', 'application/json')
        schema = operation['requestBody']['content'][content_type]['schema']
        valid = validator(schema).is_valid(request.get('body'))
        require(valid == example.get('request_valid',True), f"Request schema mismatch: {example['name']}")
    response = example['response']
    schema = operation['responses'][str(response['status'])]['content']['application/json']['schema']
    validator(schema).validate(response['body'])
    if example['operationId'] != 'getAccount':
        require(response['body']['data_origin']=='mock', f"Fictional example missing Mock label: {example['name']}")

# Reject protocol contradictions; these checks exercise the contract, not backend behavior.
by_name = {e['name']:e for e in fixtures}
single = by_name['P0 只提交一项有效指标']['request']['body']
measurement_schema = doc['components']['schemas']['MeasurementCreate']
require(validator(measurement_schema).is_valid(single), 'One measured indicator must be accepted.')
for invalid_values in ([], [{**single['values'][0], 'value': None}], [{**single['values'][0], 'source_type':'map_reference'}]):
    changed = {**copy.deepcopy(single), 'values':invalid_values}
    require(not validator(measurement_schema).is_valid(changed), 'Invalid or background-only measurement accepted.')
completed = by_name['P0 单指标分析完成且无综合分数']['response']['body']['data']
task_schema = doc['components']['schemas']['Task']
for mutate in (
    lambda item: item.update(status='running'),
    lambda item: item.update(result=None),
    lambda item: item.update(status='failed'),
    lambda item: item.update(type='plan_generation'),
):
    changed=copy.deepcopy(completed)
    mutate(changed)
    require(not validator(task_schema).is_valid(changed), 'Contradictory task/result accepted.')
for name,schema in doc['components']['schemas'].items():
    Draft202012Validator.check_schema(schema)
require({e['operationId'] for e in fixtures}.issubset(operations), 'Unknown fixture operation.')
require(sum(1 for op in operations.values() if op[2].get('x-implemented')) == 1, 'Do not label proposed endpoints implemented.')
print(f"PASS: OpenAPI valid; {len(operations)} operations, {len(doc['components']['schemas'])} schemas, {len(fixtures)} HTTP examples; negative invariants passed.")
