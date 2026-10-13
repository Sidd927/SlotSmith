"""Data validation: turn MDB rows into cable blocks, raising a TQ for every issue.

Each TQ cites the rule-register ID it relates to and the source rows (file:sheet:row),
so an engineer can send it to the customer without re-deriving the problem.
"""
from __future__ import annotations

import math
import re
from types import SimpleNamespace
from collections import defaultdict
from dataclasses import dataclass, field

import pandas as pd

from .model import TQ, CableBlock, Signal
from .rules import RuleSet


@dataclass
class ValidationResult:
    blocks: list[CableBlock]
    tqs: list[TQ]
    blocked_tags: dict[str, str] = field(default_factory=dict)   # tag (or src) -> TQ id
    held_slots: dict[str, set[int]] = field(default_factory=dict)  # cable -> pairs held by a blocked signal
    n_rows: int = 0


class _TQs:
    def __init__(self):
        self.items: list[TQ] = []

    def add(self, **kw) -> str:
        tid = f"TQ-{len(self.items) + 1:04d}"
        self.items.append(TQ(id=tid, **kw))
        return tid


def _clean(v):
    """NaN/blank -> None, everything else -> stripped string (pandas may hand us NaN for None)."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    t = str(v).strip()
    return None if t in ("", "-", "–", "nan", "None", "<NA>") else t


def _parse_int(v) -> int | None:
    if v is None:
        return None
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def validate(df: pd.DataFrame, rules: RuleSet) -> ValidationResult:
    tq = _TQs()
    blocked: dict[str, str] = {}
    src = lambda r: f"{r.src_file}:{r.src_sheet}:{r.src_row}"
    rows = [SimpleNamespace(**{k: _clean(v) for k, v in rec.items()}) for rec in df.to_dict("records")]

    # --- row-level checks -------------------------------------------------
    tag_rows = defaultdict(list)
    for r in rows:
        if r.tag:
            tag_rows[r.tag].append(r)
    dup_tags = {t for t, rs in tag_rows.items() if len(rs) > 1}
    for t in sorted(dup_tags):
        tid = tq.add(severity="blocking", category="data", rule_ref="D-4",
                     message=f"Tag {t} appears {len(tag_rows[t])} times in the MDB",
                     tags=[t], sources=[src(r) for r in tag_rows[t]],
                     suggested_action="Confirm which row is valid or rename the duplicate")
        blocked[t] = tid

    good: list[Signal] = []
    for r in rows:
        key = r.tag or src(r)
        if key in blocked:
            continue
        problems = []
        if not r.tag:
            problems.append(("D-1", "missing tag"))
        if not r.io_type:
            problems.append(("D-1", "missing IO type"))
        if not r.cable:
            problems.append(("D-1", "missing cable"))
        pair = _parse_int(r.pair)
        if pair is None or pair < 1:
            problems.append(("D-1", f"missing or invalid pair '{r.pair}'"))
        io_key = rules.normalise_io_type(r.io_type) if r.io_type else None
        # Fail closed: a signal with no hardware mapping is held as a blocking TQ whether or not R6-hardware is on.
        # The R6 switch controls only whether the verifier compares CHARM/terminal block with the table; it never
        # makes an unknown hardware assignment valid (interpretation chosen 13 Oct 2026, see docs/rule_register.md section 6).
        if io_key and rules.hardware_for(io_key) is None:
            off = "" if rules.enabled("R6-hardware") else " (R6-hardware is switched off, but unknown hardware stays unresolved)"
            problems.append(("H-*", f"IO type '{r.io_type}' has no CHARM/terminal-block rule{off}"))
        seg = r.seg.upper() if r.seg else None
        if seg and seg not in rules.segregation_values:
            problems.append(("S-3", f"segregation value '{r.seg}' is not one of {rules.segregation_values}"))
        if problems:
            rr = problems[0][0]
            tid = tq.add(severity="blocking", category="hardware" if rr.startswith("H") else "data", rule_ref=rr,
                         message=f"{key}: " + "; ".join(p[1] for p in problems),
                         tags=[r.tag] if r.tag else [], cables=[r.cable] if r.cable else [], sources=[src(r)],
                         suggested_action="Correct the MDB row or add a rule for this IO type")
            blocked[key] = tid
            continue
        good.append(Signal(tag=r.tag, io_type=io_key, io_type_raw=r.io_type, cable=r.cable, pair=pair,
                           group=r.group, seg=seg, src=src(r)))

    # --- cable-level checks -----------------------------------------------
    by_cable: dict[str, list[Signal]] = defaultdict(list)
    for s in good:
        by_cable[s.cable].append(s)
    size_decl: dict[str, set[int]] = defaultdict(set)
    for r in rows:
        if r.cable and r.cable_size:
            v = _parse_int(r.cable_size)
            if v:
                size_decl[r.cable].add(v)

    blocks: list[CableBlock] = []
    held: dict[str, set[int]] = defaultdict(set)
    inferred = []
    std = sorted(rules.standard_cable_sizes)
    # pairs held by blocked rows of otherwise valid cables (slot reserved, rule K-4)
    for r in rows:
        key = r.tag or src(r)
        p = _parse_int(r.pair)
        if key in blocked and r.cable and p:
            held[r.cable].add(p)

    for cable, sigs in by_cable.items():
        srcs = [s.src for s in sigs]
        tags = [s.tag for s in sigs]

        def block_cable(rule_ref, msg, action):
            tid = tq.add(severity="blocking", category="rule-conflict", rule_ref=rule_ref, message=msg,
                         tags=tags, cables=[cable], sources=srcs, suggested_action=action)
            for s in sigs:
                blocked[s.tag] = tid

        # size
        if len(size_decl[cable]) > 1:
            block_cable("D-3", f"Cable {cable} has conflicting sizes {sorted(size_decl[cable])}",
                        "Confirm the cable schedule size")
            continue
        max_pair = max(max(s.pair for s in sigs), max(held.get(cable, {0})))
        if size_decl[cable]:
            size = next(iter(size_decl[cable]))
            if size not in std:
                tq.add(severity="warning", category="data", rule_ref="D-3",
                       message=f"Cable {cable} has non-standard size {size} (standard: {std})",
                       cables=[cable], sources=srcs[:3], suggested_action="Confirm the cable size")
        else:
            size = next((c for c in std if c >= max_pair), max_pair)
            inferred.append(cable)
        # pair range / duplicates
        over = [s for s in sigs if s.pair > size]
        pairs = defaultdict(list)
        for s in sigs:
            pairs[s.pair].append(s)
        dups = {p: ss for p, ss in pairs.items() if len(ss) > 1}
        if over or dups:
            for s in over:
                tid = tq.add(severity="blocking", category="data", rule_ref="D-3",
                             message=f"{s.tag}: pair {s.pair} exceeds the {size}-pair size of cable {cable}",
                             tags=[s.tag], cables=[cable], sources=[s.src],
                             suggested_action="Correct the pair number or the cable size")
                blocked[s.tag] = tid
            for p, ss in dups.items():
                tid = tq.add(severity="blocking", category="data", rule_ref="D-5",
                             message=f"Cable {cable} pair {p} is assigned to {len(ss)} tags: {', '.join(x.tag for x in ss)}",
                             tags=[x.tag for x in ss], cables=[cable], sources=[x.src for x in ss],
                             suggested_action="Confirm which tag uses this pair")
                for x in ss:
                    blocked[x.tag] = tid
                held[cable].add(p)
            sigs = [s for s in sigs if s.tag not in blocked]
            if not sigs:
                continue
        # segregation inside one cable
        segs = {s.seg for s in sigs if s.seg}
        if len(segs) > 1 and rules.enabled("R2-segregation"):
            block_cable("S-2", f"Cable {cable} carries both {' and '.join(sorted(segs))} signals; "
                               f"the cable cannot be kept together and segregated", "Re-route one side to a separate cable")
            continue
        groups = {s.group for s in sigs if s.group}
        if len(groups) > 1 and rules.enabled("R1-grouping") and rules.group_isolation_level != "none":
            block_cable("G-3", f"Cable {cable} carries signals from several IO groups {sorted(groups)}",
                        "Confirm the IO grouping for this cable")
            continue
        # A cable that mixes sides (or groups) can only reach this point when the controlling switch is off. It has no single
        # side/group: it is placed as an unsided/ungrouped cable (deterministic, never "first item of a set"), every signal
        # keeps its own side/group in the export, and a warning TQ states that separation is not enforced for it.
        mixed_seg, mixed_grp = len(segs) > 1, len(groups) > 1
        seg = None if mixed_seg else next(iter(segs), None)
        group = None if mixed_grp else next(iter(groups), None)
        for flag, what, sw, code, vals in ((mixed_seg, "A/B sides", "R2-segregation", "S-2", segs),
                                           (mixed_grp, "IO groups", "R1-grouping or isolation level", "G-3", groups)):
            if flag:
                tq.add(severity="warning", category="rule-conflict", rule_ref=code,
                       message=f"Cable {cable} carries several {what} {sorted(vals)}; separation is not enforced for it because "
                               f"{sw} is switched off. It is placed as an unsided/ungrouped cable and each signal keeps its own value",
                       tags=tags, cables=[cable], sources=srcs[:5],
                       suggested_action="Re-route one side/group to a separate cable, or switch the rule back on to hold this cable")
        if (segs and any(not s.seg for s in sigs)) or (groups and any(not s.group for s in sigs)):
            tq.add(severity="warning", category="data", rule_ref="G-1/S-1",
                   message=f"Cable {cable}: some signals lack group/segregation; the cable is treated as "
                           f"group={group}, seg={seg}",
                   tags=[s.tag for s in sigs if not s.group or not s.seg], cables=[cable],
                   sources=[s.src for s in sigs if not s.group or not s.seg][:5],
                   suggested_action="Confirm grouping/segregation for the listed tags")
        blocks.append(CableBlock(cable=cable, size=size, group=group, seg=seg,
                                 signals={s.pair: s for s in sigs}))

    if inferred:
        tq.add(severity="info", category="data", rule_ref="D-3",
               message=f"{len(inferred)} cable(s) have no size column; size inferred as the smallest standard "
                       f"size ≥ highest pair used", cables=inferred[:50],
               suggested_action="Provide the cable schedule (cable size) to confirm")

    return ValidationResult(blocks=blocks, tqs=tq.items, blocked_tags=blocked,
                            held_slots={k: v for k, v in held.items()}, n_rows=len(rows))
