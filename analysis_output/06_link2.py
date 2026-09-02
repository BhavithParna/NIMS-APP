import pandas as pd, numpy as np, pickle, re, hashlib
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
def H(x): return hashlib.sha256(str(x).encode()).hexdigest()[:8]
def nm(s): return re.sub(r'[^a-z]','',str(s).lower())
fr23=D['T23_FR']; s3=D['T23_S3']; fr24=D['T24_FR']; ap=D['AP1'].iloc[:78]

print("### Are cross-file NAME matches the same person? (age agreement test)")
def tbl(df,ncol,acol,tcol):
    t=df[[ncol,acol]].copy(); t.columns=['n','age']; t['n']=t['n'].map(nm); t['age']=pd.to_numeric(t['age'],errors='coerce')
    t['ts']=pd.to_datetime(df[tcol],errors='coerce') if tcol else pd.NaT
    return t[t['n']!='']
A=tbl(ap,ap.columns[1],ap.columns[2],None)
B23=tbl(fr23,'Name ','Age','Timestamp'); B3=tbl(s3,3,4,0); B24=tbl(fr24,'Name ','Age','Timestamp')
for lbl,X,Y in [("APACHE~2024",A,B24),("2023FR~2024",B23,B24),("2023S3~2024",B3,B24),("2023FR~2023S3",B23,B3)]:
    m=X.merge(Y,on='n',suffixes=('_x','_y'))
    if len(m)==0: print(f"  {lbl}: 0 name matches"); continue
    m['dage']=(m['age_x']-m['age_y']).abs()
    close=m[m['dage']<=2]
    print(f"  {lbl}: {len(m)} name-pairs | age within 2y: {len(close)} ({len(close)/len(m):.0%}) | median |Δage|={m['dage'].median():.1f}")
    if 'ts_x' in m and m['ts_x'].notna().any():
        c2=close.dropna(subset=['ts_x','ts_y']).copy()
        if len(c2): c2['dd']=(c2['ts_y']-c2['ts_x']).dt.days; print(f"      plausible-same-person gaps (days): {sorted(c2['dd'].tolist())[:12]}")

print("\n### Within-file repeat visits (same name+age appearing >1x)")
for lbl,X in [("2023FR",B23),("2023S3",B3),("2024",B24),("APACHE",A)]:
    g=X.groupby(['n','age']).size()
    print(f"  {lbl}: rows={len(X)} unique(name,age)={len(g)} repeated={int((g>1).sum())} max_repeats={int(g.max())} extra_rows={int((g-1).sum())}")

print("\n### 2023: are 'Form Responses 1' and 'Sheet3' concurrent parallel streams?")
d1=pd.to_datetime(fr23['Timestamp'],errors='coerce'); d2=pd.to_datetime(s3[0],errors='coerce')
s1d=set(d1.dt.date.dropna()); s2d=set(d2.dt.date.dropna())
print(f"  distinct days: FR={len(s1d)} S3={len(s2d)} shared days={len(s1d&s2d)}")
print(f"  FR-only days={len(s1d-s2d)} S3-only days={len(s2d-s1d)}")
both=sorted(s1d&s2d)[:10]; print("  sample shared days:",both)
print("  hour-of-day means: FR=%.1f S3=%.1f"%(d1.dt.hour.mean(),d2.dt.hour.mean()))
print("  FR hour hist:",dict(d1.dt.hour.value_counts().sort_index()))
print("  S3 hour hist:",dict(d2.dt.hour.value_counts().sort_index()))
print("\n  On shared days, do the same collectors submit to BOTH?")
f=pd.DataFrame({'d':d1.dt.date,'e':fr23['Email Address'].astype(str).str.lower().str.strip()})
g=pd.DataFrame({'d':d2.dt.date,'e':s3[2].astype(str).str.lower().str.strip()})
mm=f.merge(g,on=['d','e']).drop_duplicates()
print(f"  (day,collector) pairs present in both streams: {len(mm)}")
print("  monthly counts FR:",dict(d1.dt.to_period('M').value_counts().sort_index().items()))
print("  monthly counts S3:",dict(d2.dt.to_period('M').value_counts().sort_index().items()))
print("  monthly counts 24:",dict(pd.to_datetime(fr24['Timestamp'],errors='coerce').dt.to_period('M').value_counts().sort_index().items()))
