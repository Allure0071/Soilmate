#!/usr/bin/env python3
"""SOILMATE N-SHI -> MFTI minimal auditable prototype.

This is NOT an ecologically validated health-index estimator. If all three
independently interpretable dimensions are unavailable, it fails closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_DIMENSIONS = {
    'nitrogen_supply': ['TN','AN','NH4_N','PMN','SOC'],
    'biological_transformation': ['MBC','MBN','NAG','LAP','UREASE'],
    'nitrogen_retention': ['CEC','BD','PH'],
}
ID_REQUIRED=['project_id','plot_id','soil_sample_id','sampling_event_id','sampling_date','depth_top_cm','depth_bottom_cm']
FORBIDDEN=['SHI','HEALTH_CLASS','HEALTH_GRADE','旧SHI','健康等级','N_SHI','N-SHI']


def export(obj, path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')


def fingerprint(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def read_table(path):
    path=Path(path)
    if path.suffix.lower() in ('.xlsx','.xls'):
        return pd.read_excel(path)
    if path.suffix.lower()=='.tsv':
        return pd.read_csv(path,sep='\t')
    return pd.read_csv(path,encoding='utf-8-sig')


def soil_audit(df, dimensions, min_sample=200):
    missing_keys=[x for x in ID_REQUIRED if x not in df]
    blank_keys={x:int(df[x].isna().sum()+df[x].astype(str).str.strip().eq('').sum())
                for x in ID_REQUIRED if x in df}
    sample_duplicates=None
    if not missing_keys:
        sample_duplicates=int(df.duplicated(subset=['project_id','plot_id','soil_sample_id','sampling_event_id']).sum())
    all_features=list(dict.fromkeys(sum(dimensions.values(), [])))
    stat={}
    for c in all_features:
        if c in df:
            series=pd.to_numeric(df[c],errors='coerce')
            stat[c]={'n_valid':int(series.notna().sum()),'missing_fraction':round(float(series.isna().mean()),4),
                     'unique_numeric_values':int(series.nunique())}
        else: stat[c]={'n_valid':0,'missing_fraction':1.,'unique_numeric_values':0}
    dimension_status={d:[x for x in colset if x in df and stat[x]['missing_fraction']<=0.30 and stat[x]['unique_numeric_values']>=3]
                      for d,colset in dimensions.items()}
    return {'n_rows':len(df), 'minimum_independent_units_target':min_sample,
            'row_count_reaches_threshold':len(df)>=min_sample,
            'n_unique_plots':int(df['plot_id'].nunique()) if 'plot_id' in df else None,
            'required_metadata_missing':missing_keys,'required_metadata_blank_counts':blank_keys,
            'required_metadata_complete':not missing_keys and all(v==0 for v in blank_keys.values()),
            'duplicate_sample_keys':sample_duplicates,
            'feature_audit':stat, 'usable_features_by_dimension':dimension_status,
            'dimensions_complete':all(bool(v) for v in dimension_status.values()),
            'dimensions_complete_is_only_minimal_presence':True,
            'cautions':['row_count_does_not_prove_independence','no_old_shi_or_health_class_used',
                        'feature_availability_does_not_establish_ecological_validity']}


def select_mds(df, audit, dim_map, per_dim=2, rho_threshold=.8, n_boot=100, seed=20261018):
    rng=np.random.default_rng(seed)
    groups={}
    for dim,cands in audit['usable_features_by_dimension'].items():
        cands=[c for c in cands if c in dim_map[dim]]
        vals=df[cands].apply(pd.to_numeric,errors='coerce')
        def rank_features(frame):
            ranked=sorted(cands,key=lambda c:(frame[c].notna().mean(),np.log1p(max(0.0,float(frame[c].std(skipna=True) or 0)))),reverse=True)
            keep=[]
            for c in ranked:
                if all(not (abs(frame[c].corr(frame[prev],method='spearman'))>=rho_threshold) for prev in keep):
                    keep.append(c)
                if len(keep)>=per_dim: break
            return keep
        selected=rank_features(vals)
        counts={c:0 for c in cands}
        group_keys = df['plot_id'].astype(str) if 'plot_id' in df else pd.Series([str(i) for i in range(len(df))])
        unique = group_keys.unique().tolist()
        for _ in range(n_boot):
            sampled=rng.choice(unique,size=len(unique),replace=True)
            ids=np.concatenate([np.flatnonzero(group_keys.values==g) for g in sampled])
            for c in rank_features(vals.iloc[ids]):counts[c]+=1
        groups[dim]={'selected':selected,'candidates':cands,'bootstrap_selection_frequencies':{c:round(v/n_boot,3) for c,v in counts.items()},
                     'strategy':'unsupervised_missingness_variability_redundancy_greedy','rho_redundancy_threshold':rho_threshold}
    return {'dimensions':groups,'seed':seed,'n_bootstrap':n_boot,'scope':'exploratory_unsupervised_only',
            'caution':'not_a_supervised_12_method_vote_or_NOTEARS_result'}


def score_soil(df, mds, config, audit):
    rules=config.get('score_rules',{})
    chosen=[x for v in mds['dimensions'].values() for x in v['selected']]
    absent=[x for x in chosen if x not in rules]
    if absent: return None,{'status':'BLOCKED_NO_SCORING_RULE','missing_rules':absent}
    all_scores={}
    param={}
    for col in chosen:
        rule=rules[col]
        s=pd.to_numeric(df[col],errors='coerce')
        if rule.get('type') not in ['higher_relative','lower_relative','optimum_external']:
            return None,{'status':'BLOCKED_BAD_SCORING_RULE','indicator':col}
        if rule['type'] in ['higher_relative','lower_relative']:
            q5,q95=s.quantile([.05,.95]).tolist()
            if q95<=q5:return None,{'status':'BLOCKED_ZERO_SCORE_SCALE','indicator':col}
            z=((s-q5)/(q95-q5)).clip(0,1)
            if rule['type']=='lower_relative':z=1-z
            param[col]={'type':rule['type'],'q05':float(q5),'q95':float(q95)}
        else:
            low,ideal,high=(float(rule[k]) for k in ['low','ideal','high'])
            if not low<ideal<high: return None,{'status':'BLOCKED_BAD_EXTERNAL_LIMITS','indicator':col}
            z=(s-low)/(ideal-low)
            z=pd.Series(np.where(s<=ideal,z,(high-s)/(high-ideal)),index=df.index).clip(0,1)
            z[s.isna()]=np.nan
            param[col]={'type':'optimum_external','low':low,'ideal':ideal,'high':high,'reference':rule.get('reference','NOT_PROVIDED')}
        all_scores[col]=z
    feature_scores=pd.DataFrame(all_scores,index=df.index)
    dim_scores={}
    for d,p in mds['dimensions'].items():
        dset=p['selected'];dim_scores[d]=feature_scores[dset].mean(axis=1,skipna=False)
    ds=pd.DataFrame(dim_scores,index=df.index)
    nshi=ds.mean(axis=1,skipna=False)
    output=df[ID_REQUIRED].copy()
    for c in ['nitrogen_supply','biological_transformation','nitrogen_retention']:
        output[c]=ds[c]
    output['n_shi_score']=nshi
    output['score_basis']='relative_exploratory'
    output['assessment_version']='N-SHI-prototype-1.2'
    output['risk_flags']='not_assessed_without_validated_thresholds'
    out_status={'status':'EXPLORATORY_SCORES_ONLY','n_scored':int(nshi.notna().sum()),'n_unscored':int(nshi.isna().sum()),
       'n_sample_threshold_met':bool(audit['row_count_reaches_threshold']),
       'score_parameters':param,'limitations':['not_calibrated_health_standard','no_causal_claims',
        'not_a_validated_nitrogen_loss_risk','no_independent_functional_validation','full_dataset_relative_reference_not_cv_test']}
    return output,out_status


def run_soil(args):
    df=read_table(args.input)
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
    rename=cfg.get('rename',{})
    df=df.rename(columns=rename)
    dim_map=cfg.get('dimensions',DEFAULT_DIMENSIONS)
    dest=Path(args.out);dest.mkdir(parents=True,exist_ok=True)
    a=soil_audit(df,dim_map,min_sample=args.min_sample)
    a['source_sha256']=fingerprint(args.input)
    export(a,dest/'soil_audit.json')
    if args.audit_only:
        print(json.dumps({'status':'AUDIT_DONE','rows':len(df),'complete':a['dimensions_complete']}));return
    if a['required_metadata_missing'] or not a['required_metadata_complete'] or a['duplicate_sample_keys'] is not None and a['duplicate_sample_keys']>0 or not a['dimensions_complete'] or not a['row_count_reaches_threshold']:
        why=[]
        if a['required_metadata_missing']:why.append('missing_required_metadata')
        if not a['required_metadata_complete']:why.append('blank_required_metadata')
        if a['duplicate_sample_keys']:why.append('duplicate_sample_identity')
        if not a['dimensions_complete']:why.append('missing_one_or_more_nshi_dimensions')
        if not a['row_count_reaches_threshold']:why.append('sample_target_not_met')
        export({'status':'BLOCKED_NO_VALID_NSHI','why':why},dest/'run_status.json')
        print(json.dumps({'status':'BLOCKED_NO_VALID_NSHI','why':why}));return
    mds=select_mds(df,a,dim_map, n_boot=args.bootstrap)
    export(mds,dest/'mds_selection.json')
    score,status=score_soil(df,mds,cfg,a)
    export(status,dest/'run_status.json')
    if score is not None:score.to_csv(dest/'nshi_exploratory.csv',index=False,encoding='utf-8-sig')
    print(json.dumps({'status':status['status'],'rows':len(df),'n_scored':status.get('n_scored',0)}))


def run_gene(args):
    df=read_table(args.input)
    required=['treatment','gene_symbol','mean_reported','sd_reported','n_reported']
    if any(c not in df for c in required):raise ValueError('missing expected published summary columns')
    if df.duplicated(subset=['treatment','gene_symbol']).any():raise ValueError('treatment/gene duplicate')
    df['mean_reported']=pd.to_numeric(df['mean_reported'],errors='raise')
    df['sd_reported']=pd.to_numeric(df['sd_reported'],errors='raise')
    df['n_reported']=pd.to_numeric(df['n_reported'],errors='raise')
    base=df[df.treatment==args.reference].set_index('gene_symbol')['mean_reported']
    out=df[['treatment','gene_symbol','mean_reported','sd_reported','n_reported']].copy()
    out['reference_treatment']=args.reference
    out['reference_mean']=out['gene_symbol'].map(base)
    out['fold_vs_reference']=out['mean_reported']/out['reference_mean']
    out['percent_vs_reference']=(out['fold_vs_reference']-1)*100
    out['data_granularity']='published_group_mean_not_biological_replicate'
    dest=Path(args.out);dest.mkdir(parents=True,exist_ok=True)
    out.to_csv(dest/'published_gene_descriptive_contrast.csv',index=False,encoding='utf-8-sig')
    top=out[out.treatment!=args.reference].sort_values('percent_vs_reference',ascending=False)
    summary={'status':'DESCRIPTIVE_SUMMARY_DONE','n_rows':len(df),'n_treatments':int(df.treatment.nunique()),
             'n_distinct_genes':int(df.gene_symbol.nunique()),'replicates_per_group_reported':sorted(df.n_reported.unique().tolist()),
             'comparison_reference':args.reference,'source_sha256':fingerprint(args.input),
             'largest_increases':top[['treatment','gene_symbol','percent_vs_reference']].head(5).round(2).to_dict('records'),
             'restrictions':['24_rows_are_not_24_independent_samples','no_sample_ko_matrix','no_KEGG_module_completeness_from_gene_summary',
                             'no_depth_calibration','no_sample_level_significance_test','no_nshi_microbe_matching']}
    export(summary,dest/'published_gene_run_status.json')
    print(json.dumps(summary,ensure_ascii=False))


def run_bridge(args):
    from jsonschema import Draft202012Validator
    src=json.loads(Path(args.input).read_text(encoding='utf-8'))
    schema=json.loads(Path(args.schema).read_text(encoding='utf-8'))
    errs=[x.message for x in Draft202012Validator(schema,format_checker=None).iter_errors(src)]
    matches=src['microbial_link']['pairing_status']=='exact_match' and bool(src['microbial_link'].get('pairing_evidence'))
    matching=src['microbial_link']
    if matches:
        # Mere label "exact_match" is not proof. Require matching IDs/time/depth in actual correspondence.
        exact=matching.get('paired_soil_sample_id')==src['soil_sample_id']
        same_date=matching.get('paired_sampling_date')==src['soil_context']['sampling_date']
        same_depth=matching.get('paired_depth_top_cm')==src['soil_context']['depth_top_cm'] and matching.get('paired_depth_bottom_cm')==src['soil_context']['depth_bottom_cm']
        matches=exact and same_date and same_depth and bool(matching.get('biosample_accession'))
    if matching['pairing_status']=='exact_match' and not matches:errs.append('unverified exact_match: need real mapped soil ID, same date/depth and BioSample accession')
    verdict={'schema_valid':not bool(errs),'schema_errors':errs,'joint_analysis_allowed':bool(matches and not errs),
             'microbial_mode':'paired_sample_analysis' if matches and not errs else 'external_method_validation_only',
             'causal_claim_permitted':False}
    export(verdict,args.out)
    print(json.dumps(verdict,ensure_ascii=False))



def run_cases(args):
    from jsonschema import Draft202012Validator
    """Turn exploratory N-SHI dimension scores into questions, never mechanism conclusions."""
    df=read_table(args.scores)
    required=ID_REQUIRED+['nitrogen_supply','biological_transformation','nitrogen_retention','n_shi_score']
    missing=[c for c in required if c not in df]
    if missing:raise ValueError(f'missing required score columns: {missing}')
    mapping=read_table(args.mapping) if args.mapping else None
    if mapping is not None and 'soil_sample_id' not in mapping:
        raise ValueError('mapping lacks soil_sample_id')
    if mapping is not None and mapping.duplicated(['soil_sample_id']).any():
        raise ValueError('mapping has ambiguous repeated soil_sample_id')
    lookup={} if mapping is None else {str(r['soil_sample_id']):r for _,r in mapping.iterrows()}
    folder=Path(args.out);folder.mkdir(parents=True,exist_ok=True)
    schema=json.loads(Path(args.schema).read_text(encoding='utf-8'))
    accepted=0;blocked=0;cases=[]
    for _,r in df.iterrows():
        smid=str(r['soil_sample_id']);m=lookup.get(smid)
        d={c:float(r[c]) if pd.notna(r[c]) else None for c in ['nitrogen_supply','biological_transformation','nitrogen_retention']}
        score=float(r['n_shi_score']) if pd.notna(r['n_shi_score']) else None
        same_identity=m is not None and str(m.get('plot_id'))==str(r['plot_id']) and str(m.get('sampling_event_id'))==str(r['sampling_event_id'])
        same_date=same_identity and str(m.get('soil_sampling_date'))==str(r['sampling_date']) and str(m.get('microbial_sampling_date'))==str(r['sampling_date'])
        def eq_depth(x,y):
            try:return abs(float(x)-float(y))<1.e-6
            except (ValueError,TypeError):return False
        same_depth=same_identity and eq_depth(m.get('soil_depth_top_cm'),r['depth_top_cm']) and eq_depth(m.get('soil_depth_bottom_cm'),r['depth_bottom_cm']) and eq_depth(m.get('microbial_depth_top_cm'),r['depth_top_cm']) and eq_depth(m.get('microbial_depth_bottom_cm'),r['depth_bottom_cm'])
        seq='none' if m is None else str(m.get('sequencing_type','none'))
        if seq not in ['shotgun_dna','16s','metatranscriptome','none']:seq='none'
        acc=None if m is None or pd.isna(m.get('biosample_accession')) else str(m.get('biosample_accession'))
        evidence=None if m is None or pd.isna(m.get('pairing_evidence')) else str(m.get('pairing_evidence'))
        matched=bool(same_identity and same_date and same_depth and acc and evidence and seq!='none')
        x={'pairing_status':'exact_match' if matched else 'unmatched', 'sequencing_type':seq,
           'biosample_accession':acc,'run_accessions':[],'pairing_evidence':evidence}
        if m is not None and pd.notna(m.get('run_accession')):x['run_accessions']=[str(m.get('run_accession'))]
        if matched:
            x.update({'paired_soil_sample_id':smid,'paired_sampling_date':str(r['sampling_date']),
              'paired_depth_top_cm':float(r['depth_top_cm']),'paired_depth_bottom_cm':float(r['depth_bottom_cm'])})
        if score is None or any(v is None for v in d.values()):
            questions=[{'question_id':'RQ_DATA','question':'缺少综合评价所需的指标，需补充数据后再提机制研究问题',
                        'candidate_processes':[], 'required_evidence':['complete_soil_assessment'], 'status':'insufficient_evidence'}]
        elif d['nitrogen_supply']>=0.65 and d['biological_transformation']<=0.40:
            questions=[{'question_id':'RQ_SUPPLY_BIO_MISMATCH','question':'相对氮供给评分较高但生物过程代理指标偏弱，是否存在与测量、环境条件或微生物氮获取相关的解释？',
                 'candidate_processes':['organic_n_acquisition','nitrogen_mineralization'],
                 'required_evidence':['NAG_LAP_MBN_assays','soil_metadata','shotgun_or_targeted_genes_if_available','independent_NMR_for_process_rate'],
                 'status':'proposed'}]
        else:
            questions=[{'question_id':'RQ_N_PROFILE','question':'分析地块氮循环分维度画像及不确定性，决定是否存在需要优先研究的过程',
                        'candidate_processes':[], 'required_evidence':['review_soil_assessment_and_external_reference'], 'status':'proposed'}]
        gaps=[]
        if not matched:gaps.append('no_verified_soil_microbe_exact_pairing')
        if seq=='16s':gaps.append('16s_cannot_directly_measure_shotgun_KO')
        if score is None:gaps.append('incomplete_nshi_dimensions')
        case={'contract_version':'1.1','project_id':str(r['project_id']), 'plot_id':str(r['plot_id']),
             'soil_sample_id':smid,'sampling_event_id':str(r['sampling_event_id']),
             'soil_context':{'sampling_date':str(r['sampling_date']),'depth_top_cm':float(r['depth_top_cm']),
                             'depth_bottom_cm':float(r['depth_bottom_cm'])},
             'assessment':{'assessment_version':'N-SHI-prototype-1.2','mds_version':'unsupervised-1.2',
                           'score_basis':'relative' if score is not None else 'not_available',
                           'n_shi_score':score,'dimension_scores':d,'risk_flags':['not_assessed_without_validated_thresholds'],
                           'evidence_gaps':gaps},'microbial_link':x,'research_questions':questions}
        errs=list(Draft202012Validator(schema).iter_errors(case))
        if errs:raise ValueError(f'contract invalid for sample {smid}: {[v.message for v in errs]}')
        cases.append(case)
        if matched:accepted+=1
        else:blocked+=1
    export(cases,folder/'microbial_research_cases.json')
    export({'case_count':len(cases),'paired_cases':accepted,'unmatched_cases':blocked,
            'status':'QUESTIONS_GENERATED_NOT_MECHANISM_PROVEN',
            'warning':'relative exploratory N-SHI; no molecular functional inference is performed'},folder/'case_generation_status.json')
    print(json.dumps({'cases':len(cases),'paired':accepted,'unmatched':blocked}))


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('soil');a.add_argument('--input',required=True);a.add_argument('--config',required=True);a.add_argument('--out',required=True)
    a.add_argument('--min-sample',type=int,default=200);a.add_argument('--bootstrap',type=int,default=100);a.add_argument('--audit-only',action='store_true');a.set_defaults(func=run_soil)
    a=sub.add_parser('genes');a.add_argument('--input',required=True);a.add_argument('--out',required=True);a.add_argument('--reference',default='F');a.set_defaults(func=run_gene)
    a=sub.add_parser('bridge');a.add_argument('--input',required=True);a.add_argument('--schema',required=True);a.add_argument('--out',required=True);a.set_defaults(func=run_bridge)
    a=sub.add_parser('cases');a.add_argument('--scores',required=True);a.add_argument('--mapping');a.add_argument('--schema',required=True);a.add_argument('--out',required=True);a.set_defaults(func=run_cases)
    args=p.parse_args();args.func(args)
if __name__=='__main__':main()
