# Claude Code prompt — NIMS ED Register: full change programme

Paste everything below the line into Claude Code from the repo root.

---

You are working in the NIMS ED Register app (`app/`, React + Vite + IndexedDB/Supabase). Before writing any code, read these in full:

1. `docs/NIMS-ED-App-Change-Spec.md` — the consolidated change spec. It is the source of truth for every field, label, option and module named below. Where this prompt summarises, the spec governs; where they conflict, tell me.
2. `README.md` — the two-store split (`encounters` holds no identifiers; `identifiers` keyed separately), the versioning rule (every record stamped with questionnaire + rulebook version; never mutate existing artifacts in place), and why outcome lives on its own worklist.
3. `src/data/db.ts`, `src/App.tsx`, `src/ui/IcuEncounterScreen.tsx`, `src/domain/questionnaire/icu-adapter.ts`, `src/domain/questionnaire/icu-apache.v1.json`, `src/domain/rulebook/icu.rules.v1.json`, `src/domain/derived.ts`, `src/data/export.ts`, and everything in `tests/`.

Then give me a written plan (per phase: files touched, new deps, data-model changes, open questions) and **wait for my go-ahead** before implementing. Work phase by phase; finish and verify each phase (tests green, brief demo notes) before starting the next. If a spec §10 decision blocks you, ask — never guess.

## Decisions I'm making now (spec §10)

- **§10.1** — Option 2: keep both instruments. The repurposed ICU form becomes the **ED Arrival register** for ambulance/resus arrivals; `triage-abcde.v1.json` stays for walk-ins. **CR number is the join key** — enforce format validation and make it the primary lookup everywhere.
- **§10.2** — Option 2: compute a **partial SOFA**. Unscored components display as UNKNOWN/unscored, never zero. Label the score "SOFA (partial)" everywhere including export.
- **§10.3** — As resolved in the spec: drop the separate serum lactate lab; lactate and base deficit come from the gas panel.
- **§10.4** — Provenance flag `qr` / `ocr` / `manual` on every value, stored with the value, visible in UI, carried to export.
- **§10.5** — Option 1: implement SOFA in-app as rulebook data; validate against MDCalc's published tables in tests.
- **§10.6** — Drop estimated ICU LOS. Other-hospital details as a conditional section on page 1. Ventilator mode as a coded list with "Other" free text.
- **§8.3** — One-tap "now" buttons for every AOD timestamp, editable afterwards.

---

## Phase 1 — Dashboard, photo + QR capture, UI overhaul (build this first)

### 1A. Tiered home dashboard

Replace the current landing screen with a tiered dashboard:

**Tier 1 — three large primary panels** (hero row, camera-first):
1. **New Arrival** — opens the photo capture flow (1B). Visually dominant; this is the primary action.
2. **Patient Board** — the existing encounter list (ESI colour-coding and sorting as the board already does), with a live count on the panel.
3. **Offloading Timers** — entry to the AOD module. In Phase 1 this is the six §8.4 events as one-tap "now" buttons writing timestamps to the encounter; the intervals and dashboard come in Phase 4.

**Tier 2 — activity strip:** last ~8 arrivals as compact cards: case-sheet thumbnail, CR number, time since arrival, ESI if known, provenance chip. Tap opens the encounter.

**Tier 3 — secondary entries:** Outcome worklist, Follow-up worklist (stub until Phase 5), Export, Settings. Smaller, quieter tiles.

Keep the ED/ICU register toggle reachable (Settings or header segmented control); rename its labels to "Walk-in (ABCDE)" / "Arrival (ED)".

### 1B. Photo capture → QR decode → encounter log

Flow on **New Arrival**:

1. **Capture.** `<input type="file" accept="image/*" capture="environment">` baseline, `getUserMedia` live viewfinder where supported, gallery fallback. Framing guide for the case sheet / OP card. Retake supported.
2. **Quality gate.** Cheap blur check (Laplacian variance on a downscaled canvas). Warn and offer retake — **warning only, never block**.
3. **Decode QR.** Native `BarcodeDetector` where available, fall back to `jsqr` (or `zxing-wasm` if `jsqr` is unreliable on real photos — justify in the plan). Try full image, then crops/rotations. I do not yet know the OP-card QR payload format: store the **raw decoded string verbatim**, parse defensively, CR number is the field that matters. Add `tests/fixtures/qr/` and a test that decodes a QR generated at test time.
4. **Persist.**
   - Image as compressed JPEG blob (~1600px long edge, ~0.8 quality; original dimensions in metadata) in the **`identifiers` store** (spec §12 — case-sheet photos are identifying). Add a photo object store with schema version bump + migration; existing records must still load.
   - Photo `kind` is an enum: `case_sheet`, `monitor`, `ventilator`, `abg_strip`, `ecg`, `ct_mri_report` (spec §6.6). Phase 1 only uses `case_sheet`; the others plug in during Phase 2.
   - Create the encounter, or attach to an open encounter with a matching CR number **after user confirmation** — never merge silently.
   - Log entry on the encounter: timestamp, photo id, kind, decode result (success/failure, raw payload, parsed fields), user placeholder.
   - QR-filled fields get provenance `qr`; typed fields `manual`. Provenance is part of the stored value and goes into `export.ts`.
5. **Review screen.** Photo beside parsed fields; machine-read fields visibly marked and editable (editing flips provenance to `manual`). Failed decode → blank fields, photo still saved, failure logged. "Save & continue" lands in the arrival form for that encounter.

**Not in Phase 1:** OCR / auto-population from strips or case-sheet body — that is Phase 6, last.

### 1C. UI overhaul — polished, animated, readable above all

Users are rotating PGs, paramedics and nurses: one-handed, phones, bad lighting, sometimes gloves. It must look like a first-rate modern product **and** survive that. Readability wins every tie.

**References** (study patterns, don't copy assets): Linear (density, restraint, crisp motion), Apple Health / Fitness (large numeric readouts, generous cards), Notion (calm neutrals, typographic hierarchy), Stripe Dashboard (tables, status chips), Things 3 / Arc (micro-interactions, spring physics).

**Design system first** (`src/ui/theme/`), used everywhere:
- Tokens: neutral scale + one accent + semantic success/warn/danger + ESI 1–5 colours; spacing, radius, elevation, type scales. Light/dark via CSS variables, `prefers-color-scheme`.
- Type: Inter or system sans with tabular numerals for vitals/timestamps. **Body ≥ 16px, secondary ≥ 14px, nothing smaller.** Critical numbers (CR, vitals, timers) large.
- WCAG AA contrast everywhere incl. ESI chips — text + colour, never colour alone.
- Touch targets ≥ 44×44px; primary actions bottom-anchored on mobile.
- Components: Card, PrimaryTile, StatChip, ProvenanceBadge, PhotoThumb, BottomSheet, Toast, Skeleton, EmptyState, NumberDropdown, NowButton. Visible focus rings.

**Motion:** `framer-motion`. Shared-layout transitions tile → screen, staggered dashboard entrance, spring press feedback, a satisfying capture → decode → success sequence (shutter flash, scanning shimmer, QR corners snapping to the code, fields filling in). UI animations ≤ 300ms, decode sequence ≤ 600ms, all disabled under `prefers-reduced-motion`. No animation may delay a save or block input.

**States:** skeletons, empty states with a next action, offline indicator (IndexedDB-first, Supabase sync as today), error toasts that say what to do.

Write `docs/design-system.md` (one page) before styling, so every later phase follows it.

---

## Phase 2 — ED Arrival questionnaire rewrite (spec §4–§7)

Create a **new** artifact `src/domain/questionnaire/ed-arrival.v1.json` (new `url`, version 1) derived from `icu-apache.v1.json`. Do not edit the ICU file. New adapter/screen (`ed-arrival-adapter.ts`, `EdArrivalScreen.tsx`) or generalise the ICU ones — your call, justify it. Four pages in this order:

**Page 1 — Arrival** (paramedic / junior PG)
- Case-sheet photo + QR (from Phase 1) at the top.
- `cr_number` KEEP (auto-filled from QR, validated format), `patient_name`, `phone_number`, `age_value`, `sex` KEEP.
- `age_unit` → options **years, months** only (remove days).
- `origin` → two options: **Direct admission / Referred from another hospital**.
- ADD conditional on referred: **Other hospital details**, **Days spent in other hospital**.
- ADD **Where is the patient coming from**, **Address**.
- REMOVE `icu_serial_no`, `pre_icu_los_days`, `emergency_surgery`.
- `icu_admission_date` → relabel **ED arrival date/time**; this is the same timestamp as AOD event 2 — one field, shared (see Phase 4).
- ADD required **Patient category**: Surgical emergency / Medical emergency / Trauma emergency — model as a branch key.
- MOVE **GCS** here from page 4: eye 1–4, verbal 1–5 + T, motor 1–6 as **number dropdowns**; reuse the verbal model from `triage-abcde.v1.json`; `gcs_total` calculated read-only.

**Page 2 — Physiology, gas, ventilation** (nurse / PG)
- `temperature` + `temperature_unit` → binary **Febrile / Afebrile**.
- KEEP `map_measured`, `hr`, `rr`, `fio2`. ADD **Systolic BP**, **Diastolic BP** (all three captured, none derived), **Arrival SpO₂**.
- ADD **S/F ratio** calculated read-only in `derived.ts` (SpO₂/FiO₂). **P/F ratio** calculated only when an arterial gas exists (`mechanical_vent = Yes`).
- ADD **Patient monitor photo** (kind `monitor`).
- Blood gas: default **VBG**; ADD **pO₂ source selector ABG/VBG**; `po2`/`pco2`/`arterial_ph` conditional on `mechanical_vent = Yes`; ADD **Lactate**, **Base deficit** in the gas group; ADD **gas strip photo** (kind `abg_strip`).
- Ventilation, conditional on `mechanical_vent = Yes`: ADD **Ventilator mode** (coded list + Other), **Tidal volume**; KEEP PEEP, FiO₂; ADD **Ventilator monitor photo** (kind `ventilator`).

**Page 3 — Labs, triage, drugs, diagnosis** (PG / doctor)
- Labs: KEEP `sodium`, `creatinine`, `urea`, `glucose`, `hematocrit`, `wbc`. `urine_output_24h` → **Oliguric / Anuric / Normal**. REMOVE `albumin`, `bilirubin`, and the separate `lactate` / `base_deficit` (moved to gas). Build labs as a **schema-driven generic section** so new analytes are a data edit, not a code change.
- ADD **ESI 1–5** — reuse the `esi` item definition from `triage-abcde.v1.json`.
- Vasopressors: `vasopressor_used` label → **"In use, or started within 1 hour of arrival"**; ADD **How many** (1/2/3); `vasopressors_detail` → multi-select of Norepinephrine, Epinephrine, Dopamine, Dobutamine, Vasopressin, Phenylephrine, Methylene blue, count constrained by How many.
- `diagnosis` → label **Provisional diagnosis**. REMOVE `aps_score`, `estimated_los_days`. MOVE `apache_iv_score` out (to Phase 5 follow-up). ADD **SOFA (partial)** and **In-hospital mortality** (Phase 3 fills the scoring).
- Imaging: ADD photo slots for **ECG** and **CT/MRI report** (text or photo). **No X-ray report field.**
- REMOVE the entire chronic-health block; the `chronic_neuro` group ceases to exist. **Preserve the field definitions** in a shared fragment for reuse in Phase 5.

**Page 4 — Outcome** (stays on its own worklist entry, not on the entry form)
- `icu_outcome` → relabel choices for ED disposition. ADD **Patient outcome**, **Interventions done in ED**, **Did the patient improve** (yes/no, separate from disposition), **Time shifted out of ED** (shared with AOD event 10).

**Rulebook:** new `ed-arrival.rules.v1.json`. Retire every rule referencing a removed field, carry over the rest, add rules for the new conditionals (referred → hospital details required; vent=Yes → ABG/ventilation groups; How many ↔ agent count). Update `export.ts` for new fields, version stamps, provenance. Tests: new `tests/ed-arrival-workflow.test.ts`, `tests/ed-arrival-rules.test.ts`; existing ICU tests must still pass unchanged.

## Phase 3 — SOFA + mortality (spec §6.4, §10.2, §10.5)

SOFA rules as **data in the rulebook**, evaluated in `derived.ts`. Six components: respiration (P/F when available, otherwise unscored), coagulation (platelets — not collected → unscored), liver (bilirubin — not collected → unscored), cardiovascular (MAP + vasopressor agents/count), CNS (GCS), renal (creatinine; categorical urine output → unscored for the UO part). Display per-component score with unscored ones explicitly shown; total labelled "SOFA (partial, n/6 scored)". In-hospital mortality estimate from a published SOFA→mortality table, cited in the rulebook, shown with the partial caveat. Tests compare against MDCalc worked examples.

## Phase 4 — Ambulance Offloading Data module + dashboard (spec §8)

Own questionnaire artifact `aod.v1.json` keyed to the encounter by CR number. Ten timestamps (§8.1), each a **NowButton** with editable time, role hint shown. Two are shared with the arrival/outcome forms (ED arrival = event 2, shifted out = event 10) — one stored value, surfaced in both places. Derived intervals in `derived.ts` (§8.2): ambulance transit, offload delay, door-to-doctor, nurse delay, trolley/boarding time, door-to-definitive-care, total ED LOS — never computed from a missing endpoint. **AOD dashboard** built on the intervals: median/p90 per interval, offload delay by hour of day, date & time range filter, the six §8.4 events as a per-patient live table. Charts follow the design system.

## Phase 5 — Follow-up sheet (spec §9)

Artifact `follow-up.v1.json`: APACHE IV (re-home `apache_iv_score` and the preserved chronic-health fields), APS, definitive-care record, definitive-care doctor time (shared with AOD event 9). Own worklist entry (patients ≥ ~24h since arrival without a follow-up), like the outcome worklist.

## Phase 6 — OCR auto-population (spec §4.1 items 3–4, §5.2) — last, highest risk

Only after everything above is shipped and green. Client-side OCR (Tesseract.js or similar; assess accuracy on real strip photos before committing) for lab strip and gas strip photos. Auto-populated values get provenance `ocr`, are editable, and are **only ever bound to an existing identified encounter** — never used to create one (§4.1). Photo quality gate becomes stricter here (blur → block with retake, since a blurred strip is a lost record). Stop and show me accuracy numbers before wiring it into the form.

## Not scheduled (spec §11) — do not build, but don't preclude

Flutter, login/auth, DPDP encryption at rest, RFID, monitor integration. Note in `docs/` where each would attach.

---

## Engineering rules (all phases)

- New artifacts, new versions; never mutate `icu-apache.v1.json`, `triage-abcde.v1.json` or existing rulebooks in place. Old records must remain readable against their own schema.
- Kleene three-valued evaluation stays: blank is UNKNOWN, never zero — in rules, SOFA, and intervals.
- Photos live in `identifiers`, never `encounters`.
- TypeScript strict, no `any` in new code. Small focused commits, one per logical step, clear messages.
- Every phase ends with the full test suite green and a `docs/phaseN-notes.md`: what shipped, what was stubbed, extension points, questions for Dr Sabheeha / Prof. Ashima Sharma.

Start with the plan for all six phases, then detail Phase 1.
