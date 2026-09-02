"""18_mor.py - the core estimand for the proposed paper:
how much of the high-acuity designation is patient physiology, and how much is which clinician?
Random-intercept logistic model -> between-rater variance, ICC, Median Odds Ratio.
Plus a feasibility check of the temporal-holdout prediction pipeline with full metrics."""
import numpy as np, pandas as pd, warnings
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
warnings.filterwarnings('ignore')
rng = np.random.default_rng(20260820)

df = pd.read_csv('csv/era2024_analysis.csv', parse_dates=['ts'])
df = df[df.high.notna()].reset_index(drop=True)

# triage-time predictors only. No Area Triaged, no interventions, no disposition.
def yn(s): return s.astype(str).str.strip().str.lower().isin(['yes','y','present','abnormal','sluggish','1']).astype(float)
df['crt_slow'] = df.crt.astype(str).str.contains(r'>\s*3|slow|delay', case=False, na=False).astype(float)
df['airway_compromised'] = (~df.airway.astype(str).str.contains('patent', case=False, na=False)).astype(float)
df['fnd_pos'] = yn(df.fnd)
df['bae_abn'] = (~df.bae.astype(str).str.contains('bilateral|equal|present|yes', case=False, na=False)).astype(float)
df['pupils_abn'] = (~df.pupils.astype(str).str.contains('bertl|equal|reactive', case=False, na=False)).astype(float)
df['tempC'] = np.where(df.tempF.between(90, 110), (df.tempF - 32) * 5 / 9,
              np.where(df.tempF.between(34, 43), df.tempF, np.nan))
df['si'] = df.hr / df.sbp
P = ['age','sex','hr','sbp','dbp','rr','spo2','tempC','pain','gcs','si',
     'crt_slow','airway_compromised','fnd_pos','bae_abn','pupils_abn']
X = df[P].astype(float); y = df.high.values.astype(int); g = df.rater.values

print('=' * 78); print('O. VARIANCE DECOMPOSITION: patient physiology vs which clinician'); print('=' * 78)
try:
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    Xi = pd.DataFrame(SimpleImputer(strategy='median').fit_transform(X), columns=P)
    Xs = pd.DataFrame(StandardScaler().fit_transform(Xi), columns=P)
    Xs['y'] = y; Xs['rater'] = g

    def fit(formula, data):
        m = BinomialBayesMixedGLM.from_formula(formula, {'rater': '0 + C(rater)'}, data)
        return m.fit_vb(verbose=False)

    r0 = fit('y ~ 1', Xs)
    tau0 = float(np.exp(r0.vcp_mean[0])) ** 2
    r1 = fit('y ~ ' + ' + '.join(P), Xs)
    tau1 = float(np.exp(r1.vcp_mean[0])) ** 2
    for nm, tau in [('UNADJUSTED (rater only)', tau0), ('ADJUSTED for all 16 physiology vars', tau1)]:
        icc = tau / (tau + np.pi ** 2 / 3)
        mor = np.exp(np.sqrt(2 * tau) * 0.6745)
        print(f"  {nm}")
        print(f"     between-rater variance tau^2 = {tau:.3f}   latent ICC = {icc:.3f}   "
              f"Median Odds Ratio = {mor:.2f}")
    print(f"  proportion of between-rater variance explained by physiology = "
          f"{(tau0 - tau1) / tau0 * 100:.1f}%")
    print("  INTERPRETATION: MOR is the median factor by which the odds of a high-acuity designation")
    print("  differ between two randomly chosen clinicians assessing identical patients.")
except Exception as e:
    print('  statsmodels GLMM unavailable/failed:', e)

# empirical version that needs no GLMM: rater-specific rates adjusted for case-mix
print()
base = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                     LogisticRegression(max_iter=2000, C=1.0))
p_phys = cross_val_predict(base, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0),
                           method='predict_proba')[:, 1]
obs_exp = pd.DataFrame({'rater': g, 'y': y, 'exp': p_phys}).groupby('rater').agg(
    n=('y', 'size'), obs=('y', 'mean'), exp=('exp', 'mean'))
obs_exp = obs_exp[obs_exp.n >= 20]
obs_exp['oe'] = obs_exp.obs / obs_exp.exp
print(f"  case-mix-adjusted observed/expected high-acuity ratio across {len(obs_exp)} raters (>=20 encounters):")
print(f"     median O/E = {obs_exp.oe.median():.2f}, IQR {obs_exp.oe.quantile(.25):.2f}-{obs_exp.oe.quantile(.75):.2f}, "
      f"range {obs_exp.oe.min():.2f}-{obs_exp.oe.max():.2f}")
print(f"     raters with O/E significantly !=1 would be the 'outlier' signal a consistency tool reports")

print(); print('=' * 78); print('P. PREDICTION PIPELINE FEASIBILITY (triage-time predictors only)'); print('=' * 78)
def metrics(yt, pp, thr=None):
    au = roc_auc_score(yt, pp); ap = average_precision_score(yt, pp)
    br = brier_score_loss(yt, pp)
    if thr is None:  # threshold at 90% sensitivity (under-triage is the dangerous error)
        order = np.argsort(-pp); cs = np.cumsum(yt[order]); need = 0.90 * yt.sum()
        thr = pp[order][np.searchsorted(cs, need)]
    yh = (pp >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(yt, yh).ravel()
    return dict(auroc=au, auprc=ap, brier=br, thr=thr,
                sens=tp/(tp+fn), spec=tn/(tn+fp), ppv=tp/(tp+fp) if tp+fp else np.nan,
                npv=tn/(tn+fn) if tn+fn else np.nan)

def boot_auc(yt, pp, B=1000):
    s = [roc_auc_score(yt[i], pp[i]) for i in
         (rng.integers(0, len(yt), len(yt)) for _ in range(B)) if len(np.unique(yt[i])) > 1]
    return np.percentile(s, [2.5, 97.5])

models = {'LogReg': base,
          'HistGB': make_pipeline(HistGradientBoostingClassifier(
              max_depth=3, max_iter=250, learning_rate=.06, random_state=0))}
print(f"  n={len(df)}, events={y.sum()} ({y.mean()*100:.1f}%), {len(P)} predictors, "
      f"{len(np.unique(g))} raters")
for nm, mdl in models.items():
    pr = cross_val_predict(mdl, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0), method='predict_proba')[:, 1]
    pg = cross_val_predict(mdl, X, y, cv=GroupKFold(5), groups=g, method='predict_proba')[:, 1]
    mr, mg = metrics(y, pr), metrics(y, pg)
    lo, hi = boot_auc(y, pg)
    print(f"  {nm:<7} random-5fold AUROC {mr['auroc']:.3f} | grouped-by-rater AUROC {mg['auroc']:.3f} "
          f"[{lo:.3f}-{hi:.3f}]  AUPRC {mg['auprc']:.3f}  Brier {mg['brier']:.3f}")
    print(f"          at 90%-sensitivity operating point: sens {mg['sens']:.2f} spec {mg['spec']:.2f} "
          f"PPV {mg['ppv']:.2f} NPV {mg['npv']:.2f}")

# temporal holdout
cut = df.ts.quantile(0.75)
tr, te = df.ts <= cut, df.ts > cut
mdl = models['LogReg'].fit(X[tr], y[tr])
pt = mdl.predict_proba(X[te])[:, 1]
mt = metrics(y[te], pt)
lo, hi = boot_auc(y[te], pt)
print(f"  TEMPORAL holdout (train<= {cut:%Y-%m-%d} n={tr.sum()}, test n={te.sum()}): "
      f"AUROC {mt['auroc']:.3f} [{lo:.3f}-{hi:.3f}]  AUPRC {mt['auprc']:.3f}  Brier {mt['brier']:.3f}")

# rater-only and leakage reference
ro = pd.get_dummies(pd.Series(g)).astype(float).values
pro = cross_val_predict(LogisticRegression(max_iter=2000), ro, y,
                        cv=StratifiedKFold(5, shuffle=True, random_state=0), method='predict_proba')[:, 1]
print(f"  reference - RATER IDENTITY ALONE: AUROC {roc_auc_score(y, pro):.3f}")
Xa = X.copy(); Xa['area'] = pd.factorize(df.area)[0]
pa = cross_val_predict(models['HistGB'], Xa, y, cv=GroupKFold(5), groups=g, method='predict_proba')[:, 1]
print(f"  reference - WITH Area Triaged (LEAKAGE, do not use): AUROC {roc_auc_score(y, pa):.3f}")

# per-rater stability of a physiology model
res = []
for r, idx in pd.Series(range(len(df))).groupby(g):
    i = idx.values
    if len(i) >= 30 and len(np.unique(y[i])) > 1:
        res.append((r, len(i), roc_auc_score(y[i], pg[i])))
rs = pd.DataFrame(res, columns=['rater', 'n', 'auc'])
print(f"  per-rater AUROC of the grouped-CV model ({len(rs)} raters with >=30 encounters): "
      f"median {rs.auc.median():.3f}, range {rs.auc.min():.3f}-{rs.auc.max():.3f}")
print(f"     raters where the model performs no better than chance (AUC<0.6): {(rs.auc<0.6).sum()}/{len(rs)}")
