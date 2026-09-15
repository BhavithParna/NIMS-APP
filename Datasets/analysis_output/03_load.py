import pandas as pd, numpy as np, os, pickle
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
BASE="/home/bhavith/Documents/Datasets"; OUT=BASE+"/analysis_output"
D={}
D['AP1']=pd.read_excel(f"{BASE}/APACHE 4.xlsx",sheet_name="Sheet1",header=0)
D['AP2']=pd.read_excel(f"{BASE}/APACHE 4.xlsx",sheet_name="Sheet2",header=0)
D['T23_FR']=pd.read_excel(f"{BASE}/NIMS TRIAGE 2023.xlsx",sheet_name="Form Responses 1",header=0)
D['T23_S2']=pd.read_excel(f"{BASE}/NIMS TRIAGE 2023.xlsx",sheet_name="Sheet2",header=0)
D['T23_S3']=pd.read_excel(f"{BASE}/NIMS TRIAGE 2023.xlsx",sheet_name="Sheet3",header=None)
D['T23_S1']=pd.read_excel(f"{BASE}/NIMS TRIAGE 2023.xlsx",sheet_name="Sheet1",header=None)
D['T24_FR']=pd.read_excel(f"{BASE}/NIMS TRIAGE 2024 (Responses).xlsx",sheet_name="Form Responses 1",header=0)
D['T24_S1']=pd.read_excel(f"{BASE}/NIMS TRIAGE 2024 (Responses).xlsx",sheet_name="Sheet1",header=None)
for k,v in D.items():
    print(f"{k:8s} shape={v.shape}  all-null-cols={int(v.isna().all().sum())}  all-null-rows={int(v.isna().all(axis=1).sum())}")
pickle.dump(D,open(f"{OUT}/data.pkl","wb"))

print("\n### APACHE Sheet2 vs Sheet1 right-block alignment")
a=D['AP1']; b=D['AP2']
blk=a.iloc[:, 26:49].reset_index(drop=True)   # AA..AW
print("Sheet1 AA..AW cols:",list(blk.columns))
print("Sheet2 cols       :",list(b.columns))
print("names identical:", [str(x).strip() for x in blk.columns]==[str(x).strip() for x in b.columns])
n=min(len(blk),len(b))
eq=(blk.iloc[:n].astype(str).values==b.iloc[:n,:23].astype(str).values)
print(f"rows compared={n} cellwise-match={eq.mean():.4f}")
mismatch_rows=np.where(~eq.all(axis=1))[0]
print("first mismatching row idx:",mismatch_rows[:10])
if len(mismatch_rows):
    r=mismatch_rows[0]
    print("S1 row:",list(blk.iloc[r].values)[:12]); print("S2 row:",list(b.iloc[r].values)[:12])

print("\n### 2023 Form Responses: schema generations (non-null profile over row blocks)")
fr=D['T23_FR']
cols=list(fr.columns)
groups={'early(B..S)':cols[1:19],'mid(T..U)':cols[19:21],'late ABCDE(V..AX)':cols[21:]}
fr['_blk']=(np.arange(len(fr))//100)
for name,cs in groups.items():
    nn=fr.groupby('_blk')[cs].apply(lambda d: d.notna().any(axis=1).mean())
    print(f"{name:20s}", " ".join(f"{v:.2f}" for v in nn.values))
print("block index = rows/100, value = fraction of rows with ANY value in that column group")
