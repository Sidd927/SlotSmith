# SlotSmith design specification

Canonical. Version 2 (11 Oct 2026). Supersedes `docs/audit/design.md` (an earlier reference-image spec) and the visual direction of the previous Streamlit UI. Evidence: [docs/ux_research.md](docs/ux_research.md). Feature truth: [docs/feature_capability_matrix.md](docs/feature_capability_matrix.md). Review history: [docs/ux_review_log.md](docs/ux_review_log.md).

> Status marker convention: **[built]** = implemented and verified; **[limit]** = known limitation, documented. This file must always describe what is actually implemented.

## A. Product intent

**Positioning.** SlotSmith is an engineering workstation that turns a customer I/O list into a rule-checked DeltaV Electronic Marshalling allocation (marshalling cabinet → CIOC → baseplate → CHARM slot), explains what it could not place, re-checks its own export with an independent verifier, and handles revisions by keeping unchanged cables where they are. It complements DeltaV tooling; it does not replace it.

**Users.** (1) DeltaV I/O / project engineer, the person who allocates and answers customer queries. (2) Cabinet panel designer, who needs to see exactly what sits in each slot and what is spare. (3) Reviewer or judge, who needs to see within a minute what was done and whether it can be trusted.

**Jobs to be done.** Load a workbook and know whether it is usable. Set project rules and see their consequences. Run an allocation and know whether it is current. See what failed and why (TQs). Inspect any slot. Compare Rev B against Rev A. Export a workbook.

**UX principles.**
1. *Show the work.* Every number on screen comes from a real run; every status says what it is based on.
2. *Neutral by default, colour means something.* Grey surfaces; accent for action and selection; saturated colour only for exceptions.
3. *Never colour alone.* Status = symbol + word + colour. Signal type = two-letter code + tint.
4. *One way to move.* One stage rail in the workbench; the landing page has no workbench chrome.
5. *State is visible.* Current, Stale, Not run: always next to the result.
6. *Honest limits.* Synthetic is labelled synthetic. Solver status is reported as the solver reports it.

**Non-goals.** Operator HMI conventions or compliance claims. Live plant connectivity. Marketing imagery. A second frontend framework. Any change to `src/slotsmith/`.

## B. Information architecture

Two experiences, one identity, joined by native Streamlit pages (`st.navigation`, hidden default nav; own header and rail).

| Route | Page | Experience |
|---|---|---|
| `/` | Landing | Public-facing |
| `/input` | 1 Input | Workbench |
| `/review` | 2 Review | Workbench |
| `/allocate` | 3 Allocate (rules + run) | Workbench |
| `/results` | 4 Results (verification, TQs, cabinet summary) | Workbench |
| `/cabinets` | 5 Cabinets (inspector) | Workbench |
| `/revise` | 6 Revise (Rev B) | Workbench |
| `/deliverables` | 7 Deliverables | Workbench |

**Navigation rules.**
- Landing: header (brand, section anchors, Appearance popover, secondary "Workbench" link). The one primary CTA is "Open the workbench" in the hero. No sidebar. [built]
- Workbench: compact header (brand, dataset chip, status chip, Appearance popover, and below 769 px a "Stages" popover that repeats the rail links) + left stage rail (sidebar) with Home, the seven stages and "Start over". The rail is the only navigation; the Stages popover is the same list, not a second system. [built] Each stage shows one of: *done*, *current*, *needs attention*, *not available yet* (disabled with reason).
- Primary action per page is a single filled button; it moves forward (page link) or runs the stage.
- Going to `/` never clears session data. "Start over" (workbench rail) is the only destructive action; it opens a confirmation dialog, clears the dataset and results, and keeps rule settings. [built]

**Session and state rules.**
- All data lives in `st.session_state`; pages are stateless functions of it. [built]
- Status is derived, never stored: lifecycle = f(has input, has allocation, rule fingerprint, input fingerprint, revision fingerprints). [built, existing tested helpers]
- A failed ingest, allocation or revision never overwrites a previous good result. [built]
- Revision input is stored in session (`revision_source`) when chosen, so leaving the Revise page does not change staleness. [built]
- Query parameters are not used for state. Page routes are the only URL state.
- Refreshing the browser starts a new session (Streamlit behaviour). [limit]

## C. Design foundations

### C1. Theme architecture (decision)
Use Streamlit's **native** light/dark themes (`[theme.light]`, `[theme.dark]` in `.streamlit/config.toml`, switched in Streamlit's Settings menu or by the system setting) and define all custom colours as CSS custom properties with `light-dark()`, declared on `.stApp`. Streamlit sets `color-scheme` on `.stApp` per active theme (verified), so tokens flip instantly with no rerun, no server-side theme detection (`st.context.theme` is documented as unreliable on change), no JavaScript and no second theme state. A hex fallback is declared before each `light-dark()` pair for browsers without support.
Trade-offs: no in-app toggle (Streamlit does not expose one); an "Appearance" popover tells users where the switch is. Theme persistence is Streamlit's (browser-local). [limit]

### C2. Colour tokens (`--ss-*`; light | dark)
| Token | Light | Dark | Use |
|---|---|---|---|
| `bg` | `#EEF0F3` | `#12161B` | page |
| `surface` | `#FFFFFF` | `#1A1F26` | panels, tables |
| `surface-2` | `#F6F7F9` | `#222831` | inset areas, table header |
| `border` | `#D3D8DF` | `#303846` | hairlines |
| `border-strong` | `#A9B1BC` | `#4A5565` | inputs, grid cells |
| `text` | `#16202B` | `#E8ECF1` | primary |
| `text-2` | `#46525F` | `#AAB4C1` | secondary |
| `text-3` | `#5F6B78` | `#8F9AA8` | captions (≥ 4.5:1 on `surface`) |
| `accent` | `#0A6C7A` | `#4FC3CF` | action, selection, links |
| `accent-fg` | `#FFFFFF` | `#062329` | text on accent |
| `accent-soft` | `#DCEFF1` | `#173840` | selected backgrounds |
| `ok` / `ok-soft` | `#187233` / `#E1F2E6` | `#4CC775` / `#173A24` | pass, current |
| `warn` / `warn-soft` | `#8A5A00` / `#FBEFD2` | `#F0B64A` / `#41330F` | stale, warning TQ |
| `bad` / `bad-soft` | `#B3261E` / `#FBE4E2` | `#FF8F86` / `#472220` | fail, blocking TQ |
| `info` / `info-soft` | `#2B5DB8` / `#E3ECFA` | `#86AEF5` / `#1C2D4C` | info TQ |

Signal-type tints (fill / text), Okabe–Ito-derived, low chroma, each with a two-letter code shown in the slot:
| Type | Code | Light fill / text | Dark fill / text |
|---|---|---|---|
| AI | `AI` | `#CFE6F5` / `#0B4A72` | `#1E3F57` / `#9FD3F5` |
| AO | `AO` | `#F0D3E3` / `#6B2146` | `#4A2A3D` / `#F1B4D2` |
| DI | `DI` | `#C8EBDD` / `#0A5640` | `#1B4636` / `#8FE0C0` |
| DO | `DO` | `#F8E3B0` / `#6B4700` | `#4D3A12` / `#F5CF75` |
| DO iso + fused TB | `DF` | `#F7D3BB` / `#7A3200` | `#55301A` / `#F5B188` |
| DO relay TB | `RL` | `#CDD6F6` / `#1F3A8A` | `#2A3566` / `#B8C6FF` |
| Wired spare pair | none | hatched `surface-2` | hatched `surface-2` |
| Free slot | none | transparent, dashed `border` | same |
| Held for TQ | `!` | `warn-soft` + `warn` outline | same |
Selected slot: 2 px `accent` ring + `accent-soft` halo.

### C3. Typography
System stacks only (no network fonts; offline demo). Sans: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`. Mono (engineering identifiers only: tags, cables, addresses, TQ IDs): `ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace`, `font-variant-numeric: tabular-nums`.
Scale (px / line-height): 12/16 caption · 13/18 table · 14/20 body-small · 16/24 body · 20/28 h3 · 28/34 h2 · 44/48 h1 (landing, `clamp(2rem, 4vw+1rem, 2.75rem)`). Weights 400, 600, 700. Headlines tight (`-0.02em`), left-aligned, ≤ 22 ch for h1. Line length ≤ 70 ch. No ALL CAPS labels; sentence case.

### C4. Spacing, grid, radii, elevation
4 px base: 4, 8, 12, 16, 24, 32, 48, 72. Content max-width: landing 1200 px; workbench 1360 px. Breakpoints: ≥ 1100 two/three columns; 700–1099 two columns max; < 700 single column. Radii: 4 (cells, chips), 6 (controls), 10 (panels). Elevation: borders, not shadows; one `0 1px 2px` shadow on popovers only.

### C5. Focus, motion, icons
Focus ring: `2px solid var(--ss-accent)`, offset 2 px, on every interactive element including native widgets (override). Motion: 120 ms ease-out for state changes; the only continuous motion is the landing figure's connector flow (2.4 s linear, ≤ 3 elements). `prefers-reduced-motion: reduce` removes it and all transitions. Icons: Streamlit's built-in Material Symbols (`:material/...:`) in buttons/page links, inline SVG elsewhere. No emoji.

## D. Components

Each component is defined in `app/ui/components.py` (or `cabinet.py`, `flow.py`); CSS lives in `app/ui/theme.py`. States listed are the contract.

| Component | Purpose / anatomy | Variants and states | Responsive |
|---|---|---|---|
| App header | Brand mark (12-cell baseplate glyph) + name; landing: anchors, Appearance popover and a secondary "Workbench" link; workbench: dataset chip, synthetic chip, status chip, Appearance popover, Stages popover (< 769 px) | landing / workbench | Anchors collapse < 700 px; Stages popover replaces the hidden sidebar < 769 px |
| Stage rail | Seven stages grouped *Prepare* (1–3), *Inspect* (4–5), *Revise & deliver* (6–7); each = icon, label, status word | done · current · attention · disabled(reason) | Streamlit's collapsible sidebar below ~769 px; the header Stages popover is the mobile path |
| Buttons | Primary (filled accent), secondary (outline), tertiary (text). One primary per page | default · hover · focus · disabled (with adjacent reason) · busy | ≥ 40 px height |
| Status chip | Symbol + word + colour: Current, Stale, Not run, Pass, Fail, Blocking, Warning, Info | as listed | Wraps |
| Banner | Full-width message with symbol, title, one-sentence body, optional action | ok · warn · bad · info | Stacks |
| Metric tile | Label, value, unit/qualifier; qualifier is mandatory when the number is a ratio or synthetic | normal · stale (dimmed + "Stale" chip) | Wraps to 2 or 1 columns |
| Table with toolbar | Native `st.dataframe` under a toolbar (search, severity filter, count); numeric right-aligned; row height ≥ 32 px; hidden index | loading (skeleton text) · empty (explains why + next action) · error | Horizontal scroll inside the table only |
| Empty state | What is missing, why, one action | per page | — |
| Detail panel | Key/value list for a selected slot or TQ | none-selected · selected | Moves below the map < 1100 px |
| Cabinet slot grid | CIOC columns × 8 baseplates × 12 slots; slot 24 × 24 px (display only, not interactive); two-letter code | occupied · spare · free · held · selected · dimmed(by filter) | Columns wrap; each CIOC scrolls horizontally if needed |
| Legend | Type code + tint + word; always visible above the grid | static | Wraps |
| Revision list | Change-type chips (moved / added / deleted / modified in place) + table | filtered · empty | As table |
| Solver status | Window repairs: proven exact N / best found M / fallback; never "optimal" without proof | none-needed · exact · best-found · fallback | Stacks |
| Export actions | Download buttons with file name, size and contents summary; disabled + reason when stale | ready · stale · unavailable | Stacks |
| Dialog | Confirmation for "Start over" (`st.dialog`) | — | — |
| Contextual help | `help=` on metrics and settings; `st.popover` for Appearance | — | — |
| Signal-flow figure | Landing signature, §F | static · animated · reduced-motion | Steps stack vertically < 900 px |

## E. Page specifications

Common to all workbench pages: header; rail; page title (h2) + one-sentence purpose; staleness banner when relevant; one primary action; empty state when a prerequisite is missing (with a button to the missing stage).

### Landing `/`
- **Purpose:** explain SlotSmith in seconds; get the user into the workbench or the demo.
- **Hierarchy:** header → hero (h1, one-paragraph subhead, primary "Open the workbench", secondary "Run the synthetic demo", signal-flow figure) → *How it works* (five real steps; revision as the fifth) → *What you can inspect* (three panels computed from the demo run: a real TQ, the rule-check ledger, the revision impact) → *Method and limits* (factual bullets and the benchmark numbers with synthetic qualifier) → closing CTA → footer.
- **Data:** a seeded synthetic MDB allocated by the real engine, cached for the server process (`st.cache_resource`).
- **States:** if the demo computation fails, the figure and panels are replaced by a short notice; the CTAs still work.
- **Backend:** `generate`, `run`, `revise`, `make_revision`.
- **Acceptance:** one primary CTA above the fold; no sidebar; no invented numbers; every demo-derived element carries "synthetic demo data"; works at 375 px with no horizontal overflow; figure readable without motion.

### 1 Input `/input`
- **Task:** get a workbook into the session.
- **Layout:** two choices side by side (stacked < 900 px): *Upload a workbook* (multi-file uploader: xlsx/xls/csv) · *Generate a synthetic benchmark* (signals, seed, injected errors; defaults 2,000 / 7 / 6). Below: dataset summary once loaded.
- **Main action:** "Review data" (appears when a dataset is loaded).
- **States:** empty (nothing loaded) · ingesting · error (plain-language reason + expandable technical detail; previous dataset kept) · loaded.
- **Backend:** `read_mdb` via `safe_read_mdb`, `generate`, `make_revision`.
- **Acceptance:** corrupt upload → alert, no traceback, previous data intact; synthetic data flagged synthetic everywhere.

### 2 Review `/review`
- **Task:** decide whether the data is usable before allocating.
- **Layout:** readiness banner (Ready / Ready with issues / Blocked) → four metric tiles (rows ingested, signals ready to place, blocking findings, warnings and info) → tabs *Findings* (table + severity filter + search) and *Column mapping* (per-sheet table with symbol + word status, unused headers, missing required fields).
- **Main action:** "Set up allocation" (disabled when Blocked, with reason).
- **Backend:** `validate` via `compute_preflight_audit`.
- **Limit:** column overrides are not supported by the pipeline contract; stated in the tab. [limit]

### 3 Allocate `/allocate`
- **Task:** set rules, run.
- **Layout:** left (wide): Rules panel in four groups: *Capacity* (read-only facts: 12 CHARMs per baseplate, 8 baseplates per CIOC, 4 CIOCs per cabinet; stated as project rules), *Separation* (A/B scope; group isolation; rule toggles), *Spare room* (slider; computed line "N of 32 baseplates kept empty per cabinet"), *Names* (area, unit; patterns shown read-only), plus *CHARM and terminal-block table* (read-only) and *Rule set file* (download / load). Right: Run card with a computed summary of the active rules, readiness, status chip (Not run / Current / Stale) and the primary "Allocate".
- **Behaviour:** editing any rule marks existing results Stale immediately. Allocation runs inside `st.status`; on success the page links to Results; on failure the error is shown and prior results stay.
- **Backend:** `run`, `RuleSet`.
- **Acceptance:** every summary sentence is generated from the current rule set (no static text); no duplicate widget keys.

### 4 Results `/results`
- **Task:** decide whether to trust and use the allocation.
- **Layout:** banner (Verification: 11 of 11 rule families pass / N fail) + status chip → metric tiles (signals allocated, signals covered by a TQ, rows total and coverage, cabinets, CIOCs, baseplates used) → tabs *Rule check* (ledger with symbols), *Technical queries* (toolbar + table + detail), *Cabinets* (summary table with fill bars).
- **Wording rules:** coverage reads "allocated or covered by a TQ"; verification reads "checked by the independent verifier"; never "certified", "guaranteed", "optimal".
- **Next actions:** Inspect cabinets · Revise · Deliverables (secondary buttons; one primary: Inspect cabinets).

### 5 Cabinets `/cabinets`
- **Task:** find and inspect any slot.
- **Layout:** toolbar (cabinet select; tag/cable search; type filter pills) → legend → grid (one column per CIOC, 8 baseplate rows × 12 slots) → detail panel for the selected slot (address, tag, IO type, cable and pair, CHARM, terminal block, group, segregation, source row, TQ ref). Selection happens via the matches table (single row) because sanitised HTML cannot carry events; the map highlights the selection and dims non-matches.
- **Accessibility:** every slot has a text label; the matches table is the keyboard path. [limit: slots are not individually focusable]
- **Acceptance:** search for a known tag highlights exactly one slot; filtered-out slots are dimmed, not removed.

### 6 Revise `/revise`
- **Task:** apply Rev B to Rev A with the fewest disturbances the engine can find.
- **Layout:** Rev B source (upload or the synthetic Rev B created with the benchmark) → "Compare and re-allocate" → solver status panel → metric tiles (moved, added, deleted, modified in place, unchanged, verifier violations) → change filter + impact table → "Download Rev B workbook".
- **Solver wording:** "Window repairs: X proven exact, Y best found within the time limit" and "Fallback: full re-allocation used" when applicable. Results vary between runs (stated). The repair is window-local (stated).
- **States:** needs Rev A (empty state) · Rev A stale (blocked with reason) · running · done · stale.
- **Backend:** `revise`, `write_workbook`, `verify`.

### 7 Deliverables `/deliverables`
- **Task:** export.
- **Layout:** one card per file: Rev A workbook (sheets listed from the real export: IO Allocation, Cabinet Summary, TQ List, Rule Check, Rule Set, Run Info), Rev B workbook (adds Revision Impact), rule set JSON. Each shows file name, size, row counts, status; downloads disabled with a reason when stale.
- **Limit:** layout follows the problem statement's description, not the organiser's template (not released). Stated on the page. [limit]

## F. Landing signature: signal-flow figure (decision in `docs/ux_research.md` §6)
A single row of five steps: **Import → Validate → Allocate → Verify → Slot**. Each step is a card with real content for the *selected* signal: the source row (file, row number, tag, IO type, cable, pair, group, side); validation outcome (TQs touching this signal: count); allocation result (cabinet, CIOC, baseplate, slot, CHARM type, terminal block); verification result (rule families passed on the exported rows); and the destination baseplate drawn as 12 cells, the signal's cell ringed. Signals are chosen with native pills (rerun scoped by `st.fragment`). Connectors carry a slow dash-flow (CSS) toward the destination. Caption: "Computed by SlotSmith from a seeded synthetic MDB when this page loaded. Illustrative; not a live connection." Reduced motion: no animation; identical content. Mobile: steps stack, connectors become vertical.

## G. Light and dark
Both themes are first-class (same token names; values in C2). Behaviour per element:
| Element | Light | Dark |
|---|---|---|
| Page / panels | `bg` / `surface` with 1 px `border` | same tokens |
| Sidebar rail | `surface`, right border | same |
| Tables | `surface`; header `surface-2`; selected row `accent-soft` | same tokens |
| Slots | tinted fills per C2 | tinted fills per C2 (darker fills, lighter text) |
| Status chips | `*-soft` background, `*` text and symbol | same |
| Popovers / dialogs | `surface`, `border-strong`, one small shadow | same |
| Focus | accent ring | accent ring (lighter accent) |
| Disabled | 45 % opacity + `cursor: not-allowed` + adjacent reason | same |
Native widgets follow the matching `[theme.light]` / `[theme.dark]` values. Contrast: body text ≥ 7:1, secondary ≥ 4.5:1, status and slot text ≥ 4.5:1 (checked by script, see review log).

## H. Accessibility and responsive
- Keyboard: every action reachable by Tab; native widgets for all controls; visible focus ring (C5); logical order = visual order; skip link at top of each page. Slot grid: text labels plus the matches table (limit stated in E5).
- Labels: every control has a visible label; icons accompany words, never replace them; status never by colour alone.
- Targets ≥ 24 × 24 px (slots) and ≥ 40 px (buttons).
- Reduced motion: no animation or transition; no auto-playing content.
- Reflow: no horizontal page scroll from 375 px upward; wide tables scroll inside their container.
- Language: sentence case, plain verbs, errors say what happened and what to do.

## I. Performance rules
1. No base64 images or large assets in HTML. Target: initial landing payload < 150 KB of app-generated HTML. Measured: 55.0 KB (previous UI: 2.37 MB, of which 2.19 MB base64 images). See review log §Performance.
2. CSS injected once per run, as a cached string (< 20 KB).
3. Heavy computation (demo allocation, ingest) cached: `st.cache_resource` for the demo, session-cached MDB keyed by input fingerprint.
4. Theme change causes no rerun and no recomputation (CSS-only).
5. Widgets on read-only pages avoid reruns of other pages' work; `st.fragment` for the landing selector and cabinet filters.
6. No external network requests (fonts, CDN, analytics).
7. Solver calls only on explicit button press.

## J. Anti-patterns (prohibited)
Fake telemetry or live indicators · unsupported performance, certification or customer claims · more than one navigation system on a page · duplicate primary CTAs · gradients and glows used as decoration · continuous or random animation · unreadable technical labels · repeated identical cards used as filler · horizontal page overflow · emoji as icons · buttons or links with no real outcome · mock functionality presented as real · static text that restates rule values (generate it from the rule set) · colour as the only status signal.

## K. Acceptance checklist
Verified results are recorded in [docs/ux_review_log.md](docs/ux_review_log.md) §Final acceptance. Items:
- [ ] Landing has no sidebar; one primary CTA above the fold; CTAs work.
- [ ] Signal-flow figure uses real engine output; labelled synthetic; reduced-motion verified.
- [ ] Single navigation system in the workbench; all seven routes load; deep links work.
- [ ] Theme switch (Streamlit Settings or system) changes the whole UI, keeps session, causes no rerun.
- [ ] Stale status appears within one interaction after a rule or input change, on every result page.
- [ ] Upload failure keeps previous results; no traceback.
- [ ] No static rule text; summaries are computed.
- [ ] Cabinet search highlights the right slot; legend and codes present.
- [ ] Revise exposes solver status honestly and offers a Rev B workbook.
- [ ] Deliverables lists real sheets; disabled when stale.
- [ ] 1440, 1280, 768, 375 px × light/dark: no horizontal page overflow, no clipped text.
- [ ] `src/slotsmith/` unchanged (`git diff` empty).
- [ ] Core and audit tests unchanged and passing; new UI tests passing.
