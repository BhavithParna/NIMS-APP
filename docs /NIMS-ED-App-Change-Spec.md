# NIMS Emergency Department App — Consolidated Change Specification

**Version:** 1.0 · **Compiled:** 12 September 2026
**Applies to:** `app/` — NIMS ED Register (React + Vite + IndexedDB/Supabase)
**Status:** consolidated from all stakeholder inputs; sections marked ⚠ need a clinical decision before build.

---

## 1. What this document is

Every requested change to the app, gathered from the four separate input streams that
arrived in `docs/`, de-duplicated, reconciled where they disagreed, and mapped onto the
code that exists today.

### Source inventory

| Code | Source | Character |
|---|---|---|
| `SPEC` | `nims-ed-app-spec.docx` | Typed summary — the most organised source, but not the most complete |
| `N1`–`N4` | Handwritten notes, pages 1–4 (`Pasted image (7)–(10).png`) | Original clinical notes from the meeting |
| `CHAT` | WhatsApp forwards (`Pasted image.png`, `(2)–(6).png`) | Point-by-point dictation; contains items absent from `SPEC` |
| `IDEAS` | `duplicate ideas evidence.txt` | Earlier brainstorm — platform/infra level, not form level |

`docs/appchanges.txt` is empty (0 bytes) and contributed nothing.

**Important:** `SPEC` is *not* a superset. Ventilation fields, imaging/photo capture, ESI
triage, the follow-up sheet, and roughly half the AOD timings appear only in `N1`–`N4` and
`CHAT`. Building from the docx alone would miss them.

### Reading the change tables

| Marker | Meaning |
|---|---|
| **ADD** | Field does not exist today |
| **KEEP** | Exists, unchanged |
| **CHANGE** | Exists, but type/options/label change |
| **REMOVE** | Delete from the instrument |
| **MOVE** | Same field, different position in the flow |
| ⚠ | Sources conflict, or a clinical decision is needed — see §10 |

---

## 2. The headline change

The instrument being edited is the **ICU / APACHE-IV register**
(`src/domain/questionnaire/icu-apache.v1.json`, 49 fields). Every field the sources name —
CR number, serial number, pre-ICU LOS, emergency surgery before ICU, APACHE, APS — is a
field in that file.

> **The ICU/APACHE-IV instrument is being repurposed into an Emergency Department
> instrument.** It stops being an ICU admission form scored with APACHE IV, and becomes an
> ED arrival form scored with SOFA.

This is a rename and a re-scope, not a tweak:

- APACHE IV comes out of the ED flow entirely — *"Don't use APACHE 4, doesn't work in emergency"* `CHAT`. It moves to a **follow-up sheet** filled after stabilisation.
- APS is dropped — *"APS not for ED"* `CHAT`, *"No APS"* `N3`.
- **SOFA replaces it**, with an in-hospital mortality estimate.
- The form is re-sequenced around **who is standing in front of the patient and when**: paramedics fill GCS at the door, so GCS moves to page 1.
- Data entry shifts from typing to **photographing** — the transmission report, the QR code on the OP card, lab strips, the patient monitor, the ventilator, the ECG.

Practical consequence: the ED/ICU toggle in `App.tsx` currently distinguishes two
registers. After this change the "ICU" register is an ED register. Decide early whether it
**replaces** the existing ED triage register (`triage-abcde.v1.json`) or sits alongside it
as a second ED instrument — see §10.1. This decision gates a lot of the work below.

---

## 3. Flow and page order

Currently four screens. The new sequence, with the reason each move is required:

| Page | Contents | Who fills it | Why here |
|---|---|---|---|
| **1 — Arrival** | Photo of transmission report + QR scan → auto-populate · CR number · admission details · patient category · **GCS** | Paramedic / senior paramedic / junior PG | *"GCS → on arrival it's done"* `N3`; *"Senior paramedic or younger pg fills up"* `CHAT`. GCS is on page 4 today, which is wrong — the person who observes it has left by then. |
| **2 — Physiology** | Febrile/afebrile · MAP, SBP, DBP · arrival SpO₂ · HR · RR · FiO₂ · S/F ratio · blood gas · ventilation | Nurse / PG | Monitor is at the bedside; photograph it. |
| **3 — Labs & assessment** | Labs (from strip photo) · urine status · ESI triage · vasopressors · provisional diagnosis · SOFA · imaging/photos | PG / doctor | Lab strips arrive later than vitals. |
| **4 — Outcome** | Patient outcome · interventions done in ED · disposition | Doctor, at disposition | Already correct — do not move it onto the entry form. |
| **Separate** | **Ambulance Offloading Data (AOD)** + dashboard | Nurse / registration | New module, §8 |
| **Separate** | **Follow-up sheet** (APACHE IV, definitive care) | Ward/ICU team, ~day 2 | New module, §9 |

> *"Definitive care happens about a day after admission into ED"* `CHAT` — this is why the
> follow-up sheet must be a separate entry point on the board, not a page of the arrival form.

---

## 4. Page 1 — Arrival

### 4.1 Photo capture and auto-population `SPEC §1`, `N1`, `CHAT`

The first screen is the **transmission report**. Nothing is typed that a camera can read.

| # | Requirement | Source |
|---|---|---|
| 1 | **ADD** — Start the form with a photo of the admission / transmission report | `CHAT` *"Start with a photo of the admission page"* |
| 2 | **ADD** — Scan the **QR code printed on the OP card**; auto-populate patient demographics from it | `SPEC §1`, `N1` *"QR (scan the OP card)"*, `CHAT` *"Has QR code"* |
| 3 | **ADD** — Auto-populate lab and blood-gas values from a photo of the **paper data strip** | `CHAT` *"Auto populate as well. From strip of paper"* |
| 4 | Every auto-populated field must remain **editable**, and visibly marked as machine-read vs. human-entered | Implied — see §10.4 |

⚠ One known gap, from the sample photos: *"The starting id of 33101 isn't there. Rest is
available on these data strips"* `CHAT`. The patient identifier is **not** on the lab strip —
only the values are. The CR number must come from the QR/OP card or be typed. Strip OCR
cannot be the sole identity path, so **auto-populated labs must be bound to an
already-identified encounter**, never used to create one.

Note the earlier decision this reverses: the app README records *"Barcode CR scan was cut
deliberately."* It is now back in scope, as QR rather than barcode.

### 4.2 Admission fields `SPEC §2`, `N1`, `CHAT`

Against `icu-apache.v1.json` → `admission` group as it exists today:

| Field (`linkId`) | Action | Detail |
|---|---|---|
| `cr_number` | **KEEP / MOVE** | The identifier everything hangs off. Sits in Admission, auto-filled from QR capture. *"CR number → identification (company registration)"* `N1` |
| `patient_name` | **KEEP** | Unchanged |
| `phone_number` | **KEEP** | Unchanged |
| `age_value` | **KEEP** | Unchanged |
| `age_unit` | **CHANGE** | Options become **years, months** only. **Remove "days"** — *"Remove days (Adult Emergency)"* `N1` |
| `sex` | **KEEP** | Unchanged |
| `origin` | **CHANGE** | Reduce from 5 options to **2: Direct admission · Other hospital**. `SPEC §2`, `N1`. ⚠ `CHAT` words it *"referral or direct admission"* — same two-way split, different label. Recommend **"Direct admission / Referred from another hospital"**. |
| — | **ADD** | **Other hospital details** — conditional on `origin = Other hospital`. Placement deliberately undecided: *"not necessarily on the first page"* `SPEC`, *"(not on admission pages)"* `N1` |
| — | **ADD** | **Days spent in the other hospital** — *"how many days in other hosp"* `N1`. This is the replacement for pre-ICU LOS: *"Pre ICU data — should be pre NIMS hospitalization"* `CHAT` |
| — | **ADD** | **Where is the patient coming from** + **address** — *"Where is he coming from → imp info"*, *"Address"* `N1`, `CHAT` |
| `icu_serial_no` | **REMOVE** | *"Remove serial no. Only CR no"* `CHAT`, `SPEC §2` |
| `pre_icu_los_days` | **REMOVE** | Superseded by days-in-other-hospital above |
| `emergency_surgery` | **REMOVE** | Superseded by Patient category, §4.3 |
| `icu_admission_date` | **CHANGE** | Relabel to ED arrival date/time; reconcile with the AOD timings module (§8) so the same timestamp is not captured twice |

### 4.3 Patient category — new `SPEC §3`, `N1`, `CHAT`

**ADD** a single required classification, placed before the clinical sections. Every
arriving patient is exactly one of:

- Surgical emergency
- Medical emergency
- Trauma emergency

`N1`: *"Has patient any → medical / surgical / trauma"*. `CHAT`: *"Medical/ surgical or
trauma case"*, *"Has patient undergone any surgical intervention"*.

This field is likely to drive downstream branching (trauma → log roll and exposure;
surgical → intervention capture). Worth building as a proper branch key rather than a flat
choice.

### 4.4 GCS — moved earlier `SPEC §4`, `N3`, `CHAT`

| Requirement | Detail |
|---|---|
| **MOVE** | Out of the `chronic_neuro` group on page 4 → onto page 1, filled on arrival |
| **CHANGE** | Eye, verbal and motor all become **number-selection dropdowns** — *"Drop-down list box — only numbers"* `CHAT` |
| **KEEP** | Ranges: Eye 1–4 · Verbal 1–5 **plus T (intubated)** · Motor 1–6. `N3` writes *"1–4 → eye, 5 → verbal → 6 (intubated), 6 → motor"* |
| — | Filled by paramedics / PG staff — `N3` *"(paramedics / PG people)"* |

The existing ED instrument already models verbal correctly (choice capped at 5 + `T`);
carry that model over rather than reinventing it. `gcs_total` stays a calculated read-only
field.

---

## 5. Page 2 — Physiology, blood gas and ventilation

### 5.1 Physiology `SPEC §5`, `N1`, `CHAT`

| Field | Action | Detail |
|---|---|---|
| `temperature` + `temperature_unit` | **CHANGE** | Replace the numeric + unit pair with a **binary: Febrile / Afebrile**. Numeric value not needed. `SPEC §5`, `N1` *"Temp → Febrile / Afebrile"*, `CHAT` *"Page 2 — Febrile or afebrile"* |
| `map_measured` | **KEEP** | MAP retained |
| — | **ADD** | **Systolic BP** |
| — | **ADD** | **Diastolic BP** |
| | | `N1`: *"MAP, SP, DP → all three"*. All three are captured, not derived from each other. |
| `hr` | **KEEP** | Heart rate |
| `rr` | **KEEP** | Respiratory rate |
| — | **ADD** | **Arrival SpO₂** — *"Arrival spo2"* `CHAT`, `N1`. Label it *arrival* explicitly; it is a specific timepoint, not a running observation |
| `fio2` | **KEEP** | FiO₂ |
| — | **ADD** | **S/F ratio** (SpO₂ / FiO₂), calculated read-only. Replaces P/F as the default — *"SF ratio and not PF ratio"* `CHAT`, `SPEC §5` |
| — | **ADD (conditional)** | **P/F ratio** — `N1` qualifies it: *"S/F ratio · P/F ratio → depending on patient"*. Show P/F only where an arterial gas exists, i.e. ventilated patients (§5.2). See ⚠ §10.2 |
| — | **ADD** | **Patient monitor photo** — *"Patient monitor vitals, added"* `N1`, *"Patient monitor pictures"* `N2` |

### 5.2 Blood gas `SPEC §5`, `N2`, `CHAT`

| Requirement | Detail |
|---|---|
| **CHANGE** | Default gas is **VBG, not ABG** `SPEC §5` |
| **ADD** | A **source selector on pO₂: ABG or VBG** — `N2` *"PO₂ (option) → ABG / VBG"*, `CHAT` *"Po2 — give option abg or [v]bg"*. The value is meaningless without knowing which |
| **CHANGE** | **Full ABG panel only for mechanically ventilated patients** — *"Full abg for mech ventilation ONLY"* `CHAT`. The existing `po2` / `pco2` / `arterial_ph` fields become conditional on `mechanical_vent = Yes` |
| **ADD** | **Lactate** and **base deficit**, read from the gas panel — `N2` *"Lactate → ABG/VBG (take from that)"*, `CHAT` *"Serum lactate, Base deficit, From abg vbg itself"*. ⚠ Conflicts with `SPEC §6`, which drops lactate. See §10.3 |
| **ADD** | **Auto-populate the gas panel from a photo of the strip** — `N2` *"Blood gases info → Auto populate"* |
| **ADD** | **Sample strip photo (ABG/VBG)** — `N2` |

### 5.3 Ventilation — new, missing from `SPEC` `N2`, `CHAT`

Not in the docx at all. Conditional on `mechanical_vent = Yes`:

| Field | Action | Source |
|---|---|---|
| **Ventilator mode** | **ADD** — free text (`N2` says *"ventilator mode → write"*; consider a coded list with an "other" escape) | `N2`, `CHAT` *"What mode of mech ventilation"* |
| **Tidal volume** | **ADD** | `N2` *"Tidal volume: Add"*, `CHAT` |
| **PEEP** | **KEEP** — already exists | `CHAT` *"Fio2, tidal volume, peep"* |
| **FiO₂** | **KEEP** — already exists | `CHAT` |
| **Ventilator monitor photo** | **ADD** | `N2`, `CHAT` *"Picture of the monitor of ventilator"* |

---

## 6. Page 3 — Labs, triage, drugs, diagnosis

### 6.1 Labs `SPEC §6`, `N2`, `CHAT`

The governing principle, in the clinicians' own words: *"Emergency → excretory functions
(creatinine / urea). Albumin is not included"* `N2`, and *"Less focus on synthetic
functions"* `CHAT`. Liver synthetic function is not an ED concern.

| Field | Action | Detail |
|---|---|---|
| `sodium` | **KEEP** | *"Correct as it stands"* `SPEC §6` |
| `creatinine` | **KEEP** | Excretory — explicitly retained `N2` |
| `urea` | **KEEP** | Excretory — explicitly retained `N2` |
| `glucose` | **KEEP** | Not mentioned for removal |
| `hematocrit` | **KEEP** | Not mentioned for removal |
| `wbc` | **KEEP** | Not mentioned for removal |
| `urine_output_24h` | **CHANGE** | Replace the 24-hour numeric with a **3-way choice: Oliguric · Anuric · Normal**. *"Nothing time-based — no waiting 24 hours"* `SPEC §6`; `N2` shows *"No UO"* struck out and replaced by *"Anuric / Oliguric (less output) / Normal"*; `CHAT` *"Is the patient anuric or not?"* |
| `albumin` | **REMOVE** | Synthetic function, not needed |
| `bilirubin` | **REMOVE** | Synthetic function, not needed. ⚠ **Required by SOFA** — see §10.3 |
| `lactate` | **MOVE** | Out of Labs; read from the blood gas panel instead (§5.2) |
| `base_deficit` | **MOVE** | Same — from the gas panel |
| — | **ADD** | **Generic labs page** — *"Labs — make a generic page"* `CHAT`. A schema-driven lab section that can take new analytes without a code change, rather than a fixed list |

### 6.2 Triage — ESI `N2`, `CHAT`

**ADD** ESI category **1–5** to this instrument — `N2` *"Triage → ESI 1, 2, 3, 4, 5 mostly"*.

The existing ED triage instrument already has a working `esi` field with the right options
(`triage-abcde.v1.json` → `triage` group). Reuse that definition rather than authoring a
second one; the board already colour-codes and sorts on ESI.

### 6.3 Vasopressors `SPEC §8`, `N3`, `CHAT`

| Field | Action | Detail |
|---|---|---|
| `vasopressor_used` | **CHANGE (label)** | The yes/no must read **"In use, or started within 1 hour of arrival"**. *"So can't be only in-use or no"* `CHAT` — the current label is wrong and changes what gets recorded |
| — | **ADD** | **How many** — dropdown: 1, 2, 3. `SPEC §8`, `N3` *"How many → 1, 2 … dropdown"* |
| `vasopressors_detail` | **CHANGE** | Free text → **multi-select naming which agents**, count driven by the field above |

Agent list (union of `SPEC §8`, `N3`, `CHAT` — all three agree):

1. Norepinephrine
2. Epinephrine
3. Dopamine
4. Dobutamine *(written "Dovitamin" in `CHAT` — transcription of dobutamine)*
5. Vasopressin
6. Phenylephrine
7. Methylene blue

### 6.4 Diagnosis and scoring `SPEC §9`, `N3`, `CHAT`

| Field | Action | Detail |
|---|---|---|
| `diagnosis` | **CHANGE (label)** | *"ICU admission diagnosis"* → **"Provisional diagnosis"** (working diagnosis, ED). `SPEC §9`, `N3`, `CHAT` *"Provisional diagnosis / Working diagnosis"* |
| `apache_iv_score` | **MOVE** | Out of the ED flow → follow-up sheet (§9). *"Don't use apache 4 — doesn't work in emergency"* `CHAT`. Note `N3`: **APACHE 4, not APACHE 2** |
| `aps_score` | **REMOVE** | *"APS not for ED"* `CHAT`, *"No APS"* `N3` |
| — | **ADD** | **SOFA score** — 6 parameters. *"They do SOFA scoring (6 parameters) → for ED"* `N3` |
| `estimated_mortality_rate` | **KEEP / CHANGE** | Re-base on SOFA. Label as **in-hospital mortality** — *"In house mortality"* `CHAT` ×2 |
| `estimated_los_days` | ⚠ **DECIDE** | An APACHE-IV output. No source mentions keeping it. Recommend **remove** from the ED instrument |
| — | **ADD** | **MDCalc integration** for SOFA and mortality — `SPEC §9`, `N3` *"MD Calc integrate: SOFA sure"*, `CHAT` *"MD calc"*. ⚠ See §10.5 |

### 6.5 Chronic health — deleted `SPEC §7`

**REMOVE the entire block.** Hepatic failure, cirrhosis, metastatic carcinoma, lymphoma,
leukaemia/myeloma, immunosuppression, AIDS, chronic renal failure on haemodialysis — all
out. These are APACHE comorbidity weights and have no role in an ED arrival form.

Note this empties the `chronic_neuro` group: GCS leaves for page 1 (§4.4), vasopressors
move to page 3 (§6.3), everything else is deleted. **The group ceases to exist.**

### 6.6 Imaging and photos `N2`, `CHAT`

| Requirement | Detail |
|---|---|
| **ADD** | **ECG photos** — *"Put ECG photos here also"* `N2` |
| **ADD** | **Patient monitor photos** — `N2` |
| **ADD** | **Ventilator monitor photos** — `N2` |
| **ADD** | **ABG/VBG sample strip photos** — `N2` |
| **DO NOT ADD** | **No X-ray report field.** *"Radiology reports are generated only for CT and MRI. Not for chest x ray"* `CHAT`; *"No X-ray report available"* `N4`. A chest film exists as an **image only** — there is no report to transcribe, so do not build a field that will sit permanently empty |
| **ADD** | CT / MRI report capture (text or photo) — these do exist |

Image quality is a stated requirement, not a nice-to-have: *"photos aren't blurry, pretty
ad inputs, filters checking"* `IDEAS`. Blur/legibility validation belongs at capture time —
a blurred strip that fails OCR at 3am is a lost record. See §11.

---

## 7. Page 4 — Outcome `SPEC §11`, `N4`, `CHAT`

| Field | Action | Detail |
|---|---|---|
| — | **ADD** | **Patient outcome** — what happened to the patient afterwards. `SPEC §11`, `N4` |
| — | **ADD** | **Interventions done in emergency** — `SPEC §11`, `N4`, `CHAT` *"What interventions are done in the ED"*. `CHAT` adds *"Should be on the case sheet"* — i.e. this is transcribed from the paper case sheet |
| — | **ADD** | **Did the patient improve or not** — `CHAT`. A distinct question from disposition; capture separately |
| — | **ADD** | **Time patient was shifted out** — `CHAT`; feeds the AOD dashboard (§8) |
| `icu_outcome` | **CHANGE** | Relabel the existing outcome choices for ED disposition rather than ICU discharge |

Keep the existing architectural decision: outcome stays on its **own worklist entry point**,
not on the entry form. The README records that outcome-as-a-field decayed to 0% fill within
eight weeks in the Google Form era. Nothing in these sources asks to reverse that.

---

## 8. New module — Ambulance Offloading Data (AOD) `SPEC §10`, `N4`, `CHAT`

> *"Overboarding in emergency is directly related to mortality"* `CHAT`
> *"ED overboarding → what time he was in trolley → lean methodology"* `N3`

This is the module with the clearest research purpose: it exists to measure **delay**. Each
timestamp is only useful as one end of an interval.

### 8.1 Timestamps to capture

All entered as times. `SPEC §10` lists four; `N4` and `CHAT` add the rest.

| # | Timestamp | Source | Entered by |
|---|---|---|---|
| 1 | Time paramedics picked the patient up | `SPEC §10` | Paramedic |
| 2 | Time of ambulance arrival at ED | `SPEC §10`, `N4`, `CHAT` | Registration |
| 3 | Time patient taken inside / offloaded | `N4`, `CHAT` *"Time of pt taken inside"*, *"Offloaded"* | Registration |
| 4 | Time of admission / entry register | `N4` *"entry register"*, `CHAT` | Registration |
| 5 | Time patient was put in trolley | `CHAT` *"Time in trolly"*, `N3` | Nurse |
| 6 | Time first seen by a doctor | `SPEC §10` *"Doctor checking time"*, `N4`, `CHAT` *"Doc first seen"* | Doctor |
| 7 | Time blood sample was sent | `N4` *"Blood sample sent (nurse side)"*, `CHAT` | Nurse |
| 8 | Time blood report came back | `SPEC §10`, `N4`, `CHAT` *"Time when blood reports are sent"* | Nurse |
| 9 | Time seen by the definitive care doctor | `N4` *"Definitive care doctor"*, `CHAT` | Doctor |
| 10 | Time patient was shifted out of ED | `CHAT` | Nurse |

### 8.2 Derived intervals — the actual output

These are what the module is for. Compute and display them; do not make anyone subtract
times by hand.

| Interval | From → To | What it measures |
|---|---|---|
| Ambulance transit time | 1 → 2 | *"How much time he was in ambulance"* `N4` |
| **Offload delay** | 2 → 3 | *"How much time to take inside"* `N4` — the module's namesake |
| Door-to-doctor | 3 → 6 | Triage responsiveness |
| **Nurse delay** | 7 → 8 | Explicitly named: *"Doc seen — time of blood report → nurse delay"* `CHAT` |
| Trolley / boarding time | 5 → 10 | ED overboarding — the mortality link |
| Door-to-definitive-care | 3 → 9 | Typically ~1 day `CHAT` |
| Total ED length of stay | 2 → 10 | Throughput |

### 8.3 Entry mode ⚠

The sources contradict themselves on this point, in the same message run:

- *"Manually fill this"* `CHAT`
- *"Needs to be manually entered"* `CHAT`
- *"Automate into the app"* `N4`

**Recommended resolution:** capture each timestamp with a **one-tap "now" button** at the
point of care — the staff member taps when the event happens, and the app stamps the time.
That is manual entry (a human asserts the event occurred) with no typing and no clock
arithmetic. Reserve full automation for timestamps the app already owns, such as the moment
the record is created. Confirm with Dr Sabheeha.

### 8.4 AOD dashboard `N4`, `CHAT`

A dashboard is explicitly requested, listing:

- Ambulance arrival
- Offloaded
- Doctor first seen
- Blood report time
- Blood sample sent
- Definitive care doctor

Plus a **date and time filter**: *"Dropdown clock (date & time)"* `N4`.

Build it against the derived intervals in §8.2 rather than the raw timestamps — a table of
ten clock times tells no one anything, whereas median offload delay by hour of day is the
finding.

---

## 9. New module — Follow-up sheet `N3`, `CHAT`

APACHE IV does not belong in the ED, but it is still wanted — *later*.

| Requirement | Detail |
|---|---|
| **ADD** | A follow-up sheet, filled **after stabilisation** — *"APS, APACHE data after stabilizing"* `N3`, *"Page 4 needs to be filled — aps and apache scores need to be done… done after stabilization"* `CHAT` |
| **ADD** | **APACHE IV** scoring lives here — *"Follow up sheet where apache 4 can also be filled"* `CHAT`. **APACHE 4, not APACHE 2** `N3` |
| **ADD** | Definitive care record — *"Sample of how the definitive care happens about a day after admission into ED"* `CHAT` |
| **ADD** | Its own board entry point and worklist, like the outcome sheet |

**This is where the chronic-health block should be re-homed rather than deleted outright.**
APACHE IV cannot be scored without the comorbidities being removed in §6.5. They are wrong
on the ED arrival form and necessary on the follow-up sheet. Preserve the field definitions
when deleting them from the ED instrument.

---

## 10. Conflicts and decisions needed ⚠

These must be resolved before implementation. Each one changes what gets built.

### 10.1 Does this replace the existing ED register, or sit beside it?

The app already has an ED instrument (`triage-abcde.v1.json`, 58 rules, ABCDE assessment)
and an ICU instrument. These changes convert the ICU instrument into an ED one — which
leaves **two ED instruments** with overlapping fields (CR number, age, sex, GCS, SBP/DBP,
SpO₂, RR, ESI). `IDEAS` names this problem directly: *"duplicate ideas… patient ID
standardization… what's the good way to do it"*.

Three options:
1. **Merge** — one ED instrument, the ABCDE assessment becoming a section of it. Cleanest data, largest job.
2. **Keep both** — ABCDE for walk-ins, the new form for ambulance/resus arrivals, keyed on CR number so they join.
3. **Replace** — retire ABCDE.

*Recommendation: option 2 for the pilot* — it ships fastest and does not disturb a working
instrument — **with CR number enforced as the join key from day one**, so option 1 remains
reachable later. Needs Prof. Ashima Sharma's call.

### 10.2 SOFA needs fields this spec removes

**SOFA's six parameters are:** respiration (PaO₂/FiO₂), coagulation (**platelets**), liver
(**bilirubin**), cardiovascular (MAP + vasopressors), CNS (GCS), renal (creatinine +
urine output).

The changes above:

- **Remove bilirubin** (§6.1) — SOFA's liver component
- **Never add platelets** — SOFA's coagulation component; not in the current form and not requested by any source
- **Replace P/F with S/F** (§5.1) — SOFA's respiratory component is defined on PaO₂/FiO₂
- **Replace numeric urine output with a 3-way category** (§6.1) — SOFA's renal component uses mL/day

MAP, vasopressors, GCS and creatinine are all fine. **Four of the six components are
affected.** Options:

1. Bring back bilirubin and add platelets, ED-only, justified as SOFA inputs.
2. Compute a **partial SOFA**, with unscored components shown explicitly as unscored — never silently zero. *(The app's existing Kleene three-valued evaluator already treats blank as UNKNOWN rather than zero; this is the natural fit.)*
3. Use a published modified SOFA that accepts S/F and categorical urine output, and state which variant on the export.

*Recommendation: option 2 for the pilot, with the score labelled as partial* — but this is a
clinical decision, not an engineering one. Raise it before the build, because a SOFA score
that silently treats a missing bilirubin as normal is a wrong number presented as a right
one, and it will propagate into the research output.

### 10.3 Lactate — the sources disagree

`SPEC §6` says lactate is *"not needed right now"*. `N2` and `CHAT` both say to take lactate
and base deficit from the ABG/VBG.

**Resolution taken in this document:** both are satisfied — remove the *separate serum
lactate lab field* (`SPEC` is right that no extra test is ordered), and surface lactate and
base deficit from the **gas panel**, where they already come for free. Recorded as §5.2.
Confirm.

### 10.4 Provenance of auto-populated values

Not raised by any source, but unavoidable once OCR is in: a sodium read by a camera and a
sodium typed by a PG are not equally trustworthy, and the app's whole design premise is
entry-time data quality. Every auto-populated field needs a provenance flag
(`qr` / `ocr` / `manual`), visible in the UI and carried into the export. Cheap now,
retrofit-hostile later.

### 10.5 "Integrate MDCalc" — what does it mean?

Requested three times. MDCalc has no public calculation API, so the literal reading may not
be buildable. Three interpretations:

1. **Implement SOFA in-app** and validate the output against MDCalc's calculator. *(Recommended — keeps the app offline-capable, which matters for an ED.)*
2. **Deep-link out** to MDCalc with values pre-filled, clinician copies the score back. Breaks offline use and loses the audit trail.
3. **Licensed API access** — commercial arrangement with MDCalc; long lead time.

*Recommendation: option 1, with the SOFA rules held as data in the rulebook* so the
scoring is versioned and auditable like everything else. Confirm what was meant.

### 10.6 Smaller opens

- **Estimated ICU LOS** (§6.4) — keep or drop? No source mentions it. Recommend drop.
- **Other-hospital details placement** (§4.2) — deliberately left open by two sources. Recommend a conditional section revealed by `origin`, on page 1 — it is admission data and belongs with admission.
- **Ventilator mode** (§5.3) — free text as written, or a coded list? Free text is what produced the 65-spelling `Log Roll` field. Recommend a coded list with an "other" escape.

---

## 11. Platform and infrastructure `IDEAS`

From `duplicate ideas evidence.txt` — a different altitude from the form changes, and
mostly not yet scheduled. Recorded here so it is not lost.

| Item | Note | Status |
|---|---|---|
| **Flutter deployment** | *"deploy it on flutter"* — the app is currently React/Vite (web). A rewrite, not a port. Assess whether a PWA meets the need first | ⚠ Major — needs a decision |
| **Basic login ID** | *"basic login id with flutter app"*. The README confirms `USER` in `App.tsx` is still a placeholder, and the audit found **35 collectors sharing one form login** | Open, high priority |
| **DPDP compliance** | *"figure out regulatory DPDP store and retrieve it safely"* — India's Digital Personal Data Protection Act. The two-store split (`encounters` holds no identifiers; `identifiers` keyed separately) is the right foundation; encryption at rest and a retrieval policy are not done | Open, blocks real patient data |
| **Patient ID standardisation** | *"patient ID standardization… tailor made exactly"*. CR number is the key (§4.2); enforce format validation | Partly covered |
| **Photo quality validation** | *"photos aren't blurry, pretty ad inputs, filters checking"* | Open — see §6.6 |
| **Multi-parameter monitor integration** | *"multiparameter monitoring system, systolic bp diastolic bp"*. Photo capture (§5.1) is the interim answer; a direct feed is the eventual one | Future |
| **RFID patient tracking** | *"RFID based tracker on the patients · tag on the hand · prox sensor clocks patient moving across it"*. This is the automated answer to the AOD timestamps in §8 — proximity sensors would stamp offload and movement times without anyone tapping | Future — but note the direct link to §8.3 |
| **Departmental scope** | *"emergency, orthopedics, lots of departments… flexibility on the protocol they are following"*. The instrument should not hard-code ED-only assumptions | Design constraint |
| **Teaching-hospital context** | *"NIMS is a teaching hospital for MD"* — data entry is largely by rotating PGs, so the form must survive high staff turnover and minimal training | Design constraint |

---

## 12. Where each change lands in the code

| Change | File(s) |
|---|---|
| All field add/remove/change (§4–§7) | `src/domain/questionnaire/icu-apache.v1.json` — rename to an ED-named instrument, bump `version`, mint a new `url` |
| Page order / sequence (§3) | `src/domain/questionnaire/icu-adapter.ts`, `src/ui/IcuEncounterScreen.tsx` |
| Removed/changed fields' validation | `src/domain/rulebook/icu.rules.v1.json` — 35 rules; every rule referencing a removed field must be retired |
| S/F ratio, SOFA total, derived intervals | `src/domain/derived.ts` — calculated, never zero-filled |
| SOFA scoring (§6.4, §10.2) | New rulebook entries + `src/domain/derived.ts`; keep scoring as data, not code |
| QR scan / OCR / photo capture (§4.1, §6.6) | New — camera permissions, image store. Note `db.ts` currently holds no blobs |
| Photo storage & identifier separation | `src/data/db.ts` — images of a transmission report **are identifying**; they belong in the `identifiers` store, not `encounters` |
| AOD module + dashboard (§8) | New screens; new questionnaire artifact; new board entry point |
| Follow-up sheet (§9) | New questionnaire artifact (re-homing the APACHE IV + chronic health fields); new worklist |
| ESI on this instrument (§6.2) | Reuse the `esi` item from `triage-abcde.v1.json` |
| Export | `src/data/export.ts` — new fields, new version stamps, provenance flags (§10.4) |
| Tests | `tests/icu-workflow.test.ts`, `tests/icu-store.test.ts`, `tests/defect-catalog.test.ts` |

**Versioning:** the app stamps every saved record with a questionnaire version and a
rulebook version. This is a breaking schema change — bump both, and do not mutate the
existing artifacts in place, or previously saved records become unreadable against their
own schema.

---

## 13. Suggested build order

| # | Work | Why here | Rough size |
|---|---|---|---|
| 1 | Resolve §10.1 (one register or two) and §10.2 (SOFA inputs) | Both gate schema design; wrong call here is expensive later | Decision only |
| 2 | Questionnaire rewrite — all of §4–§7 except photos | Pure data edit, no new infrastructure; unblocks everything | Small–medium |
| 3 | Rulebook reconciliation + tests green | Removed fields leave dangling rules | Small |
| 4 | Flow re-sequencing, GCS to page 1 | UI only, once the schema is right | Small |
| 5 | SOFA + mortality (§6.4, §10.5) | Needs the schema settled | Medium |
| 6 | AOD module + dashboard (§8) | Self-contained; highest research value; **can run in parallel from step 2** | Medium |
| 7 | Follow-up sheet (§9) | Self-contained | Small–medium |
| 8 | Photo capture + storage (§4.1, §6.6) | New infrastructure; touches the identifier boundary and DPDP | Large |
| 9 | QR auto-population | Depends on 8 | Medium |
| 10 | Strip OCR auto-population | Depends on 8; highest technical risk, lowest certainty of working | Large |
| 11 | Auth (§11) | Needed before real patient data, independent of all the above | Medium |

Items 8–10 are where the effort concentrates. Everything in 2–7 is achievable without a
camera, and delivers a usable ED instrument on its own — worth shipping as a first release
rather than waiting on OCR.

---

## 14. People and site

| | |
|---|---|
| Clinical lead | Prof. Ashima Sharma `IDEAS` |
| Day-to-day contact | Dr Sabheeha `CHAT` |
| Location | 128 Millennium Block, 1st floor `CHAT` |
| Who fills the arrival page | Senior paramedic or junior PG `CHAT`, `N3` |
| Who fills AOD | Registration and nursing staff `N4` |
| Institution | NIMS Hyderabad — teaching hospital, MD programme `IDEAS` |

> *"Please summarise all fixes point by point, so that Bhavith or you can fix it and get going"* — `CHAT`

---

## Appendix — Change count

| Section | ADD | CHANGE | REMOVE | MOVE |
|---|---|---|---|---|
| Admission (§4.2) | 3 | 3 | 3 | 1 |
| Patient category (§4.3) | 1 | — | — | — |
| GCS (§4.4) | — | 1 | — | 1 |
| Physiology (§5.1) | 5 | 1 | — | — |
| Blood gas (§5.2) | 4 | 2 | — | — |
| Ventilation (§5.3) | 3 | — | — | — |
| Labs (§6.1) | 1 | 1 | 2 | 2 |
| Triage (§6.2) | 1 | — | — | — |
| Vasopressors (§6.3) | 1 | 2 | — | — |
| Diagnosis & scoring (§6.4) | 2 | 2 | 1 | 1 |
| Chronic health (§6.5) | — | — | 8 | — |
| Imaging (§6.6) | 5 | — | — | — |
| Outcome (§7) | 4 | 1 | — | — |
| **Form totals** | **30** | **13** | **14** | **5** |

Plus three new modules (AOD + dashboard, follow-up sheet, photo/OCR capture), six open
decisions (§10), and ten platform items (§11).
