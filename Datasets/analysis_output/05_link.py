import pandas as pd, numpy as np, pickle, re, hashlib
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
def H(x): return hashlib.sha256(str(x).encode()).hexdigest()[:8]
def nm(s): return re.sub(r'[^a-z]','',str(s).lower())
def crn(v):
    if pd.isna(v): return None
    s=re.sub(r'\D','',str(v))
    return s if s else None

print("### Sheet2 subset of Sheet3 (by timestamp)")
s2,s3=D['T23_S2'],D['T23_S3']
t2=set(s2.iloc[:,0].dropna().astype(str)); t3=set(s3[0].dropna().astype(str))
print(f"  Sheet2 ts={len(t2)} Sheet3 ts={len(t3)} overlap={len(t2&t3)} -> Sheet2 subset: {t2<=t3}")

print("\n### Timestamp coverage of each response table")
fr23=D['T23_FR']; fr24=D['T24_FR']
for nmm,ser in [("2023 FormResp",fr23['Timestamp']),("2023 Sheet3",s3[0]),("2024 FormResp",fr24['Timestamp'])]:
    s=pd.to_datetime(ser,errors='coerce').dropna()
    print(f"  {nmm:15s} n={len(s):5d}  {s.min()}  ->  {s.max()}  span={(s.max()-s.min()).days}d  uniq_days={s.dt.date.nunique()}")
    print(f"      by year: {dict(s.dt.year.value_counts().sort_index())}")

print("\n### APACHE date column")
ap=D['AP1'].iloc[:78]
d=ap.iloc[:,0].astype(str)
print("  raw examples:",list(d[:3]),list(d[-3:]))
dates=d.str.extract(r'(\d{2}-\d{2}-\d{2})')[0]
dt=pd.to_datetime(dates,format='%d-%m-%y',errors='coerce')
print(f"  parsed {dt.notna().sum()}/78  range {dt.min()} -> {dt.max()}  uniq days={dt.dt.date.nunique()}")

print("\n### CR NUMBER LINKAGE (the key join test)")
ap_cr={crn(v) for v in ap.iloc[:,4] if crn(v)}
t24_cr={crn(v) for v in fr24['CR Number'] if crn(v)}
t23_cr_col=[c for c in fr23.columns if 'CR' in str(c).upper()]
t23_cr=set()
for c in t23_cr_col: t23_cr|={crn(v) for v in fr23[c] if crn(v)}
print(f"  APACHE CRNos: {len(ap_cr)} unique (of 78 rows)")
print(f"  2024 CR Numbers: {len(t24_cr)} unique (of {fr24['CR Number'].notna().sum()} non-null / {len(fr24)} rows)")
print(f"  2023 CR cols {t23_cr_col}: {len(t23_cr)} unique")
print(f"  >>> APACHE ∩ 2024 = {len(ap_cr & t24_cr)}   APACHE ∩ 2023 = {len(ap_cr & t23_cr)}   2023 ∩ 2024 = {len(t23_cr & t24_cr)}")
print("  APACHE CR sample (hashed):",[H(x) for x in list(ap_cr)[:3]], "lens:",sorted({len(x) for x in ap_cr}))
print("  2024   CR sample lens:",sorted({len(x) for x in t24_cr})[:10])
# prefix structure
print("  APACHE CR prefixes:",pd.Series([x[:8] for x in ap_cr]).value_counts().head(5).to_dict())
print("  2024   CR prefixes:",pd.Series([x[:8] for x in t24_cr]).value_counts().head(5).to_dict())

print("\n### NAME LINKAGE")
ap_n={nm(v) for v in ap.iloc[:,1] if nm(v)}
n23={nm(v) for v in fr23['Name '] if nm(v)}
n23b={nm(v) for v in s3[3] if nm(v)}
n24={nm(v) for v in fr24['Name '] if nm(v)}
print(f"  unique normalized names: APACHE={len(ap_n)} 2023FR={len(n23)} 2023S3={len(n23b)} 2024={len(n24)}")
print(f"  APACHE∩2024={len(ap_n&n24)} APACHE∩2023FR={len(ap_n&n23)} APACHE∩2023S3={len(ap_n&n23b)}")
print(f"  2023FR∩2024={len(n23&n24)}  2023FR∩2023S3={len(n23&n23b)}  2023S3∩2024={len(n23b&n24)}")
if ap_n&n24: print("   matched names (hashed):",[H(x) for x in list(ap_n&n24)][:10])

print("\n### EMAIL / COLLECTOR structure")
for lbl,ser in [("2023FR",fr23['Email Address']),("2023S3",s3[2]),("2024",fr24['Email Address'])]:
    vc=ser.dropna().astype(str).str.strip().str.lower().value_counts()
    print(f"  {lbl}: {len(vc)} distinct collectors; top counts {list(vc.values[:8])}")
    print(f"      hashed ids: {[H(x) for x in vc.index[:8]]}")
e23=set(fr23['Email Address'].dropna().astype(str).str.lower().str.strip())
e23b=set(s3[2].dropna().astype(str).str.lower().str.strip())
e24=set(fr24['Email Address'].dropna().astype(str).str.lower().str.strip())
print(f"  collector overlap: 2023FR∩2024={len(e23&e24)} of {len(e23)}/{len(e24)}; 2023FR∩2023S3={len(e23&e23b)}; 2023S3∩2024={len(e23b&e24)}")
