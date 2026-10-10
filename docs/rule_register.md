# Rule register: Project IO SIGNAL SUDOKU (PS #02 in Track_1_PS_description.pdf, form number 1.2)

Source of truth: S-01 pages 4–6 (cited below as p4, p5, p6). Evidence classes:
- **OFF**: explicit official rule.
- **ORG**: organiser clarification (none received yet).
- **EXT**: external domain fact (Emerson documentation).
- **INT**: our engineering interpretation.
- **ASM**: unresolved assumption.

Every INT/ASM item is a **rule parameter** in the rule set, not a hard-coded behaviour, so an organiser clarification changes configuration, not code.

## 1. Data model rules

| ID | Exact rule (quoted or paraphrased) | Source | Hard / soft | Proposed implementation | Test case | Ambiguity | Evidence |
|---|---|---|---|---|---|---|---|
| D-1 | "1 row = 1 signal"; columns Tag, IO, Cable, Pair, Grp, Seg | p4 | Hard (input contract) | Column auto-map with synonyms; user confirms; provenance = file + sheet + row | Mapping of renamed headers | The real MDB has unknown extra columns | OFF |
| D-2 | "1 pair = 1 signal = 1 CHARM" | p4 | Hard | One signal ⇒ exactly one slot | Verifier: no slot holds two signals | — | OFF |
| D-3 | Cables of 24, 12, 6 or 2 pairs; "unused pairs are spares" | p4 | Hard | Cable size from an MDB column if present, else the smallest standard size ≥ max pair (raises an info TQ) | Pair > size ⇒ TQ | The cable-size column may be absent | OFF + INT |
| D-4 | Tag unique | INT | Hard | Duplicate tag ⇒ TQ, both rows blocked | Duplicate rows | — | INT |
| D-5 | (Cable, Pair) unique | INT | Hard | Duplicate pair ⇒ TQ | Two tags on one pair | — | INT |

## 2. Hierarchy and capacity

| ID | Exact rule | Source | Hard / soft | Implementation | Test | Ambiguity | Evidence |
|---|---|---|---|---|---|---|---|
| C-1 | "12 CHARMs per baseplate · 8 baseplates per CIOC · 4 CIOCs per cabinet (32 baseplates)" | p5 rule 3 | Hard | Parameters `charms_per_baseplate=12`, `baseplates_per_cioc=8`, `ciocs_per_cabinet=4` | Overfill ⇒ verifier violation | 4/cabinet is a project rule, not a hardware limit (EXT S-03 states no cabinet limit) | OFF + EXT |
| C-2 | Controller in system cabinet; names given for system cabinet and controller | p4, p5 | Hard (naming) | Each CIOC is assigned to one controller; `max_ciocs_per_controller=16` (S-03) | Naming test | How CIOCs map to controllers is not specified | OFF + EXT + ASM |
| C-3 | Output must show cabinets needed, fill % and spares per cabinet | p4, p6 | Hard (report) | Summary sheet | Report test | Fill % basis: slots used ÷ installed slots, or ÷ cabinet capacity | OFF + ASM |

## 3. Cable rules

| ID | Exact rule | Source | Hard / soft | Implementation | Test | Ambiguity | Evidence |
|---|---|---|---|---|---|---|---|
| K-1 | "All pairs of a 24/12/6/2-pair cable land side by side, in pair order" | p5 rule 4 | Hard | Cable = one contiguous block; pair p at offset p−1 | Verifier: slots of the cable are consecutive and ordered | — | OFF; EXT S-05 p.7 ("core #1 → CHARM 1-1") |
| K-2 | "A 24-pair takes 2 full baseplates"; "fills exactly 2 baseplates: 22 signals + 2 wired spare pairs" | p5 | Hard | 24-pair block starts at slot 1 of baseplate n and occupies n and n+1 **in the same CIOC** (always; `multi_baseplate_cables_same_cioc` is not configurable in practice) | Verifier | Same-CIOC requirement inferred | OFF + INT |
| K-3 | Can a 12/6/2-pair cable straddle two baseplates? | — | Parameter `allow_cable_straddle=false` | Blocks ≤ 12 always stay inside one baseplate (the diagram shows no straddling). **Audit note:** the allocator never straddles even if the parameter is true; the parameter only relaxes the verifier. | Verifier | **Open question for organisers** | ASM |
| K-4 | Spare pairs of a cable are wired, so they occupy slots ("grey = spare pair, light = free slot") | p5 diagram | Hard | Block width = cable size, not signal count | Verifier counts spare slots | — | OFF |
| K-5 | Several cables may share a baseplate (e.g. CBL-105 SOVs + two 2-pair cables on 001-CBP-4) | p5 diagram | Allowed | Packing of mixed blocks | — | — | OFF |

## 4. Grouping and segregation

| ID | Exact rule | Source | Hard / soft | Implementation | Test | Ambiguity | Evidence |
|---|---|---|---|---|---|---|---|
| G-1 | "Signals with the same IO Grouping stay in the same cabinets, in sequence. No group? Fill any free slot." | p5 rule 1 | Hard | Groups are placed as consecutive runs in slot order. A group spans the minimum number of consecutive cabinets. Ungrouped cables fill free slots afterwards. | Verifier: a group's cabinet set is contiguous and minimal; no interleaving between two groups | "Same cabinets" (plural) means spill is allowed. Whether ungrouped cables may share a group's CIOC is a parameter. The diagram shows dedicated CIOCs per group. | OFF + INT |
| G-2 | Granularity of group separation (cabinet / CIOC / baseplate) | p4 diagram (CIOC 1 = G1·A, CIOC 2 = G1·B, CIOC 3 = G2, CIOC 4 = no group) | Parameter `group_isolation_level=cioc` | Default CIOC, matching the diagram | Verifier | Diagram may be illustrative only | INT |
| G-3 | Mixed groups inside one cable | — | TQ | Cable with ≥ 2 groups ⇒ TQ (cannot keep the cable together and keep groups apart); placed by majority group only if `tq_policy=place_with_warning` | Validation test | — | INT |
| S-1 | "Duty/standby or risk-area signals marked A and B go to different CIOCs" / "A and B never share a CIOC" | p4, p5 rule 2 | Hard | Every CIOC is tagged A, B or neutral; A and B never share a CIOC. Parameter `segregation_level=cioc` (option: cabinet). | Verifier | Whether A and B must also be in different cabinets for risk areas | OFF |
| S-2 | Cable containing both A and B signals | — | TQ | Blocked + TQ (K-1 and S-1 cannot both hold) | Validation test | — | INT |
| S-3 | Seg value outside {A, B, blank} | — | TQ | TQ | Validation | Possibly more classes (A/B/C) exist | INT |

## 5. Spare capacity

| ID | Exact rule | Source | Hard / soft | Implementation | Test | Ambiguity | Evidence |
|---|---|---|---|---|---|---|---|
| P-1 | "Reserve space for future growth, e.g. ~10% per cabinet by keeping some baseplates empty. Value set per project." | p5 rule 5 | Hard (with parameter) | `spare_percent=10`; reserved empty baseplates per cabinet = `ceil(spare% × 32)` = 4, so 28 usable | Verifier: each cabinet has ≥ k empty baseplates | Rounding (ceil/round/floor); basis (cabinet capacity vs used); per-CIOC spreading | OFF + ASM |
| P-2 | "Empty baseplates = cabinet spare" | p4 legend | Report | Spares reported as empty baseplates + free slots + wired spare pairs, separately | Report test | Are empty baseplates physically installed? | OFF |

## 6. Hardware selection (rule 6)

Default mapping table. It is user-editable, and keyed by an IO-type string after normalisation.

| ID | Signal | CHARM | Terminal block | Source |
|---|---|---|---|---|
| H-1 | AI: pressure, level, flow, temperature | AI CHARM (HART / RTD) | Standard | p5 rule 6 |
| H-2 | AO: control valve | AO CHARM | Standard | p5 |
| H-3 | DI: switch, status, push-button | DI CHARM | Standard | p5 |
| H-4 | DO high current: SOV, horn, beacon, sounder | Isolated DO CHARM | Fused-injected-power | p5 |
| H-5 | DO normal | High-side DO CHARM | Standard | p5 |
| H-6 | DO relay output (rule-based) | High-side DO CHARM | Relay output | p5 |

- **Ambiguity H-A.** "AI CHARM (HART / RTD)": the choice between the AI 4-20 mA HART and RTD CHARMs needs an instrument-type attribute (e.g. TE/RTD vs TT transmitter).
- **Ambiguity H-B.** Thermocouples need the TC/mV terminal block (EXT S-03 p.5), but the PS says Standard. We follow the PS and raise an info TQ for TC tags.
- **Ambiguity H-C.** The trigger condition for "relay output (rule-based)" is not defined. It is a parameterised rule (e.g. by tag prefix or a load column).
- **External rules not in the PS (offered as optional, default off):** AC/LV separation per baseplate (S-03 p.5); one injected-power source per baseplate (S-03 p.4).

## 7. Naming (user-defined patterns)

| ID | Item | Pattern | Example | Source | Notes |
|---|---|---|---|---|---|
| N-1 | System cabinet | `<Area>-DCS-<Unit>-<Seq>` | AR1-DCS-100-01 | p5 | Seq width 2 (inferred from the example) |
| N-2 | Controller | `<Area>CTL<Unit><Seq>` | AR1CTL10001 | p5 | Seq width 2 |
| N-3 | Marshalling cabinet | `<Area>-DCM-<Unit>-<Seq>` | AR1-DCM-100-01 | p5 | Seq width 2 |
| N-4 | CIOC | `<Area>CIOC<Unit><Seq>` | AR1CIOC100001 | p5 | Seq width 3 |
| N-5 | Baseplate | `<CIOC no>-CBP-<n>` | 001-CBP-1 | p5 | CIOC no = the 3-digit CIOC seq; n unpadded |
| N-6 | CHARM slot | not given | — | — | Default `<baseplate>-<slot:02>` (e.g. 001-CBP-1-01), plus a DeltaV-style `CHM<n>-<slot:02>` column (S-14, low authority) |

Area/Unit source: a project parameter, or derived from the tag prefix (`10-PT-1001A` → unit 10?). This is **ASM** and needs a mentor answer. Seq scope (global vs per unit) is also **ASM**.

## 8. Process rules (Definition of Done, p6)

| ID | Rule | Implementation | Acceptance test |
|---|---|---|---|
| Q-1 | "100% allocated: every signal has a slot, or a TQ explaining why not" | Allocation result partitions signals into placed ∪ TQ-blocked | `placed + blocked == total` (property test) |
| Q-2 | "Zero violations of the rules the user set" | Independent verifier | Verifier on every output, 0 violations |
| Q-3 | "Right hardware: correct CHARM, terminal block and names" | Mapping table + naming engine; verifier re-derives both | Verifier |
| Q-4 | "Revision-friendly: unchanged signals stay where they are" | Revision engine pins unchanged cables; minimum-move repair | Moves metric vs a from-scratch re-run |
| Q-5 | "Flexible: a new rule or new IO MDB needs no code change" | Rules = JSON/YAML data; column mapping = data | Add a rule via config only, in a test |
| Q-6 | "No hand-editing: the tool produces the allocation end-to-end" | CLI/UI produces the final workbook | End-to-end test |
| Q-7 | "Hidden test: unseen IO MDB + a revision" | Schema-tolerant ingestion | Synthetic schema-variation tests (not proof of hidden-test success) |

## 9. Revision rules (p6 feature 5)

| ID | Rule | Implementation | Ambiguity |
|---|---|---|---|
| R-1 | "Load Rev B and compare it with Rev A" | Match by Tag (primary key); diff of attributes | Tags renamed between revisions look like delete + add |
| R-2 | "Keep unchanged signals in place: fewest moves" | Objective: minimise moved signals (lexicographic: moves, then new cabinets) | Does a CHARM/TB swap in the same slot count as a move? Default: no (reported as "modified in place") |
| R-3 | "Impact report: added, deleted, moved, cabinets hit" | Impact sheet | "Cabinets hit" = cabinets with any added, deleted, moved or modified signal |
| R-4 | Deleted signal frees its slot | Slot becomes a spare pair of the same cable if the cable remains; otherwise free | — |
| R-5 | Signal added on a spare pair of an existing cable | Lands in the cable's reserved spare slot: **zero moves** | — |
