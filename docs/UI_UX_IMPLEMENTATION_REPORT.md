# UI/UX implementation report

Branch `claude/slotsmith-product-redesign-5a12d5` (worktree). Nothing committed, pushed, merged or reset. Findings and references: [UI_UX_AUDIT.md](UI_UX_AUDIT.md).

## Design direction
Premium editorial look on top of a precise workbench. Warm paper / near-black neutrals, the existing teal accent, a serif display face for titles (system stack: Iowan Old Style, Palatino, Georgia; no web fonts, works offline), pill buttons with an ink primary, shared motion tokens (120/200/420 ms, one easing). The landing page is expressive; the workbench uses only short transitions and a 6 px rise on new panels. Engineering, Python and Streamlit architecture are unchanged.

## Reference-driven decisions
- MotionSites (inspected): tight display type with one accent word, dark stage, single pill CTA → landing hero.
- Cast & Render (**not inspected**, brief only): restrained palette, scroll-controlled panels, progress line, reduced-motion care → CSS-only scroll-driven story and a scroll-progress bar. No video: a pinned stage of real baseplates communicates the product better and costs no assets. Rationale and limits in the audit.

## Page by page
- **Landing**: dark hero container carrying the real buttons ("Open the workbench", "Run the synthetic demo"); four real baseplates from the demo allocation animate in, then the 11 verifier rule families tick; scroll-driven four-chapter story (Import / Allocate / Verify / Deliver) with a pinned stage; signal trace; evidence panels; method and limits; closing CTA. Static stacked fallback for reduced motion, narrow widths and browsers without scroll timelines.
- **Workbench shell**: workflow strip on every page (state derived from session: done, attention, blocked, locked, current), "Step n of 7" eyebrow, serif title, "Next" action bar.
- **Import**: accepted formats, expected columns (from `ingest.SYNONYMS`), what happens to a file, recovery tips after a failed read.
- **Review**: readiness banner, tiles, selectable findings with effect, affected rows, source and recommended fix.
- **Allocate** (configure and run): grouped rules, only genuinely effective switches (R1, R2), "Always applied" list, spare slider, naming, rule-set file; run card lists rules in force and what a re-run replaces.
- **Results**: verification-failed / partial / complete outcome, composition bar, tiles, rule check, filterable queries, jump to the slot in Cabinets.
- **Cabinets**: CIOC cards in a wrapping grid, 28 px slots with symbol + code, BP/slot headers, occupancy, summary tiles, search and type filters, selection details above the map.
- **Revise**: how-it-works disclosure with no optimality claim, preserved vs attention panels, change kinds with symbols.
- **Deliverables**: per-artifact run id, dataset, rule set, verification, sheet list; downloads only for existing, current files.

## Design-system changes
`app/ui/theme.py` now assembles tokens plus `app/ui/css/{base,workbench,landing,responsive}.css`. New tokens `ink`, `ink-fg`; new components `stage_strip`, `page_header`, `composition_bar`, `change_kind`, `shell.header`, `shell.next_action`, `flow.viz_html`, `flow.story_html`. `.streamlit/config.toml` theme colours mirror the tokens.

## Files changed
`app/ui/{theme,components,shell,flow,cabinet}.py`, `app/ui/css/*` (new), `app/views/{landing,input,review,allocate,results,cabinets,revise,deliverables}.py`, `.streamlit/config.toml`, `tests/test_ui_app.py`, `tests/test_ui_components.py`, `tests/test_ui_redesign.py` (new), `scripts/probe_rule_switches.py` (new), `docs/UI_UX_*.md`.

## Functional findings and fixes
- Switches for R3, R4, R5, R6, R7 did not change the allocation; removed as controls and listed as always applied (an imported rule set that disables them triggers a warning). R6-off crash with an unmapped IO type is a backend defect: **documented, not fixed**.
- No change to ingestion, validation, allocation, verification, repair or export code under `src/`.

## Test changes (disclosed)
- `test_ui_app.py`: the toggle-count assertion changed 7 → 2 (the removed switches were decorative); the landing-demo test now looks for the new Review title (it moved from a markdown heading into HTML).
- `test_ui_components.py`: stylesheet size budget 20,000 → 60,000 characters (the CSS now lives in four files). No assertion about behaviour, contrast or tokens was loosened.
- Nine tests added in `test_ui_redesign.py`.

## Commands
```bash
.venv/bin/streamlit run app/streamlit_app.py          # launch (this session used the main checkout's venv on port 8511)
.venv/bin/python -m pytest -q                         # full suite
.venv/bin/python scripts/probe_rule_switches.py       # which rule switches change the engine
```

## Results
- Baseline before changes: 122 passed. After: **131 passed** (`pytest -q`, 38 s). Skipped: none. Failed: none.
- Browser inspection **occurred** (Playwright Chromium): landing at 1440 light and dark, 820 and 390 px, at four scroll positions; Import, Review, Allocate, Results (technical queries tab), Cabinets, Revise (after a real Rev B run), Deliverables at 1440; Cabinets at 820 and 390; dark Results/Cabinets. No horizontal overflow at 820 or 390 (`scrollWidth == clientWidth`). Reduced motion verified by computed style (story static, animation `none`). Rule change → results stale across strip, rail, chip and banner, and the download button disabled.
- **Not verified in a browser**: file upload (valid and invalid), Rev B upload, dataframe row selection, the Results → Cabinets jump button (covered by AppTest only), keyboard-only traversal, Safari/Firefox (the scroll story is Chromium-class and falls back to the static layout elsewhere), screen reader behaviour.

## Remaining limitations
Streamlit has no in-app theme switch and a refresh starts a new session. The scroll story depends on CSS scroll-driven animation. Column mapping cannot be overridden. The stage strip is informational; navigation stays in the sidebar because internal links would reload the app and drop the session. The R6/R3/R4/R7 backend items above remain.

---

# Round 2 (12 Oct 2026): premium redesign, motion and interaction

Same worktree and branch; nothing committed, pushed, merged or reset. The 23 uncommitted files from round 1 were preserved and built on. Design rationale: [../design.md](../design.md) (v4 section). Problems and solutions: [UI_UX_AUDIT.md](UI_UX_AUDIT.md) (Round 2).

## What changed
- **Landing**: hero rebuilt around the "bench" (source rows → wires → real baseplates → trace line → 11 verifier checks → workbook), on a masked technical grid; one connected scroll story that transforms the same bench in four chapters with a chapter rail and a scroll-progress line; editorial trace section; dark verification readout beside a technical query and a revision strip; numbered method principles beside a limits box; closing CTA with workflow index; footer with project links read from `SLOTSMITH_REPO_URL`, `SLOTSMITH_DOCS_URL`, `SLOTSMITH_VIDEO_URL` (https only; unset shows "not configured", nothing invented).
- **Interaction layer** (`app/ui/fx.py`, `base.css`): cursor ring, smooth anchors, press feedback; all disabled for coarse pointers and `prefers-reduced-motion`.
- **Workbench**: context bar (breadcrumb, dataset, run id, status), ghost step numerals on grid headers, mono KPI tiles with state rules, dark verification readout on Results, Allocate button above the fold with a sticky run card, selected-slot details above the map in a 3-pair grid, single-match search auto-locates and rings the slot, page-enter stagger, stale chip pulse.
- **Fixes**: status icons were invisible in round 1 because `st.html` strips `<svg>`; now CSS glyphs. R6-hardware crash closed; the first fix (blank hardware, `PASS`) was replaced on 13 Oct 2026 by the fail-closed design below.

## Architecture notes
- `theme.stylesheet()` concatenates `app/ui/css/{base,workbench,landing,responsive}.css` (about 50 KB, one `<style>` per page render). Cached per process: **restart Streamlit after Python or CSS edits** (the file watcher does not reload `theme`).
- Streamlit's sanitiser strips `<svg>` and breaks `<script>` bodies that contain HTML-looking literals (`'<i></i>'`), so the cursor builds its nodes with `createElement`, and diagrams are HTML/CSS. `st.html(..., unsafe_allow_javascript=True)` runs the script in the page; the script guards itself so reruns do not duplicate it (verified: one `.ss-cursor` after navigation).
- Hero and story share `flow.bench_html(bundle, mode)`; its content is the existing seeded synthetic demo (`app.core.demo.build_demo`), not a second allocator.
- Trace-on-hover uses CSS `:has()` (no JavaScript). Scroll story uses `view-timeline` named `--story`; one block guarded by `@supports`, `prefers-reduced-motion: no-preference` and `min-width:1000px`.

## Motion behaviour
Hero: wires draw (700 ms), slots pop (staggered, 480 ms), checks tick, workbook chips fade in; total about 3.3 s, content readable throughout. Story: chapters cross-fade with no overlap (verified: one chapter at opacity 1 at four scroll positions), slots fill, wires draw, checks tick, outlines turn green. Workbench: 320 ms staggered rise on new blocks, 200 ms hover/press transitions, readout cells pop. Nothing delays an action.
**Route transitions**: investigated; Streamlit page switches are server reruns, so no true cross-page animation exists. Provided: page-enter stagger, native running indicator, `st.status` for allocation and revision. No claim of animated navigation is made.

## Test report
Commands (project venv `/Users/siddhant_patil/Projects/SlotSmith/.venv`):
```bash
.venv/bin/python -m pytest -q                      # baseline before round 2: 131 passed (38-44 s)
.venv/bin/python -m pytest -q                      # final: 145 passed, 0 failed, 0 skipped (36.5 s)
.venv/bin/python -m pytest -q tests/test_hardware_switch.py tests/test_ui_redesign.py
```
New tests: 2 (`test_hardware_switch.py`, regression for the R6 crash) and 12 more in `test_ui_redesign.py` (bench traces engine rows, links never invented, cursor layer contract, reduced-motion guard on every scroll-linked rule, no `<svg>` icons, run id, readout honesty, header context, single-match locate). No assertion was weakened; the only edits to existing tests are the two disclosed in round 1.

## Responsive / accessibility report
**Verified in Chromium (Playwright automation):**
- No horizontal overflow (`scrollWidth <= clientWidth`) on all 7 workbench pages at 1024, 820 and 390 px, and on the landing page at 1024, 820, 390 and 360 px.
- Landing at 1440, 1024, 820, 390 (screenshots); hero CTAs full width when stacked; reduced motion: no cursor, `animation-name: none`, `scroll-behavior: auto`, story static (1006 px instead of 3420 px).
- Dark appearance: landing evidence section only in round 2 (the workbench dark pages were last inspected in round 1, before the v4 restyle).
- Keyboard: Tab reaches skip link, nav anchors, Appearance; focus outline is 2 px solid on every stop observed; Enter on "Open the workbench" navigates.
- Cursor: single instance, `pointer-events:none`, `link` state over buttons, click still navigates, survives navigation.
- Smooth anchors (scrollTop sampled over time), hover trace (computed display of trace rows), file upload success (CSV) and failure (corrupt .xlsx shows banner and recovery steps), single-match cabinet locate. Stale state after a rule change was verified in round 1 only (v4 restyle not re-screenshotted).
**Not verified:** Safari/Firefox (scroll story falls back to static; the cursor is plain JS), touch devices (emulated viewport widths only, no touch events), screen readers, keyboard-only completion of the whole workflow, Results→Cabinets "Find it in the cabinets" button in the browser (AppTest only; dataframe row selection is canvas-based), Rev B upload, contrast of the new dark surfaces (colours chosen to match existing contrast-tested tokens, but not re-measured), 360 px workbench pages, the narrow-header icon row fix (CSS added after the last screenshot pass).

## Remaining limitations
Streamlit's `stMain` scroll container is itself a tab stop (framework). No cross-page transitions. Landing story needs Chromium-class scroll timelines. Cabinet colour for blank-CHARM rows falls back to AI. CP-SAT revision windows vary between runs (proven exact vs best found), as already disclosed. Footer links stay "not configured" until the variables are set.

## Before / after
See the Round 2 table in the audit: (1) hero card → connected technical bench; (2) isolated story cards → one transforming stage; (3) uniform cards → varied compositions; (4) native, abrupt interaction → cursor, smooth anchors, press and entry motion, and icons that now actually render; (5) forms → instrument-like workbench with context, readouts and an above-the-fold primary action. Screenshots: `docs/ux/screens/v4/before/` and `docs/ux/screens/v4/after/` (01 landing, 02 import, 03 review, 04 allocate, 05 results, 06 inspect, 07 revise, 08 deliverables, plus error, reduced-motion, dark, story and narrow views).


---

# R6 and verification truthfulness (13 Oct 2026)

**Decision (project owner): fail closed.** Documented: an I/O type with no hardware mapping raises the blocking `H-*` technical query (dossier lines on `H-*`, rule register section 6). Not documented anywhere: what switching R6 off means. The previous fix I made assumed "R6 off = not enforced", cited the rule register for it (it does not say that), placed the row with blank CHARM/terminal block, and the verifier reported `H-1..6` as `PASS`. That was untruthful, and has been replaced. The chosen interpretation is **not organiser-approved**.

## Behaviour
- `validate()` raises the `H-*` blocking query whether or not R6 is on (message notes "R6-hardware is switched off, but unknown hardware stays unresolved"). The row is held exactly as with R6 on: status `TQ raised`, `TQ Ref` set, no slot, CHARM and terminal block empty, tag, source and original I/O type preserved; its cable pair appears as a held slot. No hardware is invented.
- `export.build_rows` raises `ValueError` if an unmapped signal ever reaches it (unreachable by construction) instead of emitting a blank allocated row.
- R6 off only changes the verifier: `H-1..6` is `SKIPPED`.

## Verification status model (`src/slotsmith/verifier.py`, `app/core/state.py`)
Per family: `PASS` (ran, no violation), `FAIL` (ran, violation), `SKIPPED` (not run: controlling switch off, or `group_isolation_level = none` for G-1). Switchable families: S-1 (R2), G-1 (R1), P-1 (R5), H-1..6 (R6). Report rows gain a `Note` key. `summarize()` gives passed / failed / skipped counts and an outcome: `passed` (all 11 ran and passed), `failed`, `incomplete` (nothing failed, something skipped), `missing`. `is_verifier_certified` is true only for `passed`. A new independent Q-1 sub-check fails any placed signal row without CHARM/terminal block regardless of switches. Allocation completeness, technical-query status, verification outcome and disabled rules are shown as four separate lines on Results.

## Export changes (workbook schema)
`Rule Check`: new `Note` column; skipped rows read `SKIPPED`. `Rule Set`: one `rule switch <id>` row per switch with `ON`/`OFF` (previously switches were not listed). `Run Info`: `disabled rule switches`, `verification` (counts, outcome, skipped families and reasons), `unresolved hardware (H-* queries)`, `technical queries`. `TQ List` already carried the `H-*` row. `IO Allocation` is unchanged in layout; unresolved rows are identified by `Status = TQ raised` and `TQ Ref`, hardware cells stay empty.

## UI changes
Results: banner separates partial allocation, unresolved hardware and incomplete verification; Outcome panel lists allocation, queries, unresolved hardware, verification counts and disabled rules; readout shows `10/11`, skipped cells and "Not a full verification"; rule table shows a Skipped chip with the note. Cabinets: red dashed `?` slot for held unresolved hardware (legend, tile qualifier, banner, aria label with TQ id); `type_code` no longer falls back to the AI tint, and any placed signal without hardware is drawn as unresolved. Revise: verification counts incl. skipped, unresolved rows stated as not preserved as valid. Deliverables: banner "not a fully resolved, fully verified result", per-workbook check text, disabled rules, unresolved count. Allocate: corrected banner (disabling a rule does not make unknown hardware valid) and a notice listing the families that will be skipped. Workflow strip flags unresolved hardware / skipped checks.

## Tests and results
Baseline before changes: 145 passed. Final: **170 passed, 0 failed, 0 skipped** (`.venv/bin/python -m pytest -q`, 41 s). `tests/test_hardware_switch.py` was rewritten (19 tests: enabled and disabled R6, traceability, TQ export, SKIPPED not PASS for R6/R1/R2/R5 and isolation none, overall status, workbook metadata read back with openpyxl, strict re-verification, mutation of a placed row, revision with R6 on and off, normal mappings, wrong-terminal-block mutation); 8 UI tests added to `tests/test_ui_redesign.py`; one existing assertion updated (banner wording). `tests/test_core.py` unchanged and passing. `git diff --check` clean.

## Browser validation (Chromium, Playwright)
R6-off rule set loaded through the Allocate page upload; Allocate, Results (incl. Rule check tab), Cabinets (unresolved slot found in cabinet 02, tile and aria label checked), Revise (real Rev B run), Deliverables inspected; R6-on Results inspected. Screenshots: `docs/ux/screens/v5/`. Not browser-tested: narrow widths and dark mode for the new states.

## Remaining ambiguity / limitations
Organiser has not defined R6-off; the interpretation above is the owner's decision. With R6 off the engine still assigns table hardware to mapped types. Pre-existing: with R2 off a cable inherits one side, so `M-1` can fail; reported as FAIL. CLI exit codes do not treat "incomplete" as failure (only violations).


---

# Closeout review of the R6 / verification changes (13 Oct 2026)

**Reproducibility.** From the worktree root: `/Users/siddhant_patil/Projects/SlotSmith/.venv/bin/python -m pytest -q -p no:cacheprovider` (Python 3.12.13, pytest 9.1.1) printed `170 passed in 40.47s` before this closeout, and `174 passed` after (4 tests added: 3 CLI, 1 end-to-end workbook consistency). **Environment risk:** that venv's editable install of `slotsmith` points at the *main checkout* (`/Users/siddhant_patil/Projects/SlotSmith`), not the worktree. Under pytest the worktree's `src` wins because of `pythonpath = ["src"]` (verified by printing `slotsmith.__file__`), and the Streamlit app inserts `ROOT/src` first. A plain `python -c "import slotsmith"` or the `slotsmith` console script, however, imports the main checkout's code. Use `PYTHONPATH=src` for CLI/script runs from the worktree.

**CLI exit codes.** Contract in the dossier: 0 = no violations, 2 = violations. Callers: `allocate`, `verify`, `revise` in `src/slotsmith/cli.py`; no other caller or documented convention. An incomplete verification exits 0 because it has no violation. I did **not** change the exit code: the contract does not say, and a new non-zero code would alter behaviour for anyone who disables a rule on purpose. I made the output truthful instead (`verify` prints SKIPPED rows with their note and a `verification: N passed, N failed, N skipped -> outcome` line; `allocate` and `revise` write that line to stderr unless the outcome is `passed`) and pinned it in `tests/test_cli_verification.py`. **Superseded:** decided later the same day, see "Resolution of the closeout decisions" (exit 3).

**R2-off / M-1.** Established by requirements: S-1 (A and B never share a CIOC) and S-2 (a cable containing both A and B is blocked with a TQ), both written with the switch on; M-1 requires exported rows to match the MDB. Not established: what a mixed A/B cable should do when R2 is off. Implemented: S-2 is raised only when R2 is on (`validate.py`); with R2 off the cable becomes one block whose side is `next(iter(segs))` over a *set*, and the export writes that single side on every signal row, so rows disagree with the MDB and `M-1` fails. That is a correct detection, not a verifier bug. New finding: the chosen side depends on string hash order, so it is **non-deterministic across processes** (`PYTHONHASHSEED=0..2` gave B, `3` gave A on the same data); there is also no technical query for the silent rewrite. **Superseded:** resolved later the same day, see "Resolution of the closeout decisions".

**Consistency checks performed.** Real workbooks (not mocks) for Rev A and Rev B written by the app session with R6 off are read back and compared with the in-memory status: verification counts and outcome, disabled switches, unresolved-hardware count, `SKIPPED` row and `H-*` TQ rows all agree. Browser (Chromium): R6-off flow in dark mode at 1440 (Results, Cabinets unresolved slot, Revise), dark at 390 and light at 820 for Results, Cabinets, Revise and Deliverables with no horizontal overflow; screenshots 09-11 in `docs/ux/screens/v5/`.

**Still not tested.** Keyboard-only use of the new states, screen readers, Safari/Firefox, touch, 360 px for the new states, R2/R1/R5-off flows in the UI (covered by engine tests only), CLI `revise` with a skipped family, and CLI behaviour from a clean venv that actually installs the worktree.

**Risks to carry into the frontend work.** (1) The header chip says "Results current" even when verification is incomplete or hardware is unresolved: it means *not stale*, which can be misread. (2) Several pages must keep deriving wording from `verification_status`; do not reintroduce "all passed". (3) Restart Streamlit after Python or CSS edits. (4) Streamlit strips `<svg>`. (5) The R2-off non-determinism can make Results flip between failed and incomplete across server restarts.


---

# Resolution of the closeout decisions (13 Oct 2026)

**1. CLI exit codes (decided: distinct code 3).** `allocate`, `verify`, `revise` return `0` (every family ran, no violation), `2` (any violation or failed family; takes precedence) or `3` (no violation, incomplete verification). Callers of `cli.main`: only the `slotsmith` console script (`pyproject.toml`); README, dossier and scripts only show the commands and contained no `$?` handling. Implemented in `src/slotsmith/cli.py` (`EXIT_*`, `_exit_code`), documented in README and the dossier, pinned by `tests/test_cli_verification.py` (full pass 0; R6 off allocate/verify/revise 3; tampered terminal block 2; violation beats skipped; unit test of the precedence).

**2. Mixed A/B cable with R2 off.** Findings: S-1/S-2 and M-1 are documented only with R2 on; nothing says what R2 off does with a mixed cable. The data model already stores a side per signal (`Signal.seg`) but the cable block holds one (`CableBlock.seg`), chosen as `next(iter(set))`, so (a) placement (the allocator packs by `block.seg`, independent of the R2 switch) and (b) the exported side of every signal varied with string hash order and overwrote original data, which M-1 correctly flagged. Fix, without a new rule: a mixed cable has no single side (`None`, so it is packed as an unsided cable); export rows keep each signal's own side (`s.seg`, falling back to the cable value only when the signal has none, i.e. unchanged behaviour for ordinary cables); a **warning** TQ `S-2` states that separation is not enforced for the cable; revision rebuilds a cable's side from its rows and treats disagreeing rows as no single side so unchanged mixed cables stay pinned. The same defect existed for mixed IO groups with R1 off or isolation `none`; fixed the same way (TQ `G-3`). M-1 is untouched: a deliberately altered side still fails it (tested). Files: `src/slotsmith/validate.py`, `export.py`, `revision.py`; tests `tests/test_mixed_cable.py` (6, including five `PYTHONHASHSEED` subprocess runs that must give identical output). **Remaining decision:** whether S-2/G-3 should stay *blocking* regardless of the switch (like `H-*`); current choice discloses but does not hold the cable.

**Tests run.** `PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider` from the worktree: **182 passed in 43.67s** (174 before this resolution + 6 in `test_mixed_cable.py` + 2 in `test_cli_verification.py`). The earlier statement that R2 off makes M-1 fail on the synthetic data no longer holds; `test_other_switchable_families_are_skipped_when_off` now asserts `incomplete`.

---

# Round 3 (13 Oct 2026): industrial SaaS transformation

Baseline at start: 42 uncommitted entries (verified, all preserved), 182 tests passing. Final: **199 passed** (`PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider`, 44 s), `git diff --check` clean. Nothing committed or pushed. Design rationale and references: `design.md` (v5 additions) and `docs/UI_UX_AUDIT.md` (Round 3).

## What changed
- **Shared status** (`app/core/status.py`): `RunStatus`, `run_status`, `revision_status`, `next_actions`. Header, rail, strip and pages read it; chips `freshness_chip` and `verification_chip` replace the single "Results current" chip (a stale run shows "Previous run: verification ...").
- **Results**: verdict first, five separate facts, required actions, readout, then tables; Violations panel and skipped-check banner in the Rule check tab; explanation that allocation success is not verification success.
- **Revise**: Rev B verdict and readout first; local repair search stated as local only, with rejected windows explained as "not accepted, nothing applied".
- **Deliverables**: file freshness and verification outcome shown separately; captions state "not a fully resolved, engineering-verified result" when applicable; Rev B card gains rule set, disabled rules and query totals. Download gating unchanged (only stale files are blocked). This policy is retained deliberately; whether failed or incomplete files should be downloadable is left as a human decision.
- **Allocate**: states what an edit makes stale; run card stacks first on tablet.
- **Review**: findings table with Affected and First source row columns; **Cabinets**: held and unresolved slots labelled correctly in the table, hardware and technical-query rows in slot details.
- **Landing**: problem section, deliverables table, Supported / Experimental / Not validated, synthetic-consistency statement; hackathon branding and placeholders removed; headline now "checked" rather than "verified".
- **Styling**: workbench titles sans, outlined numerals removed, minimum technical text 11 px, tile/chip wrapping fixes.
- **Engine fix** (`src/slotsmith/export.py`): `add_blocked_rows` keys blank tags like `validate()` and exports NaN as empty. Regression tests in `tests/test_blank_cells.py` (including that the verifier still fails if a blocked row is dropped).

## Files changed this round
`app/core/status.py` (new), `app/ui/components.py`, `app/ui/shell.py`, `app/ui/css/{base,workbench,landing,responsive}.css`, `app/views/{results,revise,deliverables,allocate,review,cabinets,landing}.py`, `src/slotsmith/export.py`, `tests/test_ui_trust.py` (new, 14), `tests/test_blank_cells.py` (new, 3), `tests/test_ui_app.py`, `tests/test_ui_redesign.py` and `tests/test_ui_components.py` (wording and CSS-size-budget updates: stylesheet budget 60k to 70k characters; results/revise/footer assertions updated to the new, stricter wording), `README.md` (screenshot paths and one description), `design.md`, `docs/UI_UX_AUDIT.md`.

## Verified (run in this round)
- **Tests:** full suite 199 passed.
- **Browser (Playwright Chromium)**, real workflows on synthetic data and fixtures: synthetic run with R6 on and off; unsupported I/O type held in both; skipped-rule incomplete verification; partially valid CSV upload (blank tag, unknown I/O type, duplicate tag, missing pair) with findings search; corrupt xlsx earlier; rule change making results stale (header, verdict, download disabled); Rev B run; **downloaded Rev A and Rev B workbooks and read them with openpyxl: verification counts, disabled switches, unresolved hardware and query totals match the UI**. A genuine verification failure occurred on the partial CSV before the engine fix (Q-1) and was observed in the UI (verdict "Verification failed", failed readout cell), which is what exposed the defect.
- **Layout:** no horizontal overflow on all seven pages at 1440x900, 1280x800 (light), 820x1000, 390x844 (dark and light) and 360x740; landing at 1280, 820, 390, 360. Dark appearance at 1280 and 390; reduced motion (verdict animation none, cursor hidden); keyboard Tab order and focus rings on the Results page; minimum text size probe (no technical text under 11 px after fixes except the 10.5 px legend swatch codes, since raised).
## Inferred, not directly tested
Contrast of the new verdict colours (they reuse contrast-tested tokens); behaviour at browser zoom other than 100%; Safari and Firefox; touch input.
## Not tested
Screen readers and automated accessibility tooling; keyboard-only completion of the whole workflow; large uploads; a UI-reachable genuine verification failure after the engine fix (the FAIL state is covered by tests with injected check results); Rev B upload; the narrow-screen header height.

## Remaining decisions for a human
(1) Whether failed or incomplete workbooks should remain downloadable (current, conservative: yes, labelled). (2) Organiser confirmation of R6-off and mixed-cable/mixed-group semantics (still open, unchanged). (3) Whether project links (repository, documentation) should be published on the landing page; they stay hidden until configured.
