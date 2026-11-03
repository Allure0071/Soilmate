const text = value => typeof value === 'string'
const texts = value => Array.isArray(value) && value.every(text)
const list = (value, valid) => Array.isArray(value) && value.every(valid)
const evidence = value => value && text(value.label) && text(value.source_id) && text(value.source_type)
export function validAnalysis(value) {
  const assessment = value?.assessment
  return Boolean(value && text(value.id) && assessment && text(assessment.summary) && ['single_indicator','partial_indicators','recommended_set'].includes(assessment.scope) && (assessment.composite_score === null || typeof assessment.composite_score === 'number' && Number.isFinite(assessment.composite_score)) && text(assessment.score_explanation)
    && list(assessment.indicator_assessments, item => item && text(item.indicator_code) && text(item.explanation) && ['needs_attention','within_reference','uncertain','descriptive_only'].includes(item.status) && list(item.evidence,evidence))
    && value.coverage && ['recommended_codes','measured_codes','missing_codes','extra_codes'].every(key=>texts(value.coverage[key]))
    && list(value.problems, item => item && text(item.id) && text(item.title) && text(item.observation) && texts(item.possible_causes) && texts(item.verification_needed) && list(item.evidence,evidence))
    && list(value.decisions, item => item && text(item.id) && text(item.action) && text(item.reason) && texts(item.conditions) && list(item.evidence,evidence))
    && texts(value.gaps) && texts(value.limitations) && value.model_info && text(value.model_info.model_name))
}
