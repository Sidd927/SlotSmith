# Presentation QA: SlotSmith_Round1 (v3, content lock, 10 Oct 2026 13:15 IST)

| File | Size | SHA-256 |
|---|---|---|
| `SlotSmith_Round1.pptx` (editable) | 1,816,838 B | `3368d6b618b1f79425937f11a31201e5eee5a5d6b46b7e3e8428566433af607a` |
| `SlotSmith_Round1.pdf` (recommended upload) | 2,778,833 B | `cdabfc67daf31b09c5f1e38a58a016f6a256d1cd33990950bc1d19a67372f2a8` |

Both are well under the 50 MB limit. Renders at 110 dpi are in `renders/slide-1.jpg … slide-8.jpg`.
- Build: `.venv/bin/python scripts/build_deck.py`, then the LibreOffice PDF export.
- Approved wording: [docs/presentation_content_lock.md](../../docs/presentation_content_lock.md).
- Claim-to-evidence table: [docs/audit/final_audit.md](../../docs/audit/final_audit.md) §2, plus the §8 addendum.

## Template compliance
All 8 template pages are used as backgrounds in the official order. Headings and branding are unchanged (rendered from the official PDF). Slide 1 fields are filled: Mac_Enthu · Aayush Aade · Track 1 (Emerson) · PS 1.2 Project IO SIGNAL SUDOKU. Slide 8 adds only a team line.

## Checks (v3)
| Check | Result |
|---|---|
| `validate.py` (pptx skill) | PASSED |
| Placeholder / forbidden-phrase scan (`lorem`, `TODO`, `[insert`, `pending`, `minimum-move`, `fewest moves`, `bottleneck`, `Proven, not claimed`, `look-alike`, `(LB)`, `guarantee`, `Faster`) | none in slide text |
| Numbers vs artifacts (scripted: every slide 3/6/7 figure compared with `benchmarks.json`, `repro/*.json`, `audit/*.json`, and present in both PPTX and PDF text) | all match |
| Clipping / overlap (visual, all 8 slides at 110 dpi) | One overlap fixed (slide 3 bullets vs "Core mechanism" heading); final render clean |
| Legibility | Body 10–12.5 pt; captions/tiles 8.5–9.5 pt (dense but legible at 100% PDF zoom). The slide 5 screenshots are small; legible when zoomed |
| Fonts | Arial / Courier New, embedded in the PDF as Liberation Sans/Mono (metric-compatible) |
| Synthetic disclosure visible | Slides 3, 5, 6, 7 |
| Screenshot ↔ figures ↔ notes consistency | The slide 5 UI screenshots were re-captured from the post-audit build: "Baseplates used 199", no "(LB)" label. Revision screenshot values (46/111/58/28/1,849/0) reproduced the pre-audit capture exactly. Slide 6 figures and slide 6 speaker notes read the same artifacts |

## v3 content changes (requested content lock)
1. Slide 1 subtitle: "minimum-move revisions" → "independently checked, revision-aware DeltaV I/O allocation".
2. Slide 2: "allocation paperwork is now the bottleneck" → "allocation planning and revision tracking remain a manual workflow burden (per the PS)".
3. Slide 3:
   - "Proven, not claimed" → "Independently checked".
   - FFD statement split into **Proved** (one A/B side, sizes 2/6/12) and **Tested, not proved** (exact CP-SAT comparison).
   - "Look-alike approaches fail" panel → "Design principles".
   - "Configurable: existing rule parameters … new rule types may need code".
   - "Placement is not probabilistic" → "No AI in placement".
4. Slide 4: simplified to straight-line flow (no diagonal arrow; Rev A store folded into the Revision engine). Same components and the same built/planned status.
5. Slide 5: UI screenshots refreshed from the post-audit build; "(LB)" removed; dataset labelled SYNTHETIC; "fewest moves" removed from the Revise card.
6. Slide 6: audited figures preserved (429–470 vs 49,805; 7/11 proven exact; synthetic qualifiers). "min-move" → "window repair"; roadmap item reworded to "Cut CP-SAT repair time and run-to-run variance".
7. Slide 7: "300" → "≤ 300 … (spec maximum) → at most 28,800"; "restarts the rework" → "means rework" (PS wording).
8. Slide 8: unchanged.

Also changed: UI labels in `app/streamlit_app.py` ("Baseplates used"; "Compare + re-allocate (keep unchanged in place)"; caption "revision-aware"). This is a wording change only, with no behaviour change.

## Remaining risks before upload
See `docs/presentation_content_lock.md` §4. These are the deadline conflict, no official data or template, open rule interpretations, non-deterministic revision counts, and the LibreOffice vs PowerPoint text wrap. **Upload the PDF.**
