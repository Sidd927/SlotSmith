"""Reproducible benchmark on SYNTHETIC MDBs. Writes artifacts/benchmarks.json.

    .venv/bin/python scripts/benchmark.py

Results describe this machine and these generated datasets only; they are not
evidence about the organiser's hidden test.
"""
from __future__ import annotations

import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slotsmith.generator import generate, make_revision  # noqa: E402
from slotsmith.ingest import read_mdb  # noqa: E402
from slotsmith.pipeline import run  # noqa: E402
from slotsmith.revision import impact_report, revise  # noqa: E402
from slotsmith.rules import default_ruleset  # noqa: E402

OUT = Path(__import__("os").environ.get("SLOTSMITH_BENCH_DIR", ROOT / "artifacts" / "bench"))
OUT.mkdir(parents=True, exist_ok=True)
R = default_ruleset()


def machine():
    try:
        cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        mem = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)) // 2**30
    except Exception:
        cpu, mem = platform.processor(), None
    return {"cpu": cpu, "ram_gb": mem, "python": platform.python_version(), "os": platform.platform()}


def scale_runs():
    out = []
    for n in [500, 2000, 10000, 20000]:
        for seed in [1, 2, 3]:
            g = generate(n, seed=seed)
            p = OUT / f"mdb_{n}_{seed}.xlsx"
            g.df.to_excel(p, index=False)
            t0 = time.perf_counter()
            res = run([p], R, OUT / f"alloc_{n}_{seed}.xlsx")
            wall = time.perf_counter() - t0
            out.append({"signals_target": n, "seed": seed, **res.metrics,
                        "exact_bp_per_group": res.allocation.lower_bounds.get("baseplates_exact_per_group"),
                        **{k: round(v, 3) for k, v in res.timings.items()}, "wall_s": round(wall, 2)})
            print("scale", n, seed, out[-1]["violations"], out[-1]["wall_s"], flush=True)
    return out


def tq_recall():
    out = []
    for seed in [1, 2, 3]:
        g = generate(10000, seed=100 + seed, inject_errors=27)
        p = OUT / f"mdb_err_{seed}.xlsx"
        g.df.to_excel(p, index=False)
        res = run([p], R, OUT / f"alloc_err_{seed}.xlsx")
        hit = sum(any(i["tag"] in q.tags or i["cable"] in q.cables for q in res.tqs if q.severity == "blocking")
                  for i in g.injected)
        out.append({"seed": 100 + seed, "injected": len(g.injected), "detected": hit,
                    "coverage_pct": res.metrics["coverage_pct"], "violations": res.metrics["violations"]})
        print("tq", out[-1], flush=True)
    return out


def revisions():
    out = []
    for n in [2000, 10000]:
        for seed in [1, 2, 3, 4, 5]:
            g = generate(n, seed=200 + seed)
            pa = OUT / f"revA_{n}_{seed}.xlsx"
            g.df.to_excel(pa, index=False)
            a = run([pa], R, None)
            b_df = make_revision(g.df, seed=300 + seed)
            pb = OUT / f"revB_{n}_{seed}.xlsx"
            b_df.to_excel(pb, index=False)
            mdb_b = read_mdb([pb]).df
            t0 = time.perf_counter()
            rr = revise(a.rows, mdb_b, R)
            t_rev = time.perf_counter() - t0
            s = run(None, R, None, df=mdb_b)
            _, ms = impact_report(a.rows, s.rows)
            out.append({"signals": n, "seed": seed, "moved_incremental": rr.metrics["moved"],
                        "moved_from_scratch": ms["moved"], "added": rr.metrics["added"],
                        "deleted": rr.metrics["deleted"], "modified_in_place": rr.metrics["modified_in_place"],
                        "violations_incremental": rr.metrics["violations"], "violations_scratch": s.metrics["violations"],
                        "cpsat_used": bool(rr.metrics["cpsat_repairs"]), "fallback": rr.metrics["fallback_full_reallocation"],
                        "cpsat_windows": [(w.get("window"), w.get("status"), w.get("wall_s")) for w in rr.metrics["cpsat_repairs"]],
                        "cpsat_accepted_optimal": rr.metrics["cpsat_accepted_optimal"],
                        "cpsat_accepted_feasible_only": rr.metrics["cpsat_accepted_feasible_only"],
                        "tqs": rr.metrics["tqs"], "capacity_unplaced": len(rr.metrics["capacity_unplaced"]),
                        "revise_s": round(t_rev, 2)})
            print("rev", out[-1], flush=True)
    return out


if __name__ == "__main__":
    t = time.time()
    res = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "machine": machine(),
           "note": "SYNTHETIC data only; default rule set (PS #02 rulebook, 10% spare, CIOC-level A/B and group isolation)"}
    res["scale"] = scale_runs()
    res["tq_recall"] = tq_recall()
    res["revisions"] = revisions()
    sc = [r for r in res["scale"]]
    res["summary"] = {
        "max_violations": max(r["violations"] for r in sc),
        "min_coverage_pct": min(r["coverage_pct"] for r in sc),
        "baseplates_over_lb_max": max(r["baseplates"] - r["lb_baseplates"] for r in sc),
        "baseplates_over_exact_max": max(r["baseplates"] - r["exact_bp_per_group"] for r in sc),
        "wall_20k_median_s": statistics.median(r["wall_s"] for r in sc if r["signals_target"] == 20000),
        "allocate_20k_median_s": statistics.median(r["allocate_s"] for r in sc if r["signals_target"] == 20000),
        "tq_detected": sum(r["detected"] for r in res["tq_recall"]),
        "tq_injected": sum(r["injected"] for r in res["tq_recall"]),
        "rev_moved_incremental_total": sum(r["moved_incremental"] for r in res["revisions"]),
        "rev_moved_scratch_total": sum(r["moved_from_scratch"] for r in res["revisions"]),
        "rev_violations_max": max(r["violations_incremental"] for r in res["revisions"]),
        "rev_cases": len(res["revisions"]),
        "rev_cpsat_cases": sum(r["cpsat_used"] for r in res["revisions"]),
        "rev_fallback_cases": sum(r["fallback"] for r in res["revisions"]),
        "rev_cpsat_windows_accepted_optimal": sum(r["cpsat_accepted_optimal"] for r in res["revisions"]),
        "rev_cpsat_windows_accepted_feasible_only": sum(r["cpsat_accepted_feasible_only"] for r in res["revisions"]),
        "rev_time_max_s": max(r["revise_s"] for r in res["revisions"]),
    }
    res["total_s"] = round(time.time() - t, 1)
    dest = Path(__import__("os").environ.get("SLOTSMITH_BENCH_JSON", ROOT / "artifacts" / "benchmarks.json"))
    dest.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["summary"], indent=1))
