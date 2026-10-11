# Final change log: pitch deck transformation (11 Oct 2026)

Nothing was committed, pushed, merged or deleted. The Round 1 deck (`deliverables/round1/`), its generator (`scripts/build_deck.py`) and `docs/presentation_content_lock.md` are untouched. `src/slotsmith/` is unchanged (checked with `git status`).

## New files
| Path | Purpose |
|---|---|
| `deliverables/pitch_deck/SlotSmith_Final_Pitch_Deck.pptx` | editable final deck (8 slides, template backgrounds, native shapes/text/charts-as-shapes, speaker notes with sources) |
| `deliverables/pitch_deck/SlotSmith_Final_Pitch_Deck.pdf` | PDF of the same build |
| `deliverables/pitch_deck/rendered/slide-{1..8}.jpg` | 144 dpi renders used for inspection |
| `deliverables/pitch_deck/assets/screens/` | `ui_cabinets.png`, `ui_results.png`, `ui_revise.png` (crops) and `raw/` full captures |
| `deliverables/pitch_deck/assets/logos/` | five CC0 Simple Icons SVGs and their light PNG renders |
| `scripts/build_final_deck.py`, `scripts/render_final_deck.sh` | reproducible build and render |
| `docs/pitch_deck/{fact_audit,benchmark_audit,research_notes,claim_slide_matrix,visual_qa_report,final_change_log}.md` | evidence and review record |
| `artifacts/pitch_deck_repro/` | 11 Oct re-run outputs: benchmark JSON/log, pytest log, exhaustive-audit JSON/logs |

Edit points: the three links are constants at the top of `scripts/build_final_deck.py` (`GITHUB_URL`, `YOUTUBE_URL`, `DOCS_URL`) and the matching text boxes on slide 8 of the PPTX.

## Slide-by-slide
1. **Cover**: template unchanged; the SlotSmith line gains one plain-language sentence and "Prototype, synthetic data".
2. **Problem**: text kept under the template headings, tightened. New: concrete A/B interaction diagram (two 6-pair cables); hierarchy chips; "six rules → 11 independent checks" mapping (6 PS rules ↔ G-1, S-1, C-1, K-1, P-1, H-1..6, plus 5 data/output families).
3. **Solution**: left text under the template headings (baseline FFD with no solver, verifier, CP-SAT role). New: five-step workflow with the verifier in amber; PROVED / TESTED / NOT CLAIMED cards (tested claim now precise: 19,682 cases and 148 of 150 groups).
4. **Architecture**: rebuilt in the template's five stack boxes plus a three-lane diagram (rule set bar; ingest → validate → allocate → export → workbook; Rev B → revision engine → export; verify re-reading the file; surfaces/tests/storage; planned items dashed). Logos for Python, pandas, pydantic, Streamlit, pytest. Removed SQLite and the React-later implication.
5. **Product proof**: tiny old-UI screenshots and hand-drawn map replaced by three real crops of the current build (dominant: cabinet inspector), seven-stage strip, large annotations, synthetic disclosure.
6. **Roadmap and evidence**: timeline with built / planned / idea states and handbook dates; per-case revision chart on a log scale; four metric cards; qualifiers on baseline and dates.
7. **Impact**: measured runtime chart (36 runs), expected benefits (not measured), sourced scale context, where it fits (complements DeltaV), limits with the next validation dependency.
8. **Closing**: one-sentence value statement, team, links panel (verified GitHub URL, two placeholders).

## Technical corrections made after inspecting the repository
- Revision moves "429–470" → **429–575 over four runs**, with per-case variance; "10 cases vs 11 windows" explained (10 revisions, 7 used CP-SAT, 11 accepted windows, 7 proven exact).
- Test count 31 → **122** (31 engine + 91 UI), re-run on 11 Oct.
- "5.99 s" → "about 6 s" (batch medians 6.0, 6.0, 6.3 s; one 8.7 s outlier).
- "12/12 benchmark runs" folded into the "exact per-group minimum" card; the 150-group audit stated exactly (148 proven, 2 unproven).
- SQLite "planned" removed (not in code or docs); React reduced to speaker-note mention.
- "Near-linear" removed. Old UI screenshots replaced. "Built today · 10 Oct" → "as of 11 Oct". "Round 2 by 16 Oct" → "15–18 Oct (handbook)".

## Findings that need the team's action
1. **The GitHub repository is private** (`gh repo view`: PRIVATE; unauthenticated request: HTTP 404). Judges cannot open the link. Make it public or share it before submission.
2. YouTube and documentation links are placeholders.
3. Organiser sample MDB/template availability was last checked 10 Oct; re-check before submitting.
4. Open the PPTX in PowerPoint once, or submit the PDF.
