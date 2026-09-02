import pandas as pd, numpy as np, pickle, hashlib, warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GroupKFold, StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
OUT="/home/bhavith/Documents/Datasets/analysis_output"
D=pickle.load(open(f"{OUT}/data.pkl","rb"))

print("### BASELINE 1 — 2023 unified register: predict red=1 from vitals")
u=pd.read_csv(f"{OUT}/csv/unified_2023_register_DEID.csv")
raw=D['T23_FR']; s3=D['T23_S3']
grp=pd.concat([raw['Email Address'],s3[2]],ignore_index=True).astype(str).str.lower().str.strip()
u['rater']=grp.values[:len(u)] if len(grp)>=len(u) else None
X=u[['age','hr','sbp','dbp','spo2','rr','Sex','Trauma=1']].apply(pd.to_numeric,errors='coerce')
y=pd.to_numeric(u['red'],errors='coerce')
m=y.notna()&u['rater'].notna(); X,y,g=X[m],y[m].astype(int),u.loc[m,'rater']
print(f"  n={len(X)} pos_rate={y.mean():.3f} groups(raters)={g.nunique()}")
pipe=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=2000))
hgb=HistGradientBoostingClassifier(max_iter=250,random_state=0)
for nm,mdl in [("LogReg",pipe),("HistGB",hgb)]:
    a=cross_val_score(mdl,X,y,cv=StratifiedKFold(5,shuffle=True,random_state=0),scoring='roc_auc')
    b=cross_val_score(mdl,X,y,cv=GroupKFold(5),groups=g,scoring='roc_auc')
    print(f"  {nm:7s} AUC  random-5fold={a.mean():.3f}±{a.std():.3f}   GROUPED-by-rater={b.mean():.3f}±{b.std():.3f}   drop={a.mean()-b.mean():+.3f}")
print("  + rater identity as the ONLY feature:")
ohe=pd.get_dummies(g)
print(f"    AUC(rater alone, random CV)={cross_val_score(LogisticRegression(max_iter=2000),ohe,y,cv=5,scoring='roc_auc').mean():.3f}  <- how much is rater style, not physiology")

print("\n### BASELINE 2 — 2024: predict ESI (binary: 1-2 'high acuity' vs 3-5)")
t=pd.read_csv(f"{OUT}/csv/triage_2024_DEID.csv")
raw24=D['T24_FR'][D['T24_FR'].Timestamp.notna()].reset_index(drop=True)
t['rater']=raw24['Email Address'].astype(str).str.lower().str.strip()
t['gcs']=pd.to_numeric(t['gcs'],errors='coerce')
X=t[['age','hr','sbp','dbp','rr','spo2','temp','pain','gcs','si']].apply(pd.to_numeric,errors='coerce')
X['crt_slow']=(t['Capillary Refill Time']=='>3 seconds').astype(int)
X['focal']=(t['Focal Neurological Deficit']=='Yes').astype(int)
X['airway_not_patent']=(t['Airway']!='Patent').astype(int)
X['male']=(t['Sex']=='Male').astype(int)
esi=pd.to_numeric(t['esi'],errors='coerce'); y=(esi<=2).astype(int)
m=esi.notna(); X,y,g=X[m],y[m],t.loc[m,'rater']
print(f"  n={len(X)} high-acuity rate={y.mean():.3f} raters={g.nunique()}")
for nm,mdl in [("LogReg",pipe),("HistGB",hgb)]:
    a=cross_val_score(mdl,X,y,cv=StratifiedKFold(5,shuffle=True,random_state=0),scoring='roc_auc')
    b=cross_val_score(mdl,X,y,cv=GroupKFold(5),groups=g,scoring='roc_auc')
    print(f"  {nm:7s} AUC  random-5fold={a.mean():.3f}±{a.std():.3f}   GROUPED-by-rater={b.mean():.3f}±{b.std():.3f}   drop={a.mean()-b.mean():+.3f}")
print(f"  rater alone AUC={cross_val_score(LogisticRegression(max_iter=2000),pd.get_dummies(g),y,cv=5,scoring='roc_auc').mean():.3f}")
print("  LEAKAGE demo — add 'Area Triaged' as a feature:")
Xl=X.copy(); Xl['area_red']=(t.loc[m,'Area Triaged']=='Red Triage').astype(int)
print(f"    HistGB AUC with Area Triaged = {cross_val_score(hgb,Xl,y,cv=StratifiedKFold(5,shuffle=True,random_state=0),scoring='roc_auc').mean():.3f}  <- inflated; Area is assigned WITH the ESI, not before it")
hgb.fit(X,y)
from sklearn.inspection import permutation_importance
pi=permutation_importance(hgb,X,y,n_repeats=8,random_state=0,scoring='roc_auc')
imp=pd.Series(pi.importances_mean,index=X.columns).sort_values(ascending=False)
print("\n  Permutation importance (2024 high-acuity model):"); print(imp.round(4).to_string())

print("\n### BASELINE 3 — APACHE: can 78 rows support modelling?")
ap=D['AP1'].iloc[:78]
S=pd.to_numeric(ap['APACHE IV SCORE'].astype(str).str.extract(r'(\d+)/')[0])
print(f"  n=78, no outcome column -> no supervised target exists.")
print(f"  Only regressible quantity is the calculator's own score, which is a deterministic function of the same inputs.")
print(f"  Events-per-variable if a mortality outcome were later collected at ~40% mortality: 31 events / 47 candidate predictors = 0.7 EPV (need >=10).")
print(f"  => Verdict: descriptive statistics and validation-against-published-benchmarks only. Not an ML dataset.")
