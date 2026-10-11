"""Real-engine preview data for the landing page.

A small seeded SYNTHETIC MDB is allocated by the real engine once per server process; the landing page shows
real rows, real addresses, a real TQ and a real revision impact from it. Nothing here is hand-written output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from slotsmith.generator import generate, make_revision
from slotsmith.pipeline import run
from slotsmith.revision import revise
from slotsmith.rules import default_ruleset

DEMO_SIGNALS, DEMO_SEED, DEMO_ERRORS = 200, 8, 3
SOURCE_FILE = "synthetic_demo.xlsx"


def _canon(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={"Tag": "tag", "IO": "io_type", "Cable": "cable", "Cable Size": "cable_size",
                            "Pair": "pair", "Grp": "group", "Seg": "seg"}).copy()
    df["src_file"], df["src_sheet"], df["src_row"] = SOURCE_FILE, "IO MDB", range(2, len(df) + 2)
    df = df.astype(object).where(df.notna(), None)
    for c in ["pair", "cable_size"]:
        df[c] = df[c].map(lambda v: None if v is None else str(int(float(v))))
    return df


@dataclass
class DemoSignal:
    tag: str
    row: dict                      # allocation row from the engine
    source_line: str               # "synthetic_demo.xlsx · row 14"
    mdb: dict                      # the canonical MDB row
    tqs_touching: int
    neighbours: list[dict] = field(default_factory=list)   # the 12 slots of its baseplate (rows incl. spares)


@dataclass
class DemoBundle:
    n_rows: int
    signals: list[DemoSignal]
    check: list[dict]
    metrics: dict
    sample_tq: Any
    revision: dict
    n_tqs: int


def build_demo() -> DemoBundle:
    rules = default_ruleset()
    g = generate(DEMO_SIGNALS, seed=DEMO_SEED, inject_errors=DEMO_ERRORS)
    df = _canon(g.df)
    res = run(None, rules, None, df=df, verify_from_file=False)
    mdb_by_tag = {r["tag"]: r for r in df.to_dict("records") if r["tag"]}
    alloc = [r for r in res.rows if r["Row Kind"] == "Signal" and r["Status"] == "Allocated"]

    # one representative signal per CHARM family, preferring A-side ones, in a stable order
    wanted = [("AI", False), ("DI", False), ("DF", False), ("AO", False)]
    from .cabinet import type_code
    chosen: list[dict] = []
    for code, _ in wanted:
        used = {c["Cable"] for c in chosen}
        cands = [r for r in alloc if type_code(r) == code and r["Cable"] not in used]
        cands.sort(key=lambda r: (r["Segregation"] != "A", r["_cab"], r["_cioc"], r["_bp"], int(r["Slot"])))
        if cands:
            chosen.append(cands[0])
    signals = []
    for r in chosen:
        m = mdb_by_tag[r["Tag"]]
        nb = [x for x in res.rows if x["CIOC"] == r["CIOC"] and x["_bp"] == r["_bp"] and x.get("Slot")]
        nb.sort(key=lambda x: int(float(x["Slot"])))
        touching = sum(1 for q in res.tqs if r["Tag"] in q.tags or r["Cable"] in q.cables)
        signals.append(DemoSignal(r["Tag"], r, f'{SOURCE_FILE} · row {m["src_row"]}', m, touching, nb))

    sample_tq = next((q for q in res.tqs if q.severity == "blocking" and q.sources), res.tqs[0] if res.tqs else None)
    revb = _canon(make_revision(g.df, seed=DEMO_SEED + 1))
    rr = revise(res.rows, revb, rules)
    m = rr.metrics
    revision = {k: m[k] for k in ("moved", "added", "deleted", "modified_in_place", "unchanged", "violations")}
    revision["cpsat_windows"] = len(m.get("cpsat_repairs", []))
    revision["fallback"] = bool(m.get("fallback_full_reallocation"))
    return DemoBundle(len(df), signals, res.check, res.metrics, sample_tq, revision, len(res.tqs))
