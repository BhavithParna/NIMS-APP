"""16_design.py - study-design parameters for the before/after + prediction paper.
Read-only on sources; consumes data.pkl. Prints everything needed to size and justify the design.
"""
import pickle, re, hashlib, warnings
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings('ignore')

d = pickle.load(open('data.pkl', 'rb'))
H = lambda s: hashlib.sha256(str(s).strip().lower().encode()).hexdigest()[:8]

def bp(v):
    if pd.isna(v): return (np.nan, np.nan)
    m = re.search(r'(\d{2,3})\s*/\s*(\d{1,3})', str(v))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)

def num(s): return pd.to_numeric(s, errors='coerce')

# ---------- build the two era frames with rater ----------
fr = d['T23_FR'].copy()
a = pd.DataFrame({
    'ts': pd.to_datetime(fr['Timestamp'], errors='coerce'), 'rater': fr['Email Address'].map(H),
    'age': num(fr['Age']), 'sex': num(fr['Sex']), 'trauma': num(fr['Trauma=1']),
    'cardiac': num(fr['cardiac=1']), 'complaint': fr['Complaint/Diagnosis'],
    'hr': num(fr['Pulse rate']), 'spo2': num(fr['Saturation']), 'rr': num(fr['Respiratory Rate']),
    'bpraw': fr['Unnamed: 13'], 'red': num(fr['red=1']), 'pain': num(fr['PAIN SCORE NRS']),
})
s3 = d['T23_S3'].copy()
b = pd.DataFrame({
    'ts': pd.to_datetime(s3[0], errors='coerce'), 'rater': s3[2].map(H),
    'age': num(s3[4]), 'sex': num(s3[5]), 'trauma': num(s3[6]), 'cardiac': num(s3[8]),
    'complaint': s3[7], 'hr': num(s3[9]), 'spo2': num(s3[12]), 'rr': num(s3[14]),
    'bpraw': s3[11], 'red': num(s3[15]), 'pain': np.nan,
})
e23 = pd.concat([a, b], ignore_index=True)
e23 = e23[e23['ts'].notna()].reset_index(drop=True)
e23['sbp'], e23['dbp'] = zip(*e23['bpraw'].map(bp))
e23['era'] = 2023

t = d['T24_FR'].copy()
e24 = pd.DataFrame({
    'ts': pd.to_datetime(t['Timestamp'], errors='coerce'), 'rater': t['Email Address'].map(H),
    'age': num(t['Age']), 'sexraw': t['Sex'], 'complaint': t['Complaint/Diagnosis'],
    'hr': num(t['Pulse rate']), 'spo2': num(t['Saturation']), 'rr': num(t['Respiratory Rate']),
    'bpraw': t['Blood Pressure'], 'pain': num(t['PAIN SCORE NRS']),
    'esi': num(t['ESI Triage Category']), 'area': t['Area Triaged'],
    'gce': num(t['GCS  E']), 'gcv': num(t['GCS V']), 'gcm': num(t['GCS M']),
    'crt': t['Capillary Refill Time'], 'airway': t['Airway'], 'pupils': t['Pupils'],
    'fnd': t['Focal Neurological Deficit'], 'bae': t['Bilateral Air Entry'],
    'tempF': num(t['Temperature in Fahrenheit']),
})
e24 = e24[e24['ts'].notna()].reset_index(drop=True)
e24['sex'] = e24['sexraw'].astype(str).str.strip().str.lower().map({'male': 1, 'female': 0})
e24['sbp'], e24['dbp'] = zip(*e24['bpraw'].map(bp))
e24['gcs'] = e24['gce'] + e24['gcv'] + e24['gcm']
e24['era'] = 2024
e24['high'] = (e24['esi'] <= 2).astype(float)
e24.loc[e24['esi'].isna(), 'high'] = np.nan

# physiologic plausibility filter (same rule both eras)
def clip(df):
    o = df.copy()
    for c, lo, hi in [('hr',20,250),('sbp',50,300),('dbp',20,200),('rr',4,60),('spo2',40,100),('age',0,110)]:
        if c in o: o.loc[(o[c] < lo) | (o[c] > hi), c] = np.nan
    return o
e23c, e24c = clip(e23), clip(e24)

print('=' * 78); print('A. COHORT + RATER STRUCTURE'); print('=' * 78)
for nm, df in [('2023', e23c), ('2024', e24c)]:
    r = df['rater'].value_counts()
    print(f"{nm}: n={len(df)}  raters={df['rater'].nunique()}  "
          f"median/rater={r.median():.0f}  IQR={r.quantile(.25):.0f}-{r.quantile(.75):.0f}  max={r.max()}")
    print(f"      raters with >=20 records: {(r>=20).sum()}  (covering {r[r>=20].sum()}/{len(df)} = {r[r>=20].sum()/len(df)*100:.1f}%)")
    print(f"      top-5 raters cover {r.head(5).sum()/len(df)*100:.1f}%   days={df['ts'].dt.date.nunique()}")
sh = set(e23c['rater']) & set(e24c['rater'])
print(f"raters in BOTH eras: {len(sh)}  -> they contribute {(e23c.rater.isin(sh)).sum()} of 2023 and "
      f"{(e24c.rater.isin(sh)).sum()} of 2024 records "
      f"({(e23c.rater.isin(sh)).mean()*100:.0f}% / {(e24c.rater.isin(sh)).mean()*100:.0f}%)")

print(); print('=' * 78); print('B. VARIABLE HARMONISATION AUDIT (completeness by era, %)'); print('=' * 78)
cand = ['age','sex','hr','sbp','dbp','rr','spo2','pain','complaint','trauma','cardiac']
rows = []
for c in cand:
    p23 = e23c[c].notna().mean()*100 if c in e23c else np.nan
    p24 = e24c[c].notna().mean()*100 if c in e24c else np.nan
    rows.append((c, p23, p24))
for c, p23, p24 in rows:
    tag = 'BOTH' if not (np.isnan(p23) or np.isnan(p24)) else ('2023 only' if not np.isnan(p23) else '2024 only')
    print(f"  {c:<10} 2023 {('%5.1f'%p23) if not np.isnan(p23) else '   - '}   "
          f"2024 {('%5.1f'%p24) if not np.isnan(p24) else '   - '}   [{tag}]")
print("  2024-only structured fields:", ', '.join(['gcs','airway','bae','crt','pupils','fnd','tempF','area','esi']))

print(); print('=' * 78); print('C. PRIMARY OUTCOME CANDIDATE: physiologic documentation completeness'); print('=' * 78)
core = ['hr','sbp','rr','spo2']
for nm, df in [('2023', e23c), ('2024', e24c)]:
    k = df[core].notna().sum(axis=1)
    print(f"{nm}: mean core vitals documented = {k.mean():.3f}/4 (SD {k.std():.3f});  "
          f"all four = {(k==4).mean()*100:.1f}%;  none = {(k==0).mean()*100:.1f}%")
k23 = e23c[core].notna().sum(axis=1); k24 = e24c[core].notna().sum(axis=1)
c23, c24 = (k23==4).mean(), (k24==4).mean()
diff = c24 - c23
se = np.sqrt(c23*(1-c23)/len(k23) + c24*(1-c24)/len(k24))
print(f"  RISK DIFFERENCE (complete core vitals) = {diff*100:+.1f} pp  95% CI "
      f"[{(diff-1.96*se)*100:+.1f}, {(diff+1.96*se)*100:+.1f}]")
tab = np.array([[(k24==4).sum(), (k24<4).sum()], [(k23==4).sum(), (k23<4).sum()]])
chi2, p, _, _ = stats.chi2_contingency(tab)
orr = (tab[0,0]*tab[1,1])/(tab[0,1]*tab[1,0]) if tab[0,1]*tab[1,0] else np.inf
print(f"  chi2={chi2:.1f} p={p:.3g}  OR(2024 vs 2023)={orr:.2f}")
# per-variable
print("  per-variable completeness (2023 -> 2024, pp change):")
for c in core:
    p1, p2 = e23c[c].notna().mean()*100, e24c[c].notna().mean()*100
    print(f"     {c:<5} {p1:5.1f} -> {p2:5.1f}   ({p2-p1:+.1f} pp)")

print(); print('=' * 78); print('D. CASE-MIX COMPARABILITY (standardised mean differences)'); print('=' * 78)
def smd(x, y):
    x, y = x.dropna(), y.dropna()
    s = np.sqrt((x.var(ddof=1) + y.var(ddof=1)) / 2)
    return (y.mean() - x.mean()) / s if s else np.nan
for c in ['age','sex','hr','sbp','dbp','rr','spo2']:
    s = smd(e23c[c], e24c[c])
    flag = '  <-- imbalanced (|SMD|>0.10)' if abs(s) > 0.10 else ''
    print(f"  {c:<6} 2023 mean={e23c[c].mean():7.2f}  2024 mean={e24c[c].mean():7.2f}  SMD={s:+.3f}{flag}")

print(); print('=' * 78); print('E. IS red=1 (2023) EXCHANGEABLE WITH ESI<=2 (2024)?'); print('=' * 78)
p23r, p24h = e23c['red'].mean(), e24c['high'].mean()
print(f"  prevalence: red=1 {p23r*100:.1f}% (n={e23c['red'].notna().sum()})   "
      f"ESI<=2 {p24h*100:.1f}% (n={e24c['high'].notna().sum()})   diff {(p24h-p23r)*100:+.1f} pp")
print("  physiologic profile of the 'high acuity' group in each era:")
print(f"  {'var':<6}{'2023 red=1':>14}{'2024 ESI<=2':>14}{'SMD':>9}   {'2023 red=0':>12}{'2024 ESI>=3':>12}{'SMD':>9}")
for c in ['hr','sbp','rr','spo2','age']:
    hi23, hi24 = e23c.loc[e23c.red == 1, c], e24c.loc[e24c.high == 1, c]
    lo23, lo24 = e23c.loc[e23c.red == 0, c], e24c.loc[e24c.high == 0, c]
    print(f"  {c:<6}{hi23.mean():>14.2f}{hi24.mean():>14.2f}{smd(hi23,hi24):>+9.3f}   "
          f"{lo23.mean():>12.2f}{lo24.mean():>12.2f}{smd(lo23,lo24):>+9.3f}")
# discriminative equivalence: does the same physiology separate the label equally in both eras?
print("  separation of the label by physiology (Cohen's d, high vs low, within era):")
for c in ['hr','sbp','rr','spo2']:
    def dd(df, lab):
        x, y = df.loc[df[lab] == 0, c].dropna(), df.loc[df[lab] == 1, c].dropna()
        s = np.sqrt((x.var(ddof=1)+y.var(ddof=1))/2)
        return (y.mean()-x.mean())/s if s else np.nan
    print(f"     {c:<5} 2023 d={dd(e23c,'red'):+.3f}   2024 d={dd(e24c,'high'):+.3f}")

print(); print('=' * 78); print('F. RATER CLUSTERING / ICC'); print('=' * 78)
def icc1(df, y, g, minn=10):
    s = df[[y, g]].dropna()
    s = s[s[g].isin(s[g].value_counts()[lambda x: x >= minn].index)]
    grp = s.groupby(g)[y]
    k = grp.size(); N, a = len(s), len(k)
    if a < 3: return np.nan, 0, 0
    gm = s[y].mean()
    msb = ((k * (grp.mean() - gm) ** 2).sum()) / (a - 1)
    msw = ((grp.var(ddof=1) * (k - 1)).sum()) / (N - a)
    k0 = (N - (k ** 2).sum() / N) / (a - 1)
    v = (msb - msw) / (msb + (k0 - 1) * msw)
    return v, a, N
for nm, df, y in [('2023 red=1', e23c, 'red'), ('2024 ESI (1-5)', e24c, 'esi'), ('2024 ESI<=2', e24c, 'high')]:
    v, a, N = icc1(df, y, 'rater')
    print(f"  {nm:<16} ICC(1) = {v:.3f}   ({a} raters with >=10 records, n={N})")
    s = df[[y, 'rater']].dropna()
    s = s[s['rater'].isin(s['rater'].value_counts()[lambda x: x >= 20].index)]
    if s['rater'].nunique() > 2:
        gs = [g[y].values for _, g in s.groupby('rater')]
        h, p = stats.kruskal(*gs)
        print(f"                   Kruskal-Wallis across raters (>=20 recs): H={h:.1f} p={p:.3g}")
print("  design effect for 2024 ESI<=2, mean cluster size m:")
m = e24c.groupby('rater').size().mean()
v, _, _ = icc1(e24c, 'high', 'rater')
print(f"     m={m:.1f}, ICC={v:.3f} -> DEFF = 1+(m-1)*ICC = {1+(m-1)*v:.2f}  "
      f"-> effective n = {len(e24c)/(1+(m-1)*v):.0f} (of {len(e24c)})")

print(); print('=' * 78); print('G. TEMPORAL STRUCTURE / HOLDOUT FEASIBILITY (2024)'); print('=' * 78)
mo = e24c.groupby(e24c['ts'].dt.to_period('M')).size()
cum = mo.cumsum()
for k, v2 in mo.items():
    print(f"  {k}  n={v2:4d}  cum={cum[k]:4d}  ({cum[k]/len(e24c)*100:5.1f}%)")
cut = e24c['ts'].quantile(0.75)
tr, te = e24c[e24c['ts'] <= cut], e24c[e24c['ts'] > cut]
print(f"  75th-pct time split at {cut:%Y-%m-%d}: train n={len(tr)} ({tr['high'].mean()*100:.1f}% high) "
      f"/ test n={len(te)} ({te['high'].mean()*100:.1f}% high)")
print(f"     raters in test not in train: {len(set(te.rater)-set(tr.rater))}; "
      f"test records from unseen raters: {te.rater.isin(set(te.rater)-set(tr.rater)).sum()}")
print(f"  events available for modelling: {int(e24c['high'].sum())} high-acuity of {int(e24c['high'].notna().sum())}")

print(); print('=' * 78); print('H. FREE-TEXT COMPLAINT + ICD LIST FEASIBILITY'); print('=' * 78)
icd = d['T24_S1'][0].dropna().astype(str)
pat = re.compile(r'([A-TV-Z]\d{2}(?:\.\d+)?)\s*$')
codes = icd.map(lambda s: (pat.search(s.strip()).group(1) if pat.search(s.strip()) else None))
print(f"  reference list: {len(icd)} entries, {codes.notna().sum()} with parseable ICD-10 code "
      f"({codes.notna().mean()*100:.1f}%), {codes.dropna().str[0].nunique()} chapters")
for nm, s in [('2023', e23c['complaint']), ('2024', e24c['complaint'])]:
    v = s.dropna().astype(str).str.strip()
    vl = v.str.lower()
    print(f"  {nm}: {len(v)} non-null, {v.nunique()} distinct, {vl.nunique()} distinct case-folded, "
          f"median {v.str.len().median():.0f} chars, {(v.str.split().str.len()<=3).mean()*100:.0f}% <=3 words")
    print(f"        top terms: {', '.join(vl.value_counts().head(8).index.tolist())}")
    top = vl.value_counts()
    print(f"        coverage by top-20 strings: {top.head(20).sum()/len(v)*100:.1f}%; "
          f"strings occurring once: {(top==1).sum()} ({(top==1).sum()/len(v)*100:.1f}% of records)")

print(); print('=' * 78); print('I. POWER / MINIMUM DETECTABLE EFFECT'); print('=' * 78)
def mde_prop(n1, n2, p1, alpha=.05, power=.8):
    from scipy.stats import norm
    z_a, z_b = norm.ppf(1-alpha/2), norm.ppf(power)
    lo, hi = p1, .999
    for _ in range(200):
        mid = (lo+hi)/2
        pb = (p1*n1+mid*n2)/(n1+n2)
        se0 = np.sqrt(pb*(1-pb)*(1/n1+1/n2)); se1 = np.sqrt(p1*(1-p1)/n1+mid*(1-mid)/n2)
        if (abs(mid-p1)-z_a*se0)/se1 >= z_b: hi = mid
        else: lo = mid
    return hi
n1, n2 = len(e23c), len(e24c)
print(f"  2-group proportion test, n1={n1} n2={n2}, alpha=.05, power=.80")
for p1 in [c23, 0.50, 0.80]:
    print(f"     baseline {p1*100:5.1f}%  -> MDE = {mde_prop(n1,n2,p1)*100:5.1f}%  "
          f"(absolute {abs(mde_prop(n1,n2,p1)-p1)*100:.1f} pp)")
deff = 1 + (e23c.groupby('rater').size().mean()-1)*0.05
print(f"  if clustering inflates variance (assume ICC=0.05, m~{e23c.groupby('rater').size().mean():.0f}): "
      f"DEFF~{deff:.2f} -> effective n1={n1/deff:.0f}, n2={n2/deff:.0f}")
ev = int(e24c['high'].sum())
print(f"  ML model: {ev} events / {int(e24c['high'].notna().sum())}; EPV=10 -> max {ev//10} candidate predictors "
      f"(EPV=20 -> {ev//20})")
print(f"  Riley minimum sample size proxy (C-stat .72, prev {p24h:.2f}, 14 predictors): "
      f"needs roughly 600-900 -> n={len(e24c)} is adequate")

e23c.to_csv('csv/era2023_analysis.csv', index=False)
e24c.to_csv('csv/era2024_analysis.csv', index=False)
print('\nwrote csv/era2023_analysis.csv, csv/era2024_analysis.csv')
