"""CP-SAT minimal-perturbation repair over a window of cabinets.

Used by the revision engine when no rule-compliant placement exists without moving other cables
(e.g. a group's cabinets are at their spare-capacity limit). Decision variables are slot-exact
start positions for every cable in the window. Starts are aligned to multiples of the cable size,
which loses nothing for the divisible sizes 2|6|12|24 (FFD packings are aligned).
Hard rules are encoded exactly; the objective minimises moved signals (Barták et al. 2004;
Zivan et al. 2011), with the Rev A positions supplied as solution hints.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

from ortools.sat.python import cp_model

from .model import CableBlock
from .rules import RuleSet

NONE_G = "__ungrouped__"


def repair_window(window_cabs: list[int], cab_cioc_nos: dict[int, list[Optional[int]]],
                  cables: list[CableBlock], old_pos: dict[str, tuple[int, int, int, int]],
                  outside_group_cabs: dict[Optional[str], set[int]], rules: RuleSet,
                  time_limit_s: float = 10.0):
    """Return {cable: (cab, cioc_index_in_cab, bp, slot)} or None if infeasible.

    cab_cioc_nos[cab] lists 4 CIOC positions (existing CIOC number or None for a free position).
    old_pos[cable] = (cab, cioc_index, bp, slot) for cables that had a position inside the window.
    """
    cap, bpc, qpc = rules.charms_per_baseplate, rules.baseplates_per_cioc, rules.ciocs_per_cabinet
    m = cp_model.CpModel()
    cand: dict[str, list[tuple[tuple[int, int, int, int], cp_model.IntVar]]] = defaultdict(list)
    covers: dict[tuple[int, int, int, int], list] = defaultdict(list)   # slot -> literals
    bp_lits: dict[tuple[int, int, int], list] = defaultdict(list)
    seg_in: dict[tuple[int, int, str], list] = defaultdict(list)
    grp_in_q: dict[tuple[int, int, str], list] = defaultdict(list)
    grp_in_cab: dict[tuple[str, int], list] = defaultdict(list)

    for b in cables:
        g = b.group if b.group is not None else NONE_G
        nb = -(-b.size // cap)
        starts = []
        old = old_pos.get(b.cable)
        # Existing cables may move at most one cabinet away; new/unplaced cables may go anywhere in the window.
        allowed = [c for c in window_cabs if old is None or abs(c - old[0]) <= 1]
        for c in allowed:
            for qi in range(1, qpc + 1):
                if b.size > cap:
                    starts += [(c, qi, bp, 1) for bp in range(1, bpc - nb + 2)]
                else:
                    step = b.size if cap % b.size == 0 else 1
                    starts += [(c, qi, bp, s) for bp in range(1, bpc + 1) for s in range(1, cap - b.size + 2, step)]
        if b.cable in old_pos and old_pos[b.cable] not in starts:
            starts.append(old_pos[b.cable])
        for pos in starts:
            lit = m.NewBoolVar("")
            cand[b.cable].append((pos, lit))
            c, qi, bp, s = pos
            lin0 = (bp - 1) * cap + (s - 1)
            for k in range(b.size):
                lin = lin0 + k
                covers[(c, qi, lin // cap + 1, lin % cap + 1)].append(lit)
                bp_lits[(c, qi, lin // cap + 1)].append(lit)
            if b.seg:
                seg_in[(c, qi, b.seg)].append(lit)
            grp_in_q[(c, qi, g)].append(lit)
            grp_in_cab[(g, c)].append(lit)
        m.AddExactlyOne(l for _, l in cand[b.cable])

    for lits in covers.values():
        if len(lits) > 1:
            m.AddAtMostOne(lits)
    # baseplate used indicators and spare budget per cabinet
    used = {}
    for key, lits in bp_lits.items():
        u = m.NewBoolVar("")
        for l in lits:
            m.AddImplication(l, u)
        used[key] = u
    for c in window_cabs:
        us = [u for (cc, _, _), u in used.items() if cc == c]
        if us and rules.enabled("R5-spare"):
            m.Add(sum(us) <= rules.usable_baseplates_per_cabinet)
    # segregation: a CIOC holds at most one side
    if rules.enabled("R2-segregation"):
        for c in window_cabs:
            for qi in range(1, qpc + 1):
                flags = []
                for s in rules.segregation_values:
                    lits = seg_in.get((c, qi, s), [])
                    if lits:
                        f = m.NewBoolVar("")
                        for l in lits:
                            m.AddImplication(l, f)
                        flags.append(f)
                if len(flags) > 1:
                    m.AddAtMostOne(flags)
    # cabinet-level segregation / isolation when configured (CIOC-level handled above/below)
    if rules.enabled("R2-segregation") and rules.segregation_level == "cabinet":
        for c in window_cabs:
            flags = []
            for s_ in rules.segregation_values:
                lits = [l for qi in range(1, qpc + 1) for l in seg_in.get((c, qi, s_), [])]
                if lits:
                    f = m.NewBoolVar("")
                    for l in lits:
                        m.AddImplication(l, f)
                    flags.append(f)
            if len(flags) > 1:
                m.AddAtMostOne(flags)
    if rules.enabled("R1-grouping") and rules.group_isolation_level == "cabinet":
        for c in window_cabs:
            flags = []
            for g in sorted({g for (_, _, g) in grp_in_q}):
                lits = grp_in_cab.get((g, c), [])
                if lits:
                    f = m.NewBoolVar("")
                    for l in lits:
                        m.AddImplication(l, f)
                    flags.append(f)
            if len(flags) > 1:
                m.AddAtMostOne(flags)
    # group isolation per CIOC
    groups = sorted({g for (_, _, g) in grp_in_q})
    if rules.enabled("R1-grouping") and rules.group_isolation_level == "cioc":
        for c in window_cabs:
            for qi in range(1, qpc + 1):
                flags = []
                for g in groups:
                    lits = grp_in_q.get((c, qi, g), [])
                    if lits:
                        f = m.NewBoolVar("")
                        for l in lits:
                            m.AddImplication(l, f)
                        if g == NONE_G and rules.ungrouped_may_share_group_cioc:
                            continue
                        flags.append(f)
                if len(flags) > 1:
                    m.AddAtMostOne(flags)
    # group contiguity across all cabinets (outside presence is fixed)
    if rules.enabled("R1-grouping") and rules.group_isolation_level != "none":
        all_cabs = sorted(set(window_cabs) | {c for s in outside_group_cabs.values() for c in s})
        for g in groups:
            if g == NONE_G:
                continue
            pres = {}
            for c in all_cabs:
                if c in window_cabs:
                    f = m.NewBoolVar("")
                    lits = grp_in_cab.get((g, c), [])
                    for l in lits:
                        m.AddImplication(l, f)
                    if lits:
                        m.AddBoolOr(lits).OnlyEnforceIf(f)
                    else:
                        m.Add(f == 0)
                    pres[c] = f
                else:
                    pres[c] = 1 if c in outside_group_cabs.get(g, set()) else 0
            cs = sorted(pres)
            for i in range(len(cs)):
                for k in range(i + 2, len(cs)):
                    for j in range(i + 1, k):
                        a, bb, mid = pres[cs[i]], pres[cs[k]], pres[cs[j]]
                        if isinstance(a, int) and isinstance(bb, int) and isinstance(mid, int):
                            continue
                        # a & bb -> mid
                        lits = [x for x in (a, bb) if not isinstance(x, int)]
                        if (isinstance(a, int) and a == 0) or (isinstance(bb, int) and bb == 0):
                            continue
                        if isinstance(mid, int):
                            if mid == 0:
                                m.AddBoolOr([x.Not() for x in lits])
                        else:
                            m.AddBoolOr([x.Not() for x in lits] + [mid])
    # objective: moved signals (weighted), then baseplates used
    stay_terms = []
    for b in cables:
        old = old_pos.get(b.cable)
        w = max(1, len(b.signals))
        for pos, lit in cand[b.cable]:
            if pos == old:
                stay_terms.append((w, lit))
                m.AddHint(lit, 1)
    moved = sum(max(1, len(b.signals)) for b in cables if b.cable in old_pos) - sum(w * l for w, l in stay_terms)
    m.Minimize(1000 * moved + sum(used.values()))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.relative_gap_limit = 0.05
    solver.parameters.num_workers = 8
    st = solver.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, {"status": solver.StatusName(st), "wall_s": solver.WallTime()}
    out = {}
    for b in cables:
        for pos, lit in cand[b.cable]:
            if solver.Value(lit):
                out[b.cable] = pos
                break
    obj, bound = solver.ObjectiveValue(), solver.BestObjectiveBound()
    return out, {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 2),
                 "objective": obj, "bound": bound, "proven_exact": abs(obj - bound) < 1e-6,
                 "moved_signals_lower_bound": int(bound // 1000),
                 "moved_signals": int(solver.Value(moved)) if not isinstance(moved, int) else moved,
                 "vars": len([1 for v in cand.values() for _ in v])}
