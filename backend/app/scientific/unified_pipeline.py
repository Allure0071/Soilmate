"""Evidence bounded SOILMATE pipeline for the 2026-10-19 handoff.

Inputs are read from the existing research handoffs. No source is modified.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT.parents[2] / "data" / "research_sources"
OUTPUT = ROOT.parents[2] / "data" / "research_outputs"
SOIL = INPUT / "local_74_soil_partial_scores.csv"
MODULES = INPUT / "pathway_definitions_kegg.json"


def read_csv(path, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        raise ValueError("No rows to write")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        average_rank = (start + 1 + stop) / 2
        for pos in range(start, stop):
            out[order[pos]] = average_rank
        start = stop
    return out


def spearman(a, b):
    x, y = ranks(a), ranks(b)
    n = len(x)
    mx, my = sum(x)/n, sum(y)/n
    numerator = sum((i-mx)*(j-my) for i,j in zip(x,y))
    denominator = (sum((i-mx)**2 for i in x)*sum((j-my)**2 for j in y))**0.5
    return numerator/denominator if denominator else 0.0


def indicator_audit(rows):
    """Exploratory redundancy baseline, not RTSS or external validation."""
    groups = {"nitrogen_supply": ("TN_raw_percent", "AN_raw_mgkg"),
              "nitrogen_retention": ("CEC_raw_cmolkg", "BD_raw_gcm3")}
    rng = random.Random(20261019)
    result=[]
    for domain,(first,second) in groups.items():
        pairs=[(float(r[first]),float(r[second])) for r in rows if r[first] and r[second]]
        if len(pairs)<10:
            result.append({"domain":domain,"status":"insufficient_data"})
            continue
        rho=spearman([a for a,b in pairs],[b for a,b in pairs])
        selected=first if abs(rho)>=0.85 else f"{first};{second}"
        stable=0
        for _ in range(100):
            sample=[pairs[rng.randrange(len(pairs))] for _ in pairs]
            r=spearman([a for a,b in sample],[b for a,b in sample])
            stable += (abs(r)>=0.85)==(abs(rho)>=0.85)
        result.append({"domain":domain,"indicator_a":first,"indicator_b":second,
                       "complete_pairs":len(pairs),"spearman_rho":round(rho,6),
                       "redundancy_cutoff_abs_rho":0.85,"selected_exploratory":selected,
                       "bootstrap_same_selection_fraction":stable/100,
                       "status":"exploratory_no_independent_functional_target"})
    return result


def local_branch():
    soil = read_csv(SOIL)
    pairing = read_csv(INPUT / "local_soil_microbiome_pairing_to_verify_v0.6.csv")
    assert len(soil) == len(pairing) == 74
    pair_by_id = {p["soil_sample_id"]: p for p in pairing}
    assert len(pair_by_id) == 74
    result, hypothetical = [], []
    for row in soil:
        sample = row["soil_sample_id"]
        p = pair_by_id[sample]
        exact = (p["pairing_status"] == "exact_match" and all(p.get(x) for x in
                 ("verified_microbiome_sample_id", "sampling_date_verified", "soil_depth_verified",
                  "microbiome_biosample_accession", "sra_run_accession", "verification_source")))
        record = {
            "sample_id": sample,
            "nitrogen_supply_relative": row["nitrogen_supply_relative"],
            "nitrogen_retention_relative": row["nitrogen_retention_relative"],
            "biological_transformation": "",
            "n_shi_score": "",
            "assessment_status": "BLOCKED_MISSING_BIOLOGICAL_DIMENSION",
            "pairing_status": "exact_match" if exact else "unverified",
            "candidate_microbiome_id": p["candidate_microbiome_sample_id"],
            "action_code": "A01_VERIFY_PAIRING_AND_BIO_ASSAY",
            "action_reason": "Need same-event pairing evidence and measured biological dimension",
            "cost": "unknown",
            "source_type": "real_local_soil_partial",
        }
        result.append(record)
        # Deliberately generated test input: exercises the completed interface only.
        bio = (int(sample[-3:]) * 37 % 101) / 100
        score = (float(row["nitrogen_supply_relative"]) +
                 float(row["nitrogen_retention_relative"]) + bio) / 3
        hypothetical.append({"sample_id": sample, "bio_dimension_assumed": round(bio, 4),
                             "composite_demo": round(score, 4),
                             "status": "SYNTHETIC_INTERFACE_TEST_ONLY",
                             "source_type": "deterministic_hypothetical_not_observed"})
    return result, hypothetical


def public_branch():
    manifest = read_csv(INPUT / "public_sample_manifest.csv")
    assert len(manifest) == 70 and len({r["sample_alias"] for r in manifest}) == 70
    definitions = json.loads(MODULES.read_text(encoding="utf-8"))["modules"]
    needed = {ko for module in definitions for stage in module["stages"]
              for alternative in stage["alternatives"] for ko in alternative}
    observed = defaultdict(dict)
    count_rows = 0
    for r in read_csv(INPUT / "ko_counts_by_sample.csv.gz", True):
        count_rows += 1
        if r["ko_id"] in needed:
            observed[r["sample_alias"]][r["ko_id"]] = int(r["n_genes_predicted"])
    assert count_rows == 1050490
    assert {r["sample_alias"] for r in manifest} == set(observed)
    out = []
    for sample in manifest:
        alias = sample["sample_alias"]
        ko = observed[alias]
        for module in definitions:
            coverage = []
            for stage in module["stages"]:
                hit = any(all(ko.get(k, 0) > 0 for k in alternative)
                          for alternative in stage["alternatives"])
                coverage.append(hit)
            structural = ("all_steps_observed" if all(coverage) else
                          "partial_steps_observed" if any(coverage) else "no_steps_observed")
            # Current paper provides predicted gene counts, not same-sample FASTQ QC or truth.
            out.append({
                "sample_alias": alias,
                "biosample": sample["sample_accession"],
                "run_accession": sample["run_accession"],
                "module_id": module["module_id"],
                "steps_observed": sum(coverage),
                "steps_total": len(coverage),
                "structural_status": structural,
                "qc_status": "not_run_for_this_70_sample_study",
                "mfti_evidence_status": "insufficient_data",
                "reason": "Published KO predicted-gene counts lack independently verified same-run QC and biological truth",
                "agent_selected_action": "A02_VERIFY_SAME_RUN_QC_AND_ANNOTATION",
                "estimated_cost": "unknown",
                "source_type": "real_public_processed_ko",
            })
    return out


def main():
    OUTPUT.mkdir(exist_ok=True)
    local, hypothetical = local_branch()
    public = public_branch()
    write_csv(OUTPUT / "local_real_partial.csv", local)
    write_csv(OUTPUT / "hypothetical_full_interface.csv", hypothetical)
    write_csv(OUTPUT / "public_ko_module_evidence.csv", public)
    audit = indicator_audit(read_csv(SOIL))
    (OUTPUT / "indicator_selection_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = defaultdict(int)
    for row in public:
        counts[(row["module_id"], row["structural_status"])] += 1
    summary = {
        "schema_version": "1.0", "local_soil_rows": len(local),
        "local_exact_pairs": sum(r["pairing_status"] == "exact_match" for r in local),
        "local_formal_nshi_scores": sum(bool(r["n_shi_score"]) for r in local),
        "hypothetical_interface_rows": len(hypothetical),
        "public_samples": len({r["sample_alias"] for r in public}),
        "public_module_rows": len(public),
        "module_structural_counts": [{"module": m, "status": s, "samples": n}
                                     for (m, s), n in sorted(counts.items())],
        "mfti_supported_claims": 0,
        "joint_plot_level_analyses": 0,
        "limitations": ["No real local biological dimension", "No exact local soil-microbe pair",
                        "Public KO values are predicted gene counts, not reads or biological truth",
                        "The 70 runs lack same-run FASTQ QC in this package"],
        "input_sha256": {p.name: sha256(p) for p in [SOIL, MODULES,
                          INPUT / "public_sample_manifest.csv", INPUT / "ko_counts_by_sample.csv.gz",
                          INPUT / "local_soil_microbiome_pairing_to_verify_v0.6.csv"]},
    }
    (OUTPUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("input_sha256", "limitations")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

