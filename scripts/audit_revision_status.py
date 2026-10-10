"""Audit: same 10 Rev B cases as scripts/benchmark.py; record per-window CP-SAT objective vs bound."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tests"))
from test_core import _canon, run_df
from slotsmith.generator import generate, make_revision
from slotsmith.revision import revise, impact_report
from slotsmith.rules import default_ruleset
R = default_ruleset(); out = []
for n in [2000, 10000]:
    for seed in [1, 2, 3, 4, 5]:
        g = generate(n, seed=200 + seed)
        a = run_df(_canon(g.df))
        b = _canon(make_revision(g.df, seed=300 + seed))
        t = time.perf_counter(); rr = revise(a.rows, b, R); dt = time.perf_counter() - t
        acc = [w for w in rr.metrics["cpsat_repairs"] if w["status"] in ("OPTIMAL", "FEASIBLE")]
        out.append({"signals": n, "seed": seed, "moved": rr.metrics["moved"], "violations": rr.metrics["violations"],
                    "fallback": rr.metrics["fallback_full_reallocation"], "revise_s": round(dt, 1),
                    "windows": [{k: w.get(k) for k in ["window", "status", "wall_s", "proven_exact", "moved_signals",
                                                        "moved_signals_lower_bound"]} for w in rr.metrics["cpsat_repairs"]],
                    "accepted": len(acc), "accepted_proven_exact": sum(1 for w in acc if w.get("proven_exact"))})
        print(out[-1], flush=True)
s = {"cases": len(out), "accepted_windows": sum(o["accepted"] for o in out),
     "accepted_proven_exact": sum(o["accepted_proven_exact"] for o in out),
     "moved_total": sum(o["moved"] for o in out), "violations_max": max(o["violations"] for o in out),
     "fallbacks": sum(o["fallback"] for o in out), "max_revise_s": max(o["revise_s"] for o in out)}
print(s)
(ROOT / "artifacts" / "audit" / "revision_status.json").write_text(json.dumps({"summary": s, "cases": out}, indent=1))
