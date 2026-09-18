# Phase 6 — OCR, built and switched off

Commit `d050b99`. **399 tests green, 1 deliberately skipped.** All checks clean.

## The hard stop is honoured

OCR is complete, tested, and reachable from `App.tsx` behind one line:

```ts
const OCR_ENABLED: boolean = false
```

**It stays false until accuracy numbers from real blood-gas strip photographs have been measured
and seen.** When they pass the gate below, flipping that flag is the only change needed — the
gas-strip photo slot then offers to read itself.

This is not caution for its own sake. **An OCR error is a plausible wrong number.** A failed QR
decode looks like a failed decode and somebody types the value instead. A pCO₂ read as 4.8
instead of 48 looks exactly like a pCO₂, sits in the record forever, and is indistinguishable
afterwards from a patient who really had one.

## What you need to do to turn it on

1. Take **at least 30** photographs of real blood-gas strips, on the phone that will be used in
   the department, across **day and night lighting**.
2. Drop matched pairs into `app/tests/fixtures/ocr/` — `0001.jpg` and `0001.json` with what is
   actually printed on it. The exact format is in that directory's README.
3. `npx vitest run tests/ocr-accuracy.test.ts`. It prints a per-analyte table.
4. **The gate is on the wrong rate, not the hit rate:**

   | Measure | Gate |
   |---|---|
   | Wrong proposals, any analyte | **0** across the sample |
   | Coverage (proposed at all) | reported, not gated — low coverage is merely unhelpful |
   | Sample size | ≥ 30 strips, day and night |

   A missed reading costs a few seconds of typing. A wrong one enters the medical record.

5. If a single wrong value appears, **that analyte comes out of `ANALYTES`** and OCR does not
   fill it. Per-analyte, not all-or-nothing.

Until step 2 happens the harness **skips with a warning** rather than passing quietly — a green
suite must never be mistakable for "OCR has been validated".

## How it refuses

The module is built around refusing rather than guessing. Each of these is a real failure mode
with a test:

- **Out of range → not proposed.** Reported with the raw line so a person reads it off the photo.
  The bands are the same ones the rulebook blocks on, so a proposal can never be something the
  form then refuses to save.
- **Lost decimal point → restored only when exactly one placement is plausible**, and only for
  analytes printed with decimals at all. Sodium `1410` is not a sodium of 141 — it is an
  unreadable sodium. A repair that could have gone two ways is a coin toss wearing a lab coat.
- **A label is never paired with a number from the next line.** That is how a pO₂ becomes a pCO₂.
- **First reading wins.** Strips reprint header blocks; a second, different value is not a
  correction.
- **Every repair is a visible flag, never a silent fix.** The raw text travels with the proposal.
- **Nothing auto-commits, nothing creates a record, nothing overwrites a typed value.** Accepted
  values are marked `ocr` in the provenance map, so the extract can tell a camera-read gas from a
  typed one and the validation study can stratify on it.

The analyte table lists only what a gas strip actually prints **and** the form actually asks for.
Creatinine, urea and WBC are deliberately absent — they come off a different report, and an OCR
table listing fields the photograph cannot contain is an invitation to point the camera at the
wrong piece of paper.

## The offline hazard, again — and worse

`tesseract.js` fetches its worker, its WASM core **and a ~4 MB language model** from a CDN on
first use. In an ED that means OCR works on the day it is demonstrated and fails the first time
the wifi drops. `useLocalAssets(localAssets())` points all three at this origin, with a test
asserting the override — because the CDN default stays in the shipped bundle as dead code and a
regression would be completely silent.

**The model is not bundled yet.** Shipping four megabytes to every phone before anyone has seen
an accuracy number is the thing the hard stop exists to prevent. When the numbers pass, copy
`node_modules/tesseract.js-core/*.wasm.js`, the worker and `eng.traineddata.gz` into
`app/public/ocr/` — `localAssets()` already points there.

**Bundle cost today:** `tesseract.js` is lazily imported into a **17 kB** chunk. The common path
pays nothing.

## What the synthetic tests do and do not prove

`tests/ocr-accuracy.test.ts` includes synthetic strips that verify the **pipeline** — text in,
proposals out, zero wrong values. They say so in their own describe block. A rendered string is
not a photograph of a thermal printout under ward lighting and nobody should treat one as
evidence about the other.

## Questions

1. **Photographs.** Thirty strips is the whole blocker. Nothing else is needed.
2. **Which analyser?** The label aliases (`pCO2`, `PaCO2`, `Lac`, `BE`, `ABE`, `Na+`…) are the
   common ones; one photograph of your printout would let them be matched exactly rather than
   guessed at.
3. **Is the gas strip the right first target**, or would the monitor photograph (HR, BP, SpO₂) be
   more valuable? The monitor is a seven-segment display, which is a different and generally
   easier OCR problem.
