"""Mixed A/B (and mixed IO-group) cables when the controlling rule is switched OFF.

Established (rule register S-1/S-2, G-3): with R2 on, a cable carrying both A and B is blocked with a TQ; M-1 requires the
exported rows to equal the MDB. NOT established: what a mixed cable should do when R2 (or R1) is off. Before this change the
allocator took `next(iter(set))` as the cable's side (string hash order -> different results per process) and the export wrote
that side on every signal row, so M-1 failed on a rewritten value.

Implemented (no new engineering rule): a mixed cable has no single side/group, so it is placed as an unsided/ungrouped cable
(deterministic), every signal row keeps its OWN side/group from the MDB, a warning TQ (S-2 / G-3) records that separation is
not enforced for it, and S-1/G-1 are reported SKIPPED. M-1 still checks every row against the MDB and is not suppressed.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from slotsmith.pipeline import run
from slotsmith.revision import revise
from slotsmith.rules import default_ruleset
from slotsmith.verifier import SKIPPED, verify
from tests.test_core import mdb

ROOT = Path(__file__).resolve().parents[1]
MIXED_AB = [
    ["T1", "AI", "CBL-1", 6, 1, "G1", "A"], ["T2", "AI", "CBL-1", 6, 2, "G1", "B"], ["T3", "AI", "CBL-1", 6, 3, "G1", None],
    ["T4", "AI", "CBL-1", 6, 4, "G1", "A"], ["T5", "AI", "CBL-2", 6, 1, "G1", "A"], ["T6", "AI", "CBL-3", 6, 1, "G1", "B"],
]
MIXED_GROUP = [
    ["U1", "AI", "CBL-1", 6, 1, "G1", None], ["U2", "AI", "CBL-1", 6, 2, "G2", None], ["U3", "AI", "CBL-1", 6, 3, None, None],
    ["U4", "AI", "CBL-2", 6, 1, "G1", None],
]


def _rules(*off, level=None):
    r = copy.deepcopy(default_ruleset())
    for t in r.toggles:
        if t.id in off:
            t.enabled = False
    if level:
        r.group_isolation_level = level
    return r


def _by_tag(res, col):
    return {r["Tag"]: r[col] for r in res.rows if r["Row Kind"] == "Signal" and r["Status"] == "Allocated"}


def test_mixed_ab_cable_keeps_each_signals_own_side_and_m1_passes():
    res = run(None, _rules("R2-segregation"), None, df=mdb(MIXED_AB))
    assert _by_tag(res, "Segregation") == {"T1": "A", "T2": "B", "T3": "", "T4": "A", "T5": "A", "T6": "B"}
    checks = {c["Rule"]: c for c in res.check}
    assert checks["M-1"]["Result"] == "PASS" and checks["S-1"]["Result"] == SKIPPED
    w = [q for q in res.tqs if q.rule_ref == "S-2"]
    assert len(w) == 1 and w[0].severity == "warning" and "separation is not enforced" in w[0].message and w[0].cables == ["CBL-1"]


def test_mixed_ab_cable_is_still_blocked_when_r2_is_on():
    res = run(None, default_ruleset(), None, df=mdb(MIXED_AB))
    q = [q for q in res.tqs if q.rule_ref == "S-2"]
    assert len(q) == 1 and q[0].severity == "blocking"
    assert not any(r["Cable"] == "CBL-1" and r["Status"] == "Allocated" for r in res.rows)


def test_m1_still_catches_a_rewritten_side():
    res = run(None, _rules("R2-segregation"), None, df=mdb(MIXED_AB))
    rows = [{k: (None if v in ("", None) else str(v)) for k, v in r.items()} for r in res.rows]
    next(r for r in rows if r["Tag"] == "T2")["Segregation"] = "A"          # genuine violation
    m1 = next(c for c in verify(rows, res.mdb.df, _rules("R2-segregation")) if c["Rule"] == "M-1")
    assert m1["Result"] == "FAIL" and "T2" in m1["Examples"]


def test_mixed_group_cable_with_isolation_off_keeps_per_signal_groups():
    for rules in (_rules("R1-grouping"), _rules(level="none")):
        res = run(None, rules, None, df=mdb(MIXED_GROUP))
        assert _by_tag(res, "IO Group") == {"U1": "G1", "U2": "G2", "U3": "", "U4": "G1"}
        assert next(c for c in res.check if c["Rule"] == "M-1")["Result"] == "PASS"
        assert any(q.rule_ref == "G-3" and q.severity == "warning" for q in res.tqs)
    assert any(q.rule_ref == "G-3" and q.severity == "blocking" for q in run(None, default_ruleset(), None, df=mdb(MIXED_GROUP)).tqs)


def test_result_does_not_depend_on_hash_order():
    code = ("import json,copy,sys\nsys.path.insert(0,'src'); sys.path.insert(0,'.')\n"
            "from slotsmith.pipeline import run\nfrom tests.test_mixed_cable import _rules, MIXED_AB, MIXED_GROUP, mdb\n"
            "out=[]\nfor rows,rules in ((MIXED_AB,_rules('R2-segregation')),(MIXED_GROUP,_rules('R1-grouping'))):\n"
            "    r=run(None,rules,None,df=mdb(rows))\n"
            "    out.append([(x['Tag'],x['Segregation'],x['IO Group'],x['CIOC'],x['Baseplate'],x['Slot']) for x in r.rows])\n"
            "print(json.dumps(out))")
    outs = []
    for seed in ("0", "1", "2", "3", "7"):
        p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                           env={**os.environ, "PYTHONHASHSEED": seed})
        assert p.returncode == 0, p.stderr[-400:]
        outs.append(p.stdout.strip().splitlines()[-1])
    assert len(set(outs)) == 1


def test_revision_keeps_a_mixed_cable_pinned_and_unchanged():
    rules = _rules("R2-segregation")
    a = run(None, rules, None, df=mdb(MIXED_AB))
    rr = revise(a.rows, mdb(MIXED_AB), rules)                 # identical Rev B
    assert rr.metrics["moved"] == 0 and rr.metrics["added"] == 0 and rr.metrics["deleted"] == 0
    assert _by_tag(rr, "Segregation") == _by_tag(a, "Segregation")
    assert next(c for c in rr.check if c["Rule"] == "M-1")["Result"] == "PASS"
