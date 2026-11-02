"""Adapter for CNPS.cycle-style KO abundance matrices.

This adapter never infers sequencing depth or annotation confidence from KO abundance.
Those quality fields must be supplied explicitly in a sample-level QC table.
"""
from pathlib import Path
import csv


def _read_delimited(path, delimiter='\t'):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"No header found: {path}")
        return reader.fieldnames, list(reader)


def _truthy(value):
    return str(value).strip().lower() in {'true','1','yes','y'}


def read_ko_matrix(path):
    """Read CNPS.cycle KO abundance matrix (first column KO ID, last may be Description).

    Both tab-delimited official-style matrices and CSV exports from the included
    RData inspection helper are accepted; delimiter is inferred from the header.
    """
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        header = f.readline()
    delimiter = '\t' if header.count('\t') > header.count(',') else ','
    fields, rows = _read_delimited(path, delimiter)
    if len(fields) < 2:
        raise ValueError('KO matrix needs a KO identifier column and at least one sample column')
    ko_col = fields[0]
    desc_cols = [x for x in fields[1:] if x.strip().lower() in {'description','function','annotation'}]
    sample_cols = [x for x in fields[1:] if x not in desc_cols]
    if not sample_cols:
        raise ValueError('No sample columns found in KO matrix')
    matrix = {}
    for row in rows:
        ko = str(row.get(ko_col,'')).strip()
        if not ko:
            continue
        vals = {}
        for sample in sample_cols:
            raw = str(row.get(sample,'')).strip()
            try: val = float(raw) if raw else 0.0
            except ValueError: raise ValueError(f'Non-numeric KO abundance: KO={ko}, sample={sample}, value={raw!r}')
            if val < 0: raise ValueError(f'Negative abundance: KO={ko}, sample={sample}')
            vals[sample] = val
        matrix[ko] = vals
    if not matrix: raise ValueError('KO matrix has no KO rows')
    return sample_cols, matrix


def read_pathway_definition(path):
    """CSV columns: module,ko_id,required,min_abundance."""
    fields, rows = _read_delimited(path, ',')
    required_cols = {'module','ko_id'}
    if not required_cols.issubset(set(fields)):
        raise ValueError('Pathway definition CSV must contain module,ko_id; optional required,min_abundance')
    modules = {}
    for row in rows:
        module, ko = row['module'].strip(), row['ko_id'].strip()
        if not module or not ko: continue
        required = _truthy(row.get('required','true'))
        if not required: continue
        try: threshold = float(row.get('min_abundance') or 0)
        except ValueError: raise ValueError(f'Invalid min_abundance for {module}/{ko}')
        if threshold < 0: raise ValueError('min_abundance must be non-negative')
        modules.setdefault(module, {})[ko] = threshold
    if not modules: raise ValueError('No required KO definitions found')
    return modules


def read_sample_qc(path):
    """CSV must explicitly provide depth and evidence-quality fields for each sample."""
    fields, rows = _read_delimited(path, ',')
    required = {'sample_id','depth_mreads','annotation_confidence','database_agreement','metadata_completeness','sample_linked_to_soil'}
    missing = required - set(fields)
    if missing: raise ValueError(f'Sample QC CSV missing required columns: {sorted(missing)}')
    out = {}
    for row in rows:
        sid = row['sample_id'].strip()
        if not sid: continue
        vals = {'sample_id':sid,'sample_linked_to_soil':_truthy(row['sample_linked_to_soil'])}
        for k in ('depth_mreads','annotation_confidence','database_agreement','metadata_completeness'):
            try: vals[k] = float(row[k])
            except ValueError: raise ValueError(f'Invalid numeric QC field {k} for sample {sid}')
        if vals['depth_mreads'] < 0: raise ValueError(f'Negative depth for sample {sid}')
        for k in ('annotation_confidence','database_agreement','metadata_completeness'):
            if not 0 <= vals[k] <= 1: raise ValueError(f'{k} must be 0..1 for sample {sid}')
        out[sid] = vals
    return out


def analyze_ko_matrix(ko_path, pathway_path, qc_path):
    """Return sample/module evidence rows and actions; fail closed on missing metadata."""
    from .core import EvidenceCase, assess_evidence, choose_next_action
    samples, matrix = read_ko_matrix(ko_path)
    modules = read_pathway_definition(pathway_path)
    qc = read_sample_qc(qc_path)
    missing_qc = sorted(set(samples) - set(qc))
    extra_qc = sorted(set(qc) - set(samples))
    if missing_qc:
        raise ValueError(f'No QC/metadata row for KO matrix sample(s): {missing_qc[:10]}')
    results=[]
    for sample in samples:
        for module, required_kos in modules.items():
            unknown = sorted(set(required_kos)-set(matrix))
            present = [ko for ko, threshold in required_kos.items() if ko in matrix and matrix[ko].get(sample,0.0) > threshold]
            coverage = len(present)/len(required_kos) if required_kos else 0.0
            q=qc[sample]
            c=EvidenceCase(f'{sample}:{module}',sample,module,q['depth_mreads'],coverage,q['annotation_confidence'],q['database_agreement'],q['metadata_completeness'],q['sample_linked_to_soil'],'NOT_PROVIDED','NOT_PROVIDED',f'present_required_kos={len(present)}/{len(required_kos)}; unknown_kos={len(unknown)}')
            e=assess_evidence(c); a=choose_next_action(c,e['predicted_state'])
            results.append({'sample_id':sample,'module':module,'n_required_kos':len(required_kos),'n_detected_required_kos':len(present),'pathway_coverage':round(coverage,4),'unknown_kos_in_matrix':len(unknown),**e,'chosen_action':a['chosen_action'],'action_utility':a['utility'],'decision_reason':a['decision_reason'],'sample_linked_to_soil':q['sample_linked_to_soil']})
    return results, {'samples':len(samples),'modules':len(modules),'ko_rows':len(matrix),'sample_ids_missing_qc':missing_qc,'qc_ids_not_in_ko_matrix':extra_qc}
