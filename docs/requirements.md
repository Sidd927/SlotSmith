# Requirements (from PS #02, Track 1 Emerson, and the Code Apex rules)

## Functional (PS p.6, "The tool you build")
| ID | Requirement | Status |
|---|---|---|
| F1 | Upload one or many customer IO MDB Excel files | Built (CLI, multi-file, multi-sheet, header detection) |
| F2 | Use the organiser IO allocation template as the output format | Partially built: our layout; real template not yet released |
| F3 | Auto-map columns: tag, IO type, cable, pair, group, segregation | Built (deterministic); LLM suggestion planned |
| F4 | User-settable rule panel, nothing hard-coded; add/edit/switch rules; save/reuse rule sets per project | Rules as JSON built; panel UI planned |
| F5 | One click: every signal → cabinet, CIOC, baseplate, CHARM | Built |
| F6 | Raise a TQ for anything it can't place | Built |
| F7 | Report cabinets and CIOCs needed, fill %, spares | Built (Cabinet Summary sheet) |
| F8 | Rule-check report: zero violations | Built (independent verifier) |
| F9 | TQ list: missing data, rule conflicts, capacity issues | Built |
| F10 | Load Rev B, compare with Rev A, keep unchanged signals in place, fewest moves | Built |
| F11 | Impact report: added, deleted, moved, cabinets hit | Built |
| F12 | Working tool with a simple UI (Python preferred; web or desktop) | Planned (Streamlit) |
| F13 | Live demo on sample data + source code + 5-min pitch | Finale |

## Non-functional
- No hand-editing: end-to-end generation (built).
- Generalise to an unseen MDB and revision (hidden test); robustness work is ongoing.
- Declare all tools, libraries and AI models used (docs/technology_decisions.md).
- Sample data for hackathon use only; do not share (.gitignore).
- Handbook: originality, IP, and explainability of AI-assisted components.

## Round 1 submission (Unstop, verified 10 Oct 2026 ~11:10 IST)
- One file, PDF or PPTX, ≤ 50 MB; multiple submissions allowed; **the provided PPT template is mandatory**.
- Upload window per round config: **11 Oct 21:00 → 12 Oct 10:00 IST**. The "important dates" list says **10 Oct 23:59 IST** → treat 10 Oct 23:59 IST as the internal deadline and upload when the window opens.
- Evaluation: conceptual clarity, innovation potential, structured problem-solving approach, technical feasibility.
