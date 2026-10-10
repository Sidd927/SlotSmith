# Source register

Every material claim in the deck and the docs traces to one of these sources. "Accessed" means the file or page was actually retrieved in this session (10 Oct 2026, IST). Local copies are kept in `reference/`. Organiser files live in `reference/official/`, which is git-ignored and must not be redistributed.

## A. Official hackathon sources

| ID | Source | Publisher | Date | Locator | Accessed how | Used for |
|---|---|---|---|---|---|---|
| S-01 | Track 1 Problem Statements (Emerson): #01 UNTANGLE, **#02 IO SIGNAL SUDOKU (pp. 4–6)**, #03 EAGLE EYE | Emerson / AISF | 2026 | Unstop attachment `Track_1_PS_description.pdf`, 1,668,412 B (`d8it4huxumps7.cloudfront.net/uploads/attachements/files/50b1e524-….pdf`) | Local file, byte size matches the Unstop attachment record | All requirements and rules |
| S-01a | Apex 3.0 PPT Template (8 pages, PDF only, Canva) | AISF | 12 Sep 2026 (PDF metadata) | Unstop attachment `eb07ff99-….pdf`, 5,890,521 B | Local file, size matches the Unstop record | Mandatory slide structure |
| S-01b | HANDBOOK CODEAPEX 3.0 | AISF VIT Pune | 2026 | Unstop attachment `8d3fe06f-….pdf` | Local file | Timeline, AI-tool policy, originality |
| S-01c | Unstop event record "VIT CODE APEX 3.0" (id 1751374): rounds, dates, file rules | Unstop / AISF | record updated 9 Oct 2026 20:26 IST | `unstop.com/api/public/competition/1751374` | Public JSON fetched 10 Oct 2026 ~11:10 IST | Deadline, format (PDF/PPTX ≤ 50 MB), evaluation criteria |
| S-01d | Team registration form (draft, PDF print) | AISF Google Form | 10 Oct 2026 | Local `reference/team/registration_form_draft.pdf` | Local file | Team name, leader, PS number 1.2 |

## B. Emerson official documentation

| ID | Title | Date | URL | Accessed | Key facts used |
|---|---|---|---|---|---|
| S-02 | DeltaV Electronic Marshalling (product page) | live page | https://www.emerson.com/en/automation-systems/distributed-control-systems-dcs/deltav-distributed-control-system/deltav-controllers-io/deltav-electronic-marshalling | WebFetch | Product overview; links to data sheets |
| S-03 | DeltaV Electronic Marshalling Product Data Sheet | Aug 2026 | https://www.emerson.com/is/content/emerson/en/systems-and-software/deltav-distributed-control-system-dcs/product-data-sheets/documents/deltav-electronic-marshalling.pdf | Downloaded, 39 pp., text extracted | 12 CHARMs/baseplate; 8 baseplates/CIOC = 96 channels; 4 controllers per CIOC (8 for PK, v15.FP3+); 16 CIOCs/controller (32 PK); 300 CIOCs/system; 6 terminal-block types; cables landed in order; AC/LV separation recommended; shared injected power per baseplate |
| S-03b | DeltaV IS Electronic Marshalling Product Data Sheet | Feb 2026 | …/deltav-is-electronic-marshalling.pdf (same folder as S-03) | Downloaded | IS CHARMs (context only) |
| S-04 | DeltaV Bulk Edit (white paper) | Sep 2022 | https://www.emerson.com/documents/automation/white-paper-deltav-bulk-edit-deltav-en-57262.pdf | Downloaded, 8 pp. | User-defined import/export, TAB-delimited Unicode, *.FMT format files, Excel template |
| S-05 | DeltaV CHARMs Commissioning (white paper) | Oct 2016 | Emerson doc en-56728; copy retrieved from https://globalgbc.org/wp-content/uploads/2022/08/01067_white-paper-deltav-charm-commissioning-en-56728.pdf | Downloaded, 23 pp. | "core #1 → CHARM 1-1" (p.7); "groups related signals together on a CIOC" (p.4); 12-channel baseplates for 12/24/36-core cables (p.6); spares usable for any type (p.4) |
| S-06 | Smart Commissioning (white paper, DeltaV v14) | Oct 2021 | https://www.emerson.com/documents/automation/white-paper-smart-commissioning-for-deltav-v14-en-57870.pdf | Downloaded, 22 pp. | Late binding; non-HART DSTs allocated manually by drag-and-drop or bulk edit (p.5); CHARM templates |
| S-07 | DeltaV v14 Smart Commissioning Enhancements (flyer) | 2018 | https://www.emerson.com/documents/automation/brochure-smart-commissioning-flyer-deltav-en-4851796.pdf | Downloaded | I/O Studio, Device Commissioner, as-built reports |
| S-08 | DeltaV Electronic Marshalling with Distributed CHARMs PDS | Aug 2024 | https://www.emerson.com/documents/automation/product-data-sheet-deltav-electronic-marshalling-distributed-charms-deltav-en-4762954.pdf | Downloaded | 96 CHARMs / 8 baseplates per CIOC still applies |

## C. Third-party engineering sources

| ID | Title | Author / publisher | Date | URL | Type | Used for |
|---|---|---|---|---|---|---|
| S-09 | Wiring CHARM I/O in SmartPlant Instrumentation | E. Nwagbara, Fluor (SPI LTUF) | 2018 | http://spi-ltuf.org/20180213/CHARM%20IO%20in%20SPI.pdf | User-group presentation | SPI–DeltaV interface; >50,000 I/O project; CHARM hierarchy in SPI |
| S-10 | Electronic Marshalling in Smart Instrumentation | J. Dressel, Fluor (SPI LTUF) | 2019 | http://spi-ltuf.org/20190813/4%20Electronic%20Marshalling%20in%20SI.pdf | User-group presentation | Cross-vendor electronic marshalling (Honeywell, Yokogawa, ABB, Siemens, Foxboro) |
| S-11 | SmartPlant Instrumentation Tutorial / Help (I/O Assignment, Auto-wiring) | Hexagon PPM | 2016 SP1 | docs.hexagonppm.com (tutorial 244166); hexagonppm.fluidtopics.net (help 195301) | Vendor documentation (summarised via search; the page returned 404 to direct fetch) | I/O assignment is drag-and-drop; auto-wiring is wiring-only. **Confidence: medium (seen through search snippets only).** |
| S-12 | US 7,684,875 B2 "Methods and apparatus to configure process control system inputs and outputs" | Fisher-Rosemount Systems (Jundt et al.) | filed 2007, granted 2010 | https://patents.google.com/patent/US7684875B2/en | Patent | Tag-based automatic binding (not rule-based placement) |
| S-13 | Pathnovo I/O list generation page | Pathnovo | live | https://pathnovo.com/solutions/instrument-index-automation/io-list | Vendor marketing (not verified) | Adjacent tooling exists (P&ID → I/O list) |
| S-14 | Emerson Exchange 365 forum threads on CHARM bulk edit/export | Community | various | emersonexchange365.com (DeltaV discussions 9306, 11077) | Community forum (low authority) | Practitioner context only; **not used for claims in the deck** |

## D. Academic and technical literature

All entries verified against Crossref, arXiv or the publisher on 10 Oct 2026. See [literature_review.md](literature_review.md) for the analysis.

| ID | Reference | Identifier |
|---|---|---|
| L-01 | Coffman, Garey, Johnson. *Bin packing with divisible item sizes.* J. Complexity 3(4), 1987 | doi:10.1016/0885-064X(87)90009-4 |
| L-02 | Coffman, Csirik, Galambos, Martello, Vigo. *Bin Packing Approximation Algorithms: Survey and Classification.* Handbook of Combinatorial Optimization, 2013 | doi:10.1007/978-1-4419-7997-1_35 |
| L-03 | Delorme, Iori, Martello. *Bin packing and cutting stock problems: Mathematical models and exact algorithms.* EJOR 255(1), 2016 | doi:10.1016/j.ejor.2016.04.030 |
| L-04 | Gendreau, Laporte, Semet. *Heuristics and lower bounds for the bin packing problem with conflicts.* Computers & OR 31(3), 2004 | doi:10.1016/S0305-0548(02)00195-8 |
| L-05 | Jansen. *An Approximation Scheme for Bin Packing with Conflicts.* J. Comb. Optim. 3, 1999 | doi:10.1023/A:1009871302966 |
| L-06 | Shachnai, Tamir. *Polynomial time approximation schemes for class-constrained packing problems.* J. Scheduling 4(6), 2001 | doi:10.1002/jos.86 |
| L-07 | Barták, Müller, Rudová. *A New Approach to Modeling and Solving Minimal Perturbation Problems.* CSCLP 2003, LNCS 3010, 2004 | doi:10.1007/978-3-540-24662-6_13 |
| L-08 | Müller, Rudová, Barták. *Minimal Perturbation Problem in Course Timetabling.* PATAT 2004, LNCS 3616, 2005 | doi:10.1007/11593577_8 |
| L-09 | Zivan, Grubshtein, Meisels. *Hybrid search for minimal perturbation in Dynamic CSPs.* Constraints 16, 2011 | doi:10.1007/s10601-011-9108-5 |
| L-10 | Verfaillie, Jussien. *Constraint Solving in Uncertain and Dynamic Environments: A Survey.* Constraints 10, 2005 | doi:10.1007/s10601-005-2239-9 |
| L-11 | McConnell, Mehlhorn, Näher, Schweitzer. *Certifying algorithms.* Computer Science Review 5(2), 2011 | doi:10.1016/j.cosrev.2010.09.009 |
| L-12 | Junker. *QuickXplain: Preferred Explanations and Relaxations for Over-Constrained Problems.* AAAI 2004 | https://cdn.aaai.org/AAAI/2004/AAAI04-027.pdf |
| L-13 | Liffiton, Sakallah. *Algorithms for Computing Minimal Unsatisfiable Subsets of Constraints.* J. Automated Reasoning 40, 2008 | doi:10.1007/s10817-007-9084-z |
| L-14 | Gamba, Bogaerts, Guns. *Efficiently Explaining CSPs with Unsatisfiable Subset Optimization.* IJCAI 2021 / JAIR 2023 | doi:10.24963/ijcai.2021/191; doi:10.1613/jair.1.14260 |
| L-15 | Claessen, Hughes. *QuickCheck: a lightweight tool for random testing of Haskell programs.* ICFP 2000 | doi:10.1145/351240.351266 |
| L-16 | MacIver, Hatfield-Dodds et al. *Hypothesis: A new approach to property-based testing.* JOSS 4(43), 2019 | doi:10.21105/joss.01891 |
| L-17 | Ramamonjison et al. *NL4Opt Competition: Formulating Optimization Problems Based on Their Natural Language Descriptions.* 2023 | arXiv:2303.08233 |
| L-18 | Tsouros, Verhaeghe, Kadıoğlu, Guns. *Holy Grail 2.0: From Natural Language to Constraint Models.* 2023 | arXiv:2308.01589 |
| L-19 | Parciak et al. *Schema Matching with Large Language Models: an Experimental Study.* 2024 | arXiv:2407.11852 |
| L-20 | Dong et al. *SpreadsheetLLM: Encoding Spreadsheets for Large Language Models.* EMNLP 2024 | doi:10.18653/v1/2024.emnlp-main.1154; arXiv:2407.09025 |
| L-21 | Vogel-Heuser, Fay, Schaefer, Tichy. *Evolution of software in automated production systems: Challenges and research directions.* JSS 110, 2015 | doi:10.1016/j.jss.2015.08.026 |
| L-22 | Zakirzyanov. *Hybrid Metaheuristic Optimization of Distributed Control System Hardware Architecture with Model-Based Verification.* 2026 (preprint) | arXiv:2605.14788 |
| L-23 | Zakirzyanov. *Bio-inspired metaheuristic optimization for hierarchical architecture design of industrial control systems.* 2026 (preprint) | arXiv:2603.16617 |
| T-01 | Google OR-Tools: CP-SAT solver documentation and bin-packing guide (Apache-2.0) | https://developers.google.com/optimization/cp/cp_solver ; https://developers.google.com/optimization/pack/bin_packing ; https://github.com/google/or-tools/blob/stable/ortools/sat/docs/README.md |
