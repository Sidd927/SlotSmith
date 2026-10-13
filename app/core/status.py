"""One derived, honest status for the current run, shared by the header, rail, strip and pages.

Separates facts that are easy to conflate:
  freshness     whether the results still match the data and rules ("in sync" says nothing about correctness)
  verification  passed / incomplete / failed / missing, from the independent check (skipped is not passed)
  allocation    complete or partial (held / unplaced rows)
  unresolved    signals with no hardware mapping (H-* queries)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .session import compute_status
from .state import unresolved_hardware, verification_status


@dataclass(frozen=True)
class RunStatus:
    freshness: str                      # none | in_sync | stale
    verification: str                   # none | passed | incomplete | failed | missing
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    held: int = 0                       # rows held or not placed (technical queries)
    unresolved_hw: int = 0
    blocking_tqs: int = 0
    disabled: tuple = ()
    skipped_rules: tuple = ()
    failed_rules: tuple = ()
    reason: str = ""

    @property
    def complete(self) -> bool:
        return self.held == 0 and self.unresolved_hw == 0

    @property
    def accepted(self) -> bool:
        """True only if nothing needs attention. Never implies engineering acceptance by a human."""
        return self.freshness == "in_sync" and self.verification == "passed" and self.complete


def status_for(res, rules, stale: bool, stale_reason: str = "") -> RunStatus:
    """Status of any result object with .rows, .tqs and .check (a RunResult or a RevisionResult)."""
    if res is None:
        return RunStatus("none", "none")
    vs = verification_status(res)
    tqs = getattr(res, "tqs", []) or []
    held = sum(1 for r in res.rows if r.get("Status") in ("TQ raised", "Not allocated"))
    return RunStatus(
        freshness="stale" if stale else "in_sync", verification=vs["outcome"], passed=vs["passed"],
        failed=vs["failed"], skipped=vs["skipped"], total=vs["total"], held=held, unresolved_hw=len(unresolved_hardware(res)),
        blocking_tqs=sum(1 for t in tqs if t.severity == "blocking"), disabled=tuple(t.id for t in rules.toggles if not t.enabled),
        skipped_rules=tuple(r for r, _ in vs["skipped_rules"]), failed_rules=tuple(vs["failed_rules"]),
        reason=stale_reason if stale else "")


def run_status(state) -> RunStatus:
    s = compute_status(state)
    return status_for(state.get("res"), state["rules"], s.alloc.is_stale, s.alloc.reason)


def revision_status(state) -> RunStatus:
    s = compute_status(state)
    return status_for(state.get("rr"), state["rules"], s.rev.is_stale, s.rev.reason)


def next_actions(rs: RunStatus) -> list[str]:
    """Concrete, ordered actions needed before the results can be relied on. Empty when nothing is outstanding."""
    out = []
    if rs.freshness == "stale":
        out.append("Run Allocate again: the data or rules changed since this run, so every result below is out of date.")
    if rs.failed:
        out.append(f"Resolve the violations in {', '.join(rs.failed_rules)}. Do not use this allocation until they are cleared.")
    if rs.unresolved_hw:
        out.append(f"Resolve {rs.unresolved_hw} unresolved hardware mapping(s): correct the I/O type in the source data or add a "
                   "mapping to the hardware table in the rule set, then re-run. SlotSmith will not invent a mapping.")
    if rs.held - rs.unresolved_hw > 0:
        out.append(f"Review the {rs.held - rs.unresolved_hw} other held or unplaced row(s) in the technical-query register and fix their source rows.")
    if rs.skipped:
        out.append(f"Re-enable the rule(s) behind {', '.join(rs.skipped_rules)} to run the skipped checks, or accept in writing that they were not checked.")
    return out
