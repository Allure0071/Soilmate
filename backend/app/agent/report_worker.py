"""Deterministic evidence-preserving Report Worker."""
from typing import Any, Dict, List


def build_report(inputs: List[Any], config: Dict[str, Any]) -> Dict[str, Any]:
    by_schema={x.get('schema_version'):x for x in inputs if isinstance(x,dict) and x.get('schema_version')}
    required=('data_profile.v1','mds_result.v1','validation_report.v1','decision_recommendation.v1')
    missing=[k for k in required if k not in by_schema]
    if missing:
        raise ValueError('report missing upstream artifacts: '+', '.join(missing))
    validation=by_schema['validation_report.v1']
    return {'schema_version':'soil_health_report.v1','status':'review_required' if validation.get('status')!='passed' else 'ready',
            'sections':{'data_profile':by_schema['data_profile.v1'],'mds_result':by_schema['mds_result.v1'],
                        'validation':validation,'decision':by_schema['decision_recommendation.v1']},
            'evidence_refs':list(required),'risks':validation.get('risks',[]),
            'evidence_tier':'computed_from_observed_input'}
