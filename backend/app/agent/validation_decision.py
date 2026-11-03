"""Deterministic Phase 4.3 validation and decision workers."""
from typing import Any, Dict, List


def validate(inputs: List[Any], config: Dict[str, Any]) -> Dict[str, Any]:
    if not inputs:
        raise ValueError('validation requires upstream MDS Artifact')
    mds = next((x for x in inputs if isinstance(x, dict) and x.get('schema_version') == 'mds_result.v1'), None)
    if mds is None:
        raise ValueError('validation requires mds_result.v1')
    metadata = mds.get('metadata') or {}
    risks=[]
    if metadata.get('kind') == 'research_reference_not_validated_health_score':
        risks.append('reference implementation output; not a validated soil-health score')
    if not metadata.get('input_sha256') or not metadata.get('config_sha256'):
        risks.append('input/config provenance is incomplete')
    return {'schema_version':'validation_report.v1','status':'warning' if risks else 'passed',
            'risks':risks,'input_sha256':mds.get('input_sha256'),'config_sha256':mds.get('config_sha256'),
            'evidence_tier':'computed_from_observed_input'}


def decide(inputs: List[Any], config: Dict[str, Any]) -> Dict[str, Any]:
    validation = next((x for x in inputs if isinstance(x, dict) and x.get('schema_version') == 'validation_report.v1'), None)
    mds = next((x for x in inputs if isinstance(x, dict) and x.get('schema_version') == 'mds_result.v1'), None)
    if validation is None or mds is None:
        raise ValueError('decision requires validation_report.v1 and mds_result.v1')
    if validation.get('status') != 'passed' and not config.get('allow_warnings'):
        return {'schema_version':'decision_recommendation.v1','status':'pending_approval',
                'recommendation':None,'blocking_risks':validation.get('risks',[]),
                'evidence_refs':['validation_report.v1','mds_result.v1']}
    return {'schema_version':'decision_recommendation.v1','status':'ready',
            'recommendation':'Review the regional MDS selection and confirm laboratory costs before action.',
            'selected_core':mds.get('metadata',{}).get('core',[]),
            'budget':config.get('budget'),'evidence_refs':['validation_report.v1','mds_result.v1']}
