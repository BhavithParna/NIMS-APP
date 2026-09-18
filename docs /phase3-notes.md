# Phase 3 — SOFA and mortality

Commit `4e289b8`. **321 tests green** (71 added). `tsc -b` clean, `oxlint` at the pre-existing
17 warnings, `npm run build` clean.

Spec §10.2 and §10.5: keep the score, never let a missing component become a zero, label every
total as partial, and hold the cut-points as **data** validated against MDCalc rather than as code.

## The shape of a partial score

A component returns one of three things, and the difference between them is the whole design.

| State | Meaning | `points` | `min`/`max` |
|---|---|---|---|
| `scored` | A definite number | set | equal |
| `ranged` | Bounded but not fixed — a vasopressor at an unrecorded dose is on rungs 3 *or* 4 | null | differ |
| `unscored` | Nothing known. **Excluded from the total, not counted as zero** | null | null |

The arithmetic of "excluded" and "contributes zero" is identical. What differs is that every
label carries the scored count — `SOFA (partial) 13–14 · 5 of 6 scored` — so a four-of-six total
cannot be read downstream as a six-of-six one. It is also why the instrument declares the SOFA
slot as a **string**: there is no honest bare number to put in an integer field.

The export carries both forms: `sofa_partial_label` for reading, and `sofa_points`, `sofa_upper`,
`sofa_scored`, `sofa_known`, `sofa_unscored`, `sofa_complete`, `sofa_mortality_percent` for
analysis. An analyst who filters on `sofa_scored = 6` gets comparable rows; one who does not has
been told, in the header, that they have not.

## Three findings the tables now state out loud

**1. Two of six can never be scored here.** Platelets and bilirubin are not collected in this
department. The cut-points for both are already in `sofa.tables.v1.json`, so adding either item
to the labs panel scores its component **with no code change** — there is a test for exactly that.

**2. The CNS component is unscored on intubated patients.** `gcs_total` is deliberately blank
when the verbal score is T. That is correct, and uncomfortable: it fails toward *less* severity,
on the patients who are most severe. A pre-intubation GCS would fix it and is not currently asked
for. **This is a question for Dr Sabheeha.**

**3. The S/F imputation cannot reach zero points at any FiO₂.** S/F maxes at 100/(FiO₂/100),
which on room air is 476 — below the 512 the zero rung needs. **A completely well patient
breathing room air scores 1 on the respiratory component.** Respiratory SOFA is therefore biased
upward by one point across the whole walk-in end of the register, and only an arterial gas
resolves it. Above 97% saturation the ratio stops discriminating at all (PaO₂ 100 and PaO₂ 300
both read 99%), so there the component is bounded from zero rather than scored.

This one was found by a test failing, not by reading the paper. It is the single most important
thing to know when reading these totals.

## Mortality

Ferreira et al., *JAMA* 2001 — **initial** SOFA score, not maximum or delta, because this
register scores once on arrival. Refused below four measured components: below that the total
carries so little information that quoting a mortality against it would be inventing precision,
and a number on a screen beside a patient is read as a fact whatever the caption says.

Where a ranged component straddles two rows the estimate is quoted as a range. `50.0%–95.2%`
turning on a vasopressor dose nobody wrote down is worth seeing rather than averaging away.

Every estimate carries its caveat, every time: derived in an adult ICU cohort, applied here on
ED arrival.

## Questions

1. **A pre-intubation GCS.** Without it SOFA's CNS component is blank on every intubated patient.
   One extra field on page 2 would close it.
2. **Platelets and bilirubin.** Two more items on the labs panel take SOFA from 4/6 to 6/6.
   Are they available on the routine ED bloods, and is the extra typing worth a complete score?
3. **Is Ferreira 2001 the right table**, or does the department prefer Vincent 1998's
   maximum-score table or a local one?
4. **The oliguric/anuric mapping.** `oliguric` is read as the published <500 mL/day rung and
   `anuric` as <200 mL/day. Stated in the tables file rather than buried; worth a clinician's eye.
