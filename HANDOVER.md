# HANDOVER — NIMS Clinical Data-Capture Platform: Strategy, Research & Plan

**Compiled 28 August 2026.** This document is a complete handover of a product-strategy + research-planning session. It contains: the project context, what the datasets established, the user-confirmed decisions, three deep research passes (eCRF/EDC landscape, FHIR/India health-IT, India regulation), the gap analysis, the ranked directions, the MVP definition, the research/publication program, and the roadmap. It is self-contained — the reader needs nothing else except the files listed in §1.3.

---

## 1. Project context

### 1.1 Who / where
- **Bhavith Parna** — B.Tech Biomedical Engineering, BVRIT (graduating 2027). Working **solo**, ~**3–6 months** build window.
- **Prof. Ashima Sharma**, Emergency Medicine, **NIMS Hyderabad** (Nizam's Institute of Medical Sciences — state government tertiary teaching hospital, MD residents). She is the guide/supervisor and authored the APACHE file.
- The professor expects **a working app for the department** — not just a paper.

### 1.2 The problem (evidence-based, not hypothetical)
Three real datasets from NIMS's ED/ICU document catastrophic ad-hoc clinical data capture on shared Google Forms:
- **65 distinct values** in a Yes/No field (`Log Roll`: `No`, `-`, `.`, `Nil`, `Nill`, `Not required`, `Non traumatic case`…)
- **Impossible vitals accepted**: SpO2 = 0, temperature 4.0°F, SBP 700, pulse 11 and 243, RR 0, GCS-V = 6 (max is 5)
- **Contradictory multi-selects**: "Patent, Intubated outside"; "Present, Absent" for bilateral air entry
- **Mid-study schema drift**: 2023 form redesigned mid-collection, both schemas side by side; 25/50 columns nearly empty; duplicate column names; BP in a column named `Unnamed: 13`
- **35 uncoordinated collectors** sharing one form login (personal Gmail addresses recorded)
- **Outcome capture decayed 40% → 0% within 8 weeks** (Disposition fill rate by month: Mar 0.40 → Apr 0.18 → May onward 0.00)
- **Broken patient IDs**: only 1,021/1,125 CR numbers have the expected 15 digits; 61 CR values map to >1 patient name
- **Identifiable PHI** (names, phones, CR numbers) collected with zero governance

### 1.3 Key files (all in `~/Documents/APP for nims /`)
- `APACHE 4.xlsx` — ICU APACHE-IV scoring, n=78, Oct 2024. **Outcome column 100% empty.**
- `NIMS TRIAGE 2023.xlsx` — ED triage, n=1,311 (⚠ split across two sheets **by sex** — must union; `Form Responses 1` = males only, `Sheet3` = females only)
- `NIMS TRIAGE 2024 (Responses).xlsx` — ED triage full ABCDE, n=1,125, ESI 1–5 target
- `analysis_output/REPORT.md` — **authoritative forensic analysis** (checksums, defect catalog, baselines, leakage analysis). Read this first.
- `analysis_output/csv/` — de-identified working copies (`triage_2024_DEID.csv`, `unified_2023_register_DEID.csv`), `DATA_DICTIONARY.csv`, quality scorecard
- `context.md` — earlier strategy document (research direction, supervisor thread)

### 1.4 Findings already settled — DO NOT re-derive
- **The 2023-vs-2024 instrument-comparison study is NULL.** Tested and corrected in REPORT.md §11.8 (completeness was already at ceiling; case-mix drifted; two-period design can't isolate the instrument). Do not build a paper on it.
- **Inter-rater ESI variability is the strongest study in the data**: ICC 0.113 (95% CI 0.041–0.205), median odds ratio 2.0–2.7, survives adjustment for all 16 physiology variables, replicates independently in the 2023 cohort (ICC 0.074). Protocol in `analysis_output/protocol.html`.
- Acuity-model ceiling from vitals ≈ **AUC 0.72**; `Area Triaged` is leakage (+0.13 AUC); rater identity alone predicts at AUC 0.631.
- **Zero patient overlap** across the three files — no row-level joins ever.
- No outcomes exist anywhere; mortality/LOS columns in APACHE are calculator outputs (circular).

### 1.5 User-confirmed decisions (28 Aug 2026)
| Question | Answer |
|---|---|
| Professor's expectation | **A working app for the department** |
| Triage collection status | **Paused; could restart** with a corrected instrument (prospective arm available) |
| Outcome retrieval (HIS/case sheets) | **Not feasible** → APACHE-IV validation permanently dead; all work must be outcome-free |
| Team & timeline | **Solo, ~3–6 months** |
| Scope | User initially said "routine clinical documentation" → **challenged and reframed (accepted)**: a **routine-use departmental register** (triage + ICU scoring used every shift, DPDP-grade governance, FHIR-shaped so it could later feed the official record) — **NOT the legal medical record**; the paper case-sheet stays authoritative |
| Hosting | **Unknown — must ask NIMS** (on-prem hospital LAN is the default posture; if cloud, India-region MeitY-empanelled) |
| Stack | No strong preference — "whatever fits best" (notes had mentioned Flutter) |
| Hardware ideas (RFID tracking, monitor integration) | **Cut.** **Keep camera-based barcode scan** of the e-Sushrut CR number (wristband/registration slip) |
| Evaluation ambition | **Lab eval inside 3–6 months** (replay study + controlled synthetic-case user study); live NIMS redeployment prepared in parallel (IEC + approvals), go-live when ready even if past month 6 |

---

## 2. Research pass 1 — eCRF / EDC / data-collection landscape

### 2.1 Platform-by-platform verdicts

**REDCap (Vanderbilt)** — the incumbent standard, structurally inaccessible here.
- Licensed **only to non-profit/government institutions, explicitly not individuals** (projectredcap.org/join). The institution must host and administer. A solo student cannot run it; NIMS could, but only via institutional IT. AIIMS Delhi runs an instance (started on an intranet desktop).
- Validation: min/max ranges are **soft by default** (collector can click through unless `@FORCE-MINMAX` per field). Cross-field checks = custom Data Quality rules with "real-time execution" — **warning-only, don't run on surveys, skipped on API/imports**. No clinical knowledge ships in the box.
- Data Quality module rules A–H run **on-demand**, not live; no live quality dashboard (Record Status Dashboard shows completion, not error rates/per-collector quality).
- Schema changes: production Draft Mode → **institutional admin approves**; destructive edits genuinely destroy data; **no schema versioning, no migration, no per-record stamps**.
- Audit trail: comprehensive, "Part 11 ready" — solved; parity territory.
- Offline: Mobile App alive (v5.30.x, Sept 2025) but needs per-user admin-issued API tokens, manual sync; developers themselves call sending data "a complicated process" (PMC8600440).
- Verdict: expertly configured inside a licensed instance it fixes ~70% of the NIMS failure modes; the access model is the unfixable part.

**KoboToolbox** — **the real incumbent to beat, not Google Forms.**
- Free Community plan (nonprofits/gov/edu): 5,000 submissions/month, 1 GB — fits an ED register.
- Full XLSForm validation incl. cross-field constraints. BUT: constraints are **hard pass/fail only** (no warn-but-allow → authors write loose constraints that admit garbage).
- **Notorious schema weakness: renaming a question silently splits data into two columns** (kobotoolbox community threads; kpi#1358) — the NIMS schema-drift disease built into the product.
- Quality monitoring = manual 3-state per-record validation status. Kobo explicitly disclaims HIPAA-grade handling on public servers → indefensible for identifiable ED data under DPDP.

**ODK (Collect + Central)** — reference open-source stack; self-host ~$10–40/mo VPS.
- XLSForm can do: range checks, cross-field constraints (`${sbp} > ${dbp}`), regex ID masks, constraint messages, skip logic. Cannot: soft warnings, cross-record duplicate detection, clinical vocabularies (contradiction rules must be hand-written per pair).
- ODK Entities (2023+) gives register-once/link-encounters — list lookup, not typo-tolerant matching.
- Audit log is Collect-only (not Enketo web). Central versions forms but **doesn't migrate data** (renamed field = blank against new schema).

**CommCare (Dimagi)** — case-management platform, deep India history; $100/mo + $2/extra user. Its **case management is the closest ready-made answer to the disposition-decay problem** (outcome lives later than entry; cases carry the patient across forms). Same rename-splits-data disease. No field-level quality dashboard.

**Teamscope (now Studypages Data)** — the one product explicitly for "clinical field research in low-resource settings": offline, eCRFs, audit trail, Part 11 claims. **Pricing kills it**: Team €159/mo capped at 1,000 cases/month (ED burns that in <1 month); **audit trail + query management gated behind €399/mo**. Its existence validates the market segment; its pricing leaves the segment unserved in India.

**SurveyCTO** — nearest existing thing to quality observability: nine automated statistical check types (range, IQR outliers, frequency, ANOVA, chi-squared). **Limits: runs nightly, outputs CSV+email, no clinical semantics, $250–700/mo.**

**Epicollect5** — free/unlimited, per-question regex/min-max only, **no cross-field constraints**, no audit trail. A better Google Form, not an EDC.

**OpenClinica / LibreClinica** — Community Edition = legacy OC3, functionally frozen; commercial OC4 ~$750–3,750/mo/study. Cross-field XML "Rules" fire as discrepancy notes (queries to clean later, not entry blocks). **CRF Version Migration is real** (per-subject/batch since 3.12) — the one genuine mid-study migration mechanism found in any system, though manual. LibreClinica fork is tiny (69 stars), sysadmin-demanding, clinician-hostile UI.

**Castor / Medrio / Viedoc** — sponsor-trial economics. Castor reviewers: "very expensive for independent researchers in middle income countries" and **"dependencies and validations are limited to a single field"** (even paid EDCs underdeliver cross-field validation). Medrio markets point-and-click mid-study changes — proof schema change is a solved, valued capability at the commercial tier.

**OpenEDC (Münster)** — offline PWA EDC, MIT-licensed, CDISC ODM native, SUS 83.1 — the architectural cousin. **Now an "unmaintained prototype"**; successor went commercial (Confimedis). Instructive: the one free tool with the right architecture went commercial and abandoned the open version.

**DHIS2 Tracker** — **strongest entry-time validation of any free tool** (program rules evaluate per keystroke; hard-blocking "show error" + warnings + cross-field expressions). But ministry-scale infrastructure; rule language far too weak for APACHE-IV; DHIS2's own docs: not designed to replace facility EMRs. Right role: reporting destination for aggregate ED indicators, not point-of-care capture. (Telangana's health bureaucracy already speaks DHIS2-style reporting via HISP India / IHIP.)

### 2.2 Data-quality tooling & effectiveness literature
- **Kahn framework (conformance/completeness/plausibility × verification/validation; eGEMS 2016, PMC5051581) and OHDSI Data Quality Dashboard (~4,000 checks on OMOP CDM) are retrospective by construction** — they measure how badly you collected; they never prevent SpO2=0 being saved.
- Error baselines: medical record abstraction 6.57% field error rate; single entry 0.29%; double entry 0.14% (93-paper meta-analysis, PMC10775420).
- **Medidata, >1.1B data values / 1.1M edit checks: ~60% of hand-authored edit checks never fired once, yet auto-queries drove 48.8% of all data corrections.** Two-sided lesson: entry-time checks carry ~half of data cleaning, but per-study hand-authoring produces massive dead weight → argument for a **pre-built clinical rulebook** rather than per-form authoring.
- REDCap-collected data still leaks quality: REPLICCAR II (9-hospital registry) — 1,949 potential errors, many traced to mid-study changes and missing branching logic (PMC7351197). A 99.8%-quality CIED registry bought it with **human labor** (weekly DQ reports + 10% source audits), not tooling.
- Live DQ observability exists only at enterprise scale (CluePoints, Medidata Detect — sponsor pricing). Nothing in between that and nightly CSVs.
- **No peer-reviewed paper quantitatively audits a Google-Forms clinical registry's data quality** — the NIMS dataset is itself publishable primary evidence of a widespread, underdocumented failure mode.
- **TITCO (4 Indian university hospitals): 18.1% of trauma patients missing ≥1 first physiological observation; missingness associated with hospital death (aOR 1.4) and off-hours arrival** (PubMed 31222639) — missingness is outcome-biased; the sickest patients get the worst data; retrospective imputation cannot fix it → live, per-collector completeness monitoring is the defensible fix.

### 2.3 What is NOT a gap — never claim these as novel
- Entry-time range/regex/cross-field checking **as a mechanism** (XLSForm, REDCap, DHIS2, every EDC has it)
- Audit trails (REDCap/EDCs strong)
- Offline collection (ODK/Kobo/CommCare/Teamscope all do it)
- Longitudinal linkage in principle (CommCare cases, ODK Entities)
- Retrospective DQ assessment (Kahn/DQD own it)

---

## 3. Research pass 2 — FHIR, triage systems, India health-IT

### 3.1 FHIR Structured Data Capture (SDC)
- FHIR `Questionnaire`/`QuestionnaireResponse`; SDC IG STU4 (v4.0.0, Mar 2026); most renderers implement STU3 + fragments.
- Well-supported: `minValue`/`maxValue`/`regex` per item; `enableWhen`/`enableWhenExpression` (FHIRPath) conditional display; `calculatedExpression` calculated fields (MAP, GCS total as read-only); `initialExpression`, `variable`, `answerValueSet`/`answerOption`; `$populate`.
- **`targetConstraint` (cross-field constraints with error messages): spec exists in STU4, renderer support ≈ zero as of Aug 2026** → cross-field validation must live server-side (+ client mirror).
- SDC cannot express the APACHE-IV mortality equation (proprietary regression) — server-side code regardless.
- Renderers: **LHC-Forms** (US NLM, active, web component, free NLM Form Builder GUI); **CSIRO Smart Forms** (SDC reference implementation, React, very active); Aidbox Forms (commercial; free tier forbids PHI); **Android FHIR SDK SDC library** (only serious native mobile renderer).
- Production proof it's not a toy: US Da Vinci DTR (CMS-0057-F forces every major US payer/EHR onto SDC by Jan 2027); Australia Smart Forms; WHO SMART Guidelines / EmCare.
- **Portability rule: author to the intersection** — enableWhen(Expression), calculatedExpression, initialExpression, variable, answerValueSet, min/max/regex.

### 3.2 Google Open Health Stack / Android FHIR SDK
- Kotlin libs: FHIR Engine (offline SQLite, SQLCipher optional, sync to any R4 server), SDC library (1.3.1 stable Nov 2025), Workflow (beta). **July 2026: Google transferred OHS to a Linux Foundation "Open Health Stack Software Foundation"** ($3M grant; repos → `ohs-foundation/`); engineering pivoting to a Kotlin Multiplatform rewrite — some roadmap uncertainty.
- Flagship users: OpenSRP 2 / Ona (Liberia/Uganda/Malawi, 6,500 CHWs, 2.5M patients), WHO EmCare. **All community/primary-care — no hospital ED deployment exists.**
- ED fit: offline-first is the draw; **no multi-user story on a shared device** (per-clinician attribution is app code you write; OpenSRP added Keycloak + FHIR Info Gateway); Android-only.
- Backend: **HAPI FHIR JPA starter** — one Docker container + Postgres, ~2 vCPU/4 GB; healthiest project in this entire space.

### 3.3 OpenMRS / Bahmni / DHIS2
- **OpenMRS O3 React Form Engine is the best forms+validation story of any platform reviewed**: JSON schemas, concept-driven range checks, `hideWhenExpression`, **`js_expression` cross-field validators**, `calculateExpression`, drag-and-drop Form Builder. But: full-EMR ops burden, micro-frontend learning curve, chained calculateExpressions break, no Indian government tertiary hospital runs vanilla OpenMRS.
- **Bahmni**: OpenMRS + OpenELIS + Odoo + dcm4chee; 8–16 GB RAM, four enterprise apps; form-condition scripts have broken across upgrades. Verified India deployments: JSS Bilaspur, Nagaland district hospitals, Gudalur, Bihar Bahmni-Lite ABDM pilot. Its differentiator: **only open-source platform with certified ABDM M1/M2/M3**.
- Verdict: deploying either for one department's register = using ~10% of the system while paying 100% of the ops cost. **Steal the design** (Patient→Visit→Encounter→Obs; concept dictionary coded to CIEL/SNOMED/LOINC) inside a lean app.
- Prior art: PIH OpenMRS ED Triage module (SATS-only, legacy 2.x stack, Haiti). A live 2025 OpenMRS Talk thread asks for ESI in O3 vitals forms — wanted, doesn't exist.

### 3.4 CRITICAL FINDING — what NIMS actually runs
1. NIMS's live HIS portal (nimsts.edu.in) is **C-DAC e-Sushrut HMIS**: OPD/IPD/billing/lab, **barcode integration for registration and lab tracking**, Aadhaar-QR provisional registration, ~2,191 OPD visits/day.
2. Official patient app: "NIMS HMIS" (`com.cdac.nimsmobile`, published by C-DAC).
3. **The tell: clinicians use a "Doctor Desk interface for scanning and viewing patient prescription images"** — clinical documentation at NIMS is handwritten and scanned as images. **Structured ED capture duplicates nothing; it fills a real hole.**
4. e-Sushrut has **no public integration API** — the realistic join is capturing the NIMS registration (CR) number, which is **already barcoded** → phone-camera scanning works today with zero hospital cooperation.
5. Telangana runs its own stack (TG-eHMIS = e-Sushrut, ~102 hospitals; State Data Centre hosting for its digital-health-profile programme) → strong state preference for state-controlled hosting.

### 3.5 ABDM / NRCeS / national rails
- ABDM: ABHA IDs (~90–94 crore claimed, many CoWIN-era auto-created), HIP/HIU consent-based exchange; **Scan & Share QR OPD registration is the one mass-adopted feature**. No universal mandate; hard lever is PMJAY empanelment conditionality.
- NRCeS FHIR IG (India, R4): OPConsultRecord, DischargeSummary etc. — **no ED-triage document type exists** (a legitimately publishable observation).
- **ABDM M1–M3 certification is not realistic for a student app** (organizational onboarding, 24/7 callback server, ECDH, 3–6 months for teams). Pragmatic middle path: optional ABHA field + Scan&Share QR parser + CR barcode as primary join key = future-linkable with zero certification burden.

### 3.6 Digital triage systems & scores
- Commercial: Epic ASAP / Cerner FirstNet / T-System — triage inside million-dollar EMRs. AI triage (TriageGO/Beckman, KATE/Mednition) **presumes structured triage data already exists** — the layer being built here is their missing prerequisite.
- **India: the AIIMS Triage Protocol (ATP)** — 3-tier Red/Yellow/Green, developed *because ESI/CTAS were judged infeasible at Indian public-ED volumes*, prospectively validated on 15,505 patients (Red: 96.2% sensitivity for 24-h mortality; JETS 2020, PubMed 36353399); Kerala DHS adopted a variant. **No electronic ATP implementation is published — an open niche.** Strategy: support ATP alongside ESI. (ESI's algorithm is ENA-maintained IP — internal/academic use low-risk; distributed commercial software may need ENA engagement.)
- Best precedent that this project shape works and publishes: **Smart Triage** (BC Children's + Uganda/Kenya) — custom mobile triage app, sustained >90% triage rates, PLOS Digital Health (DOI 10.1371/journal.pdig.0000466).
- Scores as products: MDCalc computes but **doesn't capture** (result dies on the phone screen). APACHE Medical Systems (1988) failed standalone and was absorbed by Cerner — the market chose integrated capture over standalone scoring. Philips eICU computes APACHE-IV inside workflow; ANZICS/ICNARC compute centrally from structured submissions. India: ISCCM CHITRA / IRIS registries are retrospective entry. **No Indian product computes APACHE at point of care.** Methodological trap: APACHE-IV is defined on *worst values in first 24 ICU hours*, not ED-arrival values — be explicit about the scoring window.
- Barcode: hospital wristbands are typically Code 128; ML Kit (free, on-device, robust) vs ZXing (Apache-2.0, maintenance mode) vs html5-qrcode (browser; weakest on curved Code 128 — **bench-test early**, ML-Kit-wrapped PWA as fallback). No published LMIC ED study combines phone-camera wristband scan with structured triage capture — modest citable novelty.

### 3.7 Strategic answers from this pass
- **(a) Be FHIR-native at the data layer, pragmatic at the app layer.** FHIR buys: declarative validation where it matters, coded queryable output (Observation extraction), alignment with India's national rails (ABDM mandates FHIR R4 + SNOMED/LOINC), renderer portability. It does NOT buy: APACHE computation, cross-field error messaging today, or ED workflow UI.
- **(b) Build a standalone app on FHIR building blocks** — not inside OpenMRS/Bahmni, not on DHIS2: HAPI FHIR JPA starter backend + SDC Questionnaires (NLM Form Builder) + web PWA embedding LHC-Forms (phase 1) + Android FHIR SDK tablet app only if offline proves necessary (phase 2) + OpenMRS-style concept discipline (LOINC/SNOMED from day one) + scores as ordinary unit-tested server code.
- **(c) ABDM/DPDP-era differentiators**: ABHA + CR join keys; NRCeS-aware FHIR output; DPDP-compliant-by-design capture (the governance story that makes Google Forms indefensible by May 2027); ATP support.
- **(d) The gap in one line: a departmental clinical register with EMR-grade validation at survey-tool ops burden.** Nothing in production combines point-of-entry validated capture + auto-computed validated scores (ESI/ATP/APACHE-IV) + ED workflow (queue, wristband scan, bedside speed) + offline tolerance + research-grade coded export + LMIC cost, deployable by ~one person.

---

## 4. Research pass 3 — India regulatory & ethics (NOT legal advice; flag all items to NIMS legal/IEC)

### 4.1 DPDP Act 2023 + DPDP Rules 2025
- Rules notified mid-Nov 2025 with **phased commencement: substantive Data Fiduciary obligations (notice, consent, security, breach notification, retention/erasure, penalties) bite ~May 2027**. As of Aug 2026 the clock is running but not enforceable. Build to DPDP now — it lands within the app's life.
- Interim: IT (SPDI) Rules 2011 still technically in force (health data IS "sensitive" there; applies to body corporates — doubtful for a government hospital, but it's the courts' reference for "reasonable security practices").
- **Roles: NIMS = Data Fiduciary; the student = Data Processor under a written contract (DPDP §8(2)).** If the student independently repurposes data (research/analytics decisions), they risk joint-fiduciary liability. **Never process patient data as a private individual.**
- Consent: no blanket "routine treatment" exemption. §7(a) (voluntarily provided for a specified purpose) likely covers routine ED registration — untested; §7(f) covers genuine medical emergencies. Hospital counsel should pick the house position.
- **Research exemption confirmed: §17(2)(b)** — Act doesn't apply to processing necessary for research/archiving/statistics, PROVIDED (i) not used for decisions specific to a data principal and (ii) per Rule 16 + Second Schedule standards (minimization, security, purpose limitation, accountability). **The live clinical tool is by definition "decisions specific to the data principal" — the exemption covers only the research/registry stream. Architect the two streams separately.**
- Health data is NOT a special category under DPDP (unlike GDPR). Children (<18): verifiable parental consent normally, BUT the final Rules' Fourth Schedule **exempts clinical establishments for processing necessary to provide health services to the child** — clinical care OK; research reuse of minors' identifiable data goes via IEC.
- Breach (from May 2027): notify each affected data principal without delay + Data Protection Board (initial without delay, detailed report within 72h). **No materiality threshold.** Penalties up to ₹250 crore (security failures).
- Cross-border: negative-list model, no restricted list notified yet. DPDP doesn't force India-only hosting — **government-sector cloud policy effectively does** (MeghRaj: MeitY/STQC-empanelled providers, India residency).

### 4.2 Other instruments
- **CERT-In Directions 2022 — IN FORCE NOW**: data breaches/leaks reportable to CERT-In **within 6 hours** (via NIMS nodal officer); **180-day log retention within India**; NTP sync.
- **EHR Standards for India (MoHFW 2016)** — voluntary: SNOMED CT (free India license via NRCeS), LOINC (free), tamper-evident append-only audit trails. Cheap to adopt, buys credibility.
- **Retention**: operative rule = IMC Ethics Regulations 2002 reg 1.3.1 (inpatient 3 years; supply to patient within 72h). NMC 2023 regulations (3 years from last contact, mandatory digitization) are **in abeyance**. ED-specific: **medico-legal case (MLC) records effectively indefinite — never auto-delete**; paediatric until majority + limitation. Ask the NIMS Medical Records Department for the applicable schedule.
- **Research ethics (ICMR 2017)**: IEC approval required for all human research incl. retrospective record review; **EC may waive consent** (existing records, impracticable recontact, minimal risk) — the EC's call, never the investigator's. ECs must be DHR/Naitik-registered. Professor as PI per institutional SOPs. **NDCT Rules 2019 do NOT apply** (no drug/intervention). A synthetic-data usability study with clinicians = the clinicians are the participants → minimal-risk, typically exempt/expedited, **get the letter anyway** (journals ask).
- **CDSCO SaMD**: MDR 2017 + Feb 2020 software notification; Oct 2025 draft software guidance (final pending) doesn't address data-capture/registry software or score calculators. Analysis: pure capture/registers = not a device; plausibility warnings = defensible as data-quality checks; **score computation (APACHE/ESI display) is the gray zone** — India has no statutory CDS carve-out. Design mitigations: show formula + inputs behind every score, label "for documentation/reference — not a directive," never auto-assign triage, written intended-use statement as a record system. In-house academic use inside one hospital is practically outside the licensing pipeline (inference, not explicit exemption); **distribution beyond NIMS changes this — recheck when the guidance finalizes.**
- **International**: GDPR/HIPAA irrelevant unless offered abroad; journals need IEC approval + consent/waiver statements (ICMJE), not GDPR. Part 11-style audit trails only if ever used for regulated trials — but append-only audit + unique logins are cheap now and align with EHR Standards anyway.

### 4.3 The informal-dataset problem (IMPORTANT)
The three Excel files (~2,500 identifiable records) were handed over with **no IEC approval and no data-use agreement**. Before any research use or publication:
1. Retrospective record-review protocol to the NIMS IEC, **professor as PI**, requesting consent waiver.
2. Simple departmental **data-use/transfer agreement**.
3. **De-identify** working copies (strip name/CR/phone → study IDs; key stays with the department, not the student). De-identified copies already exist in `analysis_output/csv/`.
4. Encrypted, access-limited storage. **Do not analyze-and-publish first** — an EC cannot retroactively bless published work.

### 4.4 Compliance classification
- **(A) MUST**: written NIMS↔student processor authorization · security safeguards (encryption at rest/in transit, RBAC, backups) · CERT-In 6-hour reporting + 180-day India logs (NOW) · retention ≥3y / MLC indefinite · DPDP duties by May 2027 · research stream meets §17(2)(b)+Rule 16 · stay out of SaMD by design · if cloud: India-region MeitY-empanelled.
- **(B) For publication**: IEC approval per study; regularize the Excel files (§4.3); professor as PI; consent-waiver justification; ICMJE ethics statement.
- **(C) Best practice**: append-only audit of views+edits; unique credentials for all ~35 users (no shared logins); pseudonymized exports by default; encrypted tested backups; incident runbook naming the NIMS nodal officer; field-level data-minimization review; multi-language privacy notice in the ED (Telugu/Hindi/English/Urdu).
- **(D) Nice**: SNOMED/LOINC coding; ABHA field; DPIA-lite; consent-manager-compatible records; Part 11 documentation.
- **(E) Confirm with NIMS**: hosting policy (State Data Centre? on-prem?); who signs (Medical Superintendent?); IEC Naitik registration + SOPs; ABDM/TG-eHMIS onboarding directives; MLC handling; legal basis for routine registration (§7(a) vs consent); CDSCO exposure if ever distributed.

---

## 5. The gap and the ranked directions

### 5.1 The four pillars (each exists somewhere; no accessible tool combines even two; P1's graduation and P2 barely exist anywhere)
1. **Shipped clinical plausibility rulebook** — physiological ranges, contradiction library ("Patent"∧"Intubated"), **graduated warn → justify → block** (XLSForm = block-only; REDCap = warn-only; nobody does tiered). *Content + packaging innovation, NOT mechanism — never claim entry-time validation itself as novel.*
2. **Live data-quality observability** — completeness-decay alerts, per-collector error rates, field-level trends; Kahn categories applied **prospectively**. Clearest open gap at any accessible price.
3. **Schema versioning with actual data migration + per-record version stamps** — the lightweight tier actively fails here (rename silently splits data).
4. **DPDP-aware governance** — identifier separation, audit, consent, de-identified exports. From May 2027 this makes the Google-Forms status quo legally indefensible → the adoption forcing function.

Plus NIMS-specific differentiators: point-of-care APACHE-IV (novel in India), ESI + **ATP** support (no electronic ATP exists), e-Sushrut CR-barcode capture, optional ABHA field.

**Positioning: "REDCap-grade data discipline with EDIS-grade workflow, deployable by one person."** Smart Triage (PLOS Digital Health) is the published proof this project shape works.

### 5.2 Ranking (12 criteria: usefulness, novelty, competition, technical depth, biomedical relevance, publication potential, deployability, ease of evaluation, patient-data independence, regulatory burden, product potential, solo feasibility — each /5, total /60)

| # | Direction | Score | Verdict |
|---|---|---|---|
| **A** | **Validated departmental register** (pillars 1–4 + scores + barcode) | **49** | **WINNER.** Real user, deployment path, replay-evaluable, compounds with the verification/observability research thesis |
| B | DQ observability layer bolted onto existing tools | 45 | Strong research; fails the mandate (professor wants the capture app); bolt-on reports errors, can't prevent them |
| D | Open clinical-rulebook standard + replay engine (research artifact only) | 44 | Highest novelty, lowest regulatory burden, weakest product → **absorbed into A** as the separable publishable core |
| C | Electronic ATP triage app + clinical validation study | 38 | Validation needs patients + outcomes → collides with constraints. ATP survives as a **feature** inside A, no validation claims |
| F | AI form-builder / AI data cleaning | 30 | Crowded LLM space, hard evaluation. Future work at most |
| E | Official-record EMR replacement | 18 | Rejected; user accepted the register reframe |

---

## 6. The MVP

### 6.1 Architecture
- **Backend**: HAPI FHIR JPA starter (Docker + Postgres, 2 vCPU/4 GB) — Patient/Encounter/QuestionnaireResponse/Observation, R4. Custom **validation service** (FastAPI or Spring) = the rulebook engine = the research artifact. Rulebook as **declarative, versioned, machine-readable rules (JSON/FHIRPath)** — separable and publishable on its own.
- **Frontend**: React **PWA** embedding LHC-Forms for SDC rendering. Custom shell = triage queue, barcode scan (html5-qrcode; **bench-test on curved Code 128 early**; ML-Kit-wrapped fallback), score displays, DQ dashboard. Runs on whatever devices the ED has. Offline service-worker queue = should-have (ED connectivity unknown).
- **Forms**: FHIR SDC Questionnaires (NLM Form Builder), authored to the well-supported intersection only. Derived values (GCS total, MAP, shock index) = read-only calculatedExpressions. Cross-field checks = server rulebook + client mirror (SDC targetConstraint has ~zero renderer support).
- **Scores**: APACHE-IV/APS, ESI reference, ATP — server-side, unit-tested against published worked examples and the 78 in-hand score strings ("110/286"). Show formula + inputs; label non-directive; never auto-assign triage.
- **Auth**: unique per-user logins, roles (collector / supervisor / study-admin / dept-head), JWT; Keycloak later.
- **Audit**: append-only event log of every view/edit/**override** (override justifications are themselves research data).
- **Governance**: identifiers (name, CR, phone) in a separate encrypted store keyed by study ID; de-identified export (CSV + codebook + FHIR bundles); documented retention schedule; CERT-In runbook; 180-day logs in India.

### 6.2 Scope tiers
- **MUST (months 1–3)**: auth/roles · registration + barcode CR scan + duplicate detection · triage ABCDE form (corrected 2024 instrument as SDC) · rulebook engine v1 (ranges, contradictions, graduated warn/justify/block, versioned rules) · audit log · DQ dashboard v1 (completeness by field/collector/time, decay alerts, override rates) · de-identified CSV export + codebook · schema version stamps on every record.
- **SHOULD (months 3–6)**: APACHE-IV ICU module · **disposition follow-up worklist** (open encounters needing outcome — the structural fix for the 40%→0% decay: outcome lives later than entry, so it needs a worklist, not a form field) · offline queue · multi-language consent screens · FHIR bundle export · **replay harness** (batch-run historical CSVs through the rulebook).
- **COULD**: SNOMED/LOINC coding (NRCeS free licenses) · ABHA field + Scan&Share QR parse · supervisor query/correction workflow · Android FHIR SDK tablet app (same Questionnaires).
- **DO NOT BUILD YET**: ABDM M1–M3 · e-Sushrut integration (no public API) · RFID · monitor integration · multi-hospital tenancy · AI form-builder/cleaning · any ML triage prediction · 5-class ESI models.

### 6.3 Verification
1. Rulebook unit tests seeded from the known defect catalog (SpO2=0, GCS-V=6, "Patent, Intubated", temp 4.0 must flag; legitimate outliers must warn-not-block).
2. Replay harness reproduces REPORT.md's defect counts on `triage_2024_DEID.csv` / `unified_2023_register_DEID.csv` (ground truth already quantified).
3. APACHE-IV outputs match published examples + the 78 in-hand scores.
4. Barcode bench test: e-Sushrut printout/wristband scanned by the PWA on a mid-range Android phone.
5. End-to-end: synthetic triage encounter on a phone → validated → stored → visible in DQ dashboard → exported de-identified with version stamp.

---

## 7. Research & publication program (no NEW patient data required for any paper)

| Paper | What | Data needed | Venue | Status/notes |
|---|---|---|---|---|
| **P1** (fast, mo 1–2) | "Anatomy of a consumer-form clinical registry failure" — quantified audit vs the Kahn framework. **No equivalent published audit exists.** Aggregate stats only; no patient rows released | The in-hand files (needs IEC + DUA + de-identification first) | JMIR Med Informatics / BMC MIDM | Evidence already computed in REPORT.md |
| **P2** (parallel, clinical) | Inter-rater ESI variability (ICC 0.113, MOR 2.0–2.7, replicates across cohorts under different instruments) | In-hand; anonymize rater IDs; frame as system-level variation, never individual evaluation | Clinical EM / triage journals | Protocol drafted in `analysis_output/protocol.html`; professor-pleasing |
| **P3** (main system paper, mo 4–8) | Platform + **replay study** (what % of ~2,400 records' defects each rulebook tier intercepts) + **controlled experiment**: participants enter identical synthetic cases under warn-only vs block-only vs **graduated** validation → error rate, time, override/click-through behavior. Graduated-vs-extremes is a genuinely open HCI/informatics question (Medidata 60%-dead-checks; alert-fatigue literature) | Replay: in-hand files. Experiment: synthetic cases, 15–30 students/residents; IEC exempt/expedited (get the letter) | JAMIA / JMIR | The rulebook + replay harness ARE the paper's methods |
| **P4** (post-deployment) | Interrupted time-series: completeness/vocabulary-compliance before vs after go-live; does live DQ feedback arrest decay? (TITCO: missingness is outcome-biased → prevention, not imputation) | Baseline = in-hand files; prospective = the deployed register (IEC prospective protocol) | JAMIA / npj Digital Medicine | Only paper requiring live deployment |

Honesty about patient data: real data is needed ONLY for P1/P2/replay/P4-baseline — all already in hand, all contingent on IEC + DUA. The user study is fully synthetic.

### Feature ↔ research roadmap
| Feature | Technical contribution | Research question | Evaluation | Paper |
|---|---|---|---|---|
| Rulebook engine | Declarative graduated clinical validation, versioned | Does graduated beat warn-only/block-only? | Controlled synthetic-case experiment | P3 |
| Replay harness | Retrospective validation-replay method | % of real defects intercepted, by tier? | Replay vs REPORT.md ground truth | P3 |
| DQ dashboard | Prospective Kahn observability | Does live feedback arrest completeness decay? | Interrupted time-series | P4 |
| Disposition worklist | Outcome capture as workflow, not field | Does a worklist fix outcome decay? | Fill-rate before/after | P4 |
| Governance layer | DPDP-by-design reference implementation | (compliance case study) | Checklist vs status quo | P1/P3 discussion |
| Barcode CR scan | Camera wristband ID in an LMIC ED | Does scanning cut ID error vs typing? | Error rate in user study | P3 (modest) |

---

## 8. Immediate next actions (in order)

1. **Guide meeting** (highest leverage). Agenda: scope-reframe sign-off (departmental register, not legal record) · hosting question (on-prem vs cloud; State Data Centre policy?) · start IEC process (P1/P2 protocols, professor as PI; consent-waiver request; DUA for the existing files) · "do blank intervention fields mean 'none performed' or 'not recorded'?" · which scores beyond APACHE/ESI she wants · interest in ATP support · who signs the processor authorization (Medical Superintendent?).
2. Formalize custody of the de-identified copies per the DUA; keep the identifier key with the department.
3. Scaffold: HAPI FHIR container + React PWA + first SDC Questionnaire (the corrected 2024 triage form) + rulebook engine skeleton seeded from the defect catalog.
4. Replay harness against the two DEID CSVs — it doubles as the P3 method and the engine's regression test.
5. Barcode bench test on an e-Sushrut printout early (it gates the patient-ID story).

## 9. Open questions still unanswered (carry into the guide meeting / next session)

- Devices at the triage desk (personal phones? dept tablet?) and ED connectivity → decides how hard offline-first must be.
- NIMS IEC registration status (DHR/Naitik) and its SOP for student/exempt studies.
- Budget (server, domain, a tablet) — assume ₹0 until told otherwise.
- Guide's venue preference: clinical vs informatics paper; authorship expectations.
- Whether the APACHE ICU scoring effort will resume (affects priority of the ICU module).
- ESI IP posture if the software is ever distributed beyond NIMS (ENA engagement).
- Exact DPDP Gazette dates before writing them into any institutional SOP.

---

*Compiled from: forensic dataset analysis (`analysis_output/REPORT.md`, 19–20 Aug 2026), strategy context (`context.md`, 28 Aug 2026), three web-research passes (28 Aug 2026) with sources embedded above, and user decisions recorded in §1.5. Regulatory content is research summary, not legal advice — every §4 item marked (E) needs institutional confirmation.*
