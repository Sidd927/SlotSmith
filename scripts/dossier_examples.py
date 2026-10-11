"""Compute the worked examples quoted in docs/SlotSmith_Technical_Dossier.md with the real engine.

    .venv/bin/python scripts/dossier_examples.py            # fast examples (A/B interaction, verifier mutations)
    .venv/bin/python scripts/dossier_examples.py --revision # also the CP-SAT revision example (about 20-60 s)

Everything printed here is SYNTHETIC data. Output: docs/assets/slotsmith/data/*.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import pandas as pd  # noqa: E402

from slotsmith.generator import generate, make_revision  # noqa: E402
from slotsmith.pipeline import run  # noqa: E402
from slotsmith.revision import impact_report, revise  # noqa: E402
from slotsmith.rules import default_ruleset  # noqa: E402
from slotsmith.verifier import load_allocation, verify  # noqa: E402
from test_core import _canon, mdb, run_df  # noqa: E402

OUT = ROOT / "docs" / "assets" / "slotsmith" / "data"
OUT.mkdir(parents=True, exist_ok=True)
R = default_ruleset()


def loc(r):
    return {k: r[k] for k in ("Tag", "Cable", "Pair", "Segregation", "Marshalling Cabinet", "CIOC", "Baseplate", "Slot", "Status")}


def ab_interaction():
    """Two 6-pair cables: one side A, one side B (same group) versus the same two cables without a side."""
    rows_ab = [[f"A{i}", "AI", "CBL-A", 6, i, "G1", "A"] for i in range(1, 7)] + \
              [[f"B{i}", "AI", "CBL-B", 6, i, "G1", "B"] for i in range(1, 7)]
    rows_n = [[f"A{i}", "AI", "CBL-A", 6, i, "G1", None] for i in range(1, 7)] + \
             [[f"B{i}", "AI", "CBL-B", 6, i, "G1", None] for i in range(1, 7)]
    out = {}
    for name, rows in (("with_A_B_sides", rows_ab), ("without_sides", rows_n)):
        res = run_df(mdb(rows))
        sig = [r for r in res.rows if r["Row Kind"] == "Signal"]
        out[name] = {"metrics": {k: res.metrics[k] for k in ("signals_allocated", "ciocs", "baseplates", "violations")},
                     "cables": {c: sorted({(r["CIOC"], r["Baseplate"]) for r in sig if r["Cable"] == c}) for c in ("CBL-A", "CBL-B")},
                     "slots": {c: [int(r["Slot"]) for r in sig if r["Cable"] == c] for c in ("CBL-A", "CBL-B")}}
    return out


def verifier_mutations():
    g = generate(600, seed=9)
    p = OUT / "_tmp_mdb.xlsx"
    g.df.to_excel(p, index=False)
    res = run([p], R, OUT / "_tmp_alloc.xlsx")
    rows, df = load_allocation(OUT / "_tmp_alloc.xlsx"), res.mdb.df
    base = {c["Rule"]: c["Violations"] for c in verify(rows, df, R)}
    cases = {}

    def check(name, mut_rows, rules=R):
        rep = verify(mut_rows, df, rules)
        cases[name] = [{"rule": c["Rule"], "violations": c["Violations"], "example": c["Examples"][:160]} for c in rep if c["Result"] == "FAIL"]

    r1 = copy.deepcopy(rows)
    s = [r for r in r1 if r["Row Kind"] == "Signal"]
    for k in ["Marshalling Cabinet", "CIOC", "Baseplate", "Slot", "CHARM Address"]:
        s[1][k] = s[0][k]
    check("double_booked_slot (second signal copied onto the first signal's slot)", r1)
    r2 = copy.deepcopy(rows)
    next(r for r in r2 if r["Terminal Block"] == "Fused-injected-power")["Terminal Block"] = "Standard"
    check("wrong_terminal_block (fused DO block changed to Standard)", r2)
    r3 = copy.deepcopy(rows)
    a = next(r for r in r3 if r["Segregation"] == "A")
    b = next(r for r in r3 if r["Segregation"] == "B")
    b["CIOC"], b["Baseplate"] = a["CIOC"], a["Baseplate"]
    check("A_and_B_in_one_CIOC (a B signal moved to an A baseplate name)", r3)
    r4 = [r for r in rows if r["Tag"] != a["Tag"]]
    check("missing_signal (one allocated signal row deleted)", r4)
    r5 = copy.deepcopy(rows)
    r = next(r for r in r5 if r["Row Kind"] == "Signal" and r["Pair"] == "2")
    r["Slot"] = str(int(r["Slot"]) + 5) if int(r["Slot"]) <= 7 else str(int(r["Slot"]) - 5)
    check("cable_not_side_by_side (pair 2 moved five slots)", r5)
    strict = default_ruleset()
    strict.spare_percent = 60.0
    check("spare_budget (rule set asks for 60 % empty baseplates, workbook built with 10 %)", copy.deepcopy(rows), strict)
    r7 = copy.deepcopy(rows)
    for r in r7:
        if r["Row Kind"] == "Signal":
            r["Marshalling Cabinet"] = "WRONG-NAME"
            break
    check("unparseable_name (cabinet name does not match the naming pattern)", r7)
    return {"dataset": "SYNTHETIC 600 signals, seed 9", "clean_violations_per_rule": base, "mutations": cases}


def revision_example(n_signals=2000, seed=1):
    """Same construction as scripts/benchmark.py revisions(): generate(200+seed) -> make_revision(300+seed)."""
    g = generate(n_signals, seed=200 + seed)
    a = run_df(_canon(g.df))
    b = _canon(make_revision(g.df, seed=300 + seed))
    t0 = time.perf_counter()
    rr = revise(a.rows, b, R)
    dt = time.perf_counter() - t0
    scratch = run_df(b)
    _, ms = impact_report(a.rows, scratch.rows)
    m = rr.metrics
    wins = [{k: w.get(k) for k in ("group", "window", "status", "proven_exact", "objective", "bound", "moved_signals",
                                    "moved_signals_lower_bound", "wall_s")} for w in m["cpsat_repairs"]]
    moved_rows = [r for r in rr.impact if r["Change"] == "Moved"][:5]
    return {"dataset": f"SYNTHETIC {n_signals} signals; generate(seed={200 + seed}); make_revision(seed={300 + seed})",
            "rev_a": {"signals_allocated": a.metrics["signals_allocated"], "cabinets": a.metrics["cabinets"],
                      "ciocs": a.metrics["ciocs"], "baseplates": a.metrics["baseplates"]},
            "rev_b_input_rows": int(len(b)),
            "revision_aware": {k: m[k] for k in ("moved", "added", "deleted", "modified_in_place", "unchanged", "violations",
                                                  "fallback_full_reallocation", "cpsat_accepted_optimal", "cpsat_accepted_feasible_only")}
            | {"cabinets_hit": len(m["cabinets_hit"]), "revise_seconds": round(dt, 1)},
            "full_reallocation_same_rev_b": {"moved": ms["moved"], "added": ms["added"], "deleted": ms["deleted"], "modified_in_place": ms["modified_in_place"],
                                              "unchanged": ms["unchanged"], "violations": scratch.metrics["violations"]},
            "cpsat_windows": wins, "sample_moved_rows": moved_rows}


def input_records():
    """Ten ILLUSTRATIVE rows (fabricated tags) run through the real validator: which are accepted, which become TQs."""
    rows = [["ILL-001", "AI", "CBL-X1", 12, 1, "G1", "A"], ["ILL-002", "DI", "CBL-X1", 12, 2, "G1", "A"],
            ["ILL-003", None, "CBL-X2", 6, 1, "G2", None], ["ILL-004", "PULSE-XYZ", "CBL-X3", 6, 1, None, None],
            ["ILL-005", "AI", "CBL-X4", 6, 7, None, None], ["ILL-006", "AI", "CBL-X5", 6, 1, "G3", "C"],
            ["ILL-007", "AI", "CBL-X6", 6, 1, None, None], ["ILL-007", "DI", "CBL-X6", 6, 2, None, None],
            ["ILL-008", "AI", "CBL-X7", 2, 1, "G1", "A"], ["ILL-009", "DI", "CBL-X7", 2, 2, "G1", "B"]]
    r = run_df(mdb(rows))
    return {"input_columns": ["Tag", "IO", "Cable", "Cable Size", "Pair", "Grp", "Seg"], "input_rows": rows,
            "tqs": [{"id": q.id, "severity": q.severity, "rule": q.rule_ref, "message": q.message, "sources": q.sources} for q in r.tqs],
            "row_status": [{"tag": x["Tag"], "status": x["Status"], "tq": x["TQ Ref"]} for x in r.rows if x["Tag"]],
            "violations": r.metrics["violations"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--revision", action="store_true")
    args = ap.parse_args()
    res = {"ab_interaction": ab_interaction(), "verifier_mutations": verifier_mutations(), "input_records": input_records()}
    (OUT / "examples_fast.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str)[:6000])
    for f in ("_tmp_mdb.xlsx", "_tmp_alloc.xlsx"):
        (OUT / f).unlink(missing_ok=True)
    if args.revision:
        rv = revision_example()
        (OUT / "example_revision.json").write_text(json.dumps(rv, indent=1, default=str))
        print(json.dumps(rv, indent=1, default=str))
