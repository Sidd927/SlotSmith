# Visual QA report: final pitch deck (11 Oct 2026)

Deck: `deliverables/pitch_deck/SlotSmith_Final_Pitch_Deck.pptx` → `SlotSmith_Final_Pitch_Deck.pdf` (LibreOffice 26.x via `scripts/render_final_deck.sh`) → `rendered/slide-1..8.jpg` (144 dpi). The PDF and JPGs are produced from the same PPTX in one run, so all three are the same revision.

## 1. Method
1. Built the deck, converted to PDF, rasterised every page, and **opened each image** (not only the file). Three full passes (first draft, after red-team fixes, final).
2. Programmatic checks: python-pptx opens the file; 8 slides; 13.333 × 7.458 in (the organiser template's own aspect ratio 1.788, not 16:9); every slide has a template background picture; speaker notes present on all slides; `pdftotext` finds every key figure from the PPTX in the PDF ("429–575", "49,805", "122", "7 of 11", "81/81", "19,682", the GitHub URL, both placeholders); a wording lint over PDF text and notes finds none of: certified, guarantee, violation-free, globally, production, savings, faster, "100% allocated" (the only hit for "optimal" is the NOT CLAIMED sentence).
3. Screenshots: 1440-wide captures at a 1100 px effective layout and 2× pixel density from the running app (`streamlit run app/streamlit_app.py`, dark theme, synthetic demo dataset), cropped to the main content area; raw captures kept in `assets/screens/raw/`.

## 2. First-pass defects (found by inspecting the first render) and fixes
| # | Slide | Severity | Defect | Fix | Re-checked |
|---|---|---|---|---|---|
| D1 | 2, 3 | High | New text sat on top of the template's printed headings (Who is affected, The current gap, Why it matters now; What makes it different, Core mechanism, Why it's feasible in this timeframe) | Re-laid out around the baked headings: left column text under each heading, new visuals on the right | ✅ final renders |
| D2 | 4 | High | The template's five stack boxes (Frontend, Backend, Database, AI/APIs, Hosting/DevOps) were covered by my own stack panel | Removed the panel; stack text and logos now sit inside the template boxes; Hosting/DevOps text moved right of its wide label | ✅ |
| D3 | 6 | High | Roadmap bullets overflowed their cards, chart legend collided with the footnote, metric cards overflowed | Card heights, chart height and card text re-fitted; shorter bullets | ✅ |
| D4 | 5 | High | Screenshots taller than planned, caption overlapped the footnote | Re-sized; supporting crops 3.6 in wide | ✅ |
| D5 | 1 | Medium | New description line touched the template's bottom bar | Lines moved up 0.05 in; one line of 10.5 pt | ✅ |
| D6 | 1 | Low | A cropped cabinet-map thumbnail added to the cover was unreadable at that size | Removed; cover stays clean | ✅ |
| D7 | 8 | Medium | GitHub link rendered in default dark blue on a dark background | Link set on the shape, run keeps its cyan colour | ✅ |
| D8 | 6 | Medium | Revision-chart range labels overlapped the neighbouring bars | Values moved to a row under the axis labels | ✅ |
| D9 | 5 | Medium | The "all built" chip overlapped the last stage chip | Chip removed; label reads "WORKBENCH · 7 STAGES BUILT" | ✅ |
| D10 | 7 | Low | Benefit text and scale text ran one line over their cards; chart caption touched axis labels | Copy shortened; plot area raised | ✅ |
| D11 | 2 | Low | Rule-2 chip text wrapped to two lines; "+5 checks" box text had no margin | Shorter chip text; margin added | ✅ |
| D12 | 4 | Medium | "Allocation workbook" title/subtitle overflowed its node | Renamed "Workbook"; subtitle shortened | ✅ |

## 3. Red-team review (three perspectives, after the first complete redesign)
### A. First-time viewer
| # | Finding | Severity | Fix | Status |
|---|---|---|---|---|
| A1 | "FFD" used on slide 4 before it is defined | Medium | Slide 3 now says "first-fit-decreasing (FFD)" before slide 4 uses the abbreviation | fixed |
| A2 | Slides 1–2 explain the product and the physical hierarchy; the A/B interaction makes the constraint tangible | – | kept | ok |
| A3 | Slide 2 carries a lot of terminology (CIOC, CHARM, TQ) | Medium | TQ is defined on slide 2; CIOC/CHARM terms are the organiser's own vocabulary and are shown as a hierarchy diagram; no further simplification without losing the sourced claims | accepted |
| A4 | Slide 6's log-scale chart needs a moment to read | Low | axis ticks, legend and total in the title; per-case labels | accepted |
### B. Technical reviewer
| # | Finding | Severity | Fix | Status |
|---|---|---|---|---|
| B1 | "Matched an exact optimum in 150 larger groups" over-states: 2 of the 150 were FEASIBLE, not proven | High | "148 of 150 larger groups (2 unproven, none worse)" | fixed |
| B2 | Revision range 429–470 not reproducible (re-run: 575) | High | four-run range and per-case variance shown; baseline described as naive | fixed (`benchmark_audit.md` §4) |
| B3 | "Near-linear" implied from three sizes | Medium | removed; chart caption says "observed, not a complexity proof" | fixed |
| B4 | Allocation time vs wall time unclear | Low | caption: allocation alone ≈ 0.01 s, rest is Excel I/O, validation and verification | fixed |
| B5 | "Exact per-group minimum" could be read as a CP-SAT result | Medium | card says "closed form, sizes 2/6/12" | fixed |
| B6 | Zero violations could be read as universal correctness | Medium | slide 5 annotation: "for this dataset and these rules only"; slide 3 NOT CLAIMED | fixed |
| B7 | Verifier independence is a code-structure claim | Low | wording "imports only the rule set; re-reads the exported file" (checkable in `verifier.py`) | ok |
### C. Presentation reviewer
| # | Finding | Severity | Fix | Status |
|---|---|---|---|---|
| C1 | Roadmap cards had unused space below short lists | Low | card height reduced to fit; freed space went to the evidence chart | fixed |
| C2 | Supporting screenshots (results, revision) have small internal text at slide scale | Medium | cropped to banner + tiles, big numbers legible; key facts repeated as large annotation text; the dominant cabinet map is fully legible | **residual** |
| C3 | Minimum font sizes: body 10–12.5 pt, diagram sub-labels 9–9.5 pt, chart ticks 8.5 pt, footnotes 9–10 pt; the brief's targets (labels 14+, footnotes 14) cannot be met at this density on a 13.3 in slide | Medium | body text raised from the Round 1 deck's 9.5–11 pt to 10–12.5 pt; secondary details moved to speaker notes and `docs/pitch_deck/` | **residual** |
| C4 | Template's cyber theme, logos and headings preserved | – | backgrounds are the organiser's pages; headings are the template's | ok |
| C5 | Slide 3 left column leaves ~0.6 in empty at the bottom | Low | aligned with the template heading rhythm; no filler added | accepted |

## 4. Final acceptance checks on the last render
| Check | Result |
|---|---|
| Slide count 8, order unchanged | ✅ |
| No blank slides, no missing images | ✅ (each slide inspected) |
| No clipping or overlap in slides 1–8 | ✅ in the final 144 dpi renders of slides 1, 3, 4, 5, 6, 7, 8; slide 2 was inspected at 110 dpi in the pass that produced its final layout and has not changed since |
| Screenshots undistorted (aspect preserved by width-only scaling) | ✅ |
| Status labels consistent: Built (green solid), Planned (amber dashed), Idea (grey dashed), Synthetic (cyan) | ✅ |
| Arrow directions on slides 2–4 follow the data flow | ✅ |
| Only intended placeholders: `{{YOUTUBE_DEMO_URL}}`, `{{DOCUMENTATION_URL}}` | ✅ |
| No internal logs, credentials or unrelated desktop content in screenshots | ✅ (crops show the app only) |
| PDF and PPTX the same revision | ✅ same build run |
| Official-template compatibility claimed | no |

## 5. Not verified
- The PPTX was **not opened in PowerPoint or Keynote**; only LibreOffice rendering (Liberation Sans stands in for Arial and is metric-compatible, but line breaks can differ slightly). Submitting the PDF is the safer option.
- Contrast was judged visually against the template background, not measured.
- Screen-reader order of the PPTX shapes was not checked.
