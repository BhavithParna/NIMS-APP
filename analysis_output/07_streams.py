import pandas as pd, numpy as np, pickle
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
fr=D['T23_FR']; s3=D['T23_S3']
a=pd.DataFrame({'ts':pd.to_datetime(fr['Timestamp'],errors='coerce'),'src':'FR','em':fr['Email Address'].astype(str).str.lower().str.strip()})
b=pd.DataFrame({'ts':pd.to_datetime(s3[0],errors='coerce'),'src':'S3','em':s3[2].astype(str).str.lower().str.strip()})
c=pd.concat([a,b]).dropna(subset=['ts']).sort_values('ts').reset_index(drop=True)
print("### Interleaving of the two 2023 streams in time")
runs=(c['src']!=c['src'].shift()).cumsum()
rl=c.groupby(runs).size()
print(f"  combined n={len(c)}; alternation runs={len(rl)}; mean run length={rl.mean():.2f} (1.0=perfect alternation, high=blocked)")
print(f"  run-length dist: {dict(rl.value_counts().sort_index().head(8))}")
c['gap']=c['ts'].diff().dt.total_seconds()/60
same=c['gap'][c['src']==c['src'].shift()]; diff=c['gap'][c['src']!=c['src'].shift()]
print(f"  median gap (min) same-stream={same.median():.1f}  cross-stream={diff.median():.1f}")
print("\n  Per-day: does each collector submit to only ONE stream that day?")
c['d']=c['ts'].dt.date
g=c.groupby(['d','em'])['src'].nunique()
print(f"  (day,collector) cells: {len(g)}; using BOTH streams same day: {(g>1).sum()} ({(g>1).mean():.0%})")
print("\n  Columns unique to each 2023 stream:")
print("   FR-only cols:",[str(x) for x in fr.columns[1:19]])
print("   FR extra vs S3 schema: 'GI emerg=1','stroke=1' present in FR only")
for col in ['GI emerg=1','stroke=1','Off hours triage=1']:
    s=fr[col]; print(f"   FR['{col}']: non-null={s.notna().sum()}/{len(fr)} ({s.notna().mean():.0%}) values={dict(s.value_counts().head(4))}")
    d=pd.to_datetime(fr['Timestamp'],errors='coerce')[s.notna()]
    if len(d): print(f"      populated between {d.min()} and {d.max()}")
print("\n### Combined 2023 daily volume (FR+S3) — smooth single service or two services?")
dd=c.groupby(['d','src']).size().unstack(fill_value=0)
print(dd.head(12).to_string()); print("  corr(FR,S3) daily volume: %.3f"%dd['FR'].corr(dd['S3']))
print("  days FR>0 & S3==0:",int(((dd['FR']>0)&(dd['S3']==0)).sum()),"| S3>0 & FR==0:",int(((dd['S3']>0)&(dd['FR']==0)).sum()))
print("  ratio S3/FR overall: %.3f"%(dd['S3'].sum()/dd['FR'].sum()))
