# Phase 2 — ED Arrival questionnaire rewrite

Branch `phase2-ed-arrival` in `app/` (off `phase1-dashboard-capture`). Six commits.
**250 tests green** (151 before this phase, 99 added). `tsc -b` clean, `oxlint` at the
pre-existing 17 warnings, `npm run build` clean.

The ICU/APACHE-IV register is now the **ED Arrival register**. New records are minted
against `ed-arrival.v1.json`; the ICU records already in the store keep rendering,
scoring and exporting against their own schema.

---

## What shipped

### The instruments

| Artifact | url | Notes |
|---|---|---|
| `ed-arrival.v1.json` | `…/nims-ed-arrival` | 3 pages, 15 sections, 65 items, 6 photo slots |
| `ed-arrival-outcome.v1.json` | `…/nims-ed-arrival-outcome` | Disposition, held apart from the arrival form |
| `fragments/chronic-health.json` | — | Not a Questionnaire. 8 APACHE comorbidity items, preserved verbatim for Phase 5 |

`icu-apache.v1.json`, `icu-outcome.v1.json`, `triage-abcde.v1.json`, `icu.rules.v1.json`
and `triage.rules.v1.json` are **byte-for-byte unchanged**, and
`tests/artifact-integrity.test.ts` now enforces that with a SHA-256 per file. A test
asserting a url and a version passes happily while a plausibility band is widened
underneath it — which is exactly the edit someone would make in a hurry, and it would
silently re-interpret every record already stamped 1.0.0.

Pages are ordered by who is standing in front of the patient, and each section says so:

1. **Arrival** — case-sheet photo, identity, arrival clock, origin (with a conditional
   other-hospital section), patient category, GCS. Registration desk.
2. **Physiology, gas and ventilation** — monitor photo, vitals, S/F, gas panel,
   and a ventilation section that opens only when `mechanical_vent = yes`. Nurse.
3. **Labs, triage and diagnosis** — labs panel, ESI, vasopressors, diagnosis,
   SOFA/mortality slots (Phase 3), ECG and CT/MRI photos. Doctor.
4. **Outcome** — its own sheet, answered from a worklist when the patient leaves.

### Three capabilities neither existing adapter had

- **Sections within a page**, so a long page reads as a sequence of jobs rather than
  a wall of inputs.
- **`enableWhen` on sections and items.** An *unanswered* condition **hides** its item.
  A half-filled form never asks which hospital referred a patient whose origin nobody
  has recorded yet — and `answerableThroughStage` excludes hidden items, so a
  conditional a patient never triggered is not counted as missing.
- **`attachment` photo slots**, six of them, each naming the document it holds.

### The rulebook — `ed-arrival.rules.v1.json`, 64 rules

Carried over every rule whose field survived, provenance strings intact. Retired the
rules whose fields left (temperature-as-a-number, albumin, bilirubin, pre-ICU LOS,
APACHE IV, APS, estimated mortality) and the GCS eye/motor range checks — those items
are coded choices now, and structure is the better fix than validation.

**The tier lines are drawn differently from the walk-in triage book, deliberately.**
Every patient on this sheet is sick, so a warning on each abnormal vital is a warning
on every record, and a rule that fires on everything is a rule everybody learns to
scroll past. So:

| Tier | Used for | Count |
|---|---|---|
| `info` | Severity signals that *are* the finding: shock index, lactate ≥4, S/F <235, GCS ≤8 | 4 |
| `warn` | Things that look like a **data problem** rather than a sick patient | 3 |
| `justify` | Confirm-or-explain: physiological extremes, contradictions, unexplained blanks | 26 |
| `block` | Physiologically impossible or self-contradictory | 31 |

A shocked, hypoxic, lactate-4.8 arrival **saves with no justification at all**. There is
a test for exactly that, because it is the property that decides whether the register
gets used at all.

A heart rate of 0 is `justify`, not `block`. Blocking it would push the sickest patient
in the department out of the register entirely.

New cross-field checks for the conditionals: referred → hospital named; ventilation
flipped to No → orphaned gas values and PEEP; vasopressor count vs. the agents actually
named; mode "Other" → named; and a disposition and outcome that disagree about whether
the patient died.

### Screens

- `EdArrivalSheet` — page 1 only, creates the record, saves nothing until "Add to board".
- `EdArrivalScreen` — the 3-page editor. Sections, conditionals, photo slots, autosave.
- `EdArrivalOutcomeSheet` — disposition and outcome, with a one-tap **Now** on
  `time_shifted_out` (it is also AOD offloading event 10).
- `IcuBoardScreen` / `IcuQualityScreen` / `IcuExportScreen` → `git mv` to `Arrival*`
  and retargeted. The ICU **encounter / arrival / outcome** sheets are untouched,
  because they still render every ICU record in the store.

### `registry.ts` — the piece that was missing

A record's `questionnaireUrl` is stamped once at creation and never overwritten, so it
is the only reliable answer to "what does this row mean". Everything that reads a stored
row — the board's outstanding count, the progress arithmetic, the disposition line, the
rulebook a photo-attach re-runs — now scopes against **the instrument the row was
entered under**, not the one the app is currently minting.

Without it, an ICU record scoped against the arrival instrument's field names reports
almost every check as belonging to a later step, which shows **nothing outstanding on a
record that has real gaps**. An unknown url returns `undefined` and callers show
everything rather than guessing: over-reporting is recoverable, hiding a block is not.

The arrival **board carries both urls**. ICU/APACHE IV *was* this register until the
instrument was replaced, so its records are this register's own history, not another
ward's. Splitting them behind a toggle would hide half of it.

### Three latent bugs found and fixed on the way

1. **`aod.ts` would have stamped a dead field.** Offloading event 2 is
   `ed_arrival_datetime` on the arrival form and `icu_admission_date` on the ICU one.
   `sharedWith` is now a list, and a write picks the name **this record** uses —
   writing both would leave a field the record's own questionnaire has never heard of.
2. **Attaching a photo to an ICU record would have rewritten its findings** against the
   arrival rulebook, silently clearing real defects and inventing others. `ReviewScreen`
   now re-runs the record's own rulebook and re-stamps its version.
3. **The register key `'icu'` had become a trap.** It meant "the arrival register" while
   the ICU instrument stood in for it; with both instruments live, `register === 'icu'`
   reads as the opposite of what it means. Renamed to `'arrival'`, and the union moved
   into `RegisterToggle` so its four consumers cannot drift.

### Two gaps closed

- **`CaptureScreen` gets a Skip.** Its own header says a refused permission must not stop
  a patient being registered; that was a comment until now. Skip leads to `EdArrivalSheet`.
- **Photo slots inside a record go straight to the photo store.** There is no code to read
  on a monitor and nothing to review, and routing it through the review screen would ask
  which patient it belongs to when the answer is already known.

### Derived values

`sfRatio`, `pfRatio`, `edArrivalCoreVitalsMissing`, `map_from_bp`, `ed_arrival_los_minutes`.
`shock_index` and `off_hours` now read `hr`/`ed_arrival_datetime` when the walk-in names
are absent — the same measurement under two names.

**`pfRatio` returns UNKNOWN unless `po2_source = 'abg'`.** This is stricter than the
prompt's "conditional on ventilation" wording, and deliberately: a P/F computed from a
venous pO2 is not a low P/F, it is a different measurement wearing the same name, and
SOFA's respiratory component is defined on the arterial one. Venous is this form's
default sample, so the common case is correctly *no answer* rather than a plausible
wrong one.

### The type floor

Phase 1 deferred this sweep to Phase 2. 125 occurrences of `text-[10–14px]` across
20 files → `text-secondary` (14px); the five remaining sub-44px targets → 44px;
`.eyebrow` 11px → 14px. Applied to the walk-in path too — leaving half the app below
the floor would make the two registers look like different products.

---

## What was stubbed

| Slot | State | Lands in |
|---|---|---|
| `sofa_partial` | Read-only item, renders "—". The instrument declares it; nothing computes it. | Phase 3 |
| `in_hospital_mortality` | Same. | Phase 3 |
| `fragments/chronic-health.json` | Preserved, imported by nothing. | Phase 5 |
| AOD events 1, 4, 5, 10 | Defined in `aod.ts`, not on the quick screen. Event 10 *is* written, by the outcome sheet. | Phase 4 |
| OCR on the gas-strip photo | The photo is captured and stored. Nothing reads it. | Phase 6 |
| Per-field `<field>_provenance` columns | Still the two-column form. Nothing machine-fills a clinical field yet. | Phase 6 |

`Field`'s `derivedValue` is typed `number | null`; `sofa_partial` is a string.
Phase 3 widens it — today it renders "—" either way.

---

## Extension points

- **`registry.ts`** is where Phase 5's follow-up instrument registers itself. Adding an
  entry is all that is needed for the board, the quality screen and the export to route
  it correctly.
- **`ed-arrival-adapter.ts`** now has the third copy of the adapter shape. Phase 5 is the
  point to extract a shared core — three call sites is when the pattern is actually
  visible, and two deliberate twins were not enough evidence.
- **`fields.tsx`** exports `FieldItem`, the structural superset every instrument's
  `RenderItem` satisfies. New item types are added there, once.
- **`sofa.tables.v1.json`** (Phase 3) slots beside `ed-arrival.rules.v1.json` and is read
  by `derived.ts`, exactly as the rulebook is read by `engine.ts`.

---

## Demo pass — NOT run

Login is app-wide and needs your Supabase credentials, so I could not drive the UI. The
logic most likely to be wrong is extracted and tested instead (`ed-arrival-rules`,
`ed-arrival-workflow`, `capture-attach`). These are the steps that still need a human:

1. Dashboard → **Arrival** register → **New arrival** → camera → **Skip** → the arrival
   sheet opens. Fill page 1, **Add to board**.
2. Set origin to **Referred** → the hospital name and days appear. Set it back to
   **Direct** → they disappear and are not counted as missing.
3. Page 2: set **Mechanically ventilated = Yes** → the gas fields and the whole
   ventilation section appear. Enter SpO2 91 and FiO2 40 → **S/F reads 227.5**.
4. Set `po2_source` to **Venous**, enter a pO2 → **P/F stays "—"**. Switch to
   **Arterial** → it computes.
5. Tap a photo slot → camera → take a photo → back on the same step with the thumbnail
   in the slot, **and the value you typed just before tapping is still there**.
6. Enter SBP 96 / DBP 58 and a monitor MAP of 110 → an amber `warn`, saves anyway.
   Enter DBP 96 / SBP 58 → a red `block`, will not save.
7. Enter HR 136 → `justify`. Type a reason → the save unblocks. The reason appears in
   `justifications.csv`.
8. Page 3 → ESI, diagnosis, vasopressors Yes / count 2 / name only one → count mismatch
   `justify`.
9. Board → the row appears next to the seeded **ICU** demo rows. Open an ICU row → it
   opens in the **ICU** screens with its own fields intact.
10. Outcome worklist → **Now** on "time shifted out" → editable afterwards.
11. Export → CSV header has no `cr_number`, no `patient_name`, no `*_photo`.
12. **Type scale**: nothing on any screen should look cramped or clipped after the 14px
    floor. This is the change I am least able to verify without a browser.
13. `prefers-reduced-motion: reduce` → all motion off, every flow still completes.

---

## Questions for Dr Sabheeha / Prof. Ashima Sharma

1. **The CR number format.** Still `justify` at 15 digits, not `block`. §10.1 makes it the
   join key and asks for enforced validation, but the ICU seed carries an 18-digit
   example and I will not block an unconfirmed format. **One real registration slip
   settles it** and the rule becomes a `block`.
2. **`patient_category` is a `block`.** Medical / surgical / trauma is the top-level split
   every downstream count is broken down by and nothing else on the sheet can back-fill
   it. Confirm it is always knowable at the door — if a patient can genuinely be
   uncategorised on arrival, it should be `justify` with an "unclear" option.
3. **ESI on this form.** It is asked on page 3 (doctor), not page 2 (nurse). If triage
   category is assigned by the nurse at the monitor, it belongs on page 2 and moving it
   is a one-line change to the artifact.
4. **`age_unit` is years or months only.** The walk-in form has days, for neonates. Does
   the arrival register see day-old babies?
5. **Ventilator modes.** VC, PC, PRVC, SIMV, PSV, CPAP, NIV, Other. Is that the list on
   your ventilators, and should NIV be a *mode* here or a separate support question?
6. **`ed_interventions`** — 16 coded options transcribed from the paper case sheet.
   Please strike out anything never done and add anything missing; the value of a coded
   list is entirely in it matching what the sheet actually records.
7. **Lactate ≥4 and S/F <235 are `info`** — recorded quietly, no interruption. Confirm
   that is right: the alternative is `warn`, which fires on a large fraction of this
   register's population.
8. **Carried from Phase 1, still open:** a sample OP card (the QR payload format is still
   unknown), the blur threshold on real ward-lighting photos, §8.3 one-tap-now, and photo
   retention / DPDP before any real patient data.

---

## Files

**New** — `src/domain/questionnaire/{ed-arrival.v1.json, ed-arrival-outcome.v1.json,
ed-arrival-adapter.ts, registry.ts, fragments/chronic-health.json}`,
`src/domain/rulebook/ed-arrival.rules.v1.json`,
`src/ui/{EdArrivalSheet,EdArrivalScreen,EdArrivalOutcomeSheet}.tsx`,
`tests/{ed-arrival-rules,ed-arrival-workflow,artifact-integrity}.test.ts`,
`docs /phase2-notes.md`

**Renamed** — `src/ui/Icu{Board,Quality,Export}Screen.tsx` → `Arrival*`

**Modified** — `src/App.tsx`, `src/domain/{derived.ts, aod.ts}`,
`src/data/{export.ts, seed.ts}`, `src/index.css`,
`src/ui/{fields.tsx, RegisterToggle.tsx, CaptureScreen.tsx, ReviewScreen.tsx,
AodScreen.tsx, BoardScreen.tsx, DashboardScreen.tsx, SettingsScreen.tsx,
EncounterScreen.tsx, IcuEncounterScreen.tsx}` and the type-scale sweep across `src/ui`

**Untouched, by rule** — `icu-apache.v1.json`, `icu-outcome.v1.json`,
`triage-abcde.v1.json`, `icu.rules.v1.json`, `triage.rules.v1.json`,
`IcuArrivalSheet.tsx`, `IcuOutcomeSheet.tsx`, and every existing test file.
