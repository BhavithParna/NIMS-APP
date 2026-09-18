# Phase 5 — Follow-up sheet, and the shared adapter core

Commit `ae49d21`. **374 tests green** (27 added). All checks clean.

## Why APACHE IV left the arrival form

APACHE IV is a 24-hour score. Asking for it at the door asked for a number that did not exist
yet. The eight chronic-health comorbidities it needs are questions nobody can answer about a
stranger on a trolley — nobody knows the oncology history of a patient being resuscitated, and
asking delays the resuscitation. Both moved here, to the first moment they are knowable and
harmless to ask.

## The fragment bet paid

`fragments/chronic-health.json` was written in Phase 2 for exactly this handover, and the
follow-up instrument **copies** those eight items rather than re-typing them. A test now asserts
they are identical to both the fragment *and* the ICU original — text and option codes. Re-typing
option codes across three phases is how two years of records quietly stop comparing.

Four rules came over from `icu.rules.v1.json` with their provenance strings intact (APACHE and
APS ranges, APS-cannot-exceed-APACHE, mortality-as-a-fraction). `icu.rules.v1.json` still has its
own 35 rules and is untouched: the ICU records in the store are scored against it and nothing was
taken from them.

## The tier line, drawn where the work is

Almost nothing on a follow-up is physiologically impossible, so `block` is reserved for
**self-contradiction** — a patient both alive and dead, a death before the arrival it followed —
and for the two fields without which the sheet records nothing (`follow_up_at`,
`patient_location_24h`).

Everything merely **missing** is `justify`. Half of this sheet is legitimately unobtainable by
telephone a day later, and a rulebook that treats unobtainable as wrong teaches people to invent
answers — worse than a blank and much harder to detect afterwards. `follow_up_source` includes
"Could not be established" as a real option, and there is a rule that fires when a sheet is
marked unreachable but answers things anyway.

## `sectioned.ts` — the extraction, at the point the plan named

Three call sites now exist (ed-arrival, ed-arrival-outcome, follow-up) and the shape has stopped
moving, so the parsing core came out into its own module.

- `ed-arrival-adapter.ts`: **320 → 100 lines**
- `follow-up-adapter.ts`: **70 lines**, not another hand-copied parser
- `adapter.ts` and `icu-adapter.ts` are **untouched** and stay deliberate twins. The walk-in path
  is in daily use and the reason for its isolation has not weakened.

The extraction is verified by the 347 tests that already existed passing against it unchanged.

What stayed in each adapter is what is genuinely per-instrument: which fields identify a patient,
which stages exist, which slots hold photos. Pushing those into the core is how a "generic"
module ends up with a list of special cases in it.

## The worklist

Opens on **who is due**, not on a search box. A follow-up that has to be remembered is a
follow-up that does not happen. Due = arrived more than 24 hours ago with nothing on the sheet;
the dashboard tile reads the same rule from the same module so the two cannot disagree.

`follow_up_hours` is exported rather than assumed: a "24-hour" score filled at 60 hours is a
different measurement, and an analysis that cannot see the difference will average the two
together.

The arrival diagnosis is shown at the top of the sheet, read-only. How often the day-later
diagnosis differs from the arrival impression is one of the few things this register can say
about emergency decision-making — which is why the arrival diagnosis was never editable.

## Questions

1. **Who fills this, and when?** The worklist assumes a research nurse or PG working through it
   once a day. If it is the treating team, the due-list ordering should probably be by consultant
   rather than oldest-first.
2. **Is telephone follow-up acceptable** for the survival question, or must it be from the notes?
   The instrument records which, so the analysis can separate them either way.
3. **Is 24 hours the right due point**, or should it be the next working morning?
4. **APACHE IV as calculator output.** Kept as-is from the ICU register: entered, not computed.
   An in-app reimplementation would silently diverge from whatever calculator the unit actually
   uses, and the register would then be comparing two different scores under one name. Confirm
   that is still what you want.
