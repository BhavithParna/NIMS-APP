import pandas as pd, numpy as np, pickle
OUT="/home/bhavith/Documents/Datasets/analysis_output"
prof=pd.read_csv(f"{OUT}/csv/column_profile_raw.csv")

# (table, column) -> (meaning, units, role, confidence, notes)
S={
# ---------------- APACHE ----------------
('D1_APACHE_Sheet1','Date          S.No'):("Two values crammed into one cell: ICU admission date (dd-mm-yy) + sequential serial no.","date + count","identifier + timestamp","High","MUST be split. Dates all Oct-2024. S.No 01-77 is the row key."),
('D1_APACHE_Sheet1','       NAME'):("Patient full name","text","identifier (direct PHI)","High","Remove before any sharing/modelling."),
('D1_APACHE_Sheet1','       AGE'):("Patient age at ICU admission","years","feature","High","16-80, median 45. An APACHE IV scoring input."),
('D1_APACHE_Sheet1','         SEX'):("Sex, 1=male 0=female","binary","feature","High","62M/16F. Coding inferred from the 2024 file's explicit labels + name inspection."),
('D1_APACHE_Sheet1','       CRNo'):("Hospital Central Registration (MRN) number","15-digit id","identifier (indirect PHI)","High","Format 3310 1 YY NNNNNNNN; YY=registration year. All 78 unique."),
('D1_APACHE_Sheet1','   PHONE No'):("Patient mobile number","10-digit","identifier (direct PHI)","High","Remove. No analytic value."),
('D1_APACHE_Sheet1','      TEMP(°C) '):("Core temperature","deg C","feature (APS input)","High","Values are exact C conversions of whole-degree F readings (36.556, 37.056...) - recorded in F, converted."),
('D1_APACHE_Sheet1','   MAP(mmHg) '):("Mean arterial pressure","mmHg","feature (APS input)","High","36.6-136.6."),
('D1_APACHE_Sheet1','      HR (/min) '):("Heart rate","beats/min","feature (APS input)","High",""),
('D1_APACHE_Sheet1','      RR (/min) '):("Respiratory rate","breaths/min","feature (APS input)","High",""),
('D1_APACHE_Sheet1','Mechanical vent'):("On invasive mechanical ventilation, 1=yes","binary","feature","High","75/78 ventilated - a highly selected, severe ICU cohort."),
('D1_APACHE_Sheet1','       Fio2 (%) '):("Fraction of inspired oxygen","percent","feature (APS input)","High","28-100."),
('D1_APACHE_Sheet1','    pO2(mmHg) '):("Arterial partial pressure of oxygen (ABG)","mmHg","feature (APS input)","High",""),
('D1_APACHE_Sheet1','  pCO2 (mmHg) '):("Arterial partial pressure of CO2 (ABG)","mmHg","feature (APS input)","High",""),
('D1_APACHE_Sheet1','    Arterial pH'):("Arterial pH (ABG)","pH units","feature (APS input)","High","7.03-7.55."),
('D1_APACHE_Sheet1','  Na+ ( mEq/L) '):("Serum sodium","mEq/L","feature (APS input)","High","121-182."),
('D1_APACHE_Sheet1','Urine Output(ml/24h) '):("24-hour urine output","mL/24h","feature (APS input)","High","2 patients anuric (0)."),
('D1_APACHE_Sheet1','  Creatinine(mg/dl) '):("Serum creatinine","mg/dL","feature (APS input)","High","0.14-20.03, right-skewed."),
('D1_APACHE_Sheet1','   Urea(mEq/L) '):("Blood urea","mg/dL despite the mEq/L label","feature","High","LABEL WRONG: 10-438 is a mg/dL range."),
('D1_APACHE_Sheet1','    BSL(mg/dl) '):("Blood sugar level (glucose)","mg/dL","feature (APS input)","High",""),
('D1_APACHE_Sheet1','   Albumin(g/L) '):("Serum albumin","g/dL despite the g/L label","feature (APS input)","High","LABEL WRONG: 1.7-5.1 is a g/dL range."),
('D1_APACHE_Sheet1','Bilirubin (mg/dl) '):("Serum total bilirubin","mg/dL","feature (APS input)","High",""),
('D1_APACHE_Sheet1','       Ht(%) '):("Haematocrit","percent","feature (APS input)","High",""),
('D1_APACHE_Sheet1','WBC(x1000/mm3) '):("White blood cell count","MIXED: mostly cells/mm3, 1 row in x1000/mm3","feature (APS input)","High","BROKEN UNITS: 77 rows 1020-89500 (raw), 1 row 10.2 (thousands). Must be normalised."),
('D1_APACHE_Sheet1','GCS : E'):("Glasgow Coma Scale - eye opening","1-4","feature (APS input)","High",""),
('D1_APACHE_Sheet1','V'):("GCS - verbal response","1-5 or 'T'","feature (APS input)","High","77/78 = 'T' (tubed). Near-constant, almost no information."),
('D1_APACHE_Sheet1','           M'):("GCS - motor response","1-6","feature (APS input)","High","Most informative GCS component here."),
('D1_APACHE_Sheet1','CRF/HD'):("Chronic renal failure on haemodialysis","binary","feature (chronic health)","High","4/78 positive."),
('D1_APACHE_Sheet1','pre ICU LOS(days) '):("Days in hospital before ICU admission","days","feature (APACHE IV input)","High","0-2 only."),
('D1_APACHE_Sheet1','      Origin  '):("Admission source","category","feature (APACHE IV input)","High","77 'Floor', 1 'Other hospital' - near-constant."),
('D1_APACHE_Sheet1','Emergency Sx'):("Emergency surgery before ICU","binary","feature","High","1/78 positive - near-constant."),
('D1_APACHE_Sheet1','  Cirrhosis'):("Chronic health: cirrhosis","binary","feature","High","1/78."),
('D1_APACHE_Sheet1','Hepatic failure'):("Chronic health: hepatic failure","binary","feature (DEAD)","High","ALL ZERO - zero variance."),
('D1_APACHE_Sheet1','Metastatic carcinoma'):("Chronic health: metastatic cancer","binary","feature (DEAD)","High","ALL ZERO."),
('D1_APACHE_Sheet1','Lymphoma'):("Chronic health: lymphoma","binary","feature (DEAD)","High","ALL ZERO."),
('D1_APACHE_Sheet1','Leukemia/Myeloma'):("Chronic health: leukaemia/myeloma","binary","feature (DEAD)","High","ALL ZERO."),
('D1_APACHE_Sheet1','immunosuppression'):("Chronic health: immunosuppression","binary","feature (DEAD)","High","ALL ZERO."),
('D1_APACHE_Sheet1','        AIDS'):("Chronic health: AIDS","binary","feature (DEAD)","High","ALL ZERO."),
('D1_APACHE_Sheet1','APACHE IV SCORE'):("APACHE IV severity score, stored as 'score/286'","points out of 286","derived score / pseudo-target","High","Parse the numerator. 26-148, median 80.5. = APS + age pts + chronic-health pts."),
('D1_APACHE_Sheet1','APS SCORE'):("Acute Physiology Score component, 'score/239'","points out of 239","derived score","High","Always <= APACHE IV. Gap vs age r=0.91."),
('D1_APACHE_Sheet1','Estimated mortality rate'):("Calculator-PREDICTED in-hospital mortality","proportion 0-1","derived model output","High","NOT an observed outcome. r=0.88 with the score - using it as a target is circular."),
('D1_APACHE_Sheet1','Estimated length of stay'):("Calculator-PREDICTED ICU length of stay, text '6.5 Days'","days (as text)","derived model output","High","NOT observed. Parse the number."),
('D1_APACHE_Sheet1','Lactate (mmol/L) '):("Serum lactate","mmol/L","feature (extra, not in APACHE IV)","High","0.5-11.1. Added by the investigators."),
('D1_APACHE_Sheet1','Base deficit mmol/L'):("Base deficit / excess","mmol/L","feature (extra)","High","-15.7 to 19.1; negatives are legitimate (base excess)."),
('D1_APACHE_Sheet1','PEEP'):("Positive end-expiratory pressure","cmH2O","feature (extra)","High","0-15; 0 for the 3 non-ventilated."),
('D1_APACHE_Sheet1','Vasopressors'):("Vasopressor use: 0 = none, else free-text drug names","mixed","feature (extra)","High","MIXED TYPE: 63 zeros + 15 free-text strings with spelling/spacing variants. Binarise."),
('D1_APACHE_Sheet1','    Diagnosis'):("Free-text ICU admission diagnosis","text","metadata / feature after coding","High","78 unique strings, heavy abbreviation (RTA, TBA, CVA, AKI)."),
('D1_APACHE_Sheet1','   Outcome'):("Intended: survived/died","-","TARGET (EMPTY)","High","100% EMPTY. This is the single biggest gap in the file."),
('D1_APACHE_Sheet1','Date of discharge or death'):("Intended: discharge/death date","date","TARGET (EMPTY)","High","2/78 filled, and both look mis-entered (Apr & Sep 2024, before/around admission)."),
# ---------------- 2023 ----------------
('D2a_2023_FormResponses1','Timestamp'):("Google Form submission time (proxy for triage time)","datetime","timestamp","High","Jun-2023 to Apr-2025, NOT just 2023. 113 distinct days only."),
('D2a_2023_FormResponses1','Off hours triage=1'):("Triage performed outside routine hours","binary","feature / grouping","Medium","Only 20/875 positive; inconsistent with the hour-of-day stamps (many after 18:00 coded 0)."),
('D2a_2023_FormResponses1','Email Address'):("Google account of the staff member who triaged","email","grouping variable (rater id)","High","27 raters. USE FOR GROUPED CV. Direct PHI of staff."),
('D2a_2023_FormResponses1','Name '):("Patient name","text","identifier (direct PHI)","High",""),
('D2a_2023_FormResponses1','Age'):("Patient age","years","feature","High","4-95."),
('D2a_2023_FormResponses1','Sex'):("Sex, 1=male","binary","grouping","High","CONSTANT = 1 in this sheet. This sheet holds only MALE patients."),
('D2a_2023_FormResponses1','Trauma=1'):("Trauma presentation","binary","feature","High","22% of males vs 11% of females."),
('D2a_2023_FormResponses1','GI emerg=1'):("Gastrointestinal emergency","binary","feature","Medium","Only 14% answered - question added/removed mid-study; missingness is not random."),
('D2a_2023_FormResponses1','Complaint/Diagnosis'):("Free-text presenting complaint / working diagnosis","text","feature after coding","High","626 distinct strings for 876 records; abbreviations + '?' uncertainty markers."),
('D2a_2023_FormResponses1','cardiac=1'):("Cardiac presentation","binary (but a 2 appears)","feature","Medium","Values 0/1/2 - a 2 is undefined; likely a typo."),
('D2a_2023_FormResponses1','stroke=1'):("Stroke presentation","binary","feature","Medium","Only 29% answered."),
('D2a_2023_FormResponses1','Pulse rate'):("Heart rate","beats/min","feature","High","2 zeros = cardiac arrest or missing-as-zero."),
('D2a_2023_FormResponses1','SI'):("Shock Index flag: 1 if HR/SBP >= 0.9","binary","DERIVED feature","High","99% reproducible from HR and BP. Redundant + leakage-prone. Only 35% filled."),
('D2a_2023_FormResponses1','Unnamed: 13'):("Blood pressure as 'SBP/DBP' text (header lost)","mmHg text","feature (needs parsing)","High","97.9% parseable; strays: 'NR', '40 systolic', '120/8'."),
('D2a_2023_FormResponses1','Saturation'):("Peripheral oxygen saturation SpO2","percent","feature","High","Impossible values present: 0 and 106."),
('D2a_2023_FormResponses1','venti=1, O2 =2'):("Respiratory support: 1=ventilated, 2=supplemental O2","categorical","feature","Medium","Only 3% filled; blank probably means 'room air' but that is an assumption."),
('D2a_2023_FormResponses1','Respiratory Rate'):("Respiratory rate","breaths/min","feature","High","Includes 0 and 98 - impossible."),
('D2a_2023_FormResponses1','red=1'):("RED (critical) triage designation","binary","TARGET","High","38.5% positive across the unified register. The main 2023 label."),
('D2a_2023_FormResponses1','Additional information'):("Free-text notes","text","metadata","High","97.5% empty."),
('D2b_2023_Sheet3','5'):("Sex, 0=female","binary","grouping","High","CONSTANT = 0. This sheet holds only FEMALE patients - the other half of the same register."),
# ---------------- 2024 ----------------
('D3_2024_FormResponses1','Timestamp'):("Google Form submission time","datetime","timestamp","High","Dec-2024 to Aug-2025; 96% of volume in Mar-May 2025. 62 distinct days."),
('D3_2024_FormResponses1','Email Address'):("Staff account performing the triage","email","grouping variable (rater id)","High","35 raters; 18 also appear in the 2023 file - same department."),
('D3_2024_FormResponses1','Name '):("Patient name","text","identifier (direct PHI)","High",""),
('D3_2024_FormResponses1','CR Number'):("Hospital registration number","15-digit id","identifier (unreliable)","High","Only 1021/1125 have 15 digits; 61 CR values map to >1 patient name. NOT a trustworthy key."),
('D3_2024_FormResponses1','Age'):("Patient age","years","feature","High","6-95; stored as object (some text entries)."),
('D3_2024_FormResponses1','Sex'):("Sex","category","feature","High","Male/Female + one 'male' - capitalisation inconsistency."),
('D3_2024_FormResponses1','Complaint/Diagnosis'):("Free-text presenting complaint","text","feature after coding","High","967 distinct strings for 1125 records - near-unique, needs NLP/manual coding."),
('D3_2024_FormResponses1','PAIN SCORE NRS'):("Numeric Rating Scale pain score","0-10","feature","High","100% filled (mandatory field); no association with ESI (rho=-0.008)."),
('D3_2024_FormResponses1','Airway'):("Airway status - the 'A' of ABCDE","category","feature","High","93% 'Patent'; 36 'Intubated outside'."),
('D3_2024_FormResponses1','Intervention (Airway)'):("Airway intervention performed","category","feature / outcome-of-care","High","92% empty; blank = none, but fill rate falls to 0 in later months."),
('D3_2024_FormResponses1','Respiratory Rate'):("Respiratory rate - 'B'","breaths/min","feature","High","Includes 0 and 65."),
('D3_2024_FormResponses1','Bilateral Air Entry'):("Bilateral air entry on auscultation","category","feature","High","99% 'Present' - near-constant."),
('D3_2024_FormResponses1','Saturation'):("SpO2","percent","feature","High","One 0. Strongest single vital vs ESI after GCS."),
('D3_2024_FormResponses1','Other'):("Free-text breathing findings","text","feature","Medium","97.6% empty."),
('D3_2024_FormResponses1','Intervention (Breathing)'):("Oxygen/ventilation given","category","feature / outcome-of-care","High","Face mask/cannula 240, invasive ventilation etc. Recorded AFTER assessment - leakage risk."),
('D3_2024_FormResponses1','Pulse rate'):("Heart rate - 'C'","beats/min","feature","High","11-243."),
('D3_2024_FormResponses1','Blood Pressure'):("BP as 'SBP/DBP' text","mmHg text","feature (needs parsing)","High","97.1% parseable; one 700 systolic, some '60 systolic' free text."),
('D3_2024_FormResponses1','Capillary Refill Time'):("CRT <3s or >3s","binary category","feature","High","59/1125 prolonged."),
('D3_2024_FormResponses1','Other.1'):("Free-text circulation findings","text","feature","Medium","97.5% empty."),
('D3_2024_FormResponses1','Intervention (Circulation)'):("IV access / fluids given","category","feature / outcome-of-care","High","89% filled; 'IV line, IV fluid' most common."),
('D3_2024_FormResponses1','GCS  E'):("GCS eye - 'D'","1-4","feature","High",""),
('D3_2024_FormResponses1','GCS V'):("GCS verbal","1-5 (+'T','A')","feature","High","One value of 6 = impossible; 'T'/'A' non-numeric codes."),
('D3_2024_FormResponses1','GCS M'):("GCS motor","1-6","feature","High",""),
('D3_2024_FormResponses1','GCS'):("GCS total","3-15","DERIVED","High","Only 7/1125 filled - recompute as E+V+M instead. One computed total = 16 (impossible)."),
('D3_2024_FormResponses1','Pupils'):("Pupil findings ('BERTL' = bilaterally equal, reacting to light)","category","feature","High","96% BERTL; 45 distinct spellings of the rest."),
('D3_2024_FormResponses1','Focal Neurological Deficit'):("Focal neuro deficit present","Yes/No","feature","High","160/1125 Yes."),
('D3_2024_FormResponses1','Intervention (Disability)'):("Neuro intervention","free text","feature","Low","138 distinct values that are mostly 'No'/'Nil'/'-'/'.' - unusable as-is."),
('D3_2024_FormResponses1','Temperature in Fahrenheit'):("Body temperature - 'E'","MIXED F and C","feature","High","22 out-of-range incl. 37.5/37.9 (Celsius in a Fahrenheit field) and 4.0."),
('D3_2024_FormResponses1','Log Roll'):("Log-roll (spinal) examination performed/findings","free text","feature","Low","65 distinct values, mostly placeholders."),
('D3_2024_FormResponses1','Intervention (Exposure)'):("Exposure-stage intervention","free text","feature","Low","96 distinct placeholder-heavy values."),
('D3_2024_FormResponses1','Area Triaged'):("Physical area the patient was sent to","3 categories","TARGET / near-duplicate of ESI","High","Red Triage 583, Table 1 372, Table 2 170. Almost determined by ESI - LEAKAGE if used as a feature for ESI."),
('D3_2024_FormResponses1','ESI Triage Category'):("Emergency Severity Index 1-5","ordinal 1-5","PRIMARY TARGET","High","1:129 2:376 3:492 4:111 5:14. Mixed int/str storage + one 'NS opinion'."),
('D3_2024_FormResponses1','Column 31'):("Orphan form column","-","artifact","High","13 rows of 'Option 1'. Delete."),
('D3_2024_FormResponses1','GRBS (mg/dL)'):("Random blood glucose","mg/dL","feature","Medium","Almost entirely empty - question added late."),
('D3_2024_FormResponses1','Disposition'):("Where the patient went next","category","POTENTIAL OUTCOME","High","Almost entirely empty - the outcome that was never captured."),
}

# Sheet3 = the FEMALE half of the same 2023 register; headerless, so columns are positional
_s3=['Timestamp (form submission)','Off hours triage=1','Email Address (rater)','Patient name','Age','Sex (constant 0 = female)','Trauma=1','Complaint/Diagnosis (free text)','cardiac=1 (never answered here)','Pulse rate','SI (shock-index flag)','Blood Pressure "SBP/DBP"','Saturation (SpO2)','venti=1 / O2=2','Respiratory Rate','red=1 (critical triage TARGET)','Additional information']
_s3r=['timestamp','feature / grouping','grouping variable (rater id)','identifier (direct PHI)','feature','grouping','feature','feature after coding','feature (DEAD)','feature','DERIVED feature','feature (needs parsing)','feature','feature','feature','TARGET','metadata']
for i,(m,r) in enumerate(zip(_s3,_s3r)):
    S[('D2b_2023_Sheet3',str(i))]=(m+" - HEADERLESS sheet, meaning assigned by column position against the male sheet's schema","see male sheet",r,"High" if i not in (8,13) else "Medium","Sheet3 has NO header row; identical column order to 'Form Responses 1' minus 'GI emerg' and 'stroke'.")
S[('D2b_2023_Sheet3','5')]=("Sex, 0=female","binary","grouping","High","CONSTANT = 0. This sheet holds only FEMALE patients - the other half of the same register.")
# 2023 FR vestigial tail: 2024-schema questions that reached this old sheet in only ~5 rows
for c in ['PAIN SCORE NRS','Airway','CR Number','Respiratory Rate.1','Bilateral Air Entry','Saturation.1','Capillary Refill Time','GCS  E','Other.1','INTERVENTION','GCS V','GCS M','Pupils','Focal Neurological Deficit','Temperature in Fahrenheit','Log Roll','INTERVENTION.1','INTERVENTION.2','Diagnosis']:
    S[('D2a_2023_FormResponses1',c)]=("Vestigial column from the NEWER ABCDE form schema that leaked into this older sheet","see 2024 file","artifact (near-empty)","High","Filled for only 4-5 of 880 rows (Apr-2025 submissions). Evidence the same Google Form was later rebuilt into the 2024 instrument. Drop from the 2023 analysis.")

rows=[]
for _,r in prof.iterrows():
    key=(r['table'],r['column'])
    mean,unit,role,conf,note=S.get(key,("","","unclassified / empty column","Low","Not interpreted: empty or orphan column."))
    if r['non_null']==0 and key not in S:
        mean,unit,role,conf,note=("Empty column - a form question that was created but never answered, or a leftover","-","artifact","High","0 non-null values. Drop.")
    rows.append({'dataset':{'D1_APACHE_Sheet1':'APACHE 4.xlsx','D2a_2023_FormResponses1':'NIMS TRIAGE 2023.xlsx','D2b_2023_Sheet3':'NIMS TRIAGE 2023.xlsx','D3_2024_FormResponses1':'NIMS TRIAGE 2024 (Responses).xlsx'}[r['table']],
        'worksheet':{'D1_APACHE_Sheet1':'Sheet1','D2a_2023_FormResponses1':'Form Responses 1','D2b_2023_Sheet3':'Sheet3','D3_2024_FormResponses1':'Form Responses 1'}[r['table']],
        'column':r['column'],'col_index':r['col_index'],'data_type':r['dtype'],
        'examples':r['examples'] if pd.notna(r['examples']) else '',
        'description':mean,'units':unit,'role':role,
        'missing_pct':r['missing_pct'],'unique_count':r['unique'],
        'notes':note,'confidence':conf})
dd=pd.DataFrame(rows)
dd.to_csv(f"{OUT}/csv/DATA_DICTIONARY.csv",index=False)
print("data dictionary rows:",len(dd))
print(dd.groupby('dataset')['role'].value_counts().to_string())
print("\nconfidence:",dict(dd.confidence.value_counts()))
print("uninterpreted:",int((dd.role=='unclassified / empty column').sum()))
