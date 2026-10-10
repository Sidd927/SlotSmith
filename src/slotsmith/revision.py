"""Revision engine: Rev A allocation + Rev B MDB -> Rev B allocation with the fewest moves.

Strategy (minimal-perturbation repair, cf. Barták et al. 2004):
1. Every Rev B cable that existed in Rev A with the same size, group and segregation is *pinned*
   to its Rev A slots. Signals added on its wired spare pairs therefore land with zero moves.
2. Deleted cables free their slots; CIOC numbers and controllers are kept stable.
3. Only new or changed cables are placed. Holes in compatible CIOCs are tried first, then empty
   baseplates, then new CIOCs, then a new cabinet, keeping groups in contiguous cabinets.
4. If no rule-compliant repair exists, the engine falls back to a full re-allocation and says so.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from .allocator import CIOC, AllocationResult, Cabinet, Layout, allocate, lower_bounds, natural_key
from .export import add_blocked_rows, build_rows, summary
from .model import TQ, CableBlock, Placement
from .rules import RuleSet
from .validate import ValidationResult, validate
from .verifier import _pattern_regex, verify


@dataclass
class _CIOC:
    no: int
    ctl: int
    seg: Optional[str] = None
    group: Optional[str] = None
    group_set: bool = False
    occ: dict[int, list[Optional[str]]] = field(default_factory=dict)   # bp -> 12 slots (cable or None)

    def used_bps(self) -> int:
        return sum(1 for s in self.occ.values() if any(s))


@dataclass
class RevisionResult:
    validation: ValidationResult
    allocation: AllocationResult
    rows: list[dict]
    summary: list[dict]
    impact: list[dict]
    check: list[dict]
    metrics: dict
    tqs: list = field(default_factory=list)


def _prev_layout(rows: list[dict], rules: RuleSet):
    """Rebuild Rev A geometry from allocation rows (works for in-memory rows or a re-read workbook)."""
    n = rules.naming
    rx_cab = _pattern_regex(n.marshalling_cabinet, n.area, n.unit)
    rx_cioc = _pattern_regex(n.cioc, n.area, n.unit)
    rx_bp = _pattern_regex(n.baseplate, n.area, n.unit)
    rx_ctl = _pattern_regex(n.controller, n.area, n.unit)
    cabs: dict[int, dict[int, _CIOC]] = defaultdict(dict)
    cables: dict[str, dict] = {}
    for r in rows:
        if not r.get("Slot"):
            continue
        cab = int(rx_cab.match(str(r["Marshalling Cabinet"])).group("seq"))
        no = int(rx_cioc.match(str(r["CIOC"])).group("seq"))
        bp = int(rx_bp.match(str(r["Baseplate"])).group("n"))
        slot = int(float(r["Slot"]))
        ctl = int(rx_ctl.match(str(r["Controller"])).group("seq"))
        q = cabs[cab].setdefault(no, _CIOC(no=no, ctl=ctl))
        q.occ.setdefault(bp, [None] * rules.charms_per_baseplate)
        pair = int(float(r["Pair"]))
        c = cables.setdefault(r["Cable"], {"cab": cab, "no": no, "size": int(float(r["Cable Size"])),
                                           "group": r.get("IO Group") or None, "seg": r.get("Segregation") or None,
                                           "lin": {}})
        c["lin"][pair] = (bp - 1) * rules.charms_per_baseplate + (slot - 1)
    return cabs, cables


def _free_run(slots: list[Optional[str]], size: int) -> Optional[int]:
    run = 0
    for i, v in enumerate(slots):
        run = run + 1 if v is None else 0
        if run == size:
            return i - size + 2   # 1-based start slot
    return None


def revise(prev_rows: list[dict], rev_b: pd.DataFrame, rules: RuleSet) -> RevisionResult:
    cap, bpc = rules.charms_per_baseplate, rules.baseplates_per_cioc
    val = validate(rev_b, rules)
    cabs, prev = _prev_layout(prev_rows, rules)
    blocks = {b.cable: b for b in val.blocks}

    # ---- 1. pin unchanged cables -------------------------------------------------
    pinned: dict[str, Placement] = {}
    for cable, b in blocks.items():
        p = prev.get(cable)
        if p and p["size"] == b.size and p["group"] == b.group and p["seg"] == b.seg and 1 in p["lin"]:
            start = p["lin"][1]
            bp, slot = start // cap + 1, start % cap + 1
            q = cabs[p["cab"]][p["no"]]
            for k in range(b.size):
                lin = start + k
                q.occ.setdefault(lin // cap + 1, [None] * cap)[lin % cap] = cable
            pinned[cable] = (p["cab"], p["no"], bp, slot)
    def retag():
        """CIOC side/group tags derived from current contents only."""
        for cab in cabs.values():
            for q in cab.values():
                content = {c for s in q.occ.values() for c in s if c}
                segs = {blocks[c].seg for c in content if blocks[c].seg}
                groups = {blocks[c].group for c in content}
                q.seg = next(iter(segs)) if segs else None
                q.group_set = bool(content)
                q.group = next(iter(groups)) if len(groups) == 1 else (None if not groups else sorted(groups, key=natural_key)[0])
    retag()

    def cab_used(cab: int) -> int:
        return sum(q.used_bps() for q in cabs[cab].values())

    def group_cabs(g):
        return {c for c, qs in cabs.items() for q in qs.values() if q.group_set and q.group == g}

    def compatible(q: _CIOC, b: CableBlock, cab: Optional[int] = None) -> bool:
        if b.seg and q.seg and b.seg != q.seg and rules.enabled("R2-segregation"):
            return False
        if rules.group_isolation_level == "cioc" and rules.enabled("R1-grouping") and q.group_set and q.group != b.group:
            if not (b.group is None and rules.ungrouped_may_share_group_cioc):
                return False
        if cab is not None and cab in cabs:
            others = [x for x in cabs[cab].values() if x.group_set]
            if (rules.segregation_level == "cabinet" and rules.enabled("R2-segregation") and b.seg
                    and any(x.seg and x.seg != b.seg for x in others)):
                return False
            if (rules.group_isolation_level == "cabinet" and rules.enabled("R1-grouping")
                    and any(x.group != b.group for x in others)):
                return False
        return True

    def mark(cab, q: _CIOC, bp, slot, b: CableBlock):
        start = (bp - 1) * cap + (slot - 1)
        for k in range(b.size):
            lin = start + k
            q.occ.setdefault(lin // cap + 1, [None] * cap)[lin % cap] = b.cable
        if b.seg:
            q.seg = b.seg
        if not q.group_set:
            q.group, q.group_set = b.group, True
        pinned[b.cable] = (cab, q.no, bp, slot)

    def try_cioc(cab, q: _CIOC, b: CableBlock, allow_empty_bp: bool) -> bool:
        if not compatible(q, b, cab):
            return False
        if b.size <= cap:
            for bp in range(1, bpc + 1):
                slots = q.occ.get(bp, [None] * cap)
                empty = not any(slots)
                if empty and (not allow_empty_bp or cab_used(cab) + 1 > rules.usable_baseplates_per_cabinet):
                    continue
                s = _free_run(slots, b.size)
                if s:
                    mark(cab, q, bp, s, b)
                    return True
        else:
            nb = -(-b.size // cap)
            if not allow_empty_bp or cab_used(cab) + nb > rules.usable_baseplates_per_cabinet:
                return False
            for bp in range(1, bpc - nb + 2):
                if all(not any(q.occ.get(bp + k, [None] * cap)) for k in range(nb)):
                    mark(cab, q, bp, 1, b)
                    return True
        return False

    def contiguous_ok(g, cab) -> bool:
        if g is None or rules.group_isolation_level == "none":
            return True
        cs = group_cabs(g) | {cab}
        return max(cs) - min(cs) + 1 == len(cs)

    max_no = max([q.no for qs in cabs.values() for q in qs.values()] or [0])
    max_ctl = max([q.ctl for qs in cabs.values() for q in qs.values()] or [0])
    failed: list[str] = []
    too_big: dict[str, str] = {}
    max_bp = min(bpc, rules.usable_baseplates_per_cabinet)
    for c, b in list(blocks.items()):
        if c not in pinned and -(-b.size // cap) > max_bp:
            too_big[c] = (f"{b.size}-pair cable needs {-(-b.size // cap)} baseplates; at most {max_bp} fit in one CIOC "
                          f"under the current capacity/spare rules")
    todo = [b for c, b in blocks.items() if c not in pinned and c not in too_big]
    todo.sort(key=lambda b: (natural_key(b.group), -b.size, natural_key(b.cable)))
    for b in todo:
        placed = False
        order = sorted(cabs, key=lambda c: (0 if c in group_cabs(b.group) else 1, c))
        for allow_empty in (False, True):
            for cab in order:
                if not contiguous_ok(b.group, cab):
                    continue
                for q in sorted(cabs[cab].values(), key=lambda x: x.no):
                    if try_cioc(cab, q, b, allow_empty):
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:   # new CIOC in an existing cabinet, else a new cabinet
            nb = max(1, -(-b.size // cap))
            for cab in order + [max(cabs or [0]) + 1]:
                if cab in cabs and (len(cabs[cab]) >= rules.ciocs_per_cabinet or
                                    cab_used(cab) + nb > rules.usable_baseplates_per_cabinet):
                    continue
                if not contiguous_ok(b.group, cab):
                    continue
                max_no += 1
                ctl_counts = defaultdict(int)
                for qs in cabs.values():
                    for x in qs.values():
                        ctl_counts[x.ctl] += 1
                last_ctl = max(ctl_counts) if ctl_counts else 1
                if ctl_counts.get(last_ctl, 0) >= rules.max_ciocs_per_controller:
                    max_ctl += 1
                    last_ctl = max_ctl
                q = _CIOC(no=max_no, ctl=last_ctl)
                cabs[cab][max_no] = q
                if try_cioc(cab, q, b, True):
                    placed = True
                    break
        if not placed:
            failed.append(b.cable)

    repair_log = []
    if failed:
        failed, repair_log = _cpsat_repair(failed, blocks, cabs, pinned, rules, retag, max_no, max_ctl)
    fallback = bool(failed)
    if fallback:
        res = allocate([b for b in val.blocks if b.cable not in too_big], rules)
        res.unplaced.update(too_big)
    else:
        # ---- build an AllocationResult with stable CIOC numbers -------------------------
        layout = Layout()
        placements: dict[str, Placement] = {}
        pos_of: dict[tuple[int, int], int] = {}
        for ci, cab in enumerate(sorted(cabs), 1):
            qs = [q for q in sorted(cabs[cab].values(), key=lambda x: x.no)]
            cabinet = Cabinet(ciocs=[CIOC(seg=q.seg, group=q.group, group_set=q.group_set, used_bp=q.used_bps(),
                                          no=q.no, ctl=q.ctl) for q in qs])
            layout.cabinets.append(cabinet)
            for qi, q in enumerate(qs, 1):
                pos_of[(cab, q.no)] = (ci, qi)
        for cable, (cab, no, bp, slot) in pinned.items():
            ci, qi = pos_of[(cab, no)]
            placements[cable] = Placement(cable, ci, qi, bp, slot)
        stats = {"cabinets": len(layout.cabinets), "ciocs": sum(len(c.ciocs) for c in layout.cabinets),
                 "baseplates": sum(c.used_bp for c in layout.cabinets)}
        res = AllocationResult(placements, layout, dict(too_big), lower_bounds(val.blocks, rules), stats)

    from .pipeline import capacity_tqs
    tqs = list(val.tqs) + capacity_tqs(val, res, len(val.tqs) + 1)
    if fallback:
        tqs.append(TQ(id=f"TQ-{len(tqs) + 1:04d}", severity="warning", category="capacity", rule_ref="R-2",
                      message=f"No rule-compliant minimum-move repair found for cables {failed[:10]}; "
                              f"Rev B was fully re-allocated, so unchanged signals may have moved (see impact report)",
                      cables=failed[:50], suggested_action="Review capacity/spare rules or accept the re-allocation"))
    rows = add_blocked_rows(build_rows(val, res, rules), rev_b_canon(rev_b), val)
    for r in rows:
        if r["Status"] == "Not allocated":
            r["TQ Ref"] = next((q.id for q in tqs if q.category == "capacity" and r["Cable"] in q.cables), "")
    impact, im = impact_report(prev_rows, rows)
    check = verify([{k: (None if v in ("", None) else str(v)) for k, v in r.items()} for r in rows], rev_b, rules)
    accepted = [x for x in repair_log if x.get("status") in ("OPTIMAL", "FEASIBLE")]
    metrics = {**im, "fallback_full_reallocation": fallback, "unplaced_after_repair": failed,
               "cpsat_repairs": repair_log,
               "cpsat_accepted_optimal": sum(1 for x in accepted if x["status"] == "OPTIMAL"),
               "cpsat_accepted_feasible_only": sum(1 for x in accepted if x["status"] == "FEASIBLE"),
               "capacity_unplaced": sorted(res.unplaced), "tqs": len(tqs),
               "cabinets": res.stats["cabinets"], "violations": sum(c["Violations"] for c in check)}
    return RevisionResult(val, res, rows, summary(rows, res, rules), impact, check, metrics, tqs)


def rev_b_canon(df: pd.DataFrame) -> pd.DataFrame:
    return df


def _loc(r):
    return (r.get("Marshalling Cabinet"), r.get("CIOC"), r.get("Baseplate"), str(r.get("Slot")))


def impact_report(prev_rows: list[dict], rows: list[dict]):
    a = {r["Tag"]: r for r in prev_rows if r.get("Tag") and r.get("Status") == "Allocated"}
    b = {r["Tag"]: r for r in rows if r.get("Tag") and r.get("Status") == "Allocated"}
    out, cabs_hit = [], set()
    counts = defaultdict(int)
    for t in sorted(set(a) | set(b)):
        ra, rb = a.get(t), b.get(t)
        if ra and not rb:
            kind, frm, to = "Deleted / not allocated in Rev B", _loc(ra), None
        elif rb and not ra:
            kind, frm, to = "Added", None, _loc(rb)
        elif _loc(ra) != _loc(rb):
            kind, frm, to = "Moved", _loc(ra), _loc(rb)
        elif (ra.get("IO Type"), ra.get("CHARM Type"), ra.get("Terminal Block")) != \
                (rb.get("IO Type"), rb.get("CHARM Type"), rb.get("Terminal Block")):
            kind, frm, to = "Modified in place (CHARM/TB change)", _loc(ra), _loc(rb)
        else:
            counts["Unchanged"] += 1
            continue
        counts[kind] += 1
        for l in (frm, to):
            if l:
                cabs_hit.add(l[0])
        fmt = lambda l: "" if not l else f"{l[0]} / {l[1]} / {l[2]} / slot {l[3]}"
        out.append({"Change": kind, "Tag": t, "Cable": (rb or ra).get("Cable"), "From": fmt(frm), "To": fmt(to),
                    "IO Type (A→B)": f"{(ra or {}).get('IO Type', '')} → {(rb or {}).get('IO Type', '')}"})
    metrics = {"moved": counts["Moved"], "added": counts["Added"],
               "deleted": counts["Deleted / not allocated in Rev B"],
               "modified_in_place": counts["Modified in place (CHARM/TB change)"],
               "unchanged": counts["Unchanged"], "cabinets_hit": sorted(c for c in cabs_hit if c)}
    return out, metrics


def _cpsat_repair(failed, blocks, cabs, pinned, rules: RuleSet, retag, max_no, max_ctl):
    """Widen a cabinet window around the affected groups until CP-SAT finds a minimum-move repair."""
    from .repair_cpsat import repair_window

    cap = rules.charms_per_baseplate
    log = []
    remaining = list(failed)
    while remaining:
        g = blocks[remaining[0]].group
        todo = [c for c in remaining if blocks[c].group == g]
        gcabs = sorted({c for c, qs in cabs.items() for q in qs.values() if q.group_set and q.group == g}) or [max(cabs)]
        last = max(cabs)
        solved = False
        for ext in range(0, 6):
            lo = max(1, gcabs[0] - ext // 2)
            hi = min(last, gcabs[-1] + ext)
            window = list(range(lo, hi + 1)) + ([last + 1] if hi == last else [])
            cab_nos = {}
            for c in window:
                nos = sorted(cabs.get(c, {}).keys())
                cab_nos[c] = (nos + [None] * rules.ciocs_per_cabinet)[: rules.ciocs_per_cabinet]
            win_cables = [cb for cb, (c, no, bp, sl) in pinned.items() if c in window] + todo
            old_pos = {}
            for cb, (c, no, bp, sl) in pinned.items():
                if c in window:
                    old_pos[cb] = (c, cab_nos[c].index(no) + 1, bp, sl)
            outside = defaultdict(set)
            for c, qs in cabs.items():
                if c in window:
                    continue
                for q in qs.values():
                    if q.group_set:
                        outside[q.group].add(c)
            sol, info = repair_window(window, cab_nos, [blocks[c] for c in win_cables], old_pos, outside, rules)
            log.append({"group": g, "window": [window[0], window[-1]], **info})
            if sol is None:
                continue
            # apply: rebuild occupancy of window cabinets
            for c in window:
                cabs.setdefault(c, {})
                for q in cabs[c].values():
                    q.occ = {}
            ctl_counts = defaultdict(int)
            for qs in cabs.values():
                for x in qs.values():
                    ctl_counts[x.ctl] += 1
            for cb, (c, qi, bp, sl) in sol.items():
                no = cab_nos[c][qi - 1]
                if no is None:
                    max_no += 1
                    no = max_no
                    cab_nos[c][qi - 1] = no
                    last_ctl = max(ctl_counts) if ctl_counts else 1
                    if ctl_counts.get(last_ctl, 0) >= rules.max_ciocs_per_controller:
                        max_ctl += 1
                        last_ctl = max_ctl
                    ctl_counts[last_ctl] += 1
                    cabs[c][no] = _CIOC(no=no, ctl=last_ctl)
                q = cabs[c][no]
                start = (bp - 1) * cap + (sl - 1)
                for k in range(blocks[cb].size):
                    lin = start + k
                    q.occ.setdefault(lin // cap + 1, [None] * cap)[lin % cap] = cb
                pinned[cb] = (c, no, bp, sl)
            for c in window:
                if c in cabs and not cabs[c]:
                    del cabs[c]
            retag()
            remaining = [c for c in remaining if c not in todo]
            solved = True
            break
        if not solved:
            return remaining, log
    return [], log
