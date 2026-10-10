# Development environment

Host: macOS (Darwin 27), Apple M5 laptop. Claude Code 2.1.251 (desktop).

## Project-local setup (reproducible)

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev,ui]"     # or: .venv/bin/pip install -r requirements.lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/benchmark.py     # writes artifacts/benchmarks.json (≈7 min)
.venv/bin/python scripts/build_deck.py    # writes deliverables/round1/SlotSmith_Round1.pptx
```

Key packages (exact versions in `requirements.lock.txt`): ortools 9.15, openpyxl 3.1.5, pandas 3.0, pydantic 2.14, hypothesis 6.168, streamlit 1.65, python-pptx, pymupdf, markitdown.

## System tools installed this session (Homebrew, official formulae/casks)

| Tool | Version | Why | Risk notes |
|---|---|---|---|
| poppler (`pdftoppm`) | 26.10 | Render PDF pages for slide QA | Official Homebrew formula |
| LibreOffice (cask) | 26.8.1 | PPTX → PDF conversion and visual QA | Official cask; large (~1 GB); no network services enabled |

## Claude Code skills / extensions audit

| Item | Status | Used? | Notes |
|---|---|---|---|
| `anthropic-skills:pptx` | Pre-installed (Anthropic) | **Yes** | Validation (`validate.py`), the soffice wrapper, QA checklist |
| `anthropic-skills:xlsx`, `pdf`, `docx` | Pre-installed | Not needed so far | openpyxl/pymupdf used directly |
| `anthropic-skills:deep-research` | Pre-installed | Not used | It spawns sub-agents; research was done inline with verified sources instead |
| User skills in `~/.claude/skills` (hyperframes/video family, frontend-design, skill-creator) | Pre-existing | No | Not relevant to Round 1 |
| Plugins: stitch-build / stitch-design / stitch-utilities (Google Labs) | Pre-existing | No | UI-design tooling; may help the Round 2 UI mock-ups |
| GitHub MCP plugin | **Failed to connect** (auth header error) | No | Fix needed only if we publish; repo stays local/private |
| Playwright MCP | Connected | Not yet | Candidate for UI screenshots in Round 2 |

**New third-party skills installed: none.** We found nothing that materially improves this project beyond the built-in pptx skill and standard Python packages. Installing more would add risk without benefit.

## Data handling

- Organiser files are in `reference/official/` (git-ignored; the PS says "hackathon use only, do not share").
- The team registration form is in `reference/team/` (git-ignored; contains personal data).
- Synthetic data is generated on demand into `artifacts/` and `data/synthetic/`. It is labelled synthetic.
- Nothing has been pushed or published. No API keys are used.
