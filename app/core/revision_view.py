"""Honest, plain-language summary of a revision run's solver activity (from `RevisionResult.metrics`)."""
from __future__ import annotations

from typing import Any


def solver_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    windows = metrics.get("cpsat_repairs", []) or []
    accepted = [w for w in windows if w.get("status") in ("OPTIMAL", "FEASIBLE")]
    exact = [w for w in accepted if w.get("proven_exact")]
    best = [w for w in accepted if not w.get("proven_exact")]
    rejected = [w for w in windows if w not in accepted]
    fallback = bool(metrics.get("fallback_full_reallocation"))
    if fallback:
        kind, headline = "warn", "No local repair was found, so Rev B was fully re-allocated"
    elif not windows:
        kind, headline = "ok", "No solver repair was needed"
    elif best:
        kind, headline = "info", "Local repair used; some windows are best-found, not proven minimal"
    else:
        kind, headline = "ok", "Local repair used; every accepted window is proven exact"
    if fallback:
        detail = ("Unchanged signals may have moved. See the impact list and the warning technical query in the workbook.")
    elif not windows:
        detail = "Unchanged cables stayed where they were and the new or changed cables found room without searching."
    else:
        detail = (f"{len(accepted)} repair window(s) accepted: {len(exact)} proven exact, {len(best)} best found within the "
                  f"time limit. {len(rejected)} window(s) tried and rejected (infeasible or no answer in time). "
                  "The search covers only the cabinets around each affected group, and results can differ between runs.")
    return {"kind": kind, "headline": headline, "detail": detail, "accepted": len(accepted), "exact": len(exact),
            "best_found": len(best), "rejected": len(rejected), "fallback": fallback,
            "capacity_unplaced": list(metrics.get("capacity_unplaced") or [])}
