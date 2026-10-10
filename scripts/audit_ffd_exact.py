"""Audit: allocator baseplate counts vs an exact CP-SAT bin-packing model on exhaustive small cases.

    .venv/bin/python scripts/audit_ffd_exact.py > artifacts/audit/ffd_exact.log

Exact model: items -> bins of capacity 12; a bin may hold A-side or B-side items but not both
(A and B never share a CIOC, hence never a baseplate); neutral items may join either.
Minimise the number of used bins. Independent of allocator.py (shares only the CableBlock dataclass).
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ortools.sat.python import cp_model  # noqa: E402

from slotsmith.allocator import build_units, ffd_pack  # noqa: E402
from slotsmith.model import CableBlock  # noqa: E402
from slotsmith.rules import default_ruleset  # noqa: E402

CAP = 12
R = default_ruleset()


def exact_bins(items: list[tuple[int, str | None]]) -> tuple[int, str]:
    """items: (size, side) with side in {'A','B',None}. Sizes <= 12."""
    n = len(items)
    if n == 0:
        return 0, "OPTIMAL"
    m = cp_model.CpModel()
    nb = n
    x = [[m.NewBoolVar("") for _ in range(nb)] for _ in range(n)]
    used = [m.NewBoolVar("") for _ in range(nb)]
    is_a = [m.NewBoolVar("") for _ in range(nb)]
    is_b = [m.NewBoolVar("") for _ in range(nb)]
    for i in range(n):
        m.AddExactlyOne(x[i])
    for b in range(nb):
        m.Add(sum(items[i][0] * x[i][b] for i in range(n)) <= CAP * used[b])
        m.Add(is_a[b] + is_b[b] <= 1)
        for i in range(n):
            if items[i][1] == "A":
                m.AddImplication(x[i][b], is_a[b])
            elif items[i][1] == "B":
                m.AddImplication(x[i][b], is_b[b])
        if b:
            m.Add(used[b] <= used[b - 1])  # symmetry breaking
    m.Minimize(sum(used))
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = 30
    st = s.Solve(m)
    return int(s.ObjectiveValue()), s.StatusName(st)


def blocks(items):
    return [CableBlock(cable=f"C{i:03d}", size=sz, group="G1", seg=side) for i, (sz, side) in enumerate(items)]


def alloc_bins(items) -> int:
    return sum(u.n_bp for u in build_units(blocks(items), R, "G1"))


def run():
    out = {}
    t0 = time.time()
    # 1. single class, standard sizes: exhaustive counts 0..6 of each of {2, 6, 12}
    worse = []
    n1 = 0
    for c2, c6, c12 in itertools.product(range(7), repeat=3):
        items = [(2, None)] * c2 + [(6, None)] * c6 + [(12, None)] * c12
        if not items:
            continue
        n1 += 1
        e, st = exact_bins(items)
        ffd = len(ffd_pack(blocks(items), CAP))
        assert st == "OPTIMAL"
        if ffd != e:
            worse.append({"counts": [c2, c6, c12], "ffd": ffd, "exact": e})
    out["single_class_standard"] = {"cases": n1, "ffd_worse": len(worse), "examples": worse[:5]}
    print("single class standard sizes:", out["single_class_standard"], flush=True)

    # 2. full group with A / neutral / B sides, standard sizes: exhaustive counts 0..2 per (side, size)
    worse = []
    n2 = 0
    statuses = {}
    for counts in itertools.product(range(3), repeat=9):
        items = []
        for k, (side, sz) in enumerate(itertools.product(["A", None, "B"], [2, 6, 12])):
            items += [(sz, side)] * counts[k]
        if not items:
            continue
        n2 += 1
        e, st = exact_bins(items)
        statuses[st] = statuses.get(st, 0) + 1
        a = alloc_bins(items)
        if a != e:
            worse.append({"items": items, "allocator": a, "exact": e})
    out["group_A_N_B_standard"] = {"cases": n2, "allocator_worse": len(worse), "exact_status": statuses,
                                   "max_excess": max([w["allocator"] - w["exact"] for w in worse], default=0),
                                   "examples": worse[:5]}
    print("group A/N/B standard sizes:", {k: v for k, v in out["group_A_N_B_standard"].items() if k != "examples"}, flush=True)
    for w in worse[:5]:
        print("   e.g.", w, flush=True)

    # 3. non-standard sizes (proof premise fails): single class, sizes {4, 8} and {2, 4, 6, 8, 10}
    for name, sizes, rng in [("sizes_4_8", [4, 8], range(7)), ("sizes_2_4_6_8_10", [2, 4, 6, 8, 10], range(3))]:
        worse = []
        n3 = 0
        for counts in itertools.product(rng, repeat=len(sizes)):
            items = [(sz, None) for sz, c in zip(sizes, counts) for _ in range(c)]
            if not items:
                continue
            n3 += 1
            e, st = exact_bins(items)
            ffd = len(ffd_pack(blocks(items), CAP))
            if ffd != e:
                worse.append({"items": [i[0] for i in items], "ffd": ffd, "exact": e})
        out[name] = {"cases": n3, "ffd_worse": len(worse), "examples": worse[:3]}
        print(name, out[name], flush=True)
    out["wall_s"] = round(time.time() - t0, 1)
    (ROOT / "artifacts" / "audit").mkdir(parents=True, exist_ok=True)
    (ROOT / "artifacts" / "audit" / "ffd_exact.json").write_text(json.dumps(out, indent=1))
    print("wall_s", out["wall_s"])


if __name__ == "__main__":
    run()
