# Forensic Analysis of Three Clinical Excel Workbooks

**Analyst pass:** data engineering · data science · dataset forensics
**Date of analysis:** 19 August 2026
**Source files (unmodified, checksums recorded):**

| File | Bytes | MD5 |
|---|---|---|
| `APACHE 4.xlsx` | 42,837 | `d22d17e47b3fc9b5534ec4037a21d2a9` |
| `NIMS TRIAGE 2023.xlsx` | 189,385 | `f40d51f3eb536377a5c187c028a7c813` |
| `NIMS TRIAGE 2024 (Responses).xlsx` | 268,079 | `28e6a7951f93f267660facfb8688cd5c` |

> **⚠ These files contain identifiable patient data.** Patient names, mobile numbers and hospital
> registration (CR) numbers are stored in plaintext, alongside staff email addresses. Every
> derived file in `analysis_output/` is de-identified (identifiers dropped, staff hashed), but the
> three originals are not. Treat them as protected health information: do not email them, upload
> them to a cloud notebook, or paste them into an LLM. See §10.

---

## 1. Executive summary

You have **three separate clinical data collections from what is almost certainly one hospital's
emergency and critical-care service** — not three versions of one dataset, and not three unrelated
datasets. They are three *different points in the same patient journey*, captured by overlapping
staff, at three different times, with **zero patient overlap between them**.

| | Dataset 1 | Dataset 2 | Dataset 3 |
|---|---|---|---|
| **File** | `APACHE 4.xlsx` | `NIMS TRIAGE 2023.xlsx` | `NIMS TRIAGE 2024 (Responses).xlsx` |
| **What a row is** | one **ICU admission**, scored | one **ED triage encounter** | one **ED triage encounter** |
| **Real n** | **78** | **1,311** | **1,125** |
| **Period** | 1–31 Oct 2024 | Jun 2023 – Aug 2024 | Dec 2024 – Aug 2025 |
| **Care setting** | Intensive care | Emergency triage | Emergency triage |
| **Instrument** | Manual spreadsheet + APACHE IV calculator | Google Form (v1, minimal) | Google Form (v2, full ABCDE) |
| **Target present?** | ✗ **none — outcome column is empty** | ✓ `red=1` (38.5% positive) | ✓ `ESI 1–5` + `Area Triaged` |
| **Quality score** | **77 / 100** | **80 / 100** | **88 / 100** |

**The five findings that matter most:**

1. **The 2023 workbook is one register that was split in half by sex.** `Form Responses 1` contains
   876 records that are **all male**; `Sheet3` contains 435 records that are **all female**. Same
   days, same staff, submissions minutes apart, zero patient overlap. They must be **unioned** to get
   the real dataset of **1,311 encounters** — anyone who analyses only the first sheet is silently
   analysing men only.
2. **The three files share no patients.** CR-number overlap is exactly **0** in all three pairwise
   comparisons. They cannot be joined row-to-row. They can only be *stacked* or *compared as cohorts*.
3. **The APACHE file has no outcome.** The `Outcome` column is 100% empty and `Date of discharge or
   death` is filled for 2 of 78 rows (both implausible). The mortality and length-of-stay columns are
   **calculator predictions, not observations** — using them as ML targets is circular.
4. **`Area Triaged` leaks the answer.** Adding it as a feature to an ESI model lifts AUC from 0.72 to
   0.86, because the area is assigned *with* the triage category, not before it. Same story for the
   `SI` column in the 2023 file, which is 99% reproducible as `HR/SBP ≥ 0.9`.
5. **Dataset 3 is the only one that is genuinely ML-ready**, and even there the honest ceiling from
   vitals alone is **AUC ≈ 0.72** for high-acuity classification — useful for research, not for
   deployment.

---

## 2. Dataset 1 — `APACHE 4.xlsx`

### 2.1 Structure

| Property | Finding |
|---|---|
| Worksheets | `Sheet1`, `Sheet2` — both visible, none hidden |
| `Sheet1` | 81 Excel rows × 51 cols → **78 real patient rows**, 49 headed columns; rows 79–80 blank |
| `Sheet2` | 79 Excel rows × 27 cols → **an exact duplicate of `Sheet1` columns AA:AW**, verified cell-by-cell (100.00% match over all 78 rows) |
| Formulas | **0** — every value is hard-typed |
| Merged cells / hidden sheets / tables | none |
| Metadata | created **2025-08-28**, author **"Ashima Sharma"** (from `docProps/core.xml`) |

**`Sheet2` carries no information at all.** It is a copy-paste of the right-hand block of `Sheet1`,
two rows short. Delete it from any pipeline; keeping it invites a spurious "merge".

### 2.2 What a row represents

One patient admitted to intensive care during **October 2024**, scored on the **APACHE IV**
severity-of-illness system. Column A jams two fields into one cell — an admission date (`dd-mm-yy`)
and a serial number (`01`–`77`) — e.g. `01-10-24       01`. All 78 dates parse; all fall in Oct 2024
across 28 distinct days, i.e. roughly 2.8 ICU admissions scored per day for one month.

This is a **prospective severity-scoring study**, not a hospital extract: the column set is precisely
the APACHE IV input sheet (12 acute physiology variables, GCS, chronic-health flags, admission
source, pre-ICU LOS) plus four variables the investigators added that are *not* part of APACHE IV —
`Lactate`, `Base deficit`, `PEEP`, `Vasopressors`. Those four additions are the tell: someone was
testing whether lactate/base-deficit add predictive value over APACHE IV. That is a very common
critical-care research question.

### 2.3 The cohort is extreme and highly selected

- **75 of 78 (96%) are on invasive mechanical ventilation.**
- **77 of 78 have GCS-verbal recorded as `T`** (tubed — verbal response cannot be scored).
- **77 of 78 came from "Floor"** (a ward), only 1 from another hospital. No ED admissions.
- Median APACHE IV score **80.5** (range 26–148 of a possible 286); median *predicted* mortality
  **42.8%**.

This is not "an ICU cohort" — it is the sickest, ventilated, ward-deterioration slice of one. Any
statistic from it generalises to that group only.

### 2.4 Score internals (validated)

The arithmetic is internally consistent, which is a good sign for data entry:

- `APACHE IV SCORE` is stored as text `"110/286"`; `APS SCORE` as `"110/239"`. Parse the numerator.
- **APACHE IV ≥ APS in all 78 rows**, as it must be (APACHE IV = APS + age points + chronic-health points).
- The gap `APACHE IV − APS` correlates with age at **r = 0.911** — exactly the expected relationship.
- `Estimated mortality rate` correlates with the score at **r = 0.878**. It is the calculator's
  logistic output, *not* an observed death.

### 2.5 Data-quality defects

| Defect | Evidence | Severity |
|---|---|---|
| **No outcome recorded** | `Outcome` 0/78 filled; `Date of discharge or death` 2/78, both implausible (Apr & Sep 2024 — before or around admission) | **Critical** |
| **`WBC` units are mixed** | Header says `x1000/mm3`; 77 rows are 1,020–89,500 (raw cells/mm³), 1 row is 10.2 (thousands) | **Critical** |
| **Two mislabelled units** | `Urea(mEq/L)` ranges 10–438 → mg/dL; `Albumin(g/L)` ranges 1.7–5.1 → g/dL | High |
| **Six all-zero columns** | Hepatic failure, Metastatic carcinoma, Lymphoma, Leukemia/Myeloma, Immunosuppression, AIDS — zero variance | High |
| **`Vasopressors` is mixed-type** | 63 numeric `0` + 15 free-text drug strings with spelling/spacing variants (`" Noradrenaline"`, `"Vasopressin and Norade"`, `"Vasopressin and Norad"`) | High |
| **Composite key column** | Date + serial number in one cell | Medium |
| **Temperature is low-resolution** | Only **14 distinct values** across 78 patients; all are exact °F→°C conversions (36.556 = 97.8 °F, 38.33 = 101 °F) — recorded in Fahrenheit to the nearest degree, then converted | Medium |
| **Full PHI in plaintext** | Name, 10-digit mobile, 15-digit CR number, all 78 rows | **Critical (governance)** |

Cell-level completeness across the 47 substantive columns is **100%** — genuinely impressive, and the
reason this file still has value despite the missing outcome.

---

## 3. Dataset 2 — `NIMS TRIAGE 2023.xlsx`

### 3.1 Structure — four sheets, only two of them data

| Sheet | Excel size | Real content |
|---|---|---|
| `Form Responses 1` | 977 × 50 | **876 encounters, all male.** Google Form response sheet |
| `Sheet2` | 38 × 22 | **37 rows — a verified subset of `Sheet3`** (all 37 timestamps ⊂ Sheet3). Scratch copy |
| `Sheet3` | 454 × 21 | **435 encounters, all female. No header row** — data starts at Excel row 2 |
| `Sheet1` | 2168 × 1 | **Not patient data.** 1,191 disease names with NNDSS labels and ICD-10 codes — a dropdown/validation source list |

### 3.2 The sex split — the central discovery

| | `Form Responses 1` | `Sheet3` |
|---|---|---|
| `Sex` values | **1.0 in all 876 rows** | **0.0 in all 435 rows** |
| Patient overlap | \| | 1 name pair, 0 age agreement → coincidence |
| Timestamp overlap | **0** | **0** |
| Shared calendar days | **101 of 113** | |
| Shared staff | **25 of 26 collectors** | |
| Same collector, same day, both sheets | **155 of 216 (72%)** cells | |
| Median gap between consecutive cross-sheet submissions | **4 minutes** | |
| Volume ratio | 2.01 : 1 (M:F) | |

The same nurse, on the same morning, minutes apart, files a male patient into one sheet and a female
patient into the other. This is **one triage register split by sex**, almost certainly so that male
and female cohorts could be described separately. The 2.01:1 male:female ratio matches the 1.75:1
seen in the 2024 file — consistent with the same ED population.

**Consequence:** `Sex` is a *constant* within each sheet. It cannot be used as a predictor unless you
union the sheets first. Trauma rate differs meaningfully across the split (22% male vs 11% female),
so analysing one sheet alone gives a biased picture of the service.

### 3.3 What a row represents

One ED triage encounter, recorded on a **minimal Google Form**: timestamp, staff email, patient name,
age, sex, three presentation flags (trauma / cardiac / stroke / GI), free-text complaint, four vitals
(pulse, BP, SpO₂, respiratory rate), a shock-index flag, and the outcome of triage — `red=1`.

Timestamps run **June 2023 → August 2024**, with four stragglers in April 2025 — so the filename
"2023" marks when collection *started*, not what it covers. Only **113 distinct days** are present
across a 690-day span, in two bursts (Jun–Aug 2023, then Apr–Aug 2024). This is intermittent
research-style sampling, not continuous capture.

### 3.4 Columns worth flagging

- **`Unnamed: 13` is the blood pressure column** — its header was lost. Values are `"SBP/DBP"` text,
  97.9% parseable; the residue includes `"NR"`, `"40 systolic"`, `"120/8"`, `"11070mmhg"`, `"140)90"`.
- **`SI` is a derived variable.** It agrees with `HR/SBP ≥ 0.9` on **99.0%** of the 295 rows where
  both exist. It is redundant, only 35% filled, and leakage-prone.
- **`red=1` is the target.** 505 positive / 806 negative across the unified register = **38.5%
  positive** — an unusually high critical rate, suggesting "red" here means "needs a resuscitation
  bay", not "peri-arrest".
- **`Off hours triage=1` is unreliable.** Of 88 submissions between 18:00 and 23:59, **76 are coded
  `0`**. Do not trust this flag; derive off-hours from the timestamp instead.
- **`GI emerg` (14% filled) and `stroke` (29% filled)** were added or abandoned mid-study. Their
  missingness is structural, not random — never impute them.
- **19 columns at the right edge** (`Airway`, `GCS V`, `Pupils`, `Capillary Refill Time`…) are filled
  for only **4–5 of 880 rows**, all submitted in April 2025. These are the *2024 form's* questions
  bleeding into the old sheet — direct evidence the same Google Form was later rebuilt into Dataset 3.
- **12 columns are completely empty.**

### 3.5 `Sheet1` — the reference list

1,191 rows of the form `"<disease name><source><ICD-10 code>"`, e.g. `"ShigellosisNNDSSA03.9"`,
`"Cardiac tamponade I31.4"`. 94.9% end in a valid ICD-10 pattern; the chapter distribution is
injury-heavy (S: 205, T: 122, K: 111, I: 76), consistent with an ED. **The 2024 file contains the
identical list plus 3 extra entries** — proof of shared lineage between the two workbooks.

Critically, only **4 of 940** distinct complaint strings in the 2024 file match this list exactly.
**The list was never actually used to constrain data entry** — it sits there unused while staff typed
free text. This is your ready-made coding scheme for retrospectively structuring the complaint field.

---

## 4. Dataset 3 — `NIMS TRIAGE 2024 (Responses).xlsx`

### 4.1 Structure

| Sheet | Excel size | Real content |
|---|---|---|
| `Form Responses 1` | 3306 × 36 | **1,125 encounters** (rows 1126–3306 are blank — an autofilter range artefact) |
| `Sheet1` | 2168 × 1 | The same 1,191-row ICD list, plus 3 entries |

No hidden sheets, no formulas, no merged cells. Autofilter set on `A1:AK3306`.

### 4.2 What a row represents

One ED triage encounter recorded on a **substantially better form** — a full **ABCDE primary survey**:

| Stage | Fields captured |
|---|---|
| **A**irway | Airway status, Intervention (Airway) |
| **B**reathing | Respiratory rate, Bilateral air entry, SpO₂, Other findings, Intervention |
| **C**irculation | Pulse, Blood pressure, Capillary refill time, Other, Intervention |
| **D**isability | GCS E/V/M, Pupils, Focal neurological deficit, Intervention |
| **E**xposure | Temperature, Log roll, Intervention |
| Outcome of triage | **Area Triaged**, **ESI Triage Category** |

Plus pain score (NRS 0–10), CR number, name, age, sex, free-text complaint.

Timestamps run **Dec 2024 → Aug 2025**, but **96% of the volume falls in March–May 2025** across just
62 distinct days. Two-thirds of all records come from a single month (April 2025, n=708). Treat this
as a **~3-month intensive study window**, not a 9-month series.

### 4.3 The targets

**`ESI Triage Category`** — the Emergency Severity Index, 1 (resuscitation) to 5 (non-urgent):

| ESI | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| n | 129 | 376 | 492 | 111 | **14** |
| % | 11.5 | 33.5 | 43.9 | 9.9 | **1.2** |

ESI 5 has only 14 cases — **do not attempt 5-class classification.** Collapse to
`high acuity (1–2)` vs `lower acuity (3–5)`, which gives a near-balanced 45/55 split.

**`Area Triaged`** — Red Triage (583), Table 1 (372), Table 2 (170). This is **near-deterministic
given ESI**: 126 of 129 ESI-1 patients went to Red Triage; Table 2 received zero ESI-1 patients. It
is a *parallel expression of the same decision*, not an independent variable.

### 4.4 Physiology does stratify by ESI — modestly

Spearman correlation with ESI (positive = higher ESI, i.e. less sick):

| Variable | ρ | p |
|---|---|---|
| GCS total | **+0.220** | 3e-13 |
| SpO₂ | **+0.175** | 3e-09 |
| Respiratory rate | **−0.171** | 9e-09 |
| Heart rate | **−0.149** | 5e-07 |
| Shock index | −0.089 | 0.003 |
| Age | −0.064 | 0.03 |
| Systolic BP | +0.000 | 1.0 |
| Pain score | −0.008 | 0.79 |
| Temperature | +0.037 | 0.22 |

Every significant association points the physiologically correct way. But two are notable for being
*absent*: **systolic BP carries literally no signal** (ρ = 0.000), and **pain score — the only field
that is 100% filled — is unrelated to acuity**. The pain field is mandatory in the form and is being
completed reflexively.

### 4.5 Inter-rater variability is the biggest hidden structure

35 staff accounts; among the 22 with ≥20 records, the share of patients each one assigns to **ESI 1**
ranges from **0% to 48%**.

- Kruskal-Wallis (ESI ~ rater): **H = 131.3, p = 6×10⁻¹⁸**
- Between-rater SD of mean ESI = 0.336 vs overall SD = 0.854 — **rater identity alone explains a
  substantial fraction of the variance in the label**
- **Rater identity alone predicts high-acuity at AUC 0.631** (vs 0.72 for all the physiology combined)
- Five raters produce 37% of all records

Your label is not "the patient's acuity". It is "the acuity *this particular nurse* assigned". Any
model must be validated with **grouped cross-validation by rater**, and any inter-rater reliability
claim needs paired assessments that this dataset does not contain.

### 4.6 Data-quality defects

| Defect | Evidence |
|---|---|
| **CR Number is not a reliable key** | Only 1,021/1,125 have the expected 15 digits (observed lengths 9–18). 69 CR values repeat; **61 of those map to more than one patient name** |
| **Temperature mixes °C into a °F field** | 22 out-of-range values including 37.5 and 37.9 (Celsius) and 4.0 |
| **Impossible vitals** | SBP 700 and 11; DBP 199 and 10; HR 11 and 16; RR 0 and 65; SpO₂ 0; GCS total 16 (E+V+M with V=6) |
| **Free-text intervention fields are unusable** | `Intervention (Disability)` has 138 distinct values that are overwhelmingly `No` / `Nil` / `-` / `.`; same for Log Roll (65) and Intervention-Exposure (96) |
| **Complaint field is near-unique** | 967 distinct strings for 1,125 records; 27 differ only by capitalisation; 6.9% contain `?` (diagnostic uncertainty) |
| **Sex capitalisation** | `Male` (716), `Female` (408), `male` (1) |
| **Completeness collapses over time** | `Intervention (Airway)` fill rate falls 33% → 9% → 0% from Dec-2024 to Jul-2025; `Intervention (Breathing)` 33% → 7% |
| **`Disposition` and `GRBS` are ~empty** | The two columns that would have given you an outcome |
| **`Column 31`** | 13 rows of `"Option 1"` — a form artefact |

---

## 5. Cross-dataset relationship analysis

### 5.1 The linkage tests, and what they returned

| Test | Result | Interpretation |
|---|---|---|
| **CR number overlap** (APACHE ∩ 2024) | **0** of 78 vs 1,052 | No shared patients |
| **CR number overlap** (APACHE ∩ 2023) | **0** | 2023 form never collected CR numbers |
| **CR number overlap** (2023 ∩ 2024) | **0** | No shared patients |
| **Name overlap** APACHE ∩ 2024 | 1 pair, age differs by 16 y | Coincidence |
| **Name overlap** 2023 ∩ 2024 | 109 pairs, only 13 (12%) within 2 y of age | Mostly common-name collisions; the 13 plausible ones are 234–350 days apart — genuine re-attendances, far too few to join on |
| **Timestamp overlap** | 0 across all pairs | Disjoint collection windows |
| **Staff email overlap** | 2023↔2024: **18 shared**; 2023 FR↔Sheet3: **25 shared** | **Same clinical department** |
| **ICD reference list** | 2024 list = 2023 list + 3 entries, identical prefix | **Same workbook lineage** |
| **CR number format** | `3310-1-YY-NNNNNNNN`; APACHE 73/78 are year-2024 registrations, 2024 file 765/1052 are year-2025 | **Same hospital numbering system** |

### 5.2 What the three files actually are, relative to one another

They are **complementary, sequential snapshots of one service — not versions, not splits, not
train/test, not modalities of the same rows.**

```
         ED ARRIVAL                                    ICU ADMISSION
              │                                              │
   ┌──────────┴──────────┐                                   │
   │                     │                                   │
[Dataset 2]         [Dataset 3]                        [Dataset 1]
2023 triage         2024–25 triage                     APACHE IV
Jun23–Aug24         Dec24–Aug25                        Oct 2024
n=1,311             n=1,125                            n=78
minimal form        full ABCDE form                    manual + calculator
target: red=1       target: ESI 1–5                    target: NONE
   │                     │                                   │
   └────── same staff, same hospital, same CR system ────────┘
                    ZERO shared patients
```

Specifically:

- **Dataset 2 → Dataset 3 is an instrument upgrade of the same activity.** Same department, 18 shared
  staff, same ICD reference list, and 19 of Dataset 3's exact question names appear as vestigial
  columns in Dataset 2's sheet. Dataset 2's crude `red=1` binary became Dataset 3's standard 5-level
  ESI; four vitals became a full ABCDE survey. **This is a genuine before/after methods comparison.**
- **Dataset 1 is a different care setting entirely.** ICU, not ED. Its October 2024 window falls in
  the **gap between** the two triage collections (2023 file ends Aug 2024; 2024 file starts Dec 2024),
  so the non-overlap is chronological as much as clinical.
- **Nothing here is a raw/processed pair, a train/test split, or a duplicate** — except *inside*
  `APACHE 4.xlsx`, where `Sheet2` is a literal duplicate of `Sheet1`'s right-hand block, and inside
  `NIMS TRIAGE 2023.xlsx`, where `Sheet2` is a subset of `Sheet3`.

### 5.3 Can they be combined? — the only defensible answer per pair

| Combination | Verdict | Method |
|---|---|---|
| **2023 `Form Responses 1` + `Sheet3`** | ✅ **Yes — you must** | **UNION** (stack rows). This is one register. Add a `source_sheet` column. Result: 1,311 encounters with a working `Sex` variable |
| **2023 register + 2024 register** | ⚠️ **Union of the shared columns only** | Keep the 9 truly common fields (timestamp, age, sex, complaint, HR, BP, SpO₂, RR, trauma). Harmonise `red=1` ↔ `ESI≤2` **only as a sensitivity analysis** — they are different instruments and the mapping is an assumption, not a fact. Always keep an `era` column |
| **Any triage file + APACHE** | ❌ **No row-level join is possible** | Zero shared patients. Only **cohort-level comparison** ("how do ED triage vitals compare with ICU admission physiology?") is legitimate |
| **`APACHE Sheet1` + `Sheet2`** | ❌ **Never merge** | Sheet2 is a duplicate. Merging would silently duplicate 23 columns |

**Do not merge on `CR Number`.** Even within Dataset 3 it fails: 61 CR values map to more than one
patient name, and a quarter have the wrong digit count.

---

## 6. Data-quality scorecard

Scores computed from the measured statistics (`csv/data_quality_scorecard.csv`), 0–100.

| Dimension | D1 APACHE | D2 2023 (unified) | D3 2024 |
|---|---|---|---|
| **Completeness** (substantive columns) | **100.0** | 96.8 | 98.7 |
| **Consistency** (type/unit/spelling discipline) | 91.5 | 80.0 | 80.0 |
| **Validity** (values physiologically possible) | 97.0 | 98.0 | 97.5 |
| **Uniqueness** (duplicate freedom) | **100.0** | 98.8 | 99.3 |
| **Structure** (one clean table, headers, keys) | 65 | **45** | 80 |
| **Documentation** (self-describing headers, codebook) | **25** | 20 | 55 |
| **ML readiness** | 50.6 | 88.5 | **92.1** |
| **OVERALL** | **77.2** | **80.2** | **88.1** |

Reading the scores:

- **APACHE scores highest on data hygiene and lowest on usefulness.** Perfect completeness, zero
  duplicates — and no target, n=78, six dead columns. It is a beautifully kept notebook of an
  experiment whose conclusion was never written down.
- **2023 is structurally the worst** (45): a headerless sheet, a hidden sex split, a lost BP header,
  a subset scratch sheet, cryptic `=1` headers, no patient identifier.
- **2024 is the strongest overall** and the only one with both a real target and enough rows.
- **Documentation is poor everywhere.** No codebook exists for any file. Every coding scheme in this
  report (`Sex 1=male`, `red=1`, `T`=tubed, `BERTL`) was *inferred from the data*, not read from
  documentation.

---

## 7. Use-case matrix

Legend: ✅ strong · 🟡 possible with caveats · ❌ inappropriate

| Use case | D1 APACHE (n=78) | D2 2023 (n=1,311) | D3 2024 (n=1,125) | Combined |
|---|---|---|---|---|
| Descriptive epidemiology / case-mix | ✅ | ✅ | ✅ | ✅ |
| Data visualisation / dashboard | 🟡 small n | ✅ | ✅ | ✅ |
| Hypothesis testing (group comparisons) | 🟡 underpowered | ✅ | ✅ | ✅ |
| **Instrument/methods comparison (2023 vs 2024 form)** | ❌ | ✅ | ✅ | ✅ **strongest combined use** |
| Sex-difference analysis in ED presentation | 🟡 62M/16F | ✅ **by design** | ✅ | ✅ |
| Binary classification (acuity) | ❌ no target | ✅ AUC ≈ 0.70 | ✅ AUC ≈ 0.72 | 🟡 era confounded |
| Ordinal 5-class ESI prediction | ❌ | ❌ | 🟡 ESI-5 n=14 | 🟡 |
| Regression (predict a score) | ❌ circular | ❌ | ❌ | ❌ |
| Clustering / phenotyping | ❌ n too small | 🟡 | ✅ | 🟡 |
| Anomaly detection | 🟡 QA use only | 🟡 QA use only | ✅ **data-entry QA** | 🟡 |
| Time-series / forecasting | ❌ 1 month | ❌ 113 scattered days | ❌ 62 days, 1 month dominant | ❌ |
| Longitudinal / repeated measures | ❌ | ❌ | ❌ one row per encounter | ❌ |
| Survival analysis | ❌ **no outcome** | ❌ | ❌ | ❌ |
| Mortality prediction | ❌ **no outcome** | ❌ | ❌ | ❌ |
| **Inter-rater variability study** | ❌ | ✅ 27 raters | ✅ **35 raters, huge effect** | ✅ |
| APACHE IV external validation | ❌ needs outcomes | ❌ | ❌ | ❌ |
| NLP on complaint text | 🟡 78 strings | 🟡 626 strings | ✅ 967 strings + ICD list | ✅ |
| Clinical deployment / decision support | ❌ | ❌ | ❌ **not validated, no outcomes** | ❌ |

---

## 8. ML opportunity assessment

I ran these as real baselines, not estimates. Code: `15_baseline.py`.

### Opportunity A — High-acuity triage classification (Dataset 3) · **the best available**

| | |
|---|---|
| **Inputs** | age, sex, HR, SBP, DBP, RR, SpO₂, temperature, pain, GCS total, shock index, CRT>3s, focal deficit, airway-not-patent |
| **Target** | `ESI ≤ 2` (high acuity) vs `ESI ≥ 3` — n=1,122, 45.0% positive |
| **Preprocessing** | Parse `"SBP/DBP"` text; recompute GCS as E+V+M (the `GCS` column is only 7/1,125 filled); convert the 22 Celsius temperature entries; clip impossible vitals to NaN and impute by median; **drop `Area Triaged`** |
| **Models** | Logistic regression (interpretable baseline), HistGradientBoosting |
| **Measured result** | LogReg **AUC 0.732** (random 5-fold) / **0.725** (grouped by rater); HistGB **0.726 / 0.719** |
| **Top features** (permutation importance) | SpO₂ 0.051, age 0.038, shock index 0.037, RR 0.019, HR 0.014, GCS 0.011 |
| **Metrics to report** | AUROC + **AUPRC**, sensitivity at a fixed high-sensitivity operating point (under-triage is the dangerous error), calibration curve |

**Risks, measured:**

- **`Area Triaged` leakage — demonstrated.** Adding it lifts AUC from 0.726 to **0.857**. That 0.13 is
  pure leakage. It is assigned *with* the ESI.
- **Rater effect — measured.** Rater identity alone gives **AUC 0.631**. Grouped-by-rater CV barely
  drops the score (0.726→0.719) *only because raters see similar case mixes*; that does not make the
  label objective. Always report the grouped number.
- **Temporal concentration.** 63% of rows are from a single month. A random split mixes the same
  week's patients across train and test.
- **Ceiling is real.** ~0.72 from vitals is the honest number. The signal that would push it higher —
  the free-text complaint — is unstructured.

### Opportunity B — "Red flag" classification (Dataset 2)

Target `red=1`, n=1,306, 38.6% positive. **HistGB AUC 0.719 grouped by rater** (LogReg 0.678).
Notably, **rater identity alone gives AUC 0.499 — no rater effect at all**, in sharp contrast to
Dataset 3. The cruder binary label was applied far more consistently than the 5-level ESI.
**Requires the sheet union first**, or `Sex` is a constant.

### Opportunity C — Complaint-text structuring · **highest practical value, lowest risk**

Map 967 free-text complaints onto the 1,191-entry ICD-10 list already sitting unused in `Sheet1`.
Fuzzy/embedding match, human review of low-confidence matches. This is not prediction — it is the
enabling step that makes everything else in the file analysable, and it produces a reusable asset.

### Opportunity D — Data-entry anomaly detection

Isolation Forest / rule ensemble over vitals to flag implausible entries at submission time. You
already have the training signal: SBP 700, temperature 4, GCS 16, SpO₂ 0.

### ❌ Opportunities to reject

- **Mortality prediction from APACHE** — no outcome exists. If you later add one: at ~40% mortality
  that is 31 events for 47 candidate predictors = **0.7 events per variable**; you need ≥10.
- **Regressing `Estimated mortality rate` or `Estimated LOS`** — these are deterministic calculator
  outputs of the same input columns. You would be fitting a formula, and reporting an R² near 1 as if
  it meant something.
- **5-class ESI** — 14 cases in class 5.
- **Any patient-level join across the three files** — zero overlap.

### The leakage checklist for this data specifically

1. Drop `Area Triaged` from any ESI model.
2. Drop `SI` from any 2023 model, or drop HR and SBP — not all three.
3. Drop the `Intervention (*)` columns from acuity models: they record what was done *in response* to
   the assessment.
4. Drop `GCS` (the total) when using E/V/M.
5. Never random-split without grouping by rater; report the grouped number as the headline.
6. If you union 2023 + 2024, an `era` column is mandatory — otherwise the model learns "which form
   was this" rather than "how sick is this patient".

---

## 9. Recommended visualisations

Generated in `analysis_output/plots/`:

| # | Plot | What it establishes |
|---|---|---|
| 01 | Monthly volume, all three collections | The three windows do not overlap; the ICU month sits in the triage gap |
| 02 | Age × sex histograms per dataset | Case mix is comparable; ICU cohort is not a subset |
| 03 | ESI distribution + Area×ESI stacked bars | Class imbalance and the Area-Triaged leakage |
| 04 | Vitals boxplots by ESI (small multiples) | Real but heavily overlapping separation |
| 05 | % ESI-1 by rater | The 0–48% inter-rater spread |
| 06 | Missingness maps | Abandoned form questions; APACHE's empty outcome columns |
| 07 | APACHE score vs predicted mortality; score−APS vs age | The score's internal arithmetic; why mortality is circular |
| 08 | Correlation matrices (APACHE physiology; 2024 vitals) | Derived-variable blocks; weak inter-vital correlation |
| 09 | RR / SpO₂ / HR densities by red-flag status | What actually drives the 2023 label |

**Worth building next:** a Sankey of ESI → Area Triaged; a calibration plot once a model is fit; a
per-rater ESI distribution heatmap; a complaint-category treemap after the ICD mapping.

---

## 10. Limitations — what the data proves, infers, and cannot tell you

### Proven by the data
- Row counts, date ranges, column semantics for all high-confidence fields.
- The 2023 sex split (100% constant `Sex` within each sheet).
- Zero patient overlap across the three files (exact set intersection on CR numbers).
- `APACHE Sheet2` is a byte-equivalent duplicate of `Sheet1`'s columns AA:AW.
- `SI` = `HR/SBP ≥ 0.9` (99.0% agreement).
- The inter-rater effect (p = 6×10⁻¹⁸) and the `Area Triaged` leakage (ΔAUC = +0.13).
- The 2024 ICD list = the 2023 list + 3 entries.

### Reasonably inferred
- **Same hospital** — from the shared 15-digit CR format (`3310-1-YY-…`), 18 shared staff accounts,
  and the shared reference list. *Confidence: high.*
- **`Sex`: 1 = male, 0 = female** — from the 2024 file's explicit labels producing the same ~2:1 ratio
  and the same trauma differential. *Confidence: high.*
- **APACHE is a prospective research dataset**, from the four non-APACHE additions (lactate, base
  deficit, PEEP, vasopressors) and the one-month consecutive design. *Confidence: medium-high.*
- **The 2023→2024 form change was an instrument upgrade**, from the vestigial columns and shared staff.
  *Confidence: high.*
- **The 2023 sex split was deliberate analytic separation** rather than two physical stations —
  the 4-minute cross-sheet interleaving by the same collector makes two locations implausible.
  *Confidence: medium.*

### Cannot be established from these files
- **The hospital's identity.** "NIMS" in the filename is suggestive; nothing inside the files confirms
  it. I am not going to assert a provenance the data does not carry.
- **Any patient outcome** — survived, died, admitted, discharged. Not present in any of the three files.
- **Whether triage decisions were correct.** No reference standard, no expert re-review, no outcome.
- **Ethics approval, consent, or study protocol.** Nothing in the metadata speaks to governance.
- **Why the 2023 collection paused Sep 2023 – Mar 2024**, or why the 2024 collection is 63% April.
- **Whether blank interventions mean "none performed" or "not recorded".** This distinction changes
  the meaning of ~90% of those columns, and only the collecting team can resolve it.
- **Who "Ashima Sharma" is** relative to the study — only that this account created `APACHE 4.xlsx`.

### Governance
All three files contain **direct identifiers** (names; a phone number column in APACHE; CR numbers;
staff emails). Before any sharing, publication, or cloud analysis: drop `NAME`, `PHONE No`, and
`CR No`; replace staff emails with salted hashes; consider date-shifting. Confirm the ethics approval
covers secondary analysis.

---

## 11. Prioritised next steps

**Do first — these unblock everything else**

1. **Union the two 2023 sheets.** Add a `source_sheet` column, restore the lost BP header, add a
   proper header row to `Sheet3`. Without this you are analysing men only. *(Done — see
   `csv/unified_2023_register_DEID.csv`.)*
2. **Go and get the outcomes.** For the 78 APACHE patients you have CR numbers and a one-month window
   — the ICU discharge register will close this in an afternoon. **This single action converts the
   weakest file into a publishable APACHE IV external-validation study.** It is by far the highest-value
   action available to you.
3. **Write a codebook.** One page per file: every column, its coding, its units. Everything in §2–§4
   of this report was reverse-engineered; the next person should not have to.
4. **De-identify** and store the analysis copies separately from the originals.

**Do next**

5. Fix the known unit defects: WBC (mixed scales), Urea and Albumin (mislabelled), the 22 Celsius
   temperature entries.
6. Map the free-text complaints onto the ICD list already in `Sheet1`, and **switch the live form to a
   dropdown backed by it** so this problem stops recurring.
7. Delete `APACHE Sheet2` and `NIMS 2023 Sheet2` from working copies — both are duplicates that invite
   a bad merge.

**Then, the analyses actually worth doing**

8. ~~**The 2023-vs-2024 instrument comparison.**~~ **CORRECTED 2026-08-20 — this recommendation was
   wrong.** I subsequently tested every candidate before/after outcome and all are null or untestable:
   core-vitals completeness 97.2% → 96.1% (RD −1.1 pp, 95% CI −2.5 to +0.4, p = 0.167 — the old form was
   already at ceiling); within-rater high-acuity rate +2.0 pp (95% CI −16.8 to +20.9); ICC difference
   +0.039 (95% CI −0.098 to +0.146). The apparent gain in "information captured" (4 → 12 items) is
   tautological, since the 2024 fields did not exist on the 2023 form. Case-mix also drifted between eras
   (RR SMD +0.232, SpO₂ SMD −0.284), and a two-period design cannot separate the instrument from
   everything else that changed. **Do not build a paper on this.** See `protocol.html` §1.
9. **The inter-rater variability study — this is the strongest study in the three files.** Between-clinician
   variation in high-acuity designation is large (ICC 0.113, 95% CI 0.041–0.205; median odds ratio 2.0–2.7),
   survives adjustment for all 16 physiology variables, and replicates independently in the 2023 cohort
   under a different instrument (ICC 0.074, 95% CI 0.016–0.186). Full protocol in `protocol.html`.
10. Fit the acuity model with grouped CV, report AUROC/AUPRC and calibration, and present it as a
    research finding — not a tool.
11. Add a `Disposition` field to the live form. It is the outcome you are missing, it is free to
    collect, and without it none of this can ever become outcome-linked research.

---

## 12. Plain-English verdict

**What exactly do I have?**
Three clinical data collections from one hospital's emergency and critical-care service: two
generations of an emergency-department triage register (1,311 and 1,125 patient encounters), and one
month of ICU severity scoring on 78 ventilated patients. They were collected by overlapping staff
using the same hospital's registration system, over three periods that do not overlap.

**What does it contain?**
Vital signs, presenting complaints, and a triage urgency decision for ~2,400 ED patients; and a
complete APACHE IV physiology panel for 78 ICU admissions. Identifiable patient data throughout. No
patient outcomes anywhere.

**How are the three related?**
Same hospital, same department, **zero shared patients**. Datasets 2 and 3 are the *same activity
before and after a form redesign* — that is the real relationship. Dataset 1 is a different care
setting in the calendar gap between them. Inside the 2023 file, two sheets are one register split by
sex and must be recombined; inside the APACHE file, one sheet is a duplicate of the other.

**What can I realistically do?**
Descriptive epidemiology, sex- and acuity-stratified comparisons, a genuine before/after comparison of
the two triage instruments, an inter-rater variability study, and a research-grade acuity classifier
at AUC ≈ 0.72. What you cannot do is anything requiring an outcome — no mortality prediction, no
survival analysis, no validation of whether the triage decisions were right.

**Which is most useful?**
**`NIMS TRIAGE 2024 (Responses).xlsx`** — 1,125 rows, a structured ABCDE assessment, a standard ESI
target, and the best quality score (88/100). But the **most valuable single asset is the 2023-vs-2024
pair**, because a before/after instrument comparison in the same department is a study you can write
today with no new data.

**Can they be combined?**
The two 2023 sheets: **yes, and you must** — union them. The 2023 and 2024 registers: **yes, on the
nine shared columns only**, with an `era` flag and the harmonised target treated as an assumption.
APACHE with either triage file: **no** — zero shared patients means cohort comparison only, never a
row-level join.

**Are they ML-ready?**
Dataset 3: yes, for research. Dataset 2: yes, after the union. Dataset 1: **no** — it has no target
and 78 rows. And none of the three is remotely ready for a deployed clinical tool, because none
contains an outcome against which "correct" could be defined.

**Biggest limitations?**
(1) **No outcomes anywhere** — the ceiling on everything. (2) **Zero patient overlap** — no
longitudinal view of anyone. (3) **Inter-rater variability** — your 2024 label is partly a measure of
who was on shift. (4) **Free-text everywhere** — 967 distinct complaints, 138 spellings of "no
intervention". (5) **Identifiable data** in three unprotected files.

**What should I do next?**
Recover the ICU outcomes for the 78 APACHE patients — one afternoon in the discharge register turns
your weakest file into a publishable validation study. Union the 2023 sheets. Write a codebook. Then
run the 2023-vs-2024 instrument comparison, which is sitting there fully formed and needs nothing new.

---

### Appendix — generated artefacts

All outputs are in `analysis_output/`; the three source workbooks were opened read-only and are
unmodified (checksums in §0 match).

| Path | Contents |
|---|---|
| `csv/DATA_DICTIONARY.csv` | 152 columns: dataset, worksheet, column, type, examples, description, units, role, missing %, unique count, notes, confidence |
| `csv/column_profile_raw.csv` | Machine-generated statistics for every column |
| `csv/data_quality_scorecard.csv` | The seven-dimension scores in §6 |
| `csv/dataset_summary.csv` | One-line summary per dataset |
| `csv/unified_2023_register_DEID.csv` | **The reconstructed 1,311-encounter 2023 register** (de-identified, BP parsed) |
| `csv/triage_2024_DEID.csv` | 2024 register, de-identified, vitals parsed, GCS recomputed |
| `plots/01–09*.png` | The nine figures in §9 |
| `01_inventory.py` … `15_baseline.py` | Every step, re-runnable in order |
