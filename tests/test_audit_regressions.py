"""Regression tests for defects found in the 10 Oct 2026 audit, plus exact-solver checks (small)."""
import itertools
import math

import pytest

from slotsmith import revision as rev
from slotsmith.allocator import allocate, build_units, ffd_pack
from slotsmith.generator import generate, make_revision
from slotsmith.model import CableBlock
from slotsmith.rules import default_ruleset
from slotsmith.verifier import verify
from test_core import _canon, mdb, run_df

R = default_ruleset()


def test_oversized_cable_does_not_unplace_its_group():
    r = default_ruleset(); r.spare_percent = 95.0          # one usable baseplate per cabinet
    rows = [[f"A{i}", "AI", "CA", 6, i, "G1", "A"] for i in range(1, 6)] + \
           [[f"B{i}", "AI", "C24", 24, i, "G1", "B"] for i in range(1, 20)]
    res = run_df(mdb(rows), r)
    status = {}
    for x in res.rows:
        if x["Tag"]:
            status.setdefault(x["Tag"], []).append(x["Status"])
    assert all(len(v) == 1 for v in status.values())
    assert set(status["A1"]) == {"Allocated"} and set(status["B1"]) == {"Not allocated"}
    assert all(x["TQ Ref"].startswith("TQ-") for x in res.rows if x["Status"] == "Not allocated")
    assert res.metrics["cabinets"] == 1                      # no empty cabinet left behind


def test_verifier_flags_tag_both_allocated_and_not_allocated():
    res = run_df(mdb([["T1", "AI", "C1", 6, 1, None, None]]))
    rows = [{k: (None if v in ("", None) else str(v)) for k, v in r.items()} for r in res.rows]
    rows.append({**rows[0], "Status": "Not allocated", "Slot": None, "TQ Ref": "TQ-9999"})
    rep = verify(rows, res.mdb.df, R)
    assert any(c["Rule"] == "Q-1" and c["Result"] == "FAIL" for c in rep)


def test_revision_fallback_raises_warning_tq(monkeypatch):
    g = generate(600, seed=3)
    a = run_df(_canon(g.df))
    b = _canon(make_revision(g.df, seed=4, add_frac=0.2))
    monkeypatch.setattr(rev, "_cpsat_repair", lambda failed, *a_, **k: (failed, [{"status": "INFEASIBLE"}]))
    monkeypatch.setattr(rev, "_free_run", lambda slots, size: None)    # force greedy failure -> fallback
    rr = rev.revise(a.rows, b, R)
    assert rr.metrics["fallback_full_reallocation"]
    assert any(q.severity == "warning" and q.rule_ref == "R-2" for q in rr.tqs)
    assert rr.metrics["violations"] == 0


def test_revision_oversized_new_cable_gets_capacity_tq_without_fallback():
    base = [[f"T{i}", "AI", "C1", 12, i, None, None] for i in range(1, 11)]
    a = run_df(mdb(base))
    b = mdb(base + [[f"X{i}", "AI", "CX", 120, i, None, None] for i in range(1, 5)])
    rr = rev.revise(a.rows, b, R)
    assert not rr.metrics["fallback_full_reallocation"] and rr.metrics["moved"] == 0
    assert "CX" in rr.metrics["capacity_unplaced"]
    assert any(q.category == "capacity" and "CX" in q.cables for q in rr.tqs)


def _exact_formula(items):
    A = sum(s for s, side in items if side == "A")
    B = sum(s for s, side in items if side == "B")
    N = [s for s, side in items if side is None]
    sums = {0}
    for x in N:
        sums |= {v + x for v in sums}
    if not A and not B:
        return math.ceil(sum(N) / 12)
    return min(math.ceil((A + na) / 12) + math.ceil((B + sum(N) - na) / 12) for na in sums)


def test_allocator_matches_exact_group_minimum_small_exhaustive():
    """Counts 0..1 per (side, size); full CP-SAT exhaustive run is scripts/audit_ffd_exact.py."""
    for counts in itertools.product(range(2), repeat=9):
        items = []
        for k, (side, sz) in enumerate(itertools.product(["A", None, "B"], [2, 6, 12])):
            items += [(sz, side)] * counts[k]
        blocks = [CableBlock(cable=f"C{i}", size=s, group="G", seg=side) for i, (s, side) in enumerate(items)]
        assert sum(u.n_bp for u in build_units(blocks, R, "G")) == _exact_formula(items)


def test_reported_exact_minimum_equals_allocation_on_generated_mdb():
    from slotsmith.validate import validate
    val = validate(_canon(generate(3000, seed=8).df), R)
    res = allocate(val.blocks, R)
    assert res.stats["baseplates"] == res.lower_bounds["baseplates_exact_per_group"]
