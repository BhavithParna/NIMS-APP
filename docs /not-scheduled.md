# Not scheduled (spec §11)

Six items the change sources raise that the six-phase programme deliberately did not build.
Each one is recorded here with **where it would attach**, so the decision is a deferral with a
known cost rather than an omission.

---

## 1. Flutter / native app

**Status: assess the PWA first.**

The app is a React PWA and works offline through IndexedDB, with sync layered on top. Everything
the change sources actually ask for — camera, one-handed use, bad light, no network — is already
served by it. A Flutter rewrite would restart a working, tested codebase to gain: a slightly
better camera API, background sync, and app-store distribution.

**Attach point:** the domain layer (`src/domain/**`) is pure TypeScript with no DOM dependency —
rulebook, adapters, SOFA, AOD intervals, OCR parsing. That is roughly 60% of the real logic and
it would port as-is or be servable from a shared package. The UI layer would be rewritten.

**Decide it by measuring.** Install the PWA on the phones that will actually be used, run a week
of arrivals, and see whether camera latency or offline behaviour is the thing that hurts. If it
is neither, this is not worth doing.

---

## 2. Login and authentication

**Status: already done — the README note is stale.**

`src/data/auth.tsx` plus Supabase carry real per-user identity, and the profiles table holds
`is_admin` and `can_export`. Every record stamps `enteredBy` from the signed-in profile. The
README's "USER is a placeholder" line predates that work and should be corrected.

**What is genuinely missing:** role granularity. There are two flags where the department has at
least four roles (paramedic, registration, nurse, doctor) and the instruments now say which role
fills which section. Those `filled-by` strings are already in the artifacts and could drive a
per-role default view.

**Attach point:** `src/data/auth.tsx` and `src/ui/SettingsScreen.tsx`.

---

## 3. DPDP encryption at rest

**Status: partly done; the gap is IndexedDB, and it is the biggest one.**

Supabase migration 0004 already encrypts identifiers server-side via the `save_identifiers` RPC.
The local store does not: `identifiers` and — much more seriously — the `photos` store sit
unencrypted in IndexedDB on the device.

**Case-sheet photographs are the most identifying thing this app will ever hold.** A photograph
of an admission page carries name, CR number, address and phone in one image, and Phase 1 kept
them local-only precisely because syncing them needs a Storage bucket, a retention policy and a
DPDP position that does not exist yet.

**This is the one item on this page that should block real patient data**, not merely be
scheduled. Two decisions are needed before the app touches a real arrival:

- a **retention period** for photographs, and something that enforces it
- whether photographs leave the device at all

**Attach point:** `src/data/photos.ts` (a Web Crypto layer between `putPhoto` and the store) and
a new migration for the Storage bucket and its policy.

---

## 4. RFID / automatic timestamps

**Status: the automated answer to §8.3, and the AOD module is already shaped for it.**

Spec §8.3 contradicts itself — the sources ask both for manual entry and for automation. Phase 4
resolved it with one-tap "now" buttons that are editable afterwards, which is the cheapest thing
a person holding a trolley can do. RFID would remove the tap.

**Attach point:** `writeEvent(answers, event, iso)` in `src/domain/aod.ts` is the single writer
for every offloading timestamp. An RFID reader at the ambulance bay and the trolley bay would
call it with a machine-supplied ISO string and nothing else in the app would change — including
the shared-value rule that keeps event 2 and the arrival timestamp identical.

**Worth noting:** the provenance map (`qr` / `ocr` / `manual`) already has the shape to carry an
`rfid` source, and the export already reports it.

---

## 5. Monitor integration

**Status: replaces the §5.1 photo capture, and would be the single biggest quality win.**

The monitor photograph exists because typing vitals off a screen is slow and error-prone. A
direct feed removes both the typing and the photograph.

**Attach point:** the `monitor_photo` slot in `ed-arrival.v1.json` and the fields beside it
(`sbp`, `dbp`, `map_measured`, `hr`, `rr`, `spo2_arrival`). A monitor feed would fill those
directly with a new provenance source, exactly as OCR is designed to, and the photo slot would
become optional evidence rather than the primary route.

**Blocked on:** which monitors the department has, and whether they expose HL7, a serial port or
nothing at all. That is a procurement question, not a software one.

---

## 6. HAPI FHIR server

**Status: the export is already the right shape; nothing is pointed at a server.**

`toBundle()` produces `QuestionnaireResponse` resources against versioned `Questionnaire` urls,
and the phase notes say throughout that this is what will POST unchanged. Every instrument has a
real `url` and `version`, and `artifact-integrity.test.ts` freezes the published ones so a
version stamp cannot silently start meaning something else.

**Attach point:** one function beside `toBundle` in `src/data/export.ts`, plus the server's base
url in settings. The reason it is not built is that there is no server to point at, and writing
a client against an imagined endpoint produces a client that works against an imagined endpoint.

---

## Also deferred, not from §11

- **Per-field `<field>_provenance` columns in the extract.** Still the two-column form
  (`provenance`, `n_machine_read`). Worth adding once OCR is live and there are analytes that
  are actually machine-filled; today it would be forty always-empty columns, and a column family
  that is always empty teaches an analyst to ignore the whole family.
- **A pre-intubation GCS.** Without it SOFA's CNS component is blank on every intubated patient —
  the sickest ones. See `phase3-notes.md`.
- **Platelets and bilirubin on the labs panel.** Two fields would take SOFA from 4/6 to 6/6.
  The cut-points are already in `sofa.tables.v1.json` waiting for them.
- **The walk-in (ABCDE) register's own rewrite.** Untouched by this programme by design. It has
  its own instrument, rulebook, board, quality screen and export, and they all still work.
