# UI/UX audit (12 Oct 2026)

Scope: the Streamlit app in `app/` as found on branch `claude/slotsmith-product-redesign-5a12d5` (commit `f37c595`), run locally and inspected in a real browser (Playwright Chromium at 1440×900, 820 and 390 px, light and dark). Baseline: 122 tests passed before any change. Severity: critical / high / medium / low.

## Findings

| # | Page | Observed problem | Impact | Sev. | Fix (status) | Verification |
|---|---|---|---|---|---|---|
| 1 | Allocate | Seven "Rule switches". Probe (`scripts/probe_rule_switches.py`, 600-signal synthetic run with 6 IO groups, each switch off in turn): R1 and R2 change the allocation; **R3-capacity, R4-cable, R5-spare, R6-hardware and R7-naming change nothing** (R5 only affects the verifier and repair). Separately, with R6 off and a row whose IO type has no hardware rule (the injected `PULSE-XYZ` error), allocation crashed (`AttributeError` in `export.build_rows`); **fixed in round 2** (see below). | Users believe a constraint was relaxed or enforced when it was not. Decorative controls. | High | Only R1 (grouping) and R2 (segregation), which the allocator, validator, verifier and repair read and which visibly change the result, are offered as switches. The others appear under "Always applied". A loaded rule set that disables an unsupported rule shows a warning. **Implemented.** The R6 crash was fixed in round 2. | `test_only_engine_honoured_rules_are_switchable`, `test_loaded_ruleset_with_unsupported_switch_off_warns`; `scripts/probe_rule_switches.py` |
| 2 | All workbench pages | Nothing showed where the user was in the flow or which stages needed attention; only the sidebar icons. | New users cannot tell the next action. | High | Workflow strip (Import → Review → Allocate → Results → Inspect → Revise → Deliver) on every page, derived from session state (`shell.stage_states`), plus a "Next" action bar. **Implemented.** Configure and Allocate remain one page (rules and run are one decision). | `test_workflow_strip_reflects_real_state`; browser: stale state turns Results/Inspect/Revise/Deliver amber |
| 3 | Results | A run with held rows was headed by the same layout as a clean run; "partial" was not stated. | Risk of reading a partial allocation as complete. | High | Three honest outcomes: verification failed / partial allocation / every row placed. Composition bar (placed, held, not placed). **Implemented.** | `test_results_never_calls_partial_allocation_complete`; browser |
| 4 | Landing | Static signal-flow figure under a plain headline; no sense of the product at a glance, no motion. | Weak first impression. | Medium | Cinematic hero with real engine output, scroll-driven story, same real flow figure. **Implemented.** | Browser screenshots at four scroll positions |
| 5 | Cabinets | 24 px slots, 10 px labels, sideways scrolling, selection details only at the page bottom. | Hard to read at realistic volumes. | Medium | 28 px slots, slot-number header, BP labels, CIOC cards that wrap in a grid, per-CIOC occupancy, selection details above the map, hover tooltip. **Implemented.** | Browser; overflow check (`scrollWidth == clientWidth` at 820 and 390) |
| 6 | Review | Findings table without a detail view; no "effect" explanation. | Blockers and warnings were not explained. | Medium | Selectable finding with effect, affected tags/cables, source rows and recommended fix. **Implemented.** | Browser; `test_review_page_shows_findings_and_next_action` |
| 7 | Input | Unsupported formats and expected columns were not explained; failure gave only the error text. | Users had to guess why a file failed. | Medium | "What a valid file looks like" (columns from `ingest.SYNONYMS`), recovery tips after a failed upload. Parser untouched. **Implemented.** | Existing failed-ingest tests; browser |
| 8 | Deliverables | Cards did not say which run they belong to. | Exports not traceable. | Medium | Run id (hash of rule + input fingerprints), dataset, rule set, verification result, sheet list; downloads disabled when stale. **Implemented.** | `test_deliverables_*`; browser stale check |
| 9 | Revise | No statement of what is preserved vs needs attention; change kinds only coloured text. | Harder to trust a revision. | Medium | Preserved / Needs-attention panels, symbol + word for each change kind, an explanation that no optimality claim is made. **Implemented.** | `test_change_kind_uses_symbol_not_only_colour` |
| 10 | Results → Cabinets | No way from a technical query to its slot. | Slow investigation. | Low | "Find it in the cabinets" sets cabinet and search. **Implemented**, not exercised in the browser (dataframe row selection is canvas-based and could not be clicked reliably). | `test_cabinet_jump_preselects_cabinet_and_search` |
| 11 | Global | Flat neutral-grey look, generic bold sans titles, square buttons. | "Basic" feel. | Medium | Warm paper / near-black palette, serif display titles, pill buttons, shared motion tokens. **Implemented.** | Browser, light and dark |
| 12 | Global | `/input` etc. deep links log 404 on `/<page>/_stcore/health`. | Console noise only. | Low | Framework behaviour; **not changed**. | Console log |
| 13 | Global | A refresh starts a new session; the sidebar emits an `aria-allowed-attr` warning. | Work lost on refresh. | Low | Streamlit limits; **not changed** (documented in `docs/known_limitations.md`). | — |
| 14 | Review | Column mapping is read-only. | Cannot fix a mislabeled header in-app. | Low | Stated on the page; **not implemented** (pipeline has no override). | — |

## External Design References

| Reference | Actually inspected? | What was observed | Borrowed principle | Adaptation | Limits / risks |
|---|---|---|---|---|---|
| MotionSites `/sections` (https://motionsites.ai/sections) | **Yes**, in the built-in browser: one screenshot of the page and computed styles; the home page text was also fetched. Individual section previews and paid prompts were **not** opened. | Near-black page (`rgb(18,18,18)`), system sans stack, all-caps 56 px headline at −1.68 px letter-spacing with one highlighted word, a single white pill CTA, filter chips, card grid of animated previews (15 `<video>` elements). | Tight display type with one accent word; one pill CTA; dark stage that holds the demonstration; motion that shows the product itself. | Hero in a dark surface with an accent word ("verified") and pill buttons; the stage shows real allocation output rather than stock previews. Used only on the landing page. | Gallery of other people's sites: no layouts copied. |
| Cast & Render scroll-scrubbed landing page | **No.** No URL or file was supplied, so only the description in the task brief was used. Nothing about its code or video was inspected. | — | From the description: off-white / near-black palette, editorial type with tight tracking, pill primary action, fixed progress line, text panels that fade between scroll ranges, reduced-motion care. | Pure-CSS scroll-driven story (`animation-timeline: view()`) instead of a video: four chapters fade while a pinned stage fills in with real baseplate data; thin scroll-progress bar; serif display titles. No video asset, no JavaScript. | CSS scroll timelines are Chromium-class only. Elsewhere, and under `prefers-reduced-motion` or below 1000 px, the story renders as a static stacked list (verified for reduced motion and narrow widths). |

## Remaining issues
- R3/R4/R7 toggles exist in `RuleSet` but are not read by the engine.
- Sidebar active-link highlight is subtle in light mode (Streamlit renders it).
- Streamlit has no in-app theme toggle; the Appearance popover explains where it is.
- No browser test of dataframe row selection, file upload or Rev B upload in this pass.

---

# Round 2 (12 Oct 2026): premium redesign, motion and interaction

Baseline measured independently: 131 passed before changes (23 uncommitted files from round 1 preserved). Round-1 screenshots are in `docs/ux/screens/v4/before/`.

## The five highest-impact problems and what was done

| # | Problem (observed) | Solution (implemented) |
|---|---|---|
| 1 | Hero was a text block beside a small static card; right side and bottom of the first viewport empty. | Dark instrument hero on a masked technical grid. The bench shows four source rows, wires into their real slots in four real baseplates, a trace line (Cabinet > CIOC > baseplate > slot, CHARM, source row), 11 verifier checks and the workbook sheets with the Rev B delta. Hover or focus a row to trace it. Plays once; everything is present without animation. |
| 2 | The scroll story was 480 vh with isolated single cards and large empty bands. | One connected stage (the same bench) transformed chapter by chapter in 380 vh: rows, then slots and wires, then checks and verified outlines, then the workbook. Chapter rail with progress. Static fallback has the stage sticky beside the stacked chapters. |
| 3 | Uniform cards and 88 px gaps between sections. | Varied compositions: editorial trace section, dark readout + proof column (technical query, revision strip), numbered principles beside a limits box, closing CTA with workflow index. Section gaps 60 px. |
| 4 | Interaction had no personality: native cursor, abrupt anchors, no entry motion; and **status icons never rendered** (Streamlit strips `<svg>`; round 1 claimed symbols). | Cursor ring, smooth anchors, press feedback, page-enter stagger, stale pulse, verification readout animation. Icons replaced with CSS glyphs. |
| 5 | The workbench read as forms: no run context, no sense of an instrument. | Context bar (breadcrumb, dataset, run id, status), ghost step numerals on grid headers, mono KPI tiles with state rules, dark verification readout on Results, Allocate button above the fold with a sticky run card, selected-slot details above the map, single-match search auto-locates the slot. |

## Defect fixed
R6-hardware off with an IO type that has no hardware rule: cause was `validate()` no longer raising the H-* query when the switch is off, so the row is allocated, while `export.build_rows` assumed `hardware_for()` is never `None`. **Superseded on 13 Oct 2026.** The round-2 fix placed the row with blank hardware and reported H-1..6 as PASS, which a review showed was neither documented nor truthful (the rule register never defined R6-off semantics). The fail-closed interpretation replaced it: `H-*` and the held row are unconditional; R6 off makes the verifier report `H-1..6` as SKIPPED; all pages, the workbook and the verification summary agree. See the implementation report, section "R6 and verification truthfulness".


---

# Round 3 (13 Oct 2026): industrial SaaS transformation

## External references actually inspected (MotionSites)
| URL | What was inspected | Adopted / adapted / rejected |
|---|---|---|
| https://motionsites.ai/motionsite | Full page text and hero screenshot. Thesis: "AI slop" is oversized headings, glowing gradients and generic cards; remedy is typography, spacing, structure and restraint. | **Adopted** as a design test: no glow, no generic card grids, restraint in motion. |
| https://motionsites.ai/sections | Section list (about 98 entries, categories such as Dashboard, SaaS, Footer, Pricing); card DOM; the preview opens at `?prompt=<slug>` with preview on the left and metadata on the right; source code and prompts are behind a paid "Go Unlimited" wall (not accessed). | **Adapted**: product-in-frame composition (our hero bench is real engine output in a frame). **Rejected**: video and WebGL backgrounds, stock photography, copying any prompt or layout. |
| `?prompt=nexora-features`, `?prompt=growth-analytics`, `?prompt=autonomous-ops` | Previews rendered and watched: a chapter list on the left that swaps the visual on the right (growth-analytics), card trio with one active (autonomous-ops), image-led feature cards (nexora-features). | **Adapted** the chapter-list-drives-visual pattern, already present as the scroll story (rail plus pinned stage). |
| `?prompt=nox-grid` | Preview did not render within about 10 s; nothing inspected beyond the title. | Not used. |
| Thumbnails only (not inspected as full templates) | A KPI-row plus sidebar app mock-up under a headline. | Noted only. |
No claim is made about code or assets behind the paywall. Nothing was copied.

## Findings and priority
**P0 trust:** (1) header chip "Results current" in green implied correctness; (2) rail icons and Deliverables "Ready" chip showed success for incomplete or failed work; (3) Revise led with a green "proven exact" banner unrelated to whole-result verification; (4) landing footer showed "not configured" placeholders and hackathon branding; (5) **engine defect found by a realistic partially valid CSV**: a row with a blank tag got a technical query but no output row, so the independent verifier failed Q-1 (blank cells are NaN, which is truthy; `export.add_blocked_rows` keyed it wrongly and wrote 'nan' strings). Fixed with tests; the verifier was not changed.
**P1 usability:** ghost outlined step numerals wasting space; mixed 9.5 to 11 px labels; Allocate overflow at 820 px (two columns squeezing a table); long tile values widening tiles at 360 px; findings table truncating source rows; unresolved held slots listed as "(spare)" in the cabinet table.
**P2 visual:** landing lacked a problem statement, deliverables description and a plain statement of what is and is not validated.
**P3 recorded, not implemented:** persistence and run history, versioned hardware profiles and rule packs, import/export adapters, authentication and access control, upload hardening, deployment, audit log.

## Remaining issues (Round 3)
Mobile header still uses about 300 px of height (Appearance and Stages stack). A genuine verification FAIL can be produced by the engine only through bugs (as found above) or tampering; the FAIL state is exercised through injected results in tests, not through a UI-reachable rule. Streamlit's `stMain` scroll region is a tab stop. No screen-reader or axe run was possible. Findings table cannot export. The upload widget shows Streamlit's 200 MB limit; large-file behaviour was not tested.
