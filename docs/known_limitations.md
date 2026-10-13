# Known limitations and unverified assumptions

## Missing inputs
- **The sample IO MDB and IO allocation template are not public.** The PS says they are "provided … hackathon use only". The Unstop attachments contain only PS PDFs, the handbook and the PPT template (checked 10 Oct 2026 via the Unstop API). The exporter layout is our own reading of the PS and is easy to re-map (`export.COLUMNS`).
- **The official PPT template is PDF-only.** The deck uses rendered template pages as slide backgrounds. Headings and branding are pixel-exact but are not editable text.

## Rule interpretations (parameters, pending mentor confirmation)
See [rule_register.md](rule_register.md):
- K-3 cable straddling;
- K-2 24-pair cables within one CIOC;
- G-1/G-2 group spill and isolation granularity;
- P-1 spare rounding and basis;
- C-2 CIOC→controller mapping;
- N-6 CHARM slot naming;
- area/unit source;
- R-2 whether an in-slot CHARM swap counts as a move.

## Engineering limits of the prototype
- **Rules are parameters, not open-ended rule types.** Users can toggle and parameterise the built-in rule families in the UI, and edit the CHARM/TB table and naming patterns by loading a modified rule set JSON file (the UI shows the hardware table and most naming patterns read-only); none of this needs code changes. A genuinely *new kind* of rule (e.g. "AC and LV signals on separate baseplates") still requires code. The PS asks that users can "add as many rules as needed", so this is a gap.
- `allow_cable_straddle=true` is accepted but not used by the allocator (it never straddles). `multi_baseplate_cables_same_cioc` has no effect (always the same CIOC).
- CP-SAT repair is **window-local**: the window is the group's cabinets plus neighbours, and existing cables may move at most one cabinet. Windows that stop at the 10 s limit with status FEASIBLE are accepted, so "fewest moves" is not always proven, even within the window.
- CP-SAT repair uses 8 workers and a wall-clock limit, so revision move counts can vary between runs and machines (see artifacts/repro).
- Fixed in the audit (10 Oct): a cable too large for an empty cabinet used to mark its whole group unplaced, leaving rows both allocated and not allocated. The verifier's Q-1 check missed this. Both are fixed, with regression tests.
- Cable sizes outside {2, 6, 12, 24} are packed by FFD but **without the optimality proof**. Cables over 96 pairs raise a capacity TQ.
- The cabinet-count lower bound is weak (it ignores group/CIOC isolation). Reported gaps are against baseplate bounds.
- CP-SAT repair can take up to ~55 s on 10k-signal revisions. The domains and windows can be tightened.
- "Relay output (rule-based)" has no defined trigger in the PS. It is supported only via an explicit IO type (`DO-RELAY`).
- Thermocouple terminal blocks (TC/mV TB per Emerson PDS) are not special-cased; the PS table says Standard.
- The UI is a Streamlit prototype (rule toggles/parameters, cabinet map, TQs, revision diff, Rev B export). Uploads accept `.xlsx` and `.csv` only (no `.xls`); a browser refresh starts a new session and loses the work (download deliverables first); no manual column-mapping override. See `docs/feature_capability_matrix.md` and `docs/ux_review_log.md`. The AI helpers are not built; no LLM is used at runtime.
- No time-savings study. No comparison with Emerson's internal tools (not publicly available).

## Claims we deliberately do not make
- That Emerson lacks such a tool, or that SlotSmith is better than Emerson's tools.
- That SlotSmith replaces DeltaV, Electronic Marshalling, SPI or Bulk Edit.
- Safety improvements.
- Hidden-test success.

- **Rule switches.** `RuleSet.toggles` R3-capacity, R4-cable and R7-naming are not read by the engine, and the allocator always applies the R5 spare reservation, so the UI offers switches only for R1 and R2 (see `scripts/probe_rule_switches.py`). R5 and R6 can still be disabled through a loaded rule-set file; that only changes which checks the independent verifier runs.
- **R6-hardware semantics (fail-closed interpretation, 13 Oct 2026).** *Documented:* an I/O type with no CHARM/terminal-block mapping raises the blocking `H-*` query (dossier, rule register section 6). *Not documented:* what switching R6 off means. *Chosen by the project owner, not organiser-approved:* the `H-*` query and the held row are unconditional, so disabling R6 never turns unknown hardware into a normal allocation; R6 off only makes the verifier report `H-1..6` as SKIPPED. This closes the earlier crash in `export.build_rows` (R6 off + unmapped type); that function now raises if an unmapped signal ever reaches it. *Open question for the organiser:* whether a different treatment of unknown hardware is wanted.
- **Verification states and exit codes.** A family switched off is reported `SKIPPED` (never PASS) and the run is an "incomplete" verification. CLI exit codes: 0 all families ran and passed, 2 violations (precedence), 3 incomplete.
- **Mixed A/B (or mixed IO-group) cables with the controlling rule off (13 Oct 2026).** *Documented:* with R2 on such a cable is blocked by an S-2 query (G-3 for groups); M-1 requires exported rows to match the MDB. *Not documented:* what to do when the rule is off. *Implemented, without a new engineering rule:* the cable has no single side/group, is placed as an unsided/ungrouped cable (deterministic; the old code took the first item of a set, which varied with `PYTHONHASHSEED`), each signal keeps its own side/group in the export, a warning query (S-2 / G-3) records that separation is not enforced for it, and S-1/G-1 are SKIPPED. M-1 is unchanged and still fails on any genuinely rewritten value. *Open:* the requirement owner may prefer to keep S-2/G-3 blocking regardless of the switch (as was done for `H-*`); the current choice favours not holding the cable while disclosing it.
