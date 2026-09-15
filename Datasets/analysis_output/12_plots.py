import pandas as pd, numpy as np, pickle, re, hashlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
P="/home/bhavith/Documents/Datasets/analysis_output/plots/"
SURF="#fcfcfb"; INK="#22201d"; MUT="#6d6862"; GRID="#e5e2dd"
C=["#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4"]
STATUS={'critical':"#d03b3b",'serious':"#ec835a",'warning':"#fab219",'good':"#0ca30c"}
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF,
 'axes.edgecolor':GRID,'axes.labelcolor':MUT,'text.color':INK,'xtick.color':MUT,'ytick.color':MUT,
 'font.size':9,'axes.titlesize':11,'axes.titleweight':'bold','axes.grid':True,'grid.color':GRID,
 'grid.linewidth':0.6,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
def fin(fig,name,note=None):
    if note: fig.text(0.01,0.005,note,fontsize=7,color=MUT)
    fig.tight_layout(rect=[0,0.02,1,1]); fig.savefig(P+name,bbox_inches='tight'); plt.close(fig); print("  saved",name)

D=pickle.load(open("/home/bhavith/Documents/Datasets/analysis_output/data.pkl","rb"))
u23=pd.read_csv("/home/bhavith/Documents/Datasets/analysis_output/csv/unified_2023_register_DEID.csv",parse_dates=['Timestamp'])
t24=pd.read_csv("/home/bhavith/Documents/Datasets/analysis_output/csv/triage_2024_DEID.csv",parse_dates=['Timestamp'])
ap=D['AP1'].iloc[:78].copy()

# 1 ---- timeline of the three collections
fig,ax=plt.subplots(figsize=(10,4))
m=u23.assign(mo=u23.Timestamp.dt.to_period('M')).groupby(['mo','Sex']).size().unstack(fill_value=0)
m24=t24.assign(mo=t24.Timestamp.dt.to_period('M')).groupby('mo').size()
idx=pd.period_range('2023-06','2025-09',freq='M')
m=m.reindex(idx,fill_value=0); m24=m24.reindex(idx,fill_value=0)
x=np.arange(len(idx)); w=0.28
ax.bar(x-w,m.get(1.0,0),w*0.92,color=C[0],label='2023 file · male sheet (n=876)')
ax.bar(x,m.get(0.0,0),w*0.92,color=C[1],label='2023 file · female sheet (n=435)')
ax.bar(x+w,m24,w*0.92,color=C[2],label='2024 file · ABCDE form (n=1125)')
apm=pd.to_datetime(ap.iloc[:,0].astype(str).str.extract(r'(\d{2}-\d{2}-\d{2})')[0],format='%d-%m-%y')
ai=list(idx).index(pd.Period('2024-10','M'))
ax.bar([ai],[len(ap)],w*0.92,color=STATUS['critical'],label='APACHE file · ICU (n=78, Oct-2024)',bottom=0,alpha=0.95,hatch='///',edgecolor=SURF)
ax.set_xticks(x[::2]); ax.set_xticklabels([str(p) for p in idx[::2]],rotation=45,ha='right',fontsize=7)
ax.set_ylabel('records per month'); ax.set_title('Three files, three non-overlapping collection windows')
ax.legend(frameon=False,fontsize=8)
ax.annotate('gap: Sep–Nov 2024\n(no triage data)',xy=(ai,120),fontsize=7.5,color=MUT,ha='center')
fin(fig,'01_timeline_coverage.png','Each file covers a different period. The APACHE ICU month sits inside the triage gap.')

# 2 ---- age/sex
fig,axes=plt.subplots(1,3,figsize=(12,3.6))
for a,(lbl,df,sexcol,mval,fval) in zip(axes,[("2023 register (n=1311)",u23,'Sex',1.0,0.0),
                                             ("2024 register (n=1125)",t24,'Sex','Male','Female'),
                                             ("APACHE ICU (n=78)",ap.assign(Sex=ap.iloc[:,3],age=ap.iloc[:,2]),'Sex',1.0,0.0)]):
    ages=df['age'] if 'age' in df else df['age']
    bins=np.arange(0,101,5)
    a.hist(ages[df[sexcol]==mval].dropna(),bins=bins,color=C[0],alpha=.85,label='male')
    a.hist(ages[df[sexcol]==fval].dropna(),bins=bins,color=C[1],alpha=.65,label='female')
    a.set_title(lbl); a.set_xlabel('age (years)'); a.legend(frameon=False,fontsize=8)
axes[0].set_ylabel('patients')
fin(fig,'02_age_sex.png','Adult-dominant case mix in all three; ICU cohort is not a subset of either triage cohort.')

# 3 ---- ESI + area
fig,axes=plt.subplots(1,2,figsize=(11,3.8))
vc=t24['esi'].value_counts().sort_index()
cols=[STATUS['critical'],STATUS['serious'],STATUS['warning'],C[2],C[0]]
b=axes[0].bar(vc.index,vc.values,color=cols[:len(vc)],width=.68)
for r,v in zip(b,vc.values): axes[0].text(r.get_x()+r.get_width()/2,v+8,f"{v}\n{v/vc.sum():.0%}",ha='center',fontsize=8,color=INK)
axes[0].set_title('2024: ESI triage category (target variable)'); axes[0].set_xlabel('ESI  (1 = most urgent)'); axes[0].set_ylabel('encounters')
axes[0].set_ylim(0,vc.max()*1.25)
ct=pd.crosstab(t24['Area Triaged'],t24['esi'],normalize='index')*100
bot=np.zeros(len(ct))
for i,c in enumerate(ct.columns):
    axes[1].barh(ct.index,ct[c],left=bot,color=cols[i],height=.6,edgecolor=SURF,linewidth=2,label=f'ESI {int(c)}')
    bot+=ct[c].values
axes[1].set_title('Area triaged vs ESI  (near-deterministic)'); axes[1].set_xlabel('% of encounters in area')
axes[1].legend(frameon=False,fontsize=7,ncol=5,loc='lower center',bbox_to_anchor=(.5,-.42)); axes[1].grid(axis='y',visible=False)
fin(fig,'03_esi_distribution.png','ESI 3 is the plurality; ESI 5 has only 14 cases. Area Triaged encodes urgency -> leakage if used as a feature.')

# 4 ---- vitals by ESI small multiples
vs=['hr','rr','spo2','gcs','sbp','age']; lbl={'hr':'Heart rate (/min)','rr':'Resp rate (/min)','spo2':'SpO2 (%)','gcs':'GCS total','sbp':'Systolic BP (mmHg)','age':'Age (years)'}
fig,axes=plt.subplots(2,3,figsize=(12,6))
for a,v in zip(axes.ravel(),vs):
    d=[t24.loc[t24.esi==e,v].dropna() for e in [1,2,3,4,5]]
    bp=a.boxplot(d,labels=['1','2','3','4','5'],patch_artist=True,widths=.55,showfliers=False,
                 medianprops=dict(color=INK,lw=1.6),whiskerprops=dict(color=MUT,lw=1),capprops=dict(color=MUT,lw=1))
    for patch,c in zip(bp['boxes'],cols): patch.set_facecolor(c); patch.set_alpha(.75); patch.set_edgecolor(SURF); patch.set_linewidth(2)
    a.set_title(lbl[v],fontsize=9.5); a.set_xlabel('ESI category')
fig.suptitle('2024: physiology stratifies by ESI in the expected direction — but with heavy overlap',fontsize=11,fontweight='bold')
fin(fig,'04_vitals_by_esi.png','Signal is real (Spearman |rho| 0.15-0.22 for HR, RR, SpO2, GCS) but modest: vitals alone will not reproduce ESI.')

# 5 ---- rater variability
def H(x): return "R"+hashlib.sha256(str(x).encode()).hexdigest()[:5]
t=D['T24_FR']; t=t[t.Timestamp.notna()].copy(); t['esi']=pd.to_numeric(t['ESI Triage Category'],errors='coerce')
t['r']=t['Email Address'].astype(str).str.lower().str.strip().map(H)
g=t.groupby('r').agg(n=('esi','size'),p1=('esi',lambda s:(s==1).mean()*100),me=('esi','mean'))
g=g[g.n>=20].sort_values('p1')
fig,ax=plt.subplots(figsize=(9,4.6))
c=[STATUS['critical'] if v>25 else (STATUS['warning'] if v>10 else C[0]) for v in g.p1]
ax.barh(range(len(g)),g.p1,color=c,height=.62)
ax.set_yticks(range(len(g))); ax.set_yticklabels([f"{i} (n={n})" for i,n in zip(g.index,g.n)],fontsize=7)
ax.axvline(t['esi'].eq(1).mean()*100,color=INK,ls='--',lw=1.2)
ax.text(t['esi'].eq(1).mean()*100+1,len(g)-2.5,f"cohort mean {t['esi'].eq(1).mean()*100:.1f}%",fontsize=8,color=INK)
ax.set_xlabel('% of that rater\'s patients assigned ESI 1 (resuscitation)')
ax.set_title('Inter-rater variability is the dominant nuisance signal (22 raters, ≥20 records)')
ax.grid(axis='y',visible=False)
fin(fig,'05_rater_variability.png','Range 0%–48% across raters; Kruskal-Wallis p=6e-18. Any ESI model must be validated grouped by rater.')

# 6 ---- missingness
fig,axes=plt.subplots(1,3,figsize=(13,4.2))
for a,(lbl,df) in zip(axes,[("APACHE Sheet1",ap),("2023 Form Responses 1",D['T23_FR']),("2024 Form Responses 1",D['T24_FR'])]):
    miss=df.isna().values.astype(float)
    a.imshow(miss,aspect='auto',cmap=matplotlib.colors.ListedColormap([C[0],"#f2ece4"]),interpolation='nearest')
    a.set_title(f"{lbl}\n{df.shape[0]} rows x {df.shape[1]} cols · {df.isna().mean().mean():.0%} cells empty",fontsize=9.5)
    a.set_xlabel('column index'); a.set_ylabel('row (chronological)'); a.grid(False)
fig.suptitle('Missingness maps — blue = present, cream = empty',fontsize=11,fontweight='bold')
fin(fig,'06_missingness.png','Right-hand cream blocks = form questions added later / abandoned. APACHE outcome columns are entirely empty.')

# 7 ---- APACHE
sc=ap['APACHE IV SCORE'].astype(str).str.extract(r'(\d+)/(\d+)'); S=pd.to_numeric(sc[0])
A=pd.to_numeric(ap['APS SCORE'].astype(str).str.extract(r'(\d+)/')[0]); M=ap['Estimated mortality rate']
fig,axes=plt.subplots(1,3,figsize=(12,3.8))
axes[0].scatter(S,M,s=26,color=C[0],edgecolor=SURF,linewidth=.8)
axes[0].set_xlabel('APACHE IV score (/286)'); axes[0].set_ylabel('estimated mortality (proportion)')
axes[0].set_title(f'Predicted mortality is a function\nof the score (r={S.corr(M):.2f}) — not an outcome')
axes[1].scatter(ap.iloc[:,2],S-A,s=26,color=C[1],edgecolor=SURF,linewidth=.8)
axes[1].set_xlabel('age (years)'); axes[1].set_ylabel('APACHE IV − APS (points)')
axes[1].set_title(f'The gap is the age/chronic-health\ncomponent (r={(S-A).corr(ap.iloc[:,2]):.2f})')
axes[2].hist(S,bins=18,color=C[2]); axes[2].set_xlabel('APACHE IV score'); axes[2].set_ylabel('patients')
axes[2].set_title('Severity distribution\n(median 80.5, range 26–148)')
fin(fig,'07_apache_internals.png','APACHE IV = APS + age + chronic-health points. Mortality/LOS columns are calculator outputs, so they cannot serve as ML targets.')

# 8 ---- correlation matrices
fig,axes=plt.subplots(1,2,figsize=(13,5.4))
num=ap.iloc[:,[2,6,7,8,9,11,12,13,14,15,16,17,18,19,20,21,22,24,26,42,43,44]].apply(pd.to_numeric,errors='coerce')
num.columns=[str(c).strip()[:14] for c in num.columns]; num['APACHE IV']=S; num['mortality']=M
cm=num.corr(); im=axes[0].imshow(cm,cmap='RdBu_r',vmin=-1,vmax=1)
axes[0].set_xticks(range(len(cm))); axes[0].set_xticklabels(cm.columns,rotation=90,fontsize=6.5)
axes[0].set_yticks(range(len(cm))); axes[0].set_yticklabels(cm.columns,fontsize=6.5); axes[0].grid(False)
axes[0].set_title('APACHE ICU (n=78): physiology + score')
n2=t24[['age','hr','sbp','dbp','rr','spo2','temp','pain','gcs','si','esi']].apply(pd.to_numeric,errors='coerce')
cm2=n2.corr(); im2=axes[1].imshow(cm2,cmap='RdBu_r',vmin=-1,vmax=1)
axes[1].set_xticks(range(len(cm2))); axes[1].set_xticklabels(cm2.columns,rotation=90,fontsize=7)
axes[1].set_yticks(range(len(cm2))); axes[1].set_yticklabels(cm2.columns,fontsize=7); axes[1].grid(False)
axes[1].set_title('2024 triage (n=1125): vitals + ESI')
for a,c in [(axes[0],cm),(axes[1],cm2)]:
    for i in range(len(c)):
        for j in range(len(c)):
            if abs(c.iloc[i,j])>0.55 and i!=j: a.text(j,i,f"{c.iloc[i,j]:.1f}",ha='center',va='center',fontsize=5.5,color=INK)
fig.colorbar(im2,ax=axes,shrink=.7,label='Pearson r')
fin(fig,'08_correlations.png','Strong blocks: SI=HR/SBP (derived), GCS components, APACHE score vs its inputs. Vitals are otherwise weakly inter-correlated.')

# 9 ---- 2023 red flag
fig,axes=plt.subplots(1,3,figsize=(12,3.6))
for a,v,l in zip(axes,['rr','spo2','hr'],['Respiratory rate (/min)','SpO2 (%)','Heart rate (/min)']):
    for k,(lab,col) in enumerate([('not red',C[0]),('red = 1',STATUS['critical'])]):
        d=u23.loc[u23.red==k,v].dropna()
        a.hist(d,bins=25,alpha=.7,color=col,label=lab,density=True)
    a.set_xlabel(l); a.legend(frameon=False,fontsize=8)
    if v=='spo2': a.set_xlim(70,102)
    if v=='rr': a.set_xlim(5,45)
axes[0].set_ylabel('density')
fig.suptitle('2023 register: what separates a "red" (critical) triage flag — 38.5% positive rate',fontsize=11,fontweight='bold')
fin(fig,'09_red_flag_2023.png','RR (r=+0.27) and SpO2 (r=-0.19) carry most of the separation; BP carries almost none.')
print("done")
