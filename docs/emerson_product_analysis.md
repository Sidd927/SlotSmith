# Emerson ecosystem analysis: what exists, what the hackathon asks for, and where SlotSmith fits

Status: v1, 10 Oct 2026. Researched from public sources only. Source IDs (S-xx) refer to [source_register.md](source_register.md).

> **Ground rule for this document.** "Not found in public evidence" never means "Emerson cannot do this". DeltaV engineering is a large, partly proprietary toolset (DeltaV Books Online is behind a licence wall), and Emerson project-engineering teams may use internal tools that are not published.

---

## 1. Resolving the product name

The name "Delta Five Electronic Machine" does not match any Emerson product found in public sources. The closest match by sound and by subject is **DeltaV™ Electronic Marshalling** ("DeltaV" ≈ "Delta Five"; "Electronic Marshalling" ≈ "Electronic Machine"). The hackathon problem statement (S-01, pp. 4–6) uses exactly that vocabulary: DeltaV, CHARM, CIOC, baseplate, marshalling cabinet. The working assumption is therefore:

| Term heard | Resolved to | Confidence | Evidence |
|---|---|---|---|
| "Delta Five" | **DeltaV** distributed control system (DCS), Emerson | High | S-01 p.4 ("Before the DeltaV control system can use them…"); S-02 |
| "Electronic Machine" | **DeltaV Electronic Marshalling** (CHARMs + CIOC) | High | S-02 product page; S-03 data sheet |

The hackathon is about **engineering-time allocation of signals to Electronic Marshalling hardware**. It is not about the hardware itself.

## 2. Hardware architecture (documented, official)

All from the DeltaV Electronic Marshalling Product Data Sheet, August 2026 edition (S-03), unless noted.

| Element | What it is | Key documented facts |
|---|---|---|
| **CHARM** (CHARacterization Module) | Single-channel plug-in module that characterises one field signal | Many types, e.g. AI 4-20 mA HART, RTD, TC/mV, AO 4-20 mA HART, DI NAMUR, DI 24 V DC low-side (dry contact), DI isolated, DO 24 V DC high-side, DO 24 V DC isolated, DO 100 mA energy-limited, AC DI/DO (S-03 p.4). Self-keying: a terminal block's keying posts lock to the first CHARM type inserted (S-03 p.5). |
| **CHARM terminal block** | Removable field-wiring block under each CHARM | Six types: Standard, Fused-Injected-Power, 3-wire DI Fused-Injected-Power, Relay Output, Thermocouple/mV, 3-wire AI Fused-Injected-Power (S-03 p.4). Standard works with all CHARM types. Fused-injected-power is for isolated DO; Relay Output requires the DO 24 V DC high-side CHARM (S-03 pp.4–5). |
| **CHARM baseplate** | DIN-rail baseplate | **12 CHARMs + 12 terminal blocks per baseplate** (S-03 p.2–3). All system-powered channels on one baseplate share the same injected power source (S-03 p.4). |
| **CIOC / CIOC2** (CHARM I/O Card) | Redundant pair of I/O cards on a carrier | **Up to 8 baseplates below one carrier = 96 channels** (S-03 pp.1, 3, 10). Each CIOC can serve **4 controllers** (8 for PK controllers in v15.FP3+). Max **16 CIOCs per controller** (32 for PK in v15.FP3+); **300 CIOCs per system** (S-03 p.10). |
| **Controllers** | M-series, S-series, PK, etc. | CHARM I/O can be assigned to any of up to 4 (or 8) controllers per CIOC (S-03 pp.1, 33). |
| **Cabinet** | Marshalling cabinet / field enclosure | **No cabinet-level CIOC limit is stated in the data sheet.** The hackathon's "4 CIOCs per cabinet" is a project rule from S-01 p.5, not a documented hardware limit. |

**Engineering conventions documented by Emerson.**
- Multi-core home-run cables are "landed in order on a series of CHARM terminal blocks without concern for signal types" (S-03 p.1).
- "Signal core #1 is assigned to CHARM 1-1, core #2 to CHARM 1-2, and so on" (CHARMs Commissioning white paper, S-05 p.7). This is the basis of the problem statement's "keep each cable together, in pair order" rule.
- Baseplates have 12 channels "to align with the predominant use of 12, 24 and 36 core cables" (S-05 p.6).
- "Design looks at the process requirements and groups related signals together on a CIOC" (S-05 p.4). This is the basis of the problem statement's grouping rule.
- It is "recommended that AC voltage circuits be separated from low voltage signals" (S-03 p.5; S-05 p.7). The problem statement does not include this rule; it is a candidate user-defined rule.
- Spare channels "can be used for any signal type" (S-05 p.4).

## 3. What DeltaV software does (documented)

| Software capability | What it does | Source |
|---|---|---|
| **Auto-sense** | Inserting CHARMs and auto-sensing the node creates the I/O definition in the DeltaV configuration database. In v14, multiple HART devices on a CIOC can be auto-sensed at once. | S-03 p.2; S-06 p.5 |
| **Controller assignment** | "Assign all, one or any number of channels to a controller with a simple click or drag and drop." | S-03 p.2 |
| **Late binding** | Logical signal references (Device Signal Tags, DSTs) bind to physical channels later. This is automatic for HART devices. **"For other type of signals, the user could manually allocate the proper DST … using drag and drop functionality or bulk edit capabilities."** | S-06 p.5 |
| **User-defined CHARM templates** (v14) | Define all properties per CHARM type, "practically eliminating manual configuration of CHARMS". | S-06 p.5 |
| **I/O Studio + DeltaV Device Commissioner** (v14) | Device templates, commissioning policies, automated loop tests, punch lists. The tools also generate "as-built reports using device tag, CHARM location and typical wiring diagram". | S-07 |
| **Bulk Edit** (user-defined import/export) | Bulk create or update database objects (I/O cards, channels, control modules) from TAB-delimited Unicode text via format files (*.FMT), with an Excel template supplied with DeltaV. | S-04 pp.3–5 |
| **Tag-based binding patent** | Fisher-Rosemount (an Emerson company) patent: sense the I/O, read device tags, match them to configured tags and bind automatically; wiring mismatches are flagged. | S-12 |

**Related third-party / partner ecosystem**
- **Hexagon (Intergraph) Smart Instrumentation (SPI, formerly INtools; now "Octave Facets Instrumentation")** has a jointly developed, bi-directional DeltaV interface and models the CHARM hierarchy (panel → rack → slot → strip → CHARM → channel). Fluor reports using it on a project with more than 50,000 I/O (S-09, S-10).
  - In the Hexagon tutorial, I/O assignment is an interactive step: drag a tag onto a channel (S-11).
  - "Auto-wiring" automates batch *wiring connections* between strips, not rule-based signal placement (S-11).
- **I/O-list generation tools** (e.g. Pathnovo, Tagsight) build I/O lists from P&IDs (S-13). Pathnovo also claims cabinet allocation. These are vendor marketing claims and have not been verified.

## 4. Capability comparison matrix

Gap-status legend:
- **Documented**: an official source states it explicitly.
- **Partially documented**: related functionality exists, but the exact requirement is not shown.
- **Not found in public evidence**: no supporting documentation was found.
- **Confirmed limitation**: a credible source states it.
- **Unknown**: the evidence is insufficient.

| # | Capability | What the hackathon requires (S-01) | What Emerson publicly documents | Evidence | Gap status | Confidence |
|---|---|---|---|---|---|---|
| 1 | I/O channel & CHARM configuration | Right CHARM per signal type | CHARM types, auto-sense, v14 CHARM templates | S-03, S-06 | **Documented** (configuration after hardware exists) | High |
| 2 | Controller assignment | Controller naming; implied hierarchy | Click/drag-drop/Bulk Edit assignment; 4 (8) controllers per CIOC | S-03, S-04 | **Documented** (manual or bulk); rule-based automatic assignment **not found** | Medium |
| 3 | Cable & pair representation | Cable, pair, 24/12/6/2-pair cables | Cores landed in order (core #1 → CHARM 1-1) as a design convention | S-05 | **Partially documented** (convention, not a tool feature) | Medium |
| 4 | Cable-block placement & pair order | All pairs of a cable side by side, in pair order | Recommended practice only | S-03 p.1, S-05 p.7 | **Not found in public evidence** as an automated function | Medium |
| 5 | Cabinet/CIOC/baseplate capacity planning | 12/8/4, cabinets needed, fill % | Hardware limits documented; standard CTO enclosures sized by I/O count | S-03, S-06 p.5 | **Partially documented** (limits, not an allocation planner) | Medium |
| 6 | Logical I/O grouping | Same-group signals in the same cabinets, in sequence | "Groups related signals together on a CIOC" stated as a design practice | S-05 p.4 | **Partially documented** (practice, not an automated rule) | Medium |
| 7 | A/B segregation | A and B never share a CIOC | Redundancy is documented for CIOC hardware, not for duty/standby signal placement | S-03 | **Not found in public evidence** | Medium |
| 8 | Hardware/terminal-block compatibility | Right CHARM + TB per signal | TB types and compatibility; keying prevents wrong CHARMs | S-03 pp.4–5 | **Documented** (as a hardware rule); automated *selection* from an MDB **not found** | High (rules) / Medium (selection) |
| 9 | Spare pairs & cabinet spare capacity | Wired spare pairs; ~x% empty baseplates per cabinet | Spares usable for any type | S-05 p.4 | **Partially documented** | Medium |
| 10 | Project-specific, user-defined allocation rules | Rule panel, nothing hard-coded | Templates exist for CHARMs, devices and commissioning policies; no allocation-rule engine found | S-06, S-07 | **Not found in public evidence** | Medium |
| 11 | Importing & mapping customer IO MDBs | Upload one or many Excel files; auto-map columns | Bulk Edit imports TAB-delimited data in a DeltaV-defined format (FMT) | S-04 | **Partially documented** (import of DeltaV-format data, not arbitrary customer MDBs) | Medium |
| 12 | Automatic allocation into the organiser template | Filled Excel IO allocation template | — | S-01 says it is "done by hand in Excel" today | **Not found in public evidence** | Medium-high (the sponsor states the need) |
| 13 | Detection of conflicting/missing source data | TQs for every unresolved issue | SPI flags duplicate channel assignments / type mismatches (third-party guide); Device Commissioner raises punch lists at commissioning time | S-07, S-11 | **Partially documented** (validation at other stages) | Low-medium |
| 14 | Traceable technical queries | TQ list citing data and rules | — | — | **Not found in public evidence** | Medium |
| 15 | Rev A vs Rev B impact analysis | Added/deleted/moved, cabinets hit | Hardware tolerates late changes ("without lifting a wire") | S-03, S-05 | **Partially documented** (hardware flexibility, not a document-level diff) | Medium |
| 16 | Minimising unnecessary moves | Unchanged signals stay put | — | — | **Not found in public evidence** | Medium |
| 17 | Independent verification & audit | Rule-check report: zero violations | Commissioning reports, as-built reports | S-07 | **Partially documented** (commissioning-stage, not allocation-rule verification) | Medium |
| 18 | Operation on unseen customer MDBs | Hidden test: unseen MDB + revision | — | — | **Unknown** | Low |
| 19 | 10,000+ signal allocations | 10,000+ signals | Systems up to 300 CIOCs (≈28,800 channels) | S-03 p.10 | **Documented** for hardware scale; **unknown** for allocation tooling | Medium |
| 20 | New project rules without code change | Required | Bulk Edit format files are user-defined (for data fields) | S-04 | **Partially documented** (data formats, not placement rules) | Medium |

## 5. Candidate workflow gaps (treated as hypotheses)

| # | Gap | Who experiences it | Evidence | Status | Does the PS establish the need? | How SlotSmith might address it | Might Emerson already solve it? | What would confirm it |
|---|---|---|---|---|---|---|---|---|
| G1 | Rule-based slot allocation from a customer MDB is manual (Excel) | Emerson / integrator IO engineers | S-01 p.4: "Today this is done by hand in Excel for 10,000+ signals". S-06 p.5: non-HART DST allocation is manual drag-drop or bulk edit. | **Explicitly stated by the sponsor** | **Yes** | Rule-driven allocator + Excel export | Possibly via internal macros or tools (unknown) | Ask Emerson mentors what is used today |
| G2 | Revisions require reworking the allocation and tracing impact | Same | S-01 p.4: "every customer revision means reworking it and tracing the impact again" | **Explicitly stated by the sponsor** | **Yes** | Minimum-move revision engine + impact report | Hardware makes physical changes easy (S-03); document-level diff not found | Sample Rev A/B data |
| G3 | Project-specific packing rules are hard to enforce consistently | Same | S-01 p.5 (rulebook "nothing is hard-coded") | **Reasonably inferred** from the PS | Partly | Typed rule sets + independent verifier | Unknown | Interviews; rule sets from past projects |
| G4 | Hard to trace why a signal was placed or moved | Engineers, reviewers, customers | No public tool found that records placement rationale | **Unverified** | Indirectly (TQ list, impact report) | Per-placement provenance; TQs citing rule IDs and MDB rows | Unknown | Review of the current deliverable format |
| G5 | Data-quality conflicts need engineering clarification (TQs) | Engineers ↔ customer | S-01 p.4: "raise TQs where the data conflicts" | **Explicitly stated by the sponsor** | **Yes** | Validation layer producing TQs | Partly (SPI validation, punch lists at other stages) | Examples of real TQs |
| G6 | Allocation output is not independently verifiable | QA reviewers | S-01 p.6 Definition of Done: "Zero violations of the rules the user set" | **Reasonably inferred** | **Yes** (needs a rule-check report) | Verifier that shares no code with the allocator | Unknown | — |
| G7 | Each customer's MDB schema differs | Engineers | S-01 p.6: "Auto-map columns"; hidden test uses an unseen MDB | **Explicitly stated by the sponsor** | **Yes** | Column auto-mapping (synonyms + optional LLM suggestion + user confirmation) | Bulk Edit expects the DeltaV FMT layout (S-04) | Sample MDBs |
| G8 | Interoperability: customer spreadsheets vs DeltaV/SPI | Engineers | Bulk Edit = TAB-delimited FMT; SPI–DeltaV interface exists | **Reasonably inferred** | Partly | Planned: export to Bulk-Edit-style tables (unvalidated) | Yes, partly (SPI interface) | Real FMT files and an SPI project |

## 6. Positioning recommendation

**Recommended relationship: complementary.** SlotSmith is a **pre-configuration engineering assistant**. It sits between the customer IO MDB and the existing DeltaV toolchain (DeltaV Explorer / Bulk Edit / SPI). It produces a rule-checked, revision-stable **I/O allocation document** (cabinet → CIOC → baseplate → CHARM slot, CHARM type, terminal block and names). Today that document is built by hand.

- **What SlotSmith does:** ingest and map customer MDBs; validate data and raise TQs; apply user-defined allocation rules; allocate whole cable blocks; independently verify every rule; export the organiser's Excel template; diff Rev A against Rev B with the fewest moves.
- **What SlotSmith does not do:**
  - It does not configure DeltaV, replace DeltaV Explorer, Bulk Edit, Smart Commissioning or SPI.
  - It does not change hardware or controller architecture.
  - It does not commission devices.
  - It makes no safety claims.
- **Strongest evidence-backed differentiator:**
  - The sponsor states that the allocation and its revision rework are manual (S-01).
  - Emerson's documented tools automate what happens *after* hardware exists (auto-sense, late binding, templates, commissioning) and bulk data entry (Bulk Edit).
  - No public evidence was found of a tool that decides slot placement from project rules with an independent proof of zero violations and minimum-move revisions.
- **Main uncertainty:** Emerson project teams may already use internal macros or tools for this step. We cannot see them.
- **Claims to avoid in the presentation:**
  - "Emerson has no tool for this."
  - "Replaces DeltaV" or "replaces Electronic Marshalling".
  - "Improves plant safety".
  - "Saves N hours" (we have no measurement).
  - "Works on the hidden dataset" (untested).

## 7. Open questions for the Emerson mentors

1. What tool or format produces the allocation today: Excel macros, SPI, an internal tool?
2. Can a ≤12-pair cable straddle two baseplates? Must a 24-pair cable start at slot 1?
3. Is spare capacity counted as empty baseplates per cabinet, per CIOC, or as a percentage of channels? How is it rounded?
4. Must A/B segregation also apply at cabinet level for some projects (e.g. risk areas)?
5. Is a CIOC dedicated to one controller, and what is the CIOC → controller assignment rule?
6. What is the exact output template (sheet names, columns, naming of CHARM slots)?
7. On a revision, which changes count as a "move": a slot change only, or also a CHARM or terminal-block swap in the same slot?
