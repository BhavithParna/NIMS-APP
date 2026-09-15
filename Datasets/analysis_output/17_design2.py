"""17_design2.py - consequences of 16_design.py: within-rater before/after, ICC contrast with CIs,
information-breadth outcome, and complaint-abbreviation feasibility."""
import numpy as np, pandas as pd, warnings
from scipy import stats
warnings.filterwarnings('ignore')
rng = np.random.default_rng(20260820)

e23 = pd.read_csv('csv/era2023_analysis.csv', parse_dates=['ts'])
e24 = pd.read_csv('csv/era2024_analysis.csv', parse_dates=['ts'])
shared = sorted(set(e23.rater) & set(e24.rater))

print('=' * 78); print('J. INFORMATION BREADTH (not completeness) - the honest documentation outcome'); print('=' * 78)
# physiological DOMAINS assessable per encounter, using each era's own instrument
dom23 = pd.DataFrame({
    'circulation_hr': e23.hr.notna(), 'circulation_bp': e23.sbp.notna(),
    'breathing_rr': e23.rr.notna(), 'breathing_spo2': e23.spo2.notna(),
})
dom24 = pd.DataFrame({
    'circulation_hr': e24.hr.notna(), 'circulation_bp': e24.sbp.notna(),
    'breathing_rr': e24.rr.notna(), 'breathing_spo2': e24.spo2.notna(),
    'airway': e24.airway.notna(), 'breathing_bae': e24.bae.notna(),
    'circulation_crt': e24.crt.notna(), 'disability_gcs': e24.gcs.notna(),
    'disability_pupils': e24.pupils.notna(), 'disability_fnd': e24.fnd.notna(),
    'exposure_temp': e24.tempF.notna(), 'pain': e24.pain.notna(),
})
print(f"  2023 instrument captures {dom23.shape[1]} physiological items; 2024 captures {dom24.shape[1]}")
print(f"  items documented per encounter: 2023 {dom23.sum(1).mean():.2f} (SD {dom23.sum(1).std():.2f}) | "
      f"2024 {dom24.sum(1).mean():.2f} (SD {dom24.sum(1).std():.2f})")
print("  2024 per-item availability (items that DID NOT EXIST in 2023):")
for c in dom24.columns:
    if c not in dom23.columns:
        print(f"     {c:<20} {dom24[c].mean()*100:5.1f}%")
print("  -> 2023 availability for every one of these is 0% by construction (field absent from form).")
print("     This is an instrument-capability difference, NOT a behaviour difference. Describe; do not test.")

print(); print('=' * 78); print('K. WITHIN-RATER BEFORE/AFTER (the 19 clinicians who used both forms)'); print('=' * 78)
rows = []
for r in shared:
    a, b = e23[e23.rater == r], e24[e24.rater == r]
    if len(a) >= 15 and len(b) >= 15:
        rows.append((r, len(a), a.red.mean(), len(b), b.high.mean(),
                     a[['hr','sbp','rr','spo2']].notna().all(1).mean(),
                     b[['hr','sbp','rr','spo2']].notna().all(1).mean()))
w = pd.DataFrame(rows, columns=['rater','n23','red23','n24','high24','comp23','comp24'])
print(f"  raters with >=15 encounters in BOTH eras: {len(w)} "
      f"(covering {w.n23.sum()} 2023 and {w.n24.sum()} 2024 encounters)")
print(f"  paired high-acuity rate: 2023 {w.red23.mean()*100:.1f}% -> 2024 {w.high24.mean()*100:.1f}%")
d = w.high24 - w.red23
tt = stats.ttest_rel(w.high24, w.red23); wx = stats.wilcoxon(w.high24, w.red23)
ci = stats.t.interval(.95, len(d)-1, d.mean(), stats.sem(d))
print(f"     paired diff = {d.mean()*100:+.1f} pp, 95% CI [{ci[0]*100:+.1f}, {ci[1]*100:+.1f}], "
      f"paired t p={tt.pvalue:.3f}, Wilcoxon p={wx.pvalue:.3f}")
print(f"     between-rater SD of high-acuity rate: 2023 {w.red23.std():.3f} -> 2024 {w.high24.std():.3f}")
print(f"     range of high-acuity rate across raters: 2023 [{w.red23.min()*100:.0f}, {w.red23.max()*100:.0f}]% "
      f"-> 2024 [{w.high24.min()*100:.0f}, {w.high24.max()*100:.0f}]%")
lv = stats.levene(w.red23, w.high24, center='median')
print(f"     Levene test for equality of between-rater spread: W={lv.statistic:.2f} p={lv.pvalue:.3f}")
print(f"  paired core-vitals completeness: {w.comp23.mean()*100:.1f}% -> {w.comp24.mean()*100:.1f}% "
      f"(paired diff {(w.comp24-w.comp23).mean()*100:+.1f} pp, p={stats.ttest_rel(w.comp24,w.comp23).pvalue:.3f})")

print(); print('=' * 78); print('L. ICC CONTRAST WITH BOOTSTRAP CI (binary high-acuity label, both eras)'); print('=' * 78)
def icc1(df, y, g, minn=10):
    s = df[[y, g]].dropna()
    s = s[s[g].isin(s[g].value_counts()[lambda x: x >= minn].index)]
    grp = s.groupby(g)[y]; k = grp.size(); N, a = len(s), len(k)
    if a < 3: return np.nan
    gm = s[y].mean()
    msb = ((k * (grp.mean() - gm) ** 2).sum()) / (a - 1)
    msw = ((grp.var(ddof=1) * (k - 1)).sum()) / (N - a)
    k0 = (N - (k ** 2).sum() / N) / (a - 1)
    return (msb - msw) / (msb + (k0 - 1) * msw)

def boot_icc(df, y, g, B=2000):
    gs = df[g].dropna().unique(); out = []
    for _ in range(B):
        pick = rng.choice(gs, len(gs), replace=True)
        s = pd.concat([df[df[g] == p].assign(**{g: f'{p}_{i}'}) for i, p in enumerate(pick)])
        v = icc1(s, y, g)
        if not np.isnan(v): out.append(v)
    return np.percentile(out, [2.5, 97.5]), np.array(out)

i23, i24 = icc1(e23, 'red', 'rater'), icc1(e24, 'high', 'rater')
c23, b23 = boot_icc(e23[['red','rater']].dropna(), 'red', 'rater')
c24, b24 = boot_icc(e24[['high','rater']].dropna(), 'high', 'rater')
n = min(len(b23), len(b24)); diff = b24[:n] - b23[:n]
print(f"  2023 red=1     ICC(1) = {i23:.3f}  95% CI [{c23[0]:.3f}, {c23[1]:.3f}]")
print(f"  2024 ESI<=2    ICC(1) = {i24:.3f}  95% CI [{c24[0]:.3f}, {c24[1]:.3f}]")
print(f"  difference     = {i24-i23:+.3f}  95% CI [{np.percentile(diff,2.5):+.3f}, {np.percentile(diff,97.5):+.3f}]  "
      f"P(ICC24>ICC23) = {(diff>0).mean():.3f}")
sub23 = e23[e23.rater.isin(shared)]; sub24 = e24[e24.rater.isin(shared)]
print(f"  restricted to the {len(shared)} shared raters: "
      f"2023 ICC={icc1(sub23,'red','rater'):.3f}  2024 ICC={icc1(sub24,'high','rater'):.3f}")

print(); print('=' * 78); print('M. COMPLAINT ABBREVIATION STRUCTURE (what an NLP study would face)'); print('=' * 78)
abbr = {'rta':'road traffic accident','sob':'shortness of breath','cva':'cerebrovascular accident',
        'aki':'acute kidney injury','ckd':'chronic kidney disease','cad':'coronary artery disease',
        'copd':'COPD','uti':'urinary tract infection','gi':'gastrointestinal','loc':'loss of consciousness',
        'k/c/o':'known case of','c/o':'complains of','dm':'diabetes mellitus','htn':'hypertension',
        'acs':'acute coronary syndrome','cld':'chronic liver disease','sdh':'subdural haematoma',
        'ich':'intracranial haemorrhage','mi':'myocardial infarction','ugi':'upper gastrointestinal'}
for nm, s in [('2023', e23.complaint), ('2024', e24.complaint)]:
    v = s.dropna().astype(str).str.lower()
    hit = v.apply(lambda x: any(re.search(rf'\b{re.escape(a)}\b', x) for a in abbr) if (re := __import__('re')) else False)
    toks = v.str.findall(r"[a-z/]{2,}").explode().dropna()
    print(f"  {nm}: {hit.mean()*100:.1f}% of records contain >=1 of the 20 commonest abbreviations; "
          f"{toks.nunique()} distinct tokens, {(toks.value_counts()==1).sum()} appear once")
    print(f"        records with '?' (diagnostic uncertainty): {v.str.contains(r'\?').mean()*100:.1f}%; "
          f"with a digit: {v.str.contains(r'\d').mean()*100:.1f}%")
print("  -> exact string match to the ICD list is hopeless; a chapter/category-level mapping with an")
print("     abbreviation lexicon + human adjudication is the only defensible design.")

print(); print('=' * 78); print('N. SANITY: 2023 vestigial ABCDE columns'); print('=' * 78)
print("  (from 08_profile) 19 right-edge ABCDE columns filled in 4-5 of 1311 2023 records = "
      f"{5/1311*100:.2f}% -> exclude these records from any breadth comparison or note as negligible.")
