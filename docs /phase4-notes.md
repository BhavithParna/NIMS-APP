# Phase 4 — Ambulance offloading (AOD)

Commit `9dc3ccf`. **347 tests green** (26 added). All checks clean.

Ten timestamps and the eight intervals between them (spec §8), as a versioned artifact.

## The Phase 1 bet paid

Phase 1 captured six of the ten events under linkIds chosen to be the ones Phase 4 would declare.
That held exactly: `aod.v1.json` declares those ids, so this phase is **a new artifact and
nothing else** — no migration, no re-keying, no orphaned answers. `domain/aod.ts` now reads its
table *from* the artifact rather than carrying a second copy that could drift.

Three of the ten are the same stored value as a field elsewhere. Event 2 is the arrival
timestamp, event 9 the definitive-care time on the follow-up sheet, event 10 the time shifted
out. Recording either place records both, and a write only touches the name **this record**
uses — writing both would leave an `icu_admission_date` on an ED arrival row that nothing
renders and nothing can explain later.

## The eight intervals

| id | From → to | Target |
|---|---|---|
| `transport` | pick-up → arrival | — |
| **`offload`** | arrival → offloaded | **15 min** |
| `to_register` | offloaded → register entry | — |
| `to_trolley` | offloaded → trolley | — |
| **`door_to_doctor`** | arrival → first doctor | — |
| `lab_turnaround` | sample sent → report back | — |
| **`door_to_definitive_care`** | arrival → definitive care | — |
| **`total_ed_stay`** | arrival → shifted out | — |

Bold are the dashboard headlines; the other four are one tap away.

**Targets are almost all null, on purpose.** The 15-minute ambulance handover is a published
external standard (NHS England) and is cited as one. The rest are local service decisions this
app has no business inventing: a dashboard measuring against a made-up target teaches people to
ignore the dashboard. Until the department sets them it reports what happened rather than
grading it. `meetsTarget` therefore has three answers — met, missed, **no-target** — not two.

## Two things the dashboard refuses to do

**It never hides a denominator.** Every interval says how many arrivals it was measured on and
flags itself when that is under half. A median offloading delay computed from eleven of ninety
arrivals is not a median, and a dashboard that shows the number without the denominator gets
believed anyway.

**It never quietly drops a contradiction.** An arrival whose offload time precedes its arrival
time is counted and named, not filtered out. The registers this replaces lost their defects.

Intervals are UNKNOWN when either end is missing, **never zero** — treating a missing offload
time as a zero-minute offload would report the department's worst-documented arrivals as its
fastest, which is exactly backwards.

Median and 90th centile rather than a mean: one patient boarded overnight moves a mean and
describes nobody. The 90th centile describes the bad days, which is what a department improving
a process needs.

Charts are inline SVG. Two chart types do not justify a dependency that has to be downloaded to
a phone in a resus bay.

## Also

- The timers screen and the figures screen are separate, with a door between them. Recording the
  times and reading them are different jobs done by different people.
- Offloading exports as its own CSV joined on `study_id`, with every interval **beside its two
  raw timestamps** — a blank delay with both ends recorded is a bug; a blank one with no offload
  time is a documentation gap; the CSV must not make them look alike.
- The seeded demo timelines are deliberately uneven. A demo where every arrival is perfectly
  timed teaches the wrong thing about what the figures will look like.

## Questions

1. **Targets.** What does the department want to be measured against for door-to-doctor,
   door-to-definitive-care and total ED stay? Until these are set the dashboard only describes.
2. **Is the 15-minute handover standard the right one**, or is there a local/state figure?
3. **Event 1 (paramedic pick-up)** is the only event that happens before the patient reaches the
   hospital, so it is transcribed rather than tapped and will be the most often blank. Is it
   worth keeping, or should transport time come from the ambulance service directly?
4. **§8.3 one-tap-now**, still open from Phase 1: confirm that a tap, editable afterwards, is
   the accepted resolution of the "manually fill" / "automate" contradiction in the sources.
