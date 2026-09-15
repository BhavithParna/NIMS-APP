import pandas as pd, numpy as np, pickle, re
from scipy import stats
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
def bp(v):
    m=re.search(r'(\d{2,3})\s*/\s*(\d{2,3})',str(v)) if pd.notna(v) else None
    return (float(m.group(1)),float(m.group(2))) if m else (np.nan,np.nan)

# ---- build unified 2023 register (union of the two sex-split sheets)
fr=D['T23_FR']; s3=D['T23_S3'].copy()
s3.columns=['Timestamp','Off hours triage=1','Email Address','Name ','Age','Sex','Trauma=1',
            'Complaint/Diagnosis','cardiac=1','Pulse rate','SI','BP','Saturation','venti=1, O2 =2',
            'Respiratory Rate','red=1','Additional information']
a=fr.rename(columns={'Unnamed: 13':'BP'})[['Timestamp','Off hours triage=1','Email Address','Name ','Age','Sex','Trauma=1','Complaint/Diagnosis','cardiac=1','Pulse rate','SI','BP','Saturation','venti=1, O2 =2','Respiratory Rate','red=1','Additional information']]
u23=pd.concat([a.assign(_sheet='FormResponses1'),s3.assign(_sheet='Sheet3')],ignore_index=True)
u23=u23[u23['Timestamp'].notna()].copy()
print(f"### UNIFIED 2023 REGISTER: {len(u23)} encounters  (M={int((u23.Sex==1).sum())} F={int((u23.Sex==0).sum())}, ratio {((u23.Sex==1).sum()/(u23.Sex==0).sum()):.2f})")
u23['red']=pd.to_numeric(u23['red=1'],errors='coerce')
print(f"  TARGET red=1: {dict(u23['red'].value_counts(dropna=False))}  positive rate={u23['red'].mean():.3f}")
print(f"  by sex: {u23.groupby('Sex')['red'].agg(['mean','count']).to_dict()}")
print(f"  by trauma: {u23.groupby(pd.to_numeric(u23['Trauma=1'],errors='coerce'))['red'].mean().to_dict()}")
ct=pd.crosstab(u23['Sex'],u23['red']); chi2,p,_,_=stats.chi2_contingency(ct)
print(f"  chi2 sex vs red: chi2={chi2:.2f} p={p:.4f}")
u23[['sbp','dbp']]=pd.DataFrame([bp(v) for v in u23['BP']],index=u23.index)
u23['hr']=pd.to_numeric(u23['Pulse rate'],errors='coerce'); u23['si_calc']=u23['hr']/u23['sbp']
u23['spo2']=pd.to_numeric(u23['Saturation'],errors='coerce'); u23['rr']=pd.to_numeric(u23['Respiratory Rate'],errors='coerce')
u23['age']=pd.to_numeric(u23['Age'],errors='coerce')
print("\n  Predictors of red=1 (point-biserial / mean by class):")
for c in ['age','hr','sbp','dbp','spo2','rr','si_calc']:
    g=u23.groupby('red')[c].mean()
    r=u23[[c,'red']].dropna().corr().iloc[0,1]
    print(f"   {c:8s} mean(red=0)={g.get(0,np.nan):7.2f} mean(red=1)={g.get(1,np.nan):7.2f}  r={r:+.3f}")
u23.to_csv("/home/bhavith/Documents/Datasets/analysis_output/csv/unified_2023_register_DEID.csv",
           index=False,columns=['Timestamp','_sheet','Sex','age','Trauma=1','cardiac=1','hr','sbp','dbp','spo2','rr','si_calc','red','Off hours triage=1'])

# ---- 2024
t=D['T24_FR']; t=t[t['Timestamp'].notna()].copy()
print(f"\n### 2024 REGISTER: {len(t)} encounters")
esi=pd.to_numeric(t['ESI Triage Category'],errors='coerce')
print(f"  TARGET ESI Triage Category: {dict(esi.value_counts().sort_index())} | non-numeric: {sorted(set(t['ESI Triage Category'].dropna().astype(str))-{'1.0','2.0','3.0','4.0','5.0'})}")
print(f"  proportions: {dict((esi.value_counts(normalize=True).sort_index()*100).round(1))}")
print(f"  Area Triaged: {dict(t['Area Triaged'].value_counts())}")
print(f"  crosstab Area x ESI:\n{pd.crosstab(t['Area Triaged'],esi)}")
t['sbp']=[bp(v)[0] for v in t['Blood Pressure']]; t['dbp']=[bp(v)[1] for v in t['Blood Pressure']]
t['hr']=pd.to_numeric(t['Pulse rate'],errors='coerce'); t['rr']=pd.to_numeric(t['Respiratory Rate'],errors='coerce')
t['spo2']=pd.to_numeric(t['Saturation'],errors='coerce'); t['age']=pd.to_numeric(t['Age'],errors='coerce')
t['temp']=pd.to_numeric(t['Temperature in Fahrenheit'],errors='coerce'); t['pain']=pd.to_numeric(t['PAIN SCORE NRS'],errors='coerce')
t['gcs']=pd.to_numeric(t['GCS  E'],errors='coerce')+pd.to_numeric(t['GCS V'],errors='coerce')+pd.to_numeric(t['GCS M'],errors='coerce')
t['esi']=esi; t['si']=t['hr']/t['sbp']
print("\n  Mean vital by ESI category:")
print(t.groupby('esi')[['age','hr','sbp','rr','spo2','gcs','pain','temp','si']].mean().round(1).to_string())
print("\n  Spearman corr with ESI (lower ESI = sicker):")
for c in ['age','hr','sbp','rr','spo2','gcs','pain','temp','si']:
    d=t[[c,'esi']].dropna()
    if len(d)>10:
        rho,p=stats.spearmanr(d[c],d['esi']); print(f"   {c:6s} rho={rho:+.3f} p={p:.2g} n={len(d)}")
t.to_csv("/home/bhavith/Documents/Datasets/analysis_output/csv/triage_2024_DEID.csv",index=False,
         columns=['Timestamp','age','Sex','hr','sbp','dbp','rr','spo2','temp','pain','gcs','si','Airway','Bilateral Air Entry','Capillary Refill Time','Pupils','Focal Neurological Deficit','Area Triaged','esi'])

print("\n### IMPOSSIBLE / OUT-OF-RANGE VALUES (2024)")
rules={'age':(0,110),'hr':(20,250),'sbp':(50,260),'dbp':(20,160),'rr':(4,60),'spo2':(40,100),'temp':(93,110),'gcs':(3,15),'pain':(0,10)}
for c,(lo,hi) in rules.items():
    v=t[c]; bad=((v<lo)|(v>hi)); print(f"   {c:5s}: {int(bad.sum())} outside [{lo},{hi}]  values={sorted(v[bad].dropna().unique())[:8]}")
