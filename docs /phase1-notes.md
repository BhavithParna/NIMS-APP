# Phase 1 — notes

**Branch:** `phase1-dashboard-capture` in `app/` (the embedded repo, off `master`)
**Status:** shipped. 151 tests green (83 before, 68 new), `tsc -b` clean, `oxlint` at 17
warnings — the same 17 that were there before this branch.

---

## What shipped

### 1A · Tiered dashboard

The landing screen was the board: a list, with "+ New arrival" as one button among several
in a header. That is the wrong shape now that data entry has shifted from typing to
photographing (spec §2), so the camera is the largest target on the home screen and the
board is one tap away instead of being home.

- **Tier 1** — New arrival (hero), Patient board (live count), Offloading timers
  (outstanding count).
- **Tier 2** — the last eight arrivals with case-sheet thumbnails, CR number, time in
  department, ESI chip and a provenance chip.
- **Tier 3** — outcome worklist, follow-up (disabled, labelled as Phase 5), export (behind
  the existing `canExport` gate), settings.

The register toggle moved out of the two board screens into one shared component and was
relabelled **Walk-in (ABCDE)** / **Arrival (ED)** per §10.1. Its targets went from 30px to
44px. "ICU" on a button in an emergency department was going to get the wrong form filled in.

### 1B · Photo capture → QR decode → encounter log

Capture (`CaptureScreen`) has three ways in: a live viewfinder with a case-sheet framing
guide, a `capture="environment"` file input as the baseline, and the gallery. A refused
camera permission falls back and says so rather than dead-ending.

Quality gate is Laplacian variance on a fixed 512px downscale. **Warns, never blocks** —
see the threshold note below.

Decode is `BarcodeDetector` first, `zxing-wasm` lazily second, across an attempt ladder
(full frame → centre crop → three rotations → doubled crop), asking for QR *and* the linear
formats because nobody has confirmed the OP card carries a QR.

Persistence: JPEG at ~1600px/q0.8 plus a ~240px thumbnail, in a new `photos` object store on
the **identifying** side of the boundary (§12). Schema v2 → v3, additive only.
`EncounterRecord` gained optional `provenance` and `captureLog`.

Review (`ReviewScreen`) shows the photo beside the parsed fields, marks the machine-read
ones, flips a field to `manual` when it is edited, and **stops and asks** when the CR number
matches an open encounter. Attaching fills only blank fields.

### 1C · UI overhaul

`docs/design-system.md` written first. Type scale with an enforced 16px/14px floor, ESI 1–5
promoted from stock Tailwind classes to measured tokens (every solid/ink pair ≥5.01:1, every
tint/ink pair ≥7.86:1), provenance colours, tile/skeleton/scan classes, and a motion
vocabulary behind `useMotion()` that returns stillness under `prefers-reduced-motion` so no
component has to remember the branch.

### AOD (the Phase 1 slice of §8)

The six §8.4 events as `NowButton`s, editable after the tap, role hint shown. **They write
the linkIds Phase 4's `aod.v1.json` will declare**, so Phase 4 is a new artifact and nothing
else — no migration, no re-keying. `src/domain/aod.ts` lists all ten events including the
four not yet captured, so the shape is visible now.

Event 2 is not a copy of the ED arrival time, it *is* that value: `writeEvent` writes both
keys and `readEvent` reads through, so the two screens cannot disagree about one moment.

---

## What was stubbed, and what is deliberately not done

| Thing | State | Where it lands |
|---|---|---|
| Follow-up worklist tile | Disabled, labelled | Phase 5 |
| AOD intervals + dashboard | Not built; the six timestamps are captured | Phase 4 |
| The other four AOD timestamps | Declared in `domain/aod.ts`, not captured | Phase 4 |
| OCR of strips | Not started, by design | Phase 6 |
| Photo sync | **Local-only** — see below | Needs a decision |
| Per-field provenance columns | Aggregate `provenance` + `n_machine_read` instead | Phase 6 |

### Photos do not sync, and that is a decision you should look at

A case-sheet photograph is the most identifying object this app will ever hold — name, CR
number, usually a face. The remote identifier table (migration 0004) is three encrypted
scalar columns behind an RPC; a blob needs a Storage bucket, its own RLS policy, and a
retention period under the DPDP Act. None of that is a Phase 1 afternoon.

So photos live in IndexedDB on the capturing device and nowhere else. **A photo taken on one
phone is not visible on another, and is lost if that browser's storage is cleared.** The
record, the provenance map and the capture log are unaffected — they are clinical, not
identifying.

`supabase/migrations/0005_provenance.sql` adds `provenance jsonb` and `capture_log jsonb` to
`encounters`. It is **not applied** and `sync.ts` is deliberately unchanged until it is:
`pushEncounter` swallows its errors, so pushing an unknown column would fail the sync
*silently* for everyone. Apply 0005, then a one-line change to `toRemoteEncounter` turns it on.

### The type-size sweep is half done

The ≥16px/≥14px floor and 44px targets apply to everything new and everything reworked. **104
`text-[10–13px]` occurrences remain across 18 existing files**, plus sub-44px targets in the
step rails (`min-h-[34px]`) and the ED board filters (`min-h-[30px]`).

Those are the screens Phase 2 rewrites anyway, so they are swept then rather than churned
twice. If Phase 2 slips, this is the thing to pull forward — it is the accessibility
requirement, not a polish item.

---

## Extension points

- **`src/domain/capture/parsePayload.ts`** — add a shape to the chain in `parsePayload()`
  the moment we see a real OP card. The raw string is already stored verbatim on every
  record, so *past* captures can be re-parsed against a better reader.
- **`src/domain/capture/imageQuality.ts`** — `BLUR_SUSPECT_BELOW` is one exported constant.
  Phase 6 tightens it and flips the gate to blocking.
- **`src/data/db.ts`** — `PHOTO_KINDS` already has all six; Phase 2 just starts writing
  `monitor`, `ventilator`, `abg_strip`, `ecg`, `ct_mri_report`.
- **`src/domain/aod.ts`** — `phase1: false` on four events is the entire Phase 4 to-do for
  capture.
- **`src/ui/theme/`** — tokens are structured so a dark set is a second `@theme` block, not
  a component rewrite, if ward feedback ever reverses the light-only decision.

---

## Verification

```sh
cd app
npm test        # 151 passed
npx tsc -b      # clean
npx oxlint      # 17 warnings, all pre-existing
npm run build   # clean
```

New test files: `photos-store` (11), `image-quality` (12), `qr-decode` (24),
`capture-attach` (14), `provenance-export` (7).

The `capture-attach` set is the one to read: it holds the two rules (never merge
silently, never overwrite) whose failure produces a wrong patient record rather than a
missing one.

**Confirmed by build output:** the ZXing wasm is bundled as a lazy 953 kB chunk
(`dist/assets/zxing_reader-*.wasm`, 416 kB gzipped) alongside a 36 kB reader chunk, fetched
only when the native `BarcodeDetector` is missing or fails. zxing-wasm's default is
`cdn.jsdelivr.net`, which would lose decoding exactly when the ED network drops; that
default is still present as dead code in the shipped chunk, so a test asserts our
`locateFile` override rewrites the path.

**Bundle cost:** the main chunk went 615 kB → 794 kB (gzip 160 kB → 218 kB), almost all of
it framer-motion plus the new screens. The wasm is not in that figure — it is a separate
lazy chunk.

**Confirmed by dev server:** every new module transforms and serves (HTTP 200, no Vite
errors).

### What I could NOT verify, and you should

**The interactive demo pass was not run.** Login is required app-wide and needs your Supabase
credentials, so I could not reach the dashboard in a browser. Everything below is untested by
a human and is the first thing to walk through:

1. Dashboard renders all three tiers; counts are right.
2. New Arrival → camera → capture a printed QR → decode → review shows the photo beside
   `Scanned` fields → edit one, badge flips to `Typed` → Save & continue lands on the
   **admission** step.
3. A deliberately shaken shot shows the blur warning, and **Keep** dismisses it.
4. A photo with no code → blank fields, photo still saved, failure in the capture log.
5. A CR number matching an open record → the attach/create sheet appears and **nothing is
   written until it is answered**.
6. Offloading timers → tap all six → reopen and edit one → the arrival time and event 2 agree.
7. Reload with existing records → they still load (v3 migration).
8. `prefers-reduced-motion: reduce` → all motion off, every flow still completes.

Item 5 is the one worth being unkind to. It is the only place in the phase where a bug
produces a *wrong* patient record rather than a missing one.

---

## Questions

**For Dr Sabheeha / Prof. Ashima Sharma**

1. **A photo of a real OP card.** The QR payload format is unknown — there is no sample in
   the repo (`photos/` holds screenshots of this app, not case sheets). One photo unblocks
   `parsePayload.ts`. Until then it stores the raw string and parses defensively, and past
   captures can be re-read once we know.
2. **The real CR-number format.** The rulebook rule expects 15 digits; the ICU seed carries
   an 18-digit example. §10.1 makes CR the join key and asks for enforced validation, but I
   have left it at `justify` rather than `block` an unconfirmed format — blocking the wrong
   length would stop real patients being registered.
3. **§8.3 entry mode** — confirm one-tap "now", editable afterwards, is the accepted
   resolution of the "manually fill" / "automate into the app" contradiction.
4. **Photo retention.** How long should a case-sheet photograph be kept, and who may see
   one? This gates turning on any kind of sync.
5. **Blur threshold** — needs calibrating on real ward-lighting photos before Phase 6 makes
   the gate blocking. Until then it is set low and warns only; the known false positive is a
   photograph of a near-blank page.

**For you**

6. Apply `supabase/migrations/0005_provenance.sql` when convenient, and I will turn on
   provenance sync in one line.
7. `docs ` has a trailing space in its directory name, and the root `README.md` is 0 bytes
   (the real one is `app/README.md`). Both are one-line fixes I have left alone rather than
   renaming things mid-programme.
