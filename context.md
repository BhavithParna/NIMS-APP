# Context — Research Direction & NIMS Dataset Assessment

*Compiled 28 August 2026. Working document for Bhavith (B.Tech Biomedical Engineering, BVRIT, 2027).*

> **Privacy note:** this file deliberately contains **no patient names, phone numbers, CR/MRN numbers, or collector email addresses**. Only aggregate statistics and column-level findings are recorded here. See §4.

---

## 1. Where this started

The original brief was to find **software-first biomedical/healthcare project ideas** that could become both a publishable paper and a deployable platform, under hard constraints:

- No proprietary clinical datasets
- No patient recruitment, no ethics-clearance-heavy work
- No generic diagnosis/prediction models ("AI symptom checker" explicitly ruled out)
- Buildable end-to-end by a small team (essentially solo) in 3–9 months
- Evaluable via public data, synthetic data, simulation, or non-patient user studies

An extensive research pass produced a report of ~22 ideas across six domains. The recurring structural insight:

> **The real openings are in verification, observability, provenance, and governance layers — not in new predictors.** Across BCI, lab automation, and clinical AI, the unglamorous "meta-tooling" is where reproducibility and safety failures actually live, and it is consistently underserved.

### Top three ideas from that report

| # | Idea | Why it ranked |
|---|---|---|
| **A1** | **Real-time BCI pipeline observability toolkit** — "Grafana/OpenTelemetry for neural streams". Live LSL monitoring for dropped samples, clock drift, timestamp jitter, marker–EEG desync, decoder latency. | Confirmed empty niche. Existing tools are either offline XDF diagnostics (LabRecorder) or raw live viewers (MNE-LSL StreamViewer, Timeflux). Perfect fit with existing LSL/PsychoPy/BCI skills. Venues: JOSS/SoftwareX, JNE, EMBC. |
| **A2** | **Hardware-free c-VEP/SSVEP stimulus-timing verifier + reproducibility benchmark** | Frame-accurate timing verification currently *requires* hardware (photodiode, Black Box Toolkit, StimTracker). No software-only validator exists. Needs only own lab — photodiode as ground truth. Venues: JNE, Behavior Research Methods. |
| **B1** | **Silent-mode clinical-AI monitoring harness on public waveform datasets** (PTB-XL, MIMIC-IV Waveform) | Directly extends existing work on SQI / embedding drift / conformal risk control. Turns it into an open, citable benchmark + toolkit. Venues: JAMIA, npj Digital Medicine, ML4H. |

Full ranked shortlist and idea bank live in the earlier report artifact.

---

## 2. Then: three NIMS datasets arrived

Three Excel files were uploaded and inspected. They are **real, identifiable clinical data from a tertiary hospital** — which sits in direct tension with the constraints in §1. That tension is the central strategic question now open.

### 2.1 `APACHE_4.xlsx` — ICU severity scoring

**80 rows × 51 columns.** Two sheets (Sheet2 is a partial duplicate of Sheet1's right-hand columns).

Contains: demographics, vitals (temp, MAP, HR, RR), ventilation status, FiO2, ABG (pO2, pCO2, pH), electrolytes, urine output, creatinine, urea, BSL, albumin, bilirubin, haematocrit, WBC, GCS components, chronic health conditions (cirrhosis, hepatic failure, metastatic CA, lymphoma, leukemia/myeloma, immunosuppression, AIDS), APACHE IV and APS scores, estimated mortality and LOS, lactate, base deficit, PEEP, vasopressors, diagnosis.

**Blocking problems:**

| Problem | Detail |
|---|---|
| **No outcomes** | `Outcome` column is **100% empty** (0 of 78 filled). `Date of discharge or death` filled for **2 of 78**. |
| Scores stored as text | `APACHE IV SCORE` = `"110/286"`, `"134/286"` (score/max). `APS SCORE` = `"110/239"`. `Estimated length of stay` = `"    6.5 Days"` with leading whitespace. |
| GCS-verbal unusable | `V` = `"T"` (intubated) for **77 of 78** patients; exactly one numeric value. |
| Sample size | n=80 — thin for any modelling. |
| Header hygiene | Leading/trailing whitespace throughout; `Date` and `S.No` merged into one column. |

**Consequence:** the natural study — does APACHE-IV's predicted mortality match observed mortality in an Indian tertiary ICU? — is **not possible as the data stands**. That is a calibration/validation question and it requires the outcome variable.

### 2.2 `NIMS_TRIAGE_2023.xlsx` — ED triage, 2023

**880 rows × 50 columns** (sheet `Form Responses 1`). Google Forms export.

**Blocking problems:**

- **Visible schema drift.** 25 of the 50 columns have between **0 and 4** non-null values — the form was redesigned mid-collection and the export preserves both schemas side by side.
- **Duplicate column names:** `Respiratory Rate` twice, `INTERVENTION` three times, `Other` twice, `Saturation` twice.
- **Unlabelled clinical field:** blood pressure sits in a column named `Unnamed: 13`.
- Sparse fields: `GI emerg=1` (124/876), `stroke=1` (252/876), `SI` (311/876), `venti=1, O2=2` (26/876), `Additional information` (22/876).
- `Disposition`, `Breathing`, `CR NO` columns are entirely empty.

### 2.3 `NIMS_TRIAGE_2024__Responses_.xlsx` — ED triage, 2024–25

**1,133 rows × 36 columns.** The most usable of the three, and the most informative about *how* the collection failed.

Contains a full ABCDE assessment: airway, breathing (RR, bilateral air entry, SpO2), circulation (pulse, BP, CRT), disability (GCS E/V/M, pupils, focal deficit), exposure (temperature, log roll), plus interventions at each stage, pain score, GRBS, area triaged, ESI category, and disposition.

**Collection-process findings:**

| Finding | Value |
|---|---|
| Date range | 1 Dec 2024 → 15 Aug 2025 |
| **Distinct days with any data** | **62** (out of ~257 calendar days) |
| Monthly volume | Dec-24: 3 · Feb-25: 10 · **Mar-25: 313** · **Apr-25: 708** · May-25: 53 · Jun-25: 8 · Jul-25: 29 · Aug-25: 1 |
| **Distinct submitters** | **35** individuals sharing one form |
| Duplicate CR numbers | 73 (re-presentations or re-entry) |
| **`Disposition` fill rate** | 261/1125 overall (23%); **by month: Mar 0.40 → Apr 0.18 → May onward 0.00** |

**Data-quality findings:**

| Field | Problem |
|---|---|
| **`Log Roll`** | **65 distinct values** for a Yes/No field: `No`, `-`, `.`, `` (blank), `Nil`, `Nill`, `Not required`, `Not done`, `Na`, `Non traumatic case`, `"No "` (trailing space), `Yes`… |
| **`Pupils`** | **45 distinct values.** 1,080 are `BERTL`; the remainder is free text (`Anisocoria rt - 3mm, lt -4mm`, `Can't be assessed`, `NSRL`, `NRL`…). |
| `Airway` | Contradictory multi-selects: `"Patent, Threatened"` (5), `"Patent, Intubated outside"` (3), `"Threatened, Intubated outside"` (2). |
| `Bilateral Air Entry` | `"Present, Absent"` (5 records). |
| `Blood Pressure` | Free text. 96.6% parse as `sys/dia`; the rest: `60 systolic`, `110/80mmHg`, `90/6`, `NR`, bare `345`, bare `50`. |
| `Sex` | `Male` / `Female` / `male` (case inconsistency). |
| `Disposition` | 17 distinct values including `Disposition` itself as a value (18×) and truncated `Medical Gastroenterolog`. |

**No range validation at entry** — impossible physiological values survived:

- Temperature **4.0 °F** (also 108 °F)
- SpO2 **0**
- Pulse **11** and **243**
- Respiratory rate **0**
- One GCS-V of **6** (maximum is 5)

**A genuine clinical signal already visible — acuity vs. physical placement:**

| Area Triaged | ESI 1 | ESI 2 | ESI 3 | ESI 4 | ESI 5 |
|---|---|---|---|---|---|
| Red Triage | 126 | 332 | 106 | 15 | 3 |
| Table 1 | 3 | 30 | 270 | 60 | 9 |
| Table 2 | 0 | 14 | 116 | 36 | 2 |

**124 patients rated ESI 3–5 were placed in Red Triage; 3 ESI-1 patients went to Table 1.** Acuity score and physical placement disagree systematically.

---

## 3. What can and cannot be done with this data

### Ruled out

- **APACHE-IV validation / calibration study** — no outcome variable.
- **Mortality or deterioration prediction** — no outcome variable, and 1,125 rows with 23% disposition capture would be weak regardless.
- **Any generic triage prediction model** — this is exactly the "yet another prediction model" pattern the original brief ruled out.

### Path 1 — Inter-rater variability in ESI assignment *(strongest; needs no outcomes)*

1,123 encounters, full vitals, and the identity of the triaging clinician for each. Fit a mixed-effects model with rater as a random effect: **how much of the variance in assigned acuity is attributable to who was on shift rather than to the patient?**

- Well-defined clinical-informatics question, answerable with what exists
- Requires zero outcome data
- **Caveat:** collector identities are personal email addresses. These must be replaced with anonymous rater IDs before analysis, and the framing must be *system-level variation*, not evaluation of individual residents — both an ethics requirement and a practical one.

### Path 2 — Data-capture failure case study + corrective tooling *(connects to §1)*

The problems catalogued in §2.3 are themselves the finding: a quantified portrait of ad-hoc form-based clinical data capture failing — schema drift mid-study, free text where categoricals belong, no range validation, no completion enforcement, outcome capture decaying to zero within eight weeks, 35 uncoordinated data enterers.

This motivates building the fix: a capture layer with **entry-time validation, controlled vocabularies, schema versioning, and completion tracking.**

- **Evaluation:** replay the ~2,000 historical records through the validator and measure what it would have caught (the 65 `Log Roll` variants, the impossible vitals, the contradictory multi-selects), plus a small user study with medical students entering identical scenarios into the old form vs. the new one.
- **Critical advantage:** column-level error rates and completeness statistics are publishable **without releasing a single patient row**, which drops the ethics burden dramatically versus a clinical audit.
- **This is the same thesis as idea A1** — verification and observability rather than prediction — applied to clinical data entry instead of neural streams. It compounds with the existing research direction.
- Venues: JAMIA, JMIR Medical Informatics, BMC Medical Informatics & Decision Making.

### Path 3 — Data quality audit as the paper itself

A completeness / plausibility / consistency audit framed against Kahn et al.'s conformance–completeness–plausibility taxonomy. Smaller contribution, but a legitimate short paper and the fastest route to a first publication.

### Path 4 — Acuity vs. placement audit

The ESI × Area Triaged mismatch above, as a resource-utilisation and safety question. Small clinical audit paper; needs ethics approval but retrospective audits of routinely collected data are the easiest kind to obtain.

---

## 4. Privacy and permissions — unresolved

All three files contain **direct identifiers** on ~2,000 patients:

- Full patient names
- Phone numbers (APACHE file)
- Hospital CR numbers (appear to be NIMS MRNs)
- Personal Gmail addresses of ~35 data collectors

**Required actions:**

1. Split identifiers (`Name`, `Phone No`, `CR Number`, `Email Address`) into a separate key file; work only from the de-identified copy.
2. Do not upload or share raw versions further.
3. Replace collector emails with anonymous rater IDs before any analysis touching Path 1.
4. Establish what ethics approval and data-use permission exist before any publication is attempted.

**Note the strategic tension:** this dataset moves the work *into* the ethics-and-permissions world that the original brief in §1 was specifically designed to avoid. Path 2 is the one that partially escapes it, since aggregate error statistics can be published without patient-level data.

---

## 5. Supervisor thread

Message sent to guide (11:47): summarised that APACHE has very limited usable outcome data and the 2023/24 triage datasets have many inconsistencies; asked how to proceed.

Guide's reply (11:50): **"What are the exact problems you're facing? If you can list them clearly we'll discuss."**

Two response drafts were prepared:

- **Variant A — problems only.** Matches what was literally asked for; leaves him to lead the discussion. Safer if he prefers to direct the research himself.
- **Variant B — problems plus three proposed directions.** Stronger if he rewards initiative.

Both end on the same pivot question, which is the highest-leverage unknown:

> **Can outcomes (survived/died, ICU length of stay, final disposition) be retrieved retrospectively from the HIS or case sheets for these patients?**

If **yes** → APACHE-IV validation reopens (n=80 is thin but workable for a calibration study, especially if collection resumes), and the triage data becomes usable for outcome-linked work. This becomes a clinical study.

If **no** → the work shifts to Paths 1–3, which need no outcomes. This becomes a data-quality and tooling study.

Variant B also asks explicitly what ethics approval and data permissions exist.

---

## 6. Open questions

1. **Can outcomes be retrieved retrospectively?** (Determines everything — see §5.)
2. **What is the provenance and permission status of these files?** Handed over for a college project vs. data with publication rights are very different situations.
3. **Is triage data collection still active, or can it be restarted** with a corrected instrument? If yes, Path 2 gains a prospective arm and becomes considerably stronger.
4. **Does the guide want a clinical paper or is a methods/informatics paper acceptable?** This decides between Path 4 and Path 2.
5. **How does this fit alongside the §1 research direction?** The BCI observability work (A1/A2) and the clinical-AI monitoring work (B1) remain the stronger long-term bets for the PhD/MS narrative. Path 2 is the only NIMS direction that genuinely compounds with them.

---

## 7. Suggested immediate next steps

1. Send the chosen variant to the guide; get an answer on outcome retrieval.
2. In parallel, build the de-identified working copies of all three files.
3. Regardless of the guide's answer, run the Path 3 audit — it is cheap, it is a deliverable in its own right, and it is the evidence base for Path 2.
4. Do not let this displace A1/A2. The NIMS data is an opportunity, not the plan.
