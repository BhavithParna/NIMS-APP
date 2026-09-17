# NIMS ED Register — design system

**Status:** v1, written at the start of Phase 1. Every later phase styles against this page.
**Where it lives:** tokens in `app/src/index.css` (`@theme`), their TypeScript mirror in
`app/src/ui/theme/tokens.ts`, motion variants in `app/src/ui/theme/motion.ts`, components in
`app/src/ui/components/`.

---

## 1. Who this is for, and what that costs

Rotating PGs, paramedics and nurses. One-handed, on a phone, standing up, sometimes gloved,
sometimes in a bright resus bay at 3am, sometimes at the ambulance door in daylight. Staff
turnover is high — the ward is a teaching hospital — so nothing may depend on having been
shown it once.

Three rules fall out of that, and they beat every other consideration on this page:

1. **Readability wins every tie.** If a layout is prettier at 13px, it is 15px.
2. **A target you can hit with a gloved thumb, or it is not a target.** 44×44px minimum.
3. **Nothing blocks a save.** No animation, no quality check, no confirmation, ever sits
   between a clinician and a record being written.

## 2. Light only — a decision, not an omission

There is no dark theme. A dark UI in a bright resus bay loses contrast exactly when it
matters, and the clinician has no time to adapt to it. This was already the documented
position in `index.css` and it stands.

The tokens are nonetheless defined as CSS custom properties on `@theme` and consumed only by
name, never as literal colours in components — so if ward feedback reverses this, a dark set
is a second `@theme` block under `prefers-color-scheme`, not a component rewrite.

## 3. Type

Inter Variable, with `tabular-nums` on everything numeric (the `.tabular` class). A CR number
or a vitals row must not jitter as digits change.

| Token | Size | Use |
|---|---|---|
| `--text-display` | 34px / 1.05 | The one number a screen exists to show — a timer, a count |
| `--text-title` | 24px / 1.15 | Screen title |
| `--text-heading` | 19px / 1.25 | Card and section heading |
| `--text-body` | 16px / 1.45 | **Floor for anything a clinician reads.** Field labels, values, buttons |
| `--text-secondary` | 14px / 1.4 | **Floor for anything at all.** Help text, timestamps, chip labels |
| `--text-numeric` | 28px / 1.1 | Vitals and timer readouts, `.tabular` |

**Nothing below 14px ships.** The old build used 12px and 13px widely; those sites are being
retired screen by screen as each screen is rewritten (see `phase1-notes.md` for the count
still outstanding).

## 4. Colour

### Neutrals, accent, and the validation ladder

Unchanged from the existing system — a slate-tinted neutral ramp, one NIMS-seal blue accent
(`--color-accent`), and the four-tier ladder (`info` / `warn` / `justify` / `block`), each
with a solid, an ink, a tint and a line so a chip and a page-level alert speak the same
language. Semantic `--color-good` and `--color-bad` sit alongside them.

The accent is deliberately a different hue family from every tier colour, so brand blue never
reads as a severity cue.

### ESI 1–5

Previously stock Tailwind palette classes — the one part of the UI that looked imported from
another app, and the one part where a wrong colour is a clinical error. Now tokens, measured:

| ESI | Token | Solid | On | Ratio |
|---|---|---|---|---|
| 1 Resuscitation | `--color-esi-1` | `#c9000c` | white | **6.02** |
| 2 Emergent | `--color-esi-2` | `#c64200` | white | **5.01** |
| 3 Urgent | `--color-esi-3` | `#edb417` | `--color-esi-3-ink` `#472900` | **7.03** |
| 4 Less urgent | `--color-esi-4` | `#007f35` | white | **5.11** |
| 5 Non-urgent | `--color-esi-5` | `#0073b3` | white | **5.10** |

Each also has `-tint` / `-ink` / `-line` for the quiet variant; every tint/ink pair measures
above 7.8:1.

**Colour is never the only cue.** An ESI chip always carries its digit *and* its word
("2 · Emergent"), a tier chip always carries its label, and the provenance badge always
carries its text. A red–green colour-blind user loses nothing.

## 5. Space, radius, elevation

Spacing is the Tailwind 4 scale unchanged. Radii are one step larger than stock — this is
most of what reads as "premium": `--radius-control` 14px, `--radius-card` 18px,
`--radius-sheet` 24px.

Elevation is three stacked very-low-alpha shadow layers rather than one dark blur
(`--shadow-hairline` → `--shadow-card` → `--shadow-raised` → `--shadow-overlay`). One dark
blur is what makes a UI look cheap.

## 6. Touch and focus

- **Minimum target 44×44px.** `.btn` is 48px, `.btn-sm` is 40px **and is not allowed on a
  primary path** — it is for secondary chrome inside a header where the row itself is the
  target.
- **Primary actions are bottom-anchored on mobile** (`ActionBar` in `src/ui/kit.tsx`). The
  top of a phone screen is not reachable one-handed.
- **One visible focus ring for everything, keyboard-only** — already global in `index.css`
  via `:focus-visible`. No control may opt out.

## 7. Motion

Motion exists to explain where something came from. It never decorates and it never delays.

| Budget | Limit |
|---|---|
| Any UI transition | **≤ 300ms** |
| The capture → decode → success sequence | **≤ 600ms** total |
| Anything that blocks a save or an input | **0ms — not permitted** |

Curves come from tokens: `--ease-out-quart` for entrances, `--ease-snap` for dismissals,
`--spring-press` for tap feedback. `framer-motion` reads these through
`src/ui/theme/tokens.ts` so there is one source of truth.

**`prefers-reduced-motion: reduce` disables all of it.** `index.css` already zeroes CSS
animation globally; `useReducedMotion()` in `src/ui/theme/motion.ts` does the same for
framer-motion, returning static variants. Every flow must complete with motion off — that is
part of the Phase 1 demo pass.

## 8. Components

| Component | Note |
|---|---|
| `Card` | The default container. `--radius-card`, `--shadow-card`, 1px `--color-line`. |
| `PrimaryTile` | Tier-1 dashboard panel. Large, press-springy, one icon, one label, one live number. |
| `StatChip` | A labelled count. Never colour-only. |
| `ProvenanceBadge` | `qr` / `ocr` / `manual`. Always carries its word. `manual` is intentionally the quiet one — a typed value is the norm, a machine-read one is the claim needing a mark. |
| `PhotoThumb` | Square, object-cover, revokes its object URL on unmount. |
| `BottomSheet` | Reachable-zone modal. Used for the CR-match confirmation, which must never resolve silently. |
| `Toast` | Existing (`src/ui/Toast.tsx`). Error toasts say what to do, not what failed. |
| `Skeleton` | Shape-matched to the content it replaces, not a generic grey bar. |
| `EmptyState` | Always names a next action. An empty screen with no next action is a bug. |
| `NumberDropdown` | Coded numeric choice (GCS E/V/M, vasopressor count). Not a free-text number. |
| `NowButton` | One tap stamps the current time; the value stays editable afterwards. |

Existing `Button`, `Field`, `ActionBar`, `Section`, `ProgressBar` and the `TIER_STYLE`
language are kept as they are and adopt the tokens above.

## 9. States every screen owes the user

1. **Loading** — a `Skeleton` shaped like the content, never a spinner on a blank page.
2. **Empty** — an `EmptyState` naming the next action.
3. **Offline** — a persistent indicator. The register is IndexedDB-first and fully usable
   offline; the indicator says "saved on this device" rather than implying failure.
4. **Error** — a toast that says what to do ("Your answers are still on screen. Do not close
   the tab — try again in a moment."), never a stack trace or a bare code.
