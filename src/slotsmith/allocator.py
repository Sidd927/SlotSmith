"""Constructive allocator: cable blocks -> baseplates -> CIOCs -> cabinets.

Design (see docs/architecture.md):
1. Each cable is one block of `size` slots, wired spares included (rule K-1/K-4).
2. Within a packing class (group x segregation side), blocks of <= 12 pairs are packed
   into 12-slot baseplates with First-Fit-Decreasing. Cable sizes 2|6|12|24 form a divisible
   chain, so FFD uses the minimum number of baseplates for each class (proof in
   docs/architecture.md, section 4).
3. Baseplate units are laid into CIOCs and cabinets in group order, so groups stay
   together and in sequence. A and B never share a CIOC. The spare budget leaves
   ceil(spare% x 32) baseplates empty in every cabinet.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional

from .model import CableBlock, Placement
from .rules import RuleSet


def natural_key(s: Optional[str]):
    if s is None:
        return (1, [])
    return (0, [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)])


@dataclass
class Unit:
    """One or more consecutive baseplates that move together."""

    n_bp: int
    group: Optional[str]
    seg: Optional[str]
    contents: list[tuple[CableBlock, int, int]]  # (block, baseplate offset in unit, start slot)

    @property
    def used_slots(self) -> int:
        return sum(b.size for b, _, _ in self.contents)


@dataclass
class CIOC:
    seg: Optional[str] = None
    group: Optional[str] = None
    group_set: bool = False
    used_bp: int = 0
    units: list[tuple[Unit, int]] = field(default_factory=list)  # (unit, first baseplate index 1-based)
    no: Optional[int] = None      # stable global CIOC number (kept across revisions)
    ctl: Optional[int] = None     # stable controller number (kept across revisions)


@dataclass
class Cabinet:
    ciocs: list[CIOC] = field(default_factory=list)
    seg: Optional[str] = None

    @property
    def used_bp(self) -> int:
        return sum(c.used_bp for c in self.ciocs)


@dataclass
class Layout:
    cabinets: list[Cabinet] = field(default_factory=list)


@dataclass
class AllocationResult:
    placements: dict[str, Placement]
    layout: Layout
    unplaced: dict[str, str]                 # cable -> reason (capacity etc.)
    lower_bounds: dict[str, int]
    stats: dict[str, float]


# --------------------------------------------------------------------------- packing

def ffd_pack(blocks: list[CableBlock], cap: int, order: str = "ffd",
             bins: Optional[list[list[tuple[CableBlock, int]]]] = None) -> list[list[tuple[CableBlock, int]]]:
    """First-Fit(-Decreasing) packing of <=cap blocks into bins of `cap` contiguous slots.

    Returns bins as lists of (block, start_slot). Because blocks are appended
    contiguously, a bin's free space is always one run at its end.
    """
    bins = bins if bins is not None else []
    seq = sorted(blocks, key=lambda b: (-b.size, natural_key(b.cable))) if order == "ffd" else list(blocks)
    for b in seq:
        for content in bins:
            used = sum(x.size for x, _ in content)
            if used + b.size <= cap:
                content.append((b, used + 1))
                break
        else:
            bins.append([(b, 1)])
    return bins


def build_units(blocks: list[CableBlock], rules: RuleSet, group: Optional[str]) -> list[Unit]:
    """Pack one group's blocks into baseplate units, in side order A, neutral, B.

    Neutral (unsegregated) cables first top up the spare room of A-side and B-side
    baseplates (sharing a CIOC with either side is allowed), then get their own baseplates.
    """
    cap = rules.charms_per_baseplate
    seg_values = list(rules.segregation_values)
    side_a = seg_values[0] if seg_values else None
    others = seg_values[1:]
    sides = ([side_a] if side_a else []) + [None] + others
    by_seg: dict[Optional[str], list[CableBlock]] = {s: [] for s in sides}
    for b in blocks:
        by_seg.setdefault(b.seg, []).append(b)

    big_units: dict[Optional[str], list[Unit]] = {s: [] for s in by_seg}
    bins: dict[Optional[str], list] = {}
    for side, bl in by_seg.items():
        for b in sorted((x for x in bl if x.size > cap), key=lambda x: natural_key(x.cable)):
            big_units[side].append(Unit(math.ceil(b.size / cap), group, side, [(b, 0, 1)]))
        if side is not None:
            bins[side] = ffd_pack([x for x in bl if x.size <= cap], cap, rules.block_order)
    # neutral blocks: first-fit into existing side bins, then their own bins
    shared = [content for side in sides if side is not None for content in bins.get(side, [])]
    n_shared = len(shared)
    combined = ffd_pack([x for x in by_seg.get(None, []) if x.size <= cap], cap, rules.block_order, bins=shared)
    bins[None] = combined[n_shared:]

    units: list[Unit] = []
    for side in sides:
        units += big_units.get(side, [])
        for content in bins.get(side, []):
            units.append(Unit(1, group, side, [(b, 0, s) for b, s in content]))
    return units


# --------------------------------------------------------------------------- layout

class Placer:
    def __init__(self, rules: RuleSet, layout: Optional[Layout] = None):
        self.r = rules
        self.layout = layout or Layout()

    def _cab_ok(self, cab: Cabinet, unit: Unit) -> bool:
        if cab.used_bp + unit.n_bp > self.r.usable_baseplates_per_cabinet:
            return False
        if self.r.segregation_level == "cabinet" and unit.seg and cab.seg and cab.seg != unit.seg:
            return False
        return True

    def _cioc_ok(self, cioc: CIOC, unit: Unit) -> bool:
        r = self.r
        if cioc.used_bp + unit.n_bp > r.baseplates_per_cioc:
            return False
        if unit.seg and cioc.seg and unit.seg != cioc.seg and r.enabled("R2-segregation"):
            return False
        if r.group_isolation_level == "cioc" and r.enabled("R1-grouping") and cioc.group_set:
            if cioc.group != unit.group:
                if not (unit.group is None and r.ungrouped_may_share_group_cioc):
                    return False
        return True

    def _put(self, cab: Cabinet, cioc: CIOC, unit: Unit):
        cioc.units.append((unit, cioc.used_bp + 1))
        cioc.used_bp += unit.n_bp
        if unit.seg and self.r.enabled("R2-segregation"):
            cioc.seg = unit.seg
            if self.r.segregation_level == "cabinet":
                cab.seg = unit.seg
        if not cioc.group_set:
            cioc.group, cioc.group_set = unit.group, True

    def place(self, unit: Unit, fresh_cioc: bool = False, fresh_cabinet: bool = False) -> None:
        L = self.layout
        if fresh_cabinet and L.cabinets and L.cabinets[-1].used_bp > 0:
            L.cabinets.append(Cabinet())
        if not L.cabinets:
            L.cabinets.append(Cabinet())
        cab = L.cabinets[-1]
        if cab.ciocs and not fresh_cioc and self._cab_ok(cab, unit) and self._cioc_ok(cab.ciocs[-1], unit):
            self._put(cab, cab.ciocs[-1], unit)
            return
        if len(cab.ciocs) < self.r.ciocs_per_cabinet and self._cab_ok(cab, unit):
            if not cab.ciocs or cab.ciocs[-1].used_bp > 0:
                cab.ciocs.append(CIOC())
            if self._cioc_ok(cab.ciocs[-1], unit):
                self._put(cab, cab.ciocs[-1], unit)
                return
        if not self.fits_empty(unit):   # checked before touching the layout (no empty cabinet left behind)
            raise ValueError(f"Unit of {unit.n_bp} baseplates cannot fit in an empty cabinet")
        cab = Cabinet()
        L.cabinets.append(cab)
        cab.ciocs.append(CIOC())
        self._put(cab, cab.ciocs[-1], unit)

    def fits_empty(self, unit: Unit) -> bool:
        return self._cab_ok(Cabinet(), unit) and self._cioc_ok(CIOC(), unit)

    def place_group(self, units: list[Unit]) -> None:
        if not units:
            return
        lvl = self.r.group_isolation_level if self.r.enabled("R1-grouping") else "none"
        fresh_cab = lvl == "cabinet"
        if lvl != "none" and not fresh_cab and self.layout.cabinets:
            # Look-ahead: do not split a group across cabinets if starting a new cabinet avoids it.
            if self._touched(units, fresh_cabinet=True) < self._touched(units, fresh_cabinet=False):
                fresh_cab = True
        for i, u in enumerate(units):
            self.place(u, fresh_cioc=(i == 0 and lvl == "cioc"), fresh_cabinet=(i == 0 and fresh_cab))

    def _touched(self, units: list[Unit], fresh_cabinet: bool) -> int:
        """Number of cabinets this group would touch (capacity-only simulation)."""
        skel = Layout([Cabinet([CIOC(c.seg, c.group, c.group_set, c.used_bp) for c in cab.ciocs], cab.seg)
                       for cab in self.layout.cabinets])
        p = Placer(self.r, skel)
        lvl = self.r.group_isolation_level
        touched = set()
        for i, u in enumerate(units):
            p.place(u, fresh_cioc=(i == 0 and lvl == "cioc"), fresh_cabinet=(i == 0 and fresh_cabinet))
            touched.add(len(p.layout.cabinets))
        return len(touched)


def lower_bounds(blocks: list[CableBlock], rules: RuleSet) -> dict[str, int]:
    """Valid lower bounds on baseplates and cabinets, given group isolation."""
    cap = rules.charms_per_baseplate
    groups: dict[Optional[str], list[CableBlock]] = {}
    for b in blocks:
        groups.setdefault(b.group, []).append(b)
    lb_bp = 0
    for g, bl in groups.items():
        big = sum(math.ceil(b.size / cap) for b in bl if b.size > cap)
        small = [b for b in bl if b.size <= cap]
        tot = math.ceil(sum(b.size for b in small) / cap)
        sided = sum(math.ceil(sum(b.size for b in small if b.seg == s) / cap) for s in rules.segregation_values)
        lb_bp += big + max(tot, sided)
    lb_cab = math.ceil(lb_bp / rules.usable_baseplates_per_cabinet) if lb_bp else 0
    return {"baseplates": lb_bp, "cabinets": lb_cab,
            "slots_used": sum(b.size for b in blocks),
            "baseplates_exact_per_group": exact_group_baseplates(groups, rules)}


def exact_group_baseplates(groups: dict, rules: RuleSet) -> Optional[int]:
    """Exact minimum baseplates given group isolation and A/B separation, for sizes in {2, 6, 12} and
    multiples of 12. Uses the divisible-size lemma (architecture.md §4): any multiset of such items
    with total T fits in ceil(T/12) baseplates; neutral cables may join either side.
    Returns None when a non-standard size makes the lemma inapplicable."""
    cap = rules.charms_per_baseplate
    total = 0
    for bl in groups.values():
        if any(b.size <= cap and b.size not in (2, 6, 12) for b in bl) or any(b.size > cap and b.size % cap for b in bl):
            return None
        big = sum(b.size // cap for b in bl if b.size > cap)
        sides = [sum(b.size for b in bl if b.size <= cap and b.seg == s) for s in rules.segregation_values]
        neutral = [b.size for b in bl if b.size <= cap and not b.seg]
        tot_n = sum(neutral)
        if len(sides) != 2 or not any(sides):
            total += big + math.ceil((sum(sides) + tot_n) / cap)
            continue
        sums = {0}
        for x in neutral:
            sums |= {v + x for v in sums}
        total += big + min(math.ceil((sides[0] + na) / cap) + math.ceil((sides[1] + tot_n - na) / cap) for na in sums)
    return total


def allocate(blocks: list[CableBlock], rules: RuleSet) -> AllocationResult:
    groups: dict[Optional[str], list[CableBlock]] = {}
    for b in blocks:
        groups.setdefault(b.group, []).append(b)
    placer = Placer(rules)
    unplaced: dict[str, str] = {}
    for g in sorted(groups, key=natural_key):
        units = build_units(groups[g], rules, g)
        ok = []
        for u in units:   # per-unit, so one oversized cable never unplaces its whole group
            if placer.fits_empty(u):
                ok.append(u)
            else:
                for blk, _, _ in u.contents:
                    unplaced[blk.cable] = (f"{blk.size}-pair cable needs {u.n_bp} baseplates; an empty cabinet offers "
                                           f"{min(rules.baseplates_per_cioc, rules.usable_baseplates_per_cabinet)} "
                                           f"per CIOC under the current capacity/spare rules")
        placer.place_group(ok)
    placements: dict[str, Placement] = {}
    for ci, cab in enumerate(placer.layout.cabinets, 1):
        for qi, cioc in enumerate(cab.ciocs, 1):
            for unit, bp0 in cioc.units:
                for blk, off, slot in unit.contents:
                    placements[blk.cable] = Placement(blk.cable, ci, qi, bp0 + off, slot)
    used_bp = sum(c.used_bp for c in placer.layout.cabinets)
    stats = {"cabinets": len(placer.layout.cabinets),
             "ciocs": sum(len(c.ciocs) for c in placer.layout.cabinets),
             "baseplates": used_bp}
    return AllocationResult(placements, placer.layout, unplaced, lower_bounds(blocks, rules), stats)
