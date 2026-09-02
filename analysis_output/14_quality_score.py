import pandas as pd, numpy as np, pickle
OUT="/home/bhavith/Documents/Datasets/analysis_output"
D=pickle.load(open(f"{OUT}/data.pkl","rb"))
ap=D['AP1'].iloc[:78]; fr=D['T23_FR']; s3=D['T23_S3']; t24=D['T24_FR'][D['T24_FR'].Timestamp.notna()]
u23=pd.read_csv(f"{OUT}/csv/unified_2023_register_DEID.csv")
tt=pd.read_csv(f"{OUT}/csv/triage_2024_DEID.csv")

def score(name,n,ncols,used_cols,cell_missing,invalid_rate,dup_rate,mixed_type_cols,const_cols,
          has_target,target_completeness,has_doc,id_reliability,struct_penalty,notes):
    completeness = 100*(1-cell_missing)
    validity     = 100*(1-invalid_rate)
    uniqueness   = 100*(1-dup_rate)
    consistency  = 100*(1-(mixed_type_cols/used_cols))
    structure    = 100-struct_penalty
    documentation= has_doc
    size_score   = min(100, 100*np.log10(max(n,10)/10)/np.log10(200))   # 100 rows->~35, 2000 rows->~100
    mlready      = np.average([completeness, validity, target_completeness,
                               100-100*const_cols/used_cols, id_reliability, size_score],
                              weights=[.10,.15,.35,.10,.10,.20])
    overall=np.average([completeness,consistency,validity,uniqueness,structure,documentation,mlready],
                       weights=[.15,.15,.2,.1,.1,.1,.2])
    return dict(dataset=name,rows=n,columns=ncols,usable_columns=used_cols,
        completeness=round(completeness,1),consistency=round(consistency,1),validity=round(validity,1),
        uniqueness=round(uniqueness,1),structure=round(structure,1),documentation=documentation,
        ml_readiness=round(mlready,1),OVERALL=round(overall,1),verdict=notes)

rows=[]
# APACHE: 78 rows, 49 cols, 2 empty target cols, 6 constant cols, WBC units broken, vasopressor mixed
rows.append(score("APACHE 4.xlsx (Sheet1)",78,49,47,
    cell_missing=float(ap.iloc[:,:47].isna().mean().mean()), invalid_rate=0.03, dup_rate=0.0,
    mixed_type_cols=4, const_cols=8, has_target=False, target_completeness=0.0,
    has_doc=25, id_reliability=100, struct_penalty=35,
    notes="Immaculately complete physiology; NO outcome recorded; Sheet2 is a duplicate; n=78 too small for modelling."))
# 2023 unified
inv23=0.02
rows.append(score("NIMS TRIAGE 2023.xlsx (unified register)",1311,17,15,
    cell_missing=float(u23[['Timestamp','Sex','age','Trauma=1','cardiac=1','hr','sbp','dbp','spo2','rr','red','Off hours triage=1']].isna().mean().mean()), invalid_rate=inv23,
    dup_rate=16/1311, mixed_type_cols=3, const_cols=1, has_target=True, target_completeness=99.7,
    has_doc=20, id_reliability=15, struct_penalty=55,
    notes="Good target + clean vitals, but split across sheets by sex, headerless Sheet3, no patient ID, cryptic '=1' headers."))
# 2024
rows.append(score("NIMS TRIAGE 2024 (Responses).xlsx",1125,36,30,
    cell_missing=float(t24[[c for c in t24.columns if t24[c].notna().mean()>0.5]].isna().mean().mean()), invalid_rate=0.025, dup_rate=8/1125,
    mixed_type_cols=6, const_cols=2, has_target=True, target_completeness=99.8,
    has_doc=55, id_reliability=55, struct_penalty=20,
    notes="Best of the three: structured ABCDE form, 5-class ESI target, 1125 rows; but free-text chaos, rater effects, no outcome."))
q=pd.DataFrame(rows)
q.to_csv(f"{OUT}/csv/data_quality_scorecard.csv",index=False)
pd.set_option('display.width',260)
print(q.drop(columns=['verdict']).to_string(index=False))
print()
for _,r in q.iterrows(): print(f"  {r.dataset}: {r.verdict}")

# summary stats csv
summ=pd.DataFrame([
 dict(dataset="APACHE 4.xlsx",entity="one ICU admission",n=78,period="01-31 Oct 2024",setting="ICU",
      target="none recorded (Outcome column empty)",identifiers="Name, phone, CR no (all present)",raters="n/a (single investigator file)"),
 dict(dataset="NIMS TRIAGE 2023.xlsx",entity="one ED triage encounter",n=1311,period="Jun 2023 - Aug 2024 (+4 stragglers Apr 2025)",setting="Emergency triage",
      target="red=1 (critical) - 38.5% positive",identifiers="Name only (no CR no)",raters="27 staff Google accounts"),
 dict(dataset="NIMS TRIAGE 2024 (Responses).xlsx",entity="one ED triage encounter",n=1125,period="Dec 2024 - Aug 2025 (96% Mar-May 2025)",setting="Emergency triage",
      target="ESI category 1-5 + Area Triaged",identifiers="Name + CR no (unreliable)",raters="35 staff Google accounts"),
])
summ.to_csv(f"{OUT}/csv/dataset_summary.csv",index=False)
print("\n",summ.to_string(index=False))
