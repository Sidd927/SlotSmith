"""End-to-end run: MDB(s) -> validation/TQs -> allocation -> workbook -> independent verification."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import __version__
from .allocator import AllocationResult, allocate
from .export import add_blocked_rows, build_rows, summary, write_workbook
from .ingest import MDB, read_mdb
from .model import TQ
from .rules import RuleSet
from .validate import ValidationResult, validate
from .verifier import load_allocation, total_violations, verify


@dataclass
class RunResult:
    mdb: MDB
    validation: ValidationResult
    allocation: AllocationResult
    rows: list[dict]
    summary: list[dict]
    tqs: list[TQ]
    check: list[dict]
    timings: dict[str, float]
    metrics: dict
    out_path: Path | None


def capacity_tqs(val: ValidationResult, result: AllocationResult, start: int) -> list[TQ]:
    out = []
    for i, (cable, reason) in enumerate(result.unplaced.items()):
        b = next(x for x in val.blocks if x.cable == cable)
        out.append(TQ(id=f"TQ-{start + i:04d}", severity="blocking", category="capacity", rule_ref="C-1",
                      message=f"Cable {cable} could not be placed: {reason}",
                      tags=[s.tag for s in b.signals.values()], cables=[cable],
                      sources=[s.src for s in b.signals.values()][:10],
                      suggested_action="Review the capacity rules or split the cable"))
    return out


def metrics_for(rows, val, result, check, df) -> dict:
    sig_rows = [r for r in rows if r["Row Kind"] == "Signal"]
    allocated = sum(1 for r in sig_rows if r["Status"] == "Allocated")
    tq_rows = sum(1 for r in sig_rows if r["Status"] != "Allocated")
    return {
        "mdb_rows": int(len(df)),
        "signals_allocated": allocated,
        "signals_with_tq": tq_rows,
        "coverage_pct": round(100.0 * (allocated + tq_rows) / max(1, len(df)), 3),
        "tqs": len(val.tqs) + len(result.unplaced),
        "blocking_tqs": sum(1 for t in val.tqs if t.severity == "blocking") + len(result.unplaced),
        "cabinets": result.stats["cabinets"], "ciocs": result.stats["ciocs"], "baseplates": result.stats["baseplates"],
        "lb_baseplates": result.lower_bounds["baseplates"], "lb_cabinets": result.lower_bounds["cabinets"],
        "violations": total_violations(check),
    }


def run(paths: list[str | Path] | None, rules: RuleSet, out_path: str | Path | None = None,
        df: pd.DataFrame | None = None, verify_from_file: bool = True) -> RunResult:
    t = {}
    t0 = time.perf_counter()
    if df is not None:
        mdb = MDB(df=df, mapping={})
    else:
        mdb = read_mdb(paths)
    t["ingest_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    val = validate(mdb.df, rules)
    t["validate_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    res = allocate(val.blocks, rules)
    t["allocate_s"] = time.perf_counter() - t0
    tqs = val.tqs + capacity_tqs(val, res, len(val.tqs) + 1)
    rows = add_blocked_rows(build_rows(val, res, rules), mdb.df, val)
    for r in rows:   # capacity TQ refs
        if r["Status"] == "Not allocated":
            r["TQ Ref"] = next((q.id for q in tqs if q.category == "capacity" and r["Cable"] in q.cables), "")
    summ = summary(rows, res, rules)
    out = Path(out_path) if out_path else None
    t0 = time.perf_counter()
    if out:
        meta = {"tool": f"SlotSmith {__version__}", "rule set": rules.name, "inputs": ", ".join(map(str, paths or ["<dataframe>"])),
                "note": "Generated end-to-end; no hand-editing"}
        write_workbook(out, rows, summ, tqs, [], rules, meta)
    t["export_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    if out and verify_from_file:
        check = verify(load_allocation(out), mdb.df, rules)
        write_workbook(out, rows, summ, tqs, check, rules, meta)   # embed the rule-check report
    else:
        check = verify([{k: (None if v in ("", None) else str(v)) for k, v in r.items()} for r in rows], mdb.df, rules)
    t["verify_s"] = time.perf_counter() - t0
    return RunResult(mdb, val, res, rows, summ, tqs, check, t, metrics_for(rows, val, res, check, mdb.df), out)
