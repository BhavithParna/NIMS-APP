import pandas as pd, numpy as np, pickle, re, hashlib
from scipy import stats
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
def H(x): return "R"+hashlib.sha256(str(x).encode()).hexdigest()[:6]
t=D['T24_FR']; t=t[t['Timestamp'].notna()].copy()
t['esi']=pd.to_numeric(t['ESI Triage Category'],errors='coerce')
t['rater']=t['Email Address'].astype(str).str.lower().str.strip().map(H)
t['ts']=pd.to_datetime(t['Timestamp'])

print("### RATER (collector) EFFECTS — 2024, ESI assignment")
g=t.groupby('rater').agg(n=('esi','size'),mean_esi=('esi','mean'),pct_esi1=('esi',lambda s:(s==1).mean()*100))
g=g[g.n>=20].sort_values('n',ascending=False)
print(g.round(2).to_string())
d=t.dropna(subset=['esi']); d=d[d.rater.isin(g.index)]
kw=stats.kruskal(*[x['esi'].values for _,x in d.groupby('rater')])
print(f"  Kruskal-Wallis ESI ~ rater: H={kw.statistic:.1f} p={kw.pvalue:.3g}  => raters differ systematically")
print(f"  between-rater SD of mean ESI = {g.mean_esi.std():.3f}; overall SD of ESI = {d['esi'].std():.3f}")
print(f"  top rater share: {g.n.max()/g.n.sum():.1%}; top-5 raters = {g.n.nlargest(5).sum()/g.n.sum():.1%} of records")

print("\n### TEMPORAL COMPLETENESS DRIFT — 2024 (fill rate by month)")
t['mo']=t['ts'].dt.to_period('M')
cols=['PAIN SCORE NRS','Intervention (Airway)','Intervention (Breathing)','Intervention (Circulation)','Log Roll','ESI Triage Category','GCS  E','Area Triaged']
fill=t.groupby('mo')[cols].apply(lambda d: d.notna().mean()).round(2)
fill['n']=t.groupby('mo').size()
print(fill.to_string())

print("\n### DUPLICATES")
def dupreport(lbl,df,keys):
    k=df[keys].apply(lambda r: '|'.join(map(str,r)),axis=1)
    print(f"  {lbl}: exact full-row dups={int(df.duplicated().sum())}; dup on {keys}={int(k.duplicated().sum())}")
    vc=k.value_counts(); print(f"     max repeats={vc.max()}")
dupreport("2024",t,['Name ','Age','CR Number'])
dupreport("2024 (ts)",t,['Timestamp'])
fr=D['T23_FR']
dupreport("2023FR",fr[fr['Timestamp'].notna()],['Name ','Age'])
print("\n  CR Number reuse in 2024 (same CR, different name?):")
cr=t.dropna(subset=['CR Number']).copy(); cr['crs']=cr['CR Number'].astype(str).str.replace(r'\D','',regex=True)
gg=cr.groupby('crs')['Name '].nunique(); rep=cr.groupby('crs').size()
print(f"   distinct CR={len(rep)}; CR used >1x={int((rep>1).sum())}; of those, CR mapping to >1 distinct name={int((gg>1).sum())}")
print(f"   CR digit-length distribution: {dict(cr['crs'].str.len().value_counts().sort_index())}  (expected 15)")

print("\n### FREE-TEXT COMPLAINT FIELD — vocabulary chaos")
for lbl,s in [("2023FR",D['T23_FR']['Complaint/Diagnosis']),("2024",t['Complaint/Diagnosis'])]:
    v=s.dropna().astype(str).str.strip()
    print(f"  {lbl}: n={len(v)} distinct_raw={v.nunique()} distinct_lower={v.str.lower().nunique()} ({v.nunique()-v.str.lower().nunique()} case-only dups)")
    print(f"     entries containing '?' (uncertainty): {int(v.str.contains(r'\?').sum())} ({v.str.contains(r'\?').mean():.1%})")
    print(f"     top: {dict(v.str.lower().value_counts().head(8))}")

print("\n### DISEASE REFERENCE LIST (Sheet1) — what is it?")
l=D['T24_S1'][0].astype(str)
print(f"  n={len(l)}; contains 'NNDSS': {int(l.str.contains('NNDSS').sum())}")
icd=l.str.extract(r'([A-TV-Z]\d{2}(?:\.\d+)?)$')[0]
print(f"  rows ending in an ICD-10-looking code: {icd.notna().sum()} ({icd.notna().mean():.1%})")
print(f"  ICD chapter letters: {dict(icd.dropna().str[0].value_counts().head(12))}")
print(f"  any overlap with actual complaint text used? ", end="")
comp=set(t['Complaint/Diagnosis'].dropna().astype(str).str.strip().str.lower())
lst=set(l.str.replace(r'[A-TV-Z]\d{2}(\.\d+)?$','',regex=True).str.replace('NNDSS','').str.strip().str.lower())
print(f"{len(comp&lst)} exact matches of {len(comp)} distinct complaints -> list NOT used to constrain entry")
