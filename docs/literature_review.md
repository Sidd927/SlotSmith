# Literature review

Status: v1, 10 Oct 2026. Every reference was verified against Crossref, arXiv or the publisher (IDs L-xx in [source_register.md](source_register.md)).

**Headline finding.** We found **no peer-reviewed paper on rule-based assignment of field signals to DCS electronic-marshalling slots**. The closest academic work optimises DCS *hardware architecture* (L-22, L-23). The industrial evidence (Emerson white papers, Fluor/SPI user-group decks) describes the engineering workflow but no allocation algorithm. The problem therefore sits on four well-studied adjacent areas: bin packing (with conflicts and classes), minimal-perturbation re-solving, certifying/verified outputs with explanation, and LLM-assisted schema/rule interpretation. The design draws on each, as recorded below.

## 1. Packing structure of the problem

| Ref | Contribution | Method | Relevant findings | Limitations | Effect on SlotSmith |
|---|---|---|---|---|---|
| L-01 Coffman, Garey, Johnson 1987, *Bin packing with divisible item sizes* | Studies bin packing when item sizes divide one another | Worst/average-case analysis of FF/FFD | The divisible-size structure makes greedy packing behave far better than in general bin packing | We could not read the full text in-session, so we prove the property we rely on ourselves (architecture.md §4) | Cable sizes 2 \| 6 \| 12 \| 24 and baseplate capacity 12 form a divisible chain, so per-class FFD is optimal. **Validated by our proof and a 200-case property test.** |
| L-02 Coffman et al. 2013, survey | Taxonomy of approximation algorithms | Survey | FFD and variants are the standard baselines | General survey | Justifies FFD as the baseline, and when to escalate to exact methods |
| L-03 Delorme, Iori, Martello 2016 | Exact models (assignment, arc-flow, set-cover) for BPP/CSP | ILP/branch-and-price review | Exact methods are practical for thousands of items with structure | Plain BPP only (no side constraints) | We use exact CP only where needed (revision repair). The initial allocation is already optimal per class. |
| L-04 Gendreau, Laporte, Semet 2004, *BPP with conflicts* | Items in conflict cannot share a bin | Heuristics + lower bounds | Conflict graphs fit naturally into packing heuristics | Conflicts are item-level | **A/B segregation is a conflict constraint at CIOC level**: A-items and B-items can never share a CIOC "bin". We encode it as a CIOC side tag. |
| L-05 Jansen 1999 | Approximation scheme for BPP with conflicts (special graphs) | APTAS | Theoretical tractability for structured conflict graphs | Theory | Supports treating A/B as structured (bipartite-like) conflicts |
| L-06 Shachnai, Tamir 2001, class-constrained packing | Bins hold a limited number of item classes | PTAS | Class constraints model "one group per bin" | Theory | **Group isolation per CIOC is a class-constrained packing.** We pack each class separately, which is optimal for divisible sizes. |
| L-22/L-23 Zakirzyanov 2026 (preprints) | Synthesis of a DCS hardware hierarchy (signals → devices → network) | Ant-colony metaheuristic + model-based verification | Shows DCS I/O topology as a hierarchical combinatorial optimisation | Preprints, not peer reviewed. Metaheuristics give no optimality guarantee. Different objective (cost). | Confirms the problem class. Our case is narrower (fixed CHARM hierarchy), which allows exact structure-exploiting methods instead of metaheuristics. |

## 2. Revisions as minimal-perturbation problems

| Ref | Contribution | Relevance |
|---|---|---|
| L-07 Barták, Müller, Rudová 2004 | Formal model of the minimal perturbation problem (MPP): given a solution of an old problem and a changed problem, find a solution with the fewest changed assignments | **Exact formal match** for "Rev B, keep unchanged signals in place, fewest moves". Our objective = number of moved signals. |
| L-08 Müller, Rudová, Barták 2005 | MPP in large real timetabling instances; local search with perturbation penalties | Real-world evidence that MPP is solvable at scale with incremental methods, as in our pin-then-repair design |
| L-09 Zivan, Grubshtein, Meisels 2011 | Hybrid search for MPP in dynamic CSPs | Supports combining systematic (CP) and local strategies; we use greedy pinning plus a CP-SAT window search |
| L-10 Verfaillie, Jussien 2005 | Survey of solving in dynamic environments: re-use of previous solutions, solution stability | Motivates *solution stability* as an explicit objective, and the warm start (we pass Rev A positions as CP-SAT hints) |

**Design consequence.** The engine pins every unchanged cable. When no rule-compliant repair exists, it widens a cabinet window and solves an exact CP-SAT MPP over that window only. The benchmark on 10 synthetic Rev B cases measured 470 moved signals in total, against 49,805 for from-scratch re-runs (artifacts/benchmarks.json).

## 3. Verification, explanation and testing

| Ref | Contribution | Effect on SlotSmith |
|---|---|---|
| L-11 McConnell, Mehlhorn, Näher, Schweitzer 2011, *Certifying algorithms* | An algorithm should output a certificate that a simple, independent checker can verify | **Independent verifier**: it re-reads the exported workbook, re-derives positions from names and hardware from the rule table, and shares no code with the allocator |
| L-12 Junker 2004, QuickXplain | Minimal conflict sets (explanations) for over-constrained problems | Planned: when CP-SAT reports infeasible, extract a minimal rule set that explains *why* (e.g. "G2 cabinets full under spare 10%"), so it can become a TQ |
| L-13 Liffiton, Sakallah 2008 | MUS/MCS enumeration algorithms | Same; alternative relaxations ("relax spare to 8% or allow spill to MC-05") |
| L-14 Gamba, Bogaerts, Guns 2021/2023 | Step-wise explanations of CSP solutions, optimised for human interpretability | Future: user-facing explanations of why a signal is where it is |
| L-15 Claessen, Hughes 2000, QuickCheck; L-16 MacIver et al. 2019, Hypothesis | Property-based testing | Implemented: random MDBs ⇒ 0 violations and 100% coverage; FFD optimality property |

## 4. AI-assisted engineering and its boundary

| Ref | Contribution | Effect on SlotSmith |
|---|---|---|
| L-19 Parciak et al. 2024, *Schema matching with LLMs* | Experimental study: LLMs help schema matching but need careful prompting and still make errors | Column mapping stays deterministic first (synonyms + fuzzy). An LLM may *suggest* mappings for unresolved headers; the user confirms. |
| L-20 Dong et al. 2024, *SpreadsheetLLM* | Encoding spreadsheets compactly for LLMs | Relevant if we feed messy multi-table MDB sheets to an LLM for header detection |
| L-17 Ramamonjison et al. 2023, NL4Opt | Benchmark: NL → optimisation formulations; models make formulation errors | Plain-English rules → JSON drafts must be **schema-validated and previewed**, never trusted blindly |
| L-18 Tsouros et al. 2023, *Holy Grail 2.0* | Position paper: LLMs as modelling assistants for constraint programming, with a human in the loop | Same boundary: AI proposes, the deterministic engine and verifier decide |
| L-21 Vogel-Heuser et al. 2015 | Challenges of evolving software and engineering data in automated production systems | Context: variant/revision management and inter-disciplinary data are known pain points in automation engineering |

## 5. Gaps in the literature, and what we cannot claim

- No published benchmark exists for CHARM allocation. Our numbers come from our own synthetic generator and are not comparable to any external baseline.
- No public data shows how long manual allocation takes. We therefore claim **no time savings**.
- The divisible-size optimality holds per packing class. Total cabinet count also depends on group isolation and cabinet boundaries. We report the measured gap against a computed lower bound (max +2 baseplates over 12 runs) rather than claiming global optimality.
