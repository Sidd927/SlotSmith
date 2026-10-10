# Architecture

```
Customer IO MDB(s) ──► 1 Ingest + auto-map ──► 2 Validate ──► TQ list
   (Excel/CSV)          (ingest.py)             (validate.py)
                                                    │ cable blocks
       3 Rule set (rules.py, JSON) ───────────────► 4 Allocator (allocator.py)
                                                    │ placements + layout
                                                    ▼
                                    6 Exporter (export.py) ──► workbook
                                                    │
                     5 Independent verifier (verifier.py) ◄── re-reads workbook
                                                    │
Rev A workbook ──► 7 Revision engine (revision.py + repair_cpsat.py) ──► Rev B workbook + impact
```

| # | Module | Responsibility | Key decisions |
|---|---|---|---|
| 1 | `ingest.py` | Read one or many workbooks or sheets; detect the header row; auto-map columns; keep `file:sheet:row` provenance | Deterministic synonym + fuzzy mapping (threshold 0.8). Unknown headers are reported. An LLM suggestion hook is planned. |
| 2 | `validate.py` | Build cable blocks; raise TQs for missing, invalid and conflicting data | Row-level and cable-level TQs cite rule IDs. A blocked signal's pair is *held*, so the cable's other signals keep their slots. |
| 3 | `rules.py` | Typed rule set (pydantic) with every open interpretation as a parameter | Toggles R1–R7; CHARM/TB table; aliases; naming patterns; spare % and rounding |
| 4 | `allocator.py` | Cable blocks → baseplates → CIOCs → cabinets | Per-class FFD; side order A, neutral, B; group look-ahead keeps groups in the fewest cabinets |
| 5 | `verifier.py` | Re-check every rule on the exported rows | Imports nothing from the allocator or exporter; parses names back into positions |
| 6 | `export.py` | Flat rows, summary, workbook | Sheets: IO Allocation, Cabinet Summary, TQ List, Rule Check, Revision Impact (revisions), Rule Set, Run Info |
| 7 | `revision.py`, `repair_cpsat.py` | Minimum-move Rev B | Pin unchanged cables → greedy fill of holes → CP-SAT window repair → (fallback) full re-allocation, reported |

## 4. Why first-fit-decreasing is optimal per packing class

**Claim.** Let item sizes come from S = {2, 6, 12}, where each size divides the next, and let the bin capacity C = 12 be a multiple of every size. Then FFD uses exactly ⌈Σ sizes / C⌉ bins, which is optimal.

**Proof.**
1. FFD places items in non-increasing size order. Consider the moment an item of size s is placed.
2. Every item already placed has a size that is a multiple of s, and C is a multiple of s. So every bin's free space is a multiple of s.
3. A bin with nonzero free space therefore has at least s free, and the item fits. FFD opens a new bin only when every existing bin has zero free space.
4. Hence, at the end, all bins except possibly the last are completely full, so the number of bins is ⌈Σ/C⌉. This equals the trivial lower bound, so it is optimal. ∎

A 24-pair block is two whole baseplates and does not affect the argument. `tests/test_core.py::test_ffd_divisible_sizes_is_optimal` checks the claim on 200 random instances. This is consistent with the divisible-size literature (Coffman, Garey & Johnson 1987, L-01).

**Scope of the guarantee (narrowed after the 10 Oct audit).**
- *Proven:* within one packing class whose sizes are all in {2, 6, 12} (plus whole-baseplate multiples of 12), FFD uses the minimum number of baseplates.
- *Not proven:* in a group, the allocator also lets neutral (unsegregated) cables top up the last A-side and B-side baseplates before opening new ones. Those baseplates' free space is a multiple of the smallest *A/B* item, not of the current neutral item, so step 2 of the proof does not carry over.
- *Verified empirically:* the group-level result matched the exact minimum in:
  - all 19,682 exhaustive cases with 0–2 cables of each (side, size) against a CP-SAT bin-packing model (all solves OPTIMAL);
  - 150 random larger groups (148 proven OPTIMAL, 2 FEASIBLE within 30 s, allocator never worse);
  - all 12 benchmark instances against the exact per-group formula.

  See `scripts/audit_ffd_exact.py`, `scripts/audit_lb_gap.py` and `artifacts/audit/`.
- *Not claimed:* minimum CIOCs or cabinets. Those also depend on group isolation, CIOC side tags and cabinet boundaries.
- *Non-standard sizes* (e.g. 4, 8, 16, 36 pairs) are packed by the same code without the proof. No counter-example appeared in small exhaustive checks, but none is ruled out. Cables over 12 pairs that are not a multiple of 12 leave the remainder of their last baseplate unused.

The earlier "+2 baseplates above the lower bound" came from a weak bound in `lower_bounds()`, not from wasted baseplates. The exact per-group minimum is now reported as `baseplates_exact_per_group`.

## 5. Revision engine detail

1. **Diff by tag.** Classify each signal as added, deleted, moved, modified in place (CHARM/TB swap, same slot) or unchanged.
2. **Pin.** A cable keeps its Rev A slots if its size, group and side are unchanged. Signals added on its spare pairs land with zero moves. Deleted signals turn into spare pairs.
3. **Greedy fill.** Place new or changed cables, preferring:
   1. holes in compatible CIOCs of the group's cabinets;
   2. empty baseplates, if the cabinet's spare budget allows;
   3. new CIOC positions;
   4. a new cabinet, only if group contiguity is preserved.
4. **CP-SAT window repair.** This handles cases where the greedy fill cannot comply, for example a group's cabinets already at the spare limit.
   - Window: start with the group's cabinets, then widen (both sides, plus one new cabinet at the end).
   - Variables: one Boolean per aligned start position per cable.
   - Hard constraints: slot exclusivity, spare budget, A/B per CIOC, one group per CIOC, group contiguity against fixed outside cabinets.
   - Objective: minimise 1000 · moved signals + baseplates used.
   - Rev A positions are supplied as hints. Settings: 10 s limit, 5% relative gap.
   - Existing cables may move at most one cabinet away.
5. **Fallback.** If the repair fails, do a full re-allocation and flag it in the metrics (0 of 10 benchmark cases).
6. **Verification.** Run the same independent verifier, plus the impact report.

Stable identities: CIOC numbers and controllers are kept from Rev A. New CIOCs get new numbers, so no existing name changes.

## 6. Where AI fits (planned, bounded)

| Task | AI role | Guardrail |
|---|---|---|
| Unresolved column headers | Suggest a mapping | The user confirms; the mapping is stored as data |
| Plain-English rule ("keep SIS signals in their own cabinets") | Draft a RuleSet JSON patch | Pydantic schema validation, then a diff preview, then the user saves |
| TQ text | Rewrite into customer-ready language | The original structured TQ is kept |

AI never places signals and never overrides the verifier.
