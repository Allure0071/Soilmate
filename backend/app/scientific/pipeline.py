"""KEGG module stage structural matching."""
def stage_status(stage, matrix, sample, threshold):
    alternatives=stage['alternatives']
    alt_results=[]; all_required=set(); absent_from_matrix=set(); zero_or_low=set()
    for route in alternatives:
        route_seen=[]; route_missing=[]; route_low=[]
        for ko in route:
            all_required.add(ko)
            if ko not in matrix:
                absent_from_matrix.add(ko); route_missing.append(ko)
            elif matrix[ko].get(sample,0.0) <= threshold:
                zero_or_low.add(ko); route_low.append(ko)
            else: route_seen.append(ko)
        alt_results.append({'route_kos':route,'complete':len(route_seen)==len(route),'missing_from_matrix':route_missing,'zero_or_below_threshold':route_low})
    complete=any(a['complete'] for a in alt_results)
    return {'stage_id':stage['stage_id'],'label':stage['label'],'status':'OBSERVED_SUPPORTED' if complete else 'INCOMPLETE_OR_UNOBSERVED',
            'any_route_complete':complete,'alternatives':alt_results,
            'required_kos':sorted(all_required),'kos_not_in_matrix':sorted(absent_from_matrix),'kos_zero_or_below_threshold':sorted(zero_or_low)}

