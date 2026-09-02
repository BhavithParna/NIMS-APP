import pandas as pd, numpy as np, pickle
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
def norm(df):
    o=df.copy()
    for c in o.columns:
        o[c]=o[c].map(lambda v: '' if pd.isna(v) else (f"{float(v):.6g}" if isinstance(v,(int,float,np.number)) else str(v).strip()))
    return o
print("### A. APACHE Sheet2 == Sheet1[AA:AW] ?")
a,b=D['AP1'],D['AP2']
blk=norm(a.iloc[:,26:49]).reset_index(drop=True); b2=norm(b.iloc[:,:23]).reset_index(drop=True)
n=min(len(blk),len(b2)); eq=blk.iloc[:n].values==b2.iloc[:n].values
print(f"  rows {len(blk)} vs {len(b2)}; cellwise match over first {n} rows = {eq.mean():.4f}")
bad=np.where(~eq.all(axis=1))[0]
print("  mismatching row idxs:",bad[:20])
for r in bad[:3]:
    d=[(blk.columns[j],blk.iloc[r,j],b2.iloc[r,j]) for j in range(23) if not eq[r,j]]
    print(f"   row{r}:",d)
print("  Sheet1 rows 78-79 (beyond Sheet2):"); print(a.iloc[78:80,[0,1,2,26,38,40]].to_string())

print("\n### B. 2023 Sheet2 vs Sheet3")
s2,s3=D['T23_S2'],D['T23_S3']
s3c=s3.copy(); s3c.columns=list(s2.columns)[:s3.shape[1]]+[f"x{i}" for i in range(s3.shape[1]-s2.shape[1])] if s3.shape[1]>s2.shape[1] else list(s2.columns)[:s3.shape[1]]
n=min(len(s2),len(s3c)); k=min(s2.shape[1],s3c.shape[1])
eq=norm(s2.iloc[:n,:k]).values==norm(s3c.iloc[:n,:k]).values
print(f"  Sheet2 {s2.shape} Sheet3 {s3.shape}; first {n} rows x {k} cols match={eq.mean():.4f}")
print("  -> Sheet2 is prefix of Sheet3:", eq.mean()>0.99)
print("  Sheet3 timestamp range:", s3[0].min(), "->", s3[0].max())
print("  Sheet2 timestamp range:", s2.iloc[:,0].min(), "->", s2.iloc[:,0].max())

print("\n### C. 2023 Form Responses schema generations per row")
fr=D['T23_FR']; cols=list(fr.columns)
early=cols[1:19]; late=cols[19:]
fr2=fr.copy()
fr2['_early']=fr[early].notna().sum(axis=1); fr2['_late']=fr[late].notna().sum(axis=1)
late_rows=fr2.index[fr2['_late']>0]
print("  rows with ANY late-schema value:",len(late_rows), list(late_rows)[:40])
print("  their timestamps:"); print(fr.loc[late_rows,cols[0]].to_string()[:1200])
print("  Timestamp range whole sheet:",fr[cols[0]].min(),"->",fr[cols[0]].max())

print("\n### D. 2023 FR vs Sheet3 overlap (same patients?)")
fr_keys=set(zip(fr[cols[0]].astype(str),fr['Name '].astype(str).str.strip().str.lower()))
s3_keys=set(zip(s3[0].astype(str),s3[3].astype(str).str.strip().str.lower()))
print("  FR rows",len(fr_keys),"S3 rows",len(s3_keys),"intersection(ts+name):",len(fr_keys&s3_keys))
fr_ts=set(fr[cols[0]].dropna().astype(str)); s3_ts=set(s3[0].dropna().astype(str))
print("  timestamp-only intersection:",len(fr_ts&s3_ts))

print("\n### E. Disease reference lists (Sheet1 in both triage files)")
l23=D['T23_S1'][0].astype(str); l24=D['T24_S1'][0].astype(str)
print("  2023 n=",len(l23)," 2024 n=",len(l24)," identical prefix:",(l23.values[:min(len(l23),len(l24))]==l24.values[:min(len(l23),len(l24))]).mean())
print("  set overlap:",len(set(l23)&set(l24)),"only23:",len(set(l23)-set(l24)),"only24:",len(set(l24)-set(l23)))
print("  samples:",list(l24[:3]),"|",list(l24[-3:]))
