"""Audit: capacity-model and failure-path edge cases. Prints PASS/FAIL per check."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tests"))
from test_core import mdb, run_df, _canon
from slotsmith.rules import default_ruleset
from slotsmith.revision import revise
from slotsmith.generator import generate, make_revision
from collections import Counter

def report(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

# a. capacity failure mid-group must not leave a cable both allocated and 'Not allocated'
r = default_ruleset(); r.spare_percent = 95.0      # 31 of 32 baseplates reserved -> 1 usable
rows = [[f"A{i}", "AI", "CA", 6, i, "G1", "A"] for i in range(1, 6)] + \
       [[f"B{i}", "AI", "C24", 24, i, "G1", "B"] for i in range(1, 20)]
res = run_df(mdb(rows), r)
st = Counter((x["Tag"], x["Status"]) for x in res.rows if x["Tag"])
dup = [t for t in {t for t, _ in st} if sum(1 for (tt, s) in st if tt == t) > 1]
cap_tqs = [q for q in res.tqs if q.category == "capacity"]
report("a. no tag both allocated and not-allocated", not dup, f"dups={dup[:3]}")
report("a. capacity failure raises traceable TQ", bool(cap_tqs) and all(q.sources for q in cap_tqs),
       f"capacity TQs={[ (q.id, q.cables) for q in cap_tqs]}")
report("a. verifier still 0 violations", res.metrics["violations"] == 0, str({c['Rule']: c['Violations'] for c in res.check if c['Violations']}))
nalloc = [x for x in res.rows if x["Status"] == "Not allocated"]
report("a. unplaced rows reference a real TQ id", all(x["TQ Ref"].startswith("TQ-") for x in nalloc), str({x['TQ Ref'] for x in nalloc}))

# b. cable larger than a CIOC (120 pairs)
res = run_df(mdb([[f"T{i}", "AI", "CBIG", 120, i, None, None] for i in range(1, 101)]))
report("b. 120-pair cable -> capacity TQ, 100% coverage", res.metrics["coverage_pct"] == 100.0 and
       any(q.category == "capacity" for q in res.tqs) and res.metrics["violations"] == 0,
       f"cov={res.metrics['coverage_pct']} tq={[q.rule_ref for q in res.tqs]}")

# c. non-standard sizes 16 and 36 (Emerson mentions 36-core cables)
res = run_df(mdb([[f"S{i}", "AI", "C16", 16, i, None, None] for i in range(1, 15)] +
                 [[f"T{i}", "DI", "C36", 36, i, None, None] for i in range(1, 33)]))
bp = {x["Cable"]: sorted({x["Baseplate"] for x in res.rows if x["Cable"] == x["Cable"] and x["Slot"]}) for x in res.rows}
report("c. 16- and 36-pair cables allocate with 0 violations", res.metrics["violations"] == 0,
       f"baseplates used={res.metrics['baseplates']} (16-pair uses 2 bp, 4 slots unusable by others)")

# d. allow_cable_straddle=True: does the allocator use it?
r = default_ruleset(); r.allow_cable_straddle = True
res = run_df(mdb([[f"A{i}", "AI", f"C{i}", 6, 1, None, None] for i in range(1, 4)]), r)
report("d. allow_cable_straddle is honoured by the allocator", False,
       "allocator never straddles (parameter only relaxes the verifier) -> document, conservative")

# e. revision under cabinet-level segregation / isolation
for lvl in [("segregation_level", "cabinet"), ("group_isolation_level", "cabinet")]:
    r = default_ruleset(); setattr(r, *lvl)
    g = generate(2000, seed=41)
    a = run_df(_canon(g.df), r)
    rr = revise(a.rows, _canon(make_revision(g.df, seed=42)), r)
    report(f"e. revision with {lvl[0]}={lvl[1]}: 0 violations", rr.metrics["violations"] == 0 and a.metrics["violations"] == 0,
           f"A viol={a.metrics['violations']} B viol={rr.metrics['violations']} moved={rr.metrics['moved']} "
           f"fallback={rr.metrics['fallback_full_reallocation']} fails={[c['Rule'] for c in rr.check if c['Violations']]}")

# f. revision that cannot be repaired -> fallback; are TQs produced for anything unplaced?
r = default_ruleset()
base = [[f"T{i}", "AI", f"C{i}", 12, 1, None, None] for i in range(1, 29)]       # 28 baseplates = full cabinet budget
a = run_df(mdb(base), r)
b = mdb(base + [[f"N{i}", "AI", f"CN{i}", 12, 1, None, None] for i in range(1, 3)])
rr = revise(a.rows, b, r)
statuses = [x.get("status") for x in rr.metrics["cpsat_repairs"]]
report("f. revision needing a new cabinet succeeds with 0 violations", rr.metrics["violations"] == 0,
       f"moved={rr.metrics['moved']} cpsat={statuses} fallback={rr.metrics['fallback_full_reallocation']}")
nal = [x for x in rr.rows if x["Status"] == "Not allocated"]
report("f. revision: any unplaced signal has a TQ object", not nal or all(x["TQ Ref"].startswith("TQ-") for x in nal), f"{len(nal)} unplaced")
