"""Audit: where does 'baseplates above lower bound' come from on benchmark instances?

Per group, exact minimum baseplates = big-cable baseplates + min over subsets N_a of the neutral
cables of ceil((A+N_a)/12) + ceil((B+N_b)/12). This uses the lemma that any multiset of
{2,6,12} items with total T fits in ceil(T/12) bins (proved in architecture.md section 4 and checked
exhaustively in audit_ffd_exact.py). Also: random larger groups vs CP-SAT exact.
"""
import json, math, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from slotsmith.generator import generate
from slotsmith.validate import validate
from slotsmith.allocator import allocate, build_units, lower_bounds
from slotsmith.rules import default_ruleset
from audit_ffd_exact import exact_bins, alloc_bins
sys.path.insert(0, str(ROOT / "tests"))
from test_core import _canon

R = default_ruleset()

def exact_group(bl):
    big = sum(math.ceil(b.size / 12) for b in bl if b.size > 12)
    A = sum(b.size for b in bl if b.size <= 12 and b.seg == "A")
    B = sum(b.size for b in bl if b.size <= 12 and b.seg == "B")
    N = [b.size for b in bl if b.size <= 12 and not b.seg]
    sums = {0}
    for s in N:
        sums |= {x + s for x in sums}
    tot = sum(N)
    if A == 0 and B == 0:
        return big + math.ceil(tot / 12)
    return big + min(math.ceil((A + na) / 12) + math.ceil((B + tot - na) / 12) for na in sums)

out = {"benchmark_instances": []}
for n in [500, 2000, 10000, 20000]:
    for seed in [1, 2, 3]:
        val = validate(_canon(generate(n, seed=seed).df), R)
        res = allocate(val.blocks, R)
        groups = {}
        for b in val.blocks:
            groups.setdefault(b.group, []).append(b)
        ex = sum(exact_group(bl) for bl in groups.values())
        out["benchmark_instances"].append({"n": n, "seed": seed, "allocator_bp": res.stats["baseplates"],
                                           "exact_bp": ex, "reported_lb": res.lower_bounds["baseplates"]})
        print(out["benchmark_instances"][-1], flush=True)

random.seed(5)
worse, st_count = [], {}
for k in range(150):
    items = []
    for side in ["A", None, "B"]:
        for sz in [2, 6, 12]:
            items += [(sz, side)] * random.randint(0, 5)
    if not items:
        continue
    e, st = exact_bins(items)
    st_count[st] = st_count.get(st, 0) + 1
    a = alloc_bins(items)
    if a != e:
        worse.append({"items": items, "allocator": a, "exact": e, "status": st})
out["random_larger_groups"] = {"cases": 150, "exact_status": st_count, "allocator_worse": len(worse), "examples": worse[:3]}
print(out["random_larger_groups"])
(ROOT / "artifacts" / "audit" / "lb_gap.json").write_text(json.dumps(out, indent=1))
