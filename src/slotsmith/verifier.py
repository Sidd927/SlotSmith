"""Independent rule verifier.

Reads the *exported* allocation (the rows a judge or engineer receives) plus the original MDB
and the rule set, and re-checks every rule. It deliberately imports nothing from allocator.py
or export.py: positions are re-derived from the names in the workbook, and hardware is re-looked-up
from the rule table, so a bug in the allocator is unlikely to be mirrored here
(cf. certifying algorithms, McConnell et al. 2011).
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

from .rules import RuleSet

CHECKS = [
    ("Q-1", "Every MDB signal is allocated or has a TQ"),
    ("D-2", "One signal per CHARM slot (no slot used twice)"),
    ("C-1", "Capacity: 12 CHARMs/baseplate, 8 baseplates/CIOC, 4 CIOCs/cabinet"),
    ("K-1", "Each cable lands complete, side by side, in pair order"),
    ("S-1", "A and B signals never share a CIOC"),
    ("G-1", "IO groups isolated and kept in contiguous cabinets"),
    ("P-1", "Spare room: required empty baseplates in every cabinet"),
    ("H-1..6", "Correct CHARM and terminal block per signal type"),
    ("N-1..6", "Names follow the user-defined patterns"),
    ("C-2", "Each CIOC has one controller; controller CIOC limit respected"),
    ("M-1", "Allocated rows match the MDB (IO type, cable, pair, group, seg)"),
]


def _pattern_regex(pat: str, area: str, unit: str) -> re.Pattern:
    out, i = "", 0
    for m in re.finditer(r"\{(\w+)(?::0?(\d+)d)?\}", pat):
        out += re.escape(pat[i:m.start()])
        name, width = m.group(1), m.group(2)
        if name == "area":
            out += re.escape(area)
        elif name == "unit":
            out += re.escape(unit)
        else:
            out += rf"(?P<{name}>\d{{{width},}})" if width else rf"(?P<{name}>\d+)"
        i = m.end()
    return re.compile("^" + out + re.escape(pat[i:]) + "$")


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def load_allocation(path: str | Path) -> list[dict]:
    df = pd.read_excel(path, sheet_name="IO Allocation", dtype=str)
    return [{k: (None if _blank(v) else str(v).strip()) for k, v in r.items()} for r in df.to_dict("records")]


def verify(rows: list[dict], mdb: pd.DataFrame, rules: RuleSet, blocked_ok: bool = True) -> list[dict]:
    v: dict[str, list[str]] = defaultdict(list)
    n = rules.naming
    rx = {k: _pattern_regex(getattr(n, k), n.area, n.unit) for k in
          ["system_cabinet", "controller", "marshalling_cabinet", "cioc", "baseplate", "charm_slot"]}
    placed = [r for r in rows if r.get("Slot")]

    # ---- Q-1 completeness -------------------------------------------------
    mdb = mdb.astype(object).where(mdb.notna(), None)
    mdb_tags = [t for t in mdb["tag"].tolist() if t]
    by_tag = defaultdict(list)
    for r in rows:
        if r.get("Tag"):
            by_tag[r["Tag"]].append(r)
    for t in set(mdb_tags):
        rs = by_tag.get(t, [])
        if not rs:
            v["Q-1"].append(f"{t}: missing from the allocation")
        elif any(r.get("Status") == "Allocated" for r in rs):
            if sum(1 for r in rs if r.get("Status") == "Allocated") > 1:
                v["Q-1"].append(f"{t}: allocated more than once")
            elif len(rs) > 1:
                v["Q-1"].append(f"{t}: allocated but also listed as {sorted({r.get('Status') for r in rs} - {'Allocated'})}")
        elif not all(r.get("TQ Ref") for r in rs):
            v["Q-1"].append(f"{t}: neither allocated nor covered by a TQ")
    untagged = mdb[mdb["tag"].map(lambda x: x is None or str(x).strip() == "")]
    for r in untagged.itertuples(index=False):
        src = f"{r.src_file}:{r.src_sheet}:{r.src_row}"
        if not any(x.get("Source") == src and x.get("TQ Ref") for x in rows):
            v["Q-1"].append(f"{src}: row without tag has no TQ")

    # ---- positions from names ---------------------------------------------
    pos = []
    for r in placed:
        mb = rx["baseplate"].match(r.get("Baseplate") or "")
        mc = rx["cioc"].match(r.get("CIOC") or "")
        mm = rx["marshalling_cabinet"].match(r.get("Marshalling Cabinet") or "")
        try:
            slot = int(float(r["Slot"]))
        except (TypeError, ValueError):
            slot = -1
        if not (mb and mc and mm):
            v["N-1..6"].append(f"{r.get('Cable')}/{r.get('Pair')}: unparseable location names "
                               f"{r.get('Marshalling Cabinet')}/{r.get('CIOC')}/{r.get('Baseplate')}")
            continue
        if int(mb.group("cioc_no")) != int(mc.group("seq")):
            v["N-1..6"].append(f"{r['Baseplate']} does not belong to {r['CIOC']}")
        pos.append((r, int(mm.group("seq")), r["CIOC"], int(mb.group("n")), slot))

    # ---- D-2 unique slots, C-1 capacity -------------------------------------
    seen = {}
    cab_ciocs, cioc_bps, cioc_cab = defaultdict(set), defaultdict(set), {}
    for r, cab, cioc, bp, slot in pos:
        key = (cioc, bp, slot)
        if key in seen:
            v["D-2"].append(f"{cioc} BP{bp} slot {slot}: {seen[key]} and {r.get('Tag') or r.get('Cable')}")
        seen[key] = r.get("Tag") or f"{r.get('Cable')}/{r.get('Pair')}"
        if not 1 <= slot <= rules.charms_per_baseplate:
            v["C-1"].append(f"{cioc} BP{bp}: slot {slot} out of range")
        if not 1 <= bp <= rules.baseplates_per_cioc:
            v["C-1"].append(f"{cioc}: baseplate {bp} out of range")
        cab_ciocs[cab].add(cioc)
        cioc_bps[cioc].add(bp)
        if cioc_cab.setdefault(cioc, cab) != cab:
            v["C-1"].append(f"{cioc} appears in two cabinets")
    for cab, cs in cab_ciocs.items():
        if len(cs) > rules.ciocs_per_cabinet:
            v["C-1"].append(f"cabinet #{cab}: {len(cs)} CIOCs")

    # ---- K-1 cable integrity --------------------------------------------------
    cap = rules.charms_per_baseplate
    by_cable = defaultdict(list)
    for p in pos:
        by_cable[p[0].get("Cable")].append(p)
    for cable, ps in by_cable.items():
        size = int(float(ps[0][0].get("Cable Size") or 0))
        pairs = sorted(int(float(p[0]["Pair"])) for p in ps)
        if pairs != list(range(1, size + 1)):
            v["K-1"].append(f"{cable}: pairs present {pairs[:5]}… do not cover 1..{size} exactly once")
            continue
        if len({p[2] for p in ps}) != 1:
            v["K-1"].append(f"{cable}: spread over several CIOCs")
            continue
        lin = {int(float(p[0]["Pair"])): (p[3] - 1) * cap + (p[4] - 1) for p in ps}
        start = lin[1]
        if any(lin[q] != start + q - 1 for q in range(1, size + 1)):
            v["K-1"].append(f"{cable}: pairs are not side by side in pair order")
        bps = {p[3] for p in ps}
        if size <= cap and not rules.allow_cable_straddle and len(bps) != 1:
            v["K-1"].append(f"{cable}: {size}-pair cable straddles baseplates {sorted(bps)}")
        if size > cap and start % cap != 0:
            v["K-1"].append(f"{cable}: {size}-pair cable does not start at slot 1")

    # ---- S-1 segregation --------------------------------------------------------
    if rules.enabled("R2-segregation"):
        unit_of = (lambda p: p[2]) if rules.segregation_level == "cioc" else (lambda p: p[1])
        sides = defaultdict(set)
        for p in pos:
            s = p[0].get("Segregation")
            if s:
                sides[unit_of(p)].add(s)
        for u, ss in sides.items():
            if len(ss) > 1:
                v["S-1"].append(f"{u}: holds {' and '.join(sorted(ss))} signals")

    # ---- G-1 grouping ------------------------------------------------------------
    if rules.enabled("R1-grouping") and rules.group_isolation_level != "none":
        unit_of = (lambda p: p[2]) if rules.group_isolation_level == "cioc" else (lambda p: p[1])
        grp_in = defaultdict(set)
        for p in pos:
            grp_in[unit_of(p)].add(p[0].get("IO Group") or None)
        for u, gs in grp_in.items():
            named = {g for g in gs if g}
            if len(named) > 1:
                v["G-1"].append(f"{u}: mixes groups {sorted(named)}")
            elif named and None in gs and not rules.ungrouped_may_share_group_cioc:
                v["G-1"].append(f"{u}: group {next(iter(named))} shares space with ungrouped signals")
        cabs_of = defaultdict(set)
        for p in pos:
            g = p[0].get("IO Group")
            if g:
                cabs_of[g].add(p[1])
        for g, cs in cabs_of.items():
            if max(cs) - min(cs) + 1 != len(cs):
                v["G-1"].append(f"group {g}: cabinets {sorted(cs)} are not contiguous")

    # ---- P-1 spare room -------------------------------------------------------------
    if rules.enabled("R5-spare"):
        need = rules.reserved_baseplates_per_cabinet
        used = defaultdict(set)
        for p in pos:
            used[p[1]].add((p[2], p[3]))
        for cab, bps in used.items():
            empty = rules.baseplates_per_cabinet - len(bps)
            if empty < need:
                v["P-1"].append(f"cabinet #{cab}: {empty} empty baseplates, {need} required")

    # ---- H hardware, M-1 MDB consistency, C-2 controllers ---------------------------------
    mdb_by_tag = {r.tag: r for r in mdb.itertuples(index=False) if r.tag}
    ctl_of = defaultdict(set)
    ctl_ciocs = defaultdict(set)
    for r, cab, cioc, bp, slot in pos:
        ctl_of[cioc].add(r.get("Controller"))
        ctl_ciocs[r.get("Controller")].add(cioc)
        if not rx["controller"].match(r.get("Controller") or ""):
            v["N-1..6"].append(f"controller name '{r.get('Controller')}' does not match pattern")
        if not rx["system_cabinet"].match(r.get("System Cabinet") or ""):
            v["N-1..6"].append(f"system cabinet name '{r.get('System Cabinet')}' does not match pattern")
        if not rx["charm_slot"].match(r.get("CHARM Address") or ""):
            v["N-1..6"].append(f"CHARM address '{r.get('CHARM Address')}' does not match pattern")
        if r.get("Row Kind") != "Signal":
            continue
        m = mdb_by_tag.get(r.get("Tag"))
        if m is None:
            v["M-1"].append(f"{r.get('Tag')}: allocated but not in the MDB")
            continue
        for col, mv in [("IO Type", m.io_type), ("Cable", m.cable), ("IO Group", m.group), ("Segregation", m.seg)]:
            a = (r.get(col) or "").upper()
            b = (mv or "").upper()
            if b and a != b:  # blank MDB group/seg may be inherited from the cable (warning TQ)
                v["M-1"].append(f"{r['Tag']}: {col} '{r.get(col)}' differs from MDB '{mv}'")
        if str(int(float(r["Pair"]))) != re.sub(r"\D", "", str(m.pair)):
            v["M-1"].append(f"{r['Tag']}: pair differs from MDB")
        if rules.enabled("R6-hardware"):
            key = str(m.io_type).strip().upper().replace("_", "-").replace(" ", "-")
            key = rules.io_type_aliases.get(key, key)
            row = next((h for h in rules.hardware if key in h.io_types), None)
            if row is None or (r.get("CHARM Type"), r.get("Terminal Block")) != (row.charm, row.terminal_block):
                exp = (row.charm, row.terminal_block) if row else "no rule"
                v["H-1..6"].append(f"{r['Tag']}: {r.get('CHARM Type')} / {r.get('Terminal Block')} (expected {exp})")
    for cioc, cs in ctl_of.items():
        if len(cs) != 1:
            v["C-2"].append(f"{cioc}: assigned to {len(cs)} controllers")
    for ctl, cs in ctl_ciocs.items():
        if len(cs) > rules.max_ciocs_per_controller:
            v["C-2"].append(f"{ctl}: {len(cs)} CIOCs > {rules.max_ciocs_per_controller}")

    report = []
    for rid, desc in CHECKS:
        items = v.get(rid, [])
        report.append({"Rule": rid, "Check": desc, "Result": "PASS" if not items else "FAIL",
                       "Violations": len(items), "Examples": " | ".join(items[:5])})
    return report


def total_violations(report: list[dict]) -> int:
    return sum(r["Violations"] for r in report)
