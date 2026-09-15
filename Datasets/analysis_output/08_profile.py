import pandas as pd, numpy as np, pickle, re, json
from scipy import stats
D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
OUT="/home/bhavith/Documents/Datasets/analysis_output"
PII={'name','email','phone','crno','cr number','cr no'}
def is_pii(c):
    c=str(c).strip().lower()
    return any(k in c for k in ['name','email','phone','cr no','crno','cr number'])

TABLES={
 'D1_APACHE_Sheet1': D['AP1'].iloc[:78,:49],
 'D2a_2023_FormResponses1': D['T23_FR'],
 'D2b_2023_Sheet3': D['T23_S3'],
 'D3_2024_FormResponses1': D['T24_FR'],
}
rows=[]
for tname,df in TABLES.items():
    n=len(df)
    for i,c in enumerate(df.columns):
        s=df[c]; nn=s.notna().sum(); miss=1-nn/n
        num=pd.to_numeric(s,errors='coerce')
        numeric_frac = num.notna().sum()/max(nn,1)
        vals=s.dropna()
        uniq=vals.astype(str).nunique()
        ex=[str(x)[:40] for x in vals.astype(str).unique()[:4]]
        d={'table':tname,'col_index':i,'column':str(c),'dtype':str(s.dtype),
           'non_null':int(nn),'missing_pct':round(miss*100,2),'unique':int(uniq),
           'numeric_parse_rate':round(numeric_frac*100,1),'examples':' | '.join(ex) if not is_pii(c) else '<PII redacted>'}
        if numeric_frac>0.8 and nn>3:
            v=num.dropna()
            d.update(min=round(float(v.min()),3),q1=round(float(v.quantile(.25)),3),median=round(float(v.median()),3),
                     mean=round(float(v.mean()),3),q3=round(float(v.quantile(.75)),3),max=round(float(v.max()),3),
                     std=round(float(v.std()),3),zeros=int((v==0).sum()),negatives=int((v<0).sum()),
                     skew=round(float(stats.skew(v)),2) if len(v)>2 else None)
            if len(v)>3:
                q1,q3=v.quantile(.25),v.quantile(.75); iqr=q3-q1
                d['outliers_iqr']=int(((v<q1-1.5*iqr)|(v>q3+1.5*iqr)).sum())
        else:
            vc=vals.astype(str).str.strip().value_counts()
            d['top_values']=' | '.join(f"{k}({v})" for k,v in list(vc.items())[:6]) if not is_pii(c) else '<PII redacted>'
            if len(vc): d['mode_share_pct']=round(100*vc.iloc[0]/nn,1)
            # capitalization/whitespace inconsistency
            raw=vals.astype(str); low=raw.str.strip().str.lower()
            d['case_ws_collapse']=int(raw.nunique()-low.nunique())
        rows.append(d)
prof=pd.DataFrame(rows)
prof.to_csv(f"{OUT}/csv/column_profile_raw.csv",index=False)
print("profiled columns:",len(prof))
for t in TABLES:
    p=prof[prof.table==t]
    print(f"\n{'='*100}\n{t}: {len(TABLES[t])} rows x {len(p)} cols | empty cols={int((p.non_null==0).sum())}")
    cols=['col_index','column','dtype','non_null','missing_pct','unique','numeric_parse_rate','min','median','max','zeros','negatives','skew','outliers_iqr','top_values','case_ws_collapse']
    cols=[c for c in cols if c in p.columns]
    print(p[cols].to_string(index=False,max_colwidth=44))
