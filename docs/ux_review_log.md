# UX review log

Red team (find what is wrong), green team (confirm what must be kept), and final acceptance for the 11 Oct 2026 redesign. Everything below was observed in this session; where something was not re-checked after a fix, that is said. Specification: [design.md](../design.md). Research: [ux_research.md](ux_research.md). Features: [feature_capability_matrix.md](feature_capability_matrix.md).

Method: the old UI was run and measured first (screenshots in `docs/ux/screens/before/`); the new UI was then built and inspected in a real Chromium pane at 1440×900, 1280×800, 768×1024 and 375×812 in light and dark across the seven workbench views (56 screenshots in `docs/ux/screens/after/matrix/`), plus targeted journey screenshots in `docs/ux/screens/after/`. Automated checks: 122 tests (see §Tests).

## Red team findings

| # | Sev | Finding | Evidence | Fix | Verified | Remaining risk |
|---|---|---|---|---|---|---|
| R1 | High | Old app crashed on the Allocate page with `StreamlitDuplicateElementKey` (two widgets shared a key). | Reproduced by loading data then opening Allocate in the old UI. | Rewrote the page; rule widgets use unique `rule::` keys; `test_*` journey tests render every page. | Journeys in AppTest and browser; no exceptions on any page. | None known. |
| R2 | High | Old rule summary was hard-coded text ("20% spare" etc.), so it stayed wrong after the user changed a rule. | Read of old `streamlit_app.py`. | `rules_view.rule_summary(rules)` generates every sentence from the current `RuleSet`. | `test_changing_spare_percent_changes_summary_and_marks_results_stale`; browser: loaded a 30 % rule set and the text changed. | New rule types need new summary text (code). |
| R3 | High | Old landing page showed invented-looking numbers and a decorative "live" visual not tied to the engine. | Before screenshots. | Landing figure and panels are computed by the real engine from a seeded synthetic MDB and labelled synthetic. | `test_demo_bundle_is_real_engine_output`, `test_flow_figure_shows_real_values_and_label`. | Figure is a snapshot taken when the server starts, not live (stated on the page). |
| R4 | High | Old landing page was slow and re-sent 2.19 MB of base64 images on every rerun. | Measured: see §Performance. | Removed all embedded images; HTML is style plus small inline SVG. | Re-measured: 0 data URIs. | None. |
| R5 | High | `.streamlit/config.toml` in the working copy set `enableCORS=false` and `enableXsrfProtection=false`. | File read. | Removed both from the worktree copy; the originals in the main checkout are untouched. | `grep` of config. | If the main checkout is used, the user should decide whether it needs those flags. |
| R6 | High | A new upload was not reflected until the next interaction (the page rendered before session state changed). | Browser only; AppTest cannot upload. | `st.rerun()` after a successful load or Rev B upload. | Browser: upload of a 607-row workbook updated the dataset chip immediately. | None known. |
| R7 | Med | Several colour pairs failed contrast (secondary text, some chip tints, caption text). | Computed contrast script. | Adjusted tokens; added `ok` `#187233`; stylesheet tests assert the key pairs in both themes. | `test_*contrast*`; browser spot checks. | Native Streamlit widget text uses Streamlit's own theme values (mirrored in `config.toml`). |
| R8 | Med | `help=` tooltip on enabled page links produced noise and a focus trap. | Browser. | Tooltip only on disabled links, where it explains why. | Browser. | None. |
| R9 | Med | On narrow screens the sidebar is hidden, leaving no obvious way to move between stages. | 375 px screenshot. | Header "Stages" popover appears below 769 px and repeats the rail links. | 375 and 768 px screenshots. | The Stages popover is a second control for the same links; it is hidden above 769 px. |
| R10 | Med | At 768 px the header overflowed. | 768 screenshot. | Re-flowed the header columns; Appearance and Stages share the right-hand column. | 11 Oct, after the fix: all seven views at 768×1024 **dark** have `scrollWidth` ≤ `clientWidth` (768 / 767). The 768 dark screenshots in `matrix/` were captured before this fix; the 768 light ones were re-checked after. | The overflow check is numeric for dark; screenshots for 768 dark were not retaken. |
| R11 | Med | Cabinet legend was not exposed to assistive technology and the scroll region had no keyboard stop. | Axe-style review of markup. | `role=list/listitem` legend; scroll region has `tabindex="0"` and a label; slots are `role="img"` with text labels. | `test_cabinet_*`; browser. | Individual slots are not focusable (limit documented). |
| R12 | Med | `.xls` was advertised in both uploaders but `xlrd` is not installed, so such a file always failed. | Ingest returned "Install xlrd >= 2.0.1". Present in the old UI too. | Removed `xls` from the file types and copy; the backend failure remained graceful in any case. | `grep` of `app/views`; tests. | Users with `.xls` must convert to `.xlsx` or CSV. |
| R13 | Low | The app requests Material Symbols (icon font) from Google Fonts. | Network log: 1 external request. | Left as is: the font is bundled by Streamlit's icon syntax and cannot be removed without losing icons. Documented. | Network log. | Offline use loses icon glyphs (labels remain). Landing and review were checked offline: `offline_*_1440_light.png`. |
| R14 | Low | Streamlit's sidebar emits an `aria-allowed-attr` violation. | Accessibility scan. | Framework element; not changed. | – | Remains. |
| R15 | Info | 27 tests in the old `tests/test_ui.py` asserted old strings and internals. | Listed in the session log (`kept 50, dropped 27`). | Replaced with `tests/test_ui_core.py` (50 kept as-is, same logic), `test_ui_components.py` and `test_ui_app.py` that test the new behaviour. No test was loosened to pass; the removed ones tested UI that no longer exists. | `artifacts/baseline_test_ui.log` (before) vs `artifacts/final_tests.log` (after). | The reviewer should judge whether the 27 removals are acceptable. |
| R16 | Info | A browser refresh starts a new session (Streamlit design). | Browser. | Routes show empty states with a button to the missing stage. | Browser. | Work is lost on refresh. |

## Green team: kept on purpose

- Derived status from fingerprints (existing, tested), shown in the header, rail, and a banner on each result page.
- Failure never overwrites a previous good result.
- Verification wording: "all 11 rule families passed the independent check on the exported rows". There is no "certified" or "violation-free" claim anywhere.
- CP-SAT is described only as revision repair; baseline allocation is described as first-fit-decreasing packing.
- Synthetic data labels on every demo-derived element.
- Native widgets everywhere interactive; no custom JavaScript.

## Performance

Measured in the same Chromium pane, 1440 px, cold load of `/`, light scheme.

| Metric | Old UI | New UI |
|---|---|---|
| Landing HTML in DOM | 2,365,932 B | 54,996 B |
| Base64 data-URI bytes | 2,186,360 (35 images) | 0 |
| DOM nodes | 1,235 | 510 |
| WebSocket frames / bytes to first stable view | 83 / 2,331,755 (largest frame 1.2 MB) | 46 / 37,187 |
| Time to hero visible | not recorded | 944 ms |
| Frames sent when switching light ↔ dark | – | 0 |
| External requests | – | 1 (icon font) |

Cause of the old lag: the large base64 images were re-sent on each rerun. The new landing page also caches the demo allocation (`st.cache_resource`) and uses a scoped `st.fragment` for the signal selector. These are one-machine, one-session numbers, not a benchmark.

## Final acceptance (design.md §K)

| Item | Result |
|---|---|
| Landing has no sidebar, one primary CTA above the fold, CTAs work | Pass (browser; `test_landing_*`) |
| Signal-flow figure uses real engine output, labelled synthetic, reduced motion | Pass: animation name `ss-flow` normally, `none` under `prefers-reduced-motion` (computed style) |
| Single navigation system; all seven routes load; deep links | Pass (browser, all seven at four widths) with the caveat that the Stages popover repeats the rail links on narrow screens |
| Theme switch changes the whole UI, keeps session, no rerun | Pass: background `rgb(18,22,27)` dark vs `rgb(238,240,243)` light; 0 frames on switch |
| Stale status within one interaction on every result page | Pass (journey tests; browser stale chain) |
| Upload failure keeps previous results; no traceback | Pass (`test_failed_ingest_keeps_previous_dataset`; browser corrupt-file screenshot) |
| No static rule text | Pass (R2) |
| Cabinet search highlights the right slot | Pass (browser with search and selected-row screenshots) |
| Revise exposes solver status honestly and offers Rev B workbook | Pass (`test_solver_summary_is_honest_about_exactness`, browser) |
| Deliverables lists real sheets and disables when stale | Pass (`test_deliverables_lists_real_sheets`, `deliverables_stale_1440_light.png`) |
| 1440 / 1280 / 768 / 375 × light/dark: no horizontal overflow, no clipped text | Inspected all 56 combinations visually; 768 dark re-verified numerically after the header fix (R10). Not tested: other widths, other browsers, high zoom. |
| `src/slotsmith/` unchanged | Pass: `git diff -- src/` and `git status --short src/` empty |
| Backend and audit tests unchanged and passing; new UI tests passing | Pass: 122 passed (31 backend/audit + 50 + 20 + 21) |

## Tests

`.venv/bin/python -m pytest -q tests/` → **122 passed** (about 36 s). Log: `artifacts/final_tests.log`. AppTest cannot drive a file uploader or `switch_page` across files, so uploads were verified in the browser and page journeys use `tests/_page_harness.py`.

## Not verified / manual checks recommended

- Screen reader (VoiceOver/NVDA) use; only markup and keyboard order were checked.
- Safari and Firefox; Chromium only.
- Real customer workbooks and the organiser's template (neither is available).
- Slot-level keyboard access to the cabinet map (not available, see R11).
- Long revisions on large inputs (the CP-SAT repair can take about a minute and the page blocks while it runs).
- Whether the `.streamlit/config.toml` security flags removed in R5 are needed in the user's own setup.
