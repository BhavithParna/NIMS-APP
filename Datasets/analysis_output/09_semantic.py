import pandas as pd, numpy as np, pickle, re
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
def bp(v):
    if pd.isna(v): return (np.nan,np.nan)
    m=re.search(r'(\d{2,3})\s*/\s*(\d{2,3})',str(v))
    return (float(m.group(1)),float(m.group(2))) if m else (np.nan,np.nan)

print("="*90,"\n### BLOOD PRESSURE parsing + SHOCK INDEX validation")
sets={'2023_FR':(D['T23_FR'],'Unnamed: 13','Pulse rate','SI'),
      '2023_S3':(D['T23_S3'],11,9,10)}
for lbl,(df,bpc,hrc,sic) in sets.items():
    p=df[bpc].map(bp); sbp=p.map(lambda t:t[0]); dbp=p.map(lambda t:t[1])
    hr=pd.to_numeric(df[hrc],errors='coerce'); si=pd.to_numeric(df[sic],errors='coerce')
    ok=sbp.notna()
    print(f"\n{lbl}: BP parseable {ok.sum()}/{df[bpc].notna().sum()} ({ok.sum()/max(df[bpc].notna().sum(),1):.1%}) unparsed examples: {list(df.loc[df[bpc].notna()&~ok,bpc].astype(str).unique()[:6])}")
    print(f"   SBP med={sbp.median():.0f} range {sbp.min():.0f}-{sbp.max():.0f} | DBP med={dbp.median():.0f} range {dbp.min():.0f}-{dbp.max():.0f}")
    print(f"   impossible: SBP<=DBP: {int((sbp<=dbp).sum())} | SBP<60: {int((sbp<60).sum())} | SBP>250: {int((sbp>250).sum())}")
    shock=hr/sbp
    m=si.notna()&shock.notna()
    for thr in [0.7,0.8,0.9,1.0]:
        pred=(shock[m]>=thr).astype(int); print(f"   SI col vs (HR/SBP>={thr}): agreement={ (pred==si[m]).mean():.3f}  (n={m.sum()})")
    print(f"   SI col values: {dict(si.value_counts(dropna=False).head(4))}; SI non-null {si.notna().sum()}/{len(df)}")

df=D['T24_FR']
p=df['Blood Pressure'].map(bp); sbp=p.map(lambda t:t[0]); dbp=p.map(lambda t:t[1])
ok=sbp.notna(); nn=df['Blood Pressure'].notna().sum()
print(f"\n2024_FR: BP parseable {ok.sum()}/{nn} ({ok.sum()/nn:.1%}) unparsed: {list(df.loc[df['Blood Pressure'].notna()&~ok,'Blood Pressure'].astype(str).unique()[:10])}")
print(f"   SBP med={sbp.median():.0f} range {sbp.min():.0f}-{sbp.max():.0f} | DBP med={dbp.median():.0f} range {dbp.min():.0f}-{dbp.max():.0f} | SBP<=DBP:{int((sbp<=dbp).sum())}")

print("\n"+"="*90,"\n### 2024 GCS internal consistency")
E=pd.to_numeric(df['GCS  E'],errors='coerce');V=pd.to_numeric(df['GCS V'],errors='coerce');M=pd.to_numeric(df['GCS M'],errors='coerce')
tot=E+V+M
print(f"  E range {E.min()}-{E.max()} (valid 1-4) out-of-range={int(((E<1)|(E>4)).sum())}")
print(f"  V range {V.min()}-{V.max()} (valid 1-5) out-of-range={int(((V<1)|(V>5)).sum())}  non-numeric V values: {sorted(set(df['GCS V'].astype(str))-set(df['GCS V'].map(lambda x: str(x) if pd.to_numeric(pd.Series([x]),errors='coerce').notna()[0] else None)))[:6]}")
print(f"  M range {M.min()}-{M.max()} (valid 1-6) out-of-range={int(((M<1)|(M>6)).sum())}")
print(f"  derived total: min={tot.min()} max={tot.max()} median={tot.median()} | <15: {int((tot<15).sum())} ({(tot<15).mean():.1%})")
print(f"  explicit 'GCS' col filled only {df['GCS'].notna().sum()} times -> redundant/derivable")

print("\n"+"="*90,"\n### APACHE IV score fields")
ap=D['AP1'].iloc[:78]
sc=ap['APACHE IV SCORE'].astype(str).str.extract(r'(\d+)\s*/\s*(\d+)')
aps=ap['APS SCORE'].astype(str).str.extract(r'(\d+)\s*/\s*(\d+)')
S=pd.to_numeric(sc[0]); Smax=pd.to_numeric(sc[1]); A=pd.to_numeric(aps[0]); Amax=pd.to_numeric(aps[1])
print(f"  APACHE IV numerator: {S.min()}-{S.max()} median {S.median()}; denominators: {dict(Smax.value_counts())}")
print(f"  APS numerator: {A.min()}-{A.max()} median {A.median()}; denominators: {dict(Amax.value_counts())}")
print(f"  APACHE-IV >= APS always? {(S>=A).all()}  cases where APS>APACHE: {int((A>S).sum())}")
diff=S-A
print(f"  (APACHE IV - APS) distribution: min={diff.min()} max={diff.max()} median={diff.median()}")
age=ap.iloc[:,2]
print(f"  corr(diff, age) = {diff.corr(age):.3f}  <- APACHE IV = APS + age points + chronic-health points")
mort=ap['Estimated mortality rate']
los=pd.to_numeric(ap['Estimated length of stay'].astype(str).str.extract(r'([\d.]+)')[0])
print(f"  Est mortality: {mort.min()}-{mort.max()} median {mort.median():.3f} (proportion)")
print(f"  corr(APACHE IV score, est mortality) = {S.corr(mort):.4f} (spearman {S.corr(mort,method='spearman'):.4f})")
print(f"  corr(APS, est mortality) = {A.corr(mort):.4f}")
print(f"  Est LOS days: {los.min()}-{los.max()} median {los.median()}; corr with score={S.corr(los):.3f}")
print("  >>> mortality & LOS are MODEL OUTPUTS of the score, not observed outcomes -> leakage if used as targets")

print("\n"+"="*90,"\n### APACHE impossible / suspicious values")
print(f"  WBC col: min={ap['WBC(x1000/mm3) '].min()} max={ap['WBC(x1000/mm3) '].max()} -> values <100: {int((ap['WBC(x1000/mm3) ']<100).sum())}, >1000: {int((ap['WBC(x1000/mm3) ']>1000).sum())} => MIXED UNITS")
print(f"  Urea labelled mEq/L but ranges {ap['   Urea(mEq/L) '].min()}-{ap['   Urea(mEq/L) '].max()} (mg/dL scale)")
print(f"  Albumin labelled g/L but ranges {ap['   Albumin(g/L) '].min()}-{ap['   Albumin(g/L) '].max()} (g/dL scale)")
print(f"  GCS V: {dict(ap['V'].value_counts())} -> 'T' = intubated, not scoreable")
print(f"  Vasopressors col dtype mixed: {dict(ap['Vasopressors'].value_counts().head(8))}")
print(f"  Outcome column: {ap['   Outcome'].notna().sum()} non-null of 78  ** NO OUTCOME RECORDED **")
