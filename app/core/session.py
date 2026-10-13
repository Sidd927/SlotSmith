"""Session actions and derived status for the SlotSmith workbench.

All functions take a mutable mapping (``st.session_state`` in the app, a plain dict in tests) so the
logic is testable without a running Streamlit script. Nothing here changes backend behaviour: it only
calls the public entry points (`generate`, `make_revision`, `read_mdb`, `run`, `revise`, `write_workbook`,
`verify`).
"""
from __future__ import annotations

import copy
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, MutableMapping

import pandas as pd

from slotsmith.export import write_workbook
from slotsmith.generator import generate, make_revision
from slotsmith.revision import revise
from slotsmith.pipeline import run
from slotsmith.rules import RuleSet
from slotsmith.verifier import load_allocation, total_violations, verify

from .state import (
    AppLifecycleState,
    StalenessStatus,
    check_allocation_staleness,
    check_revision_staleness,
    compute_allocation_input_fingerprint,
    compute_revision_input_fingerprint,
    compute_rule_fingerprint,
    get_lifecycle_state,
    init_session_state,
    safe_read_mdb,
)

State = MutableMapping[str, Any]

EXTRA_DEFAULTS = {
    "dataset": None,          # {"names": [...], "synthetic": bool, "label": str}
    "revb": None,             # synthetic Rev B DataFrame created together with a synthetic Rev A
    "revision_source": None,  # {"kind": "synthetic"|"upload", "label": str, "paths"|"df", "fp": str}
    "rev_out": None,          # path of the Rev B workbook written for download
    "revision_error": None,
    "allocation_error": None,
    "last_run_note": None,
}


def ensure_session(state: State) -> None:
    init_session_state(state)
    for k, v in EXTRA_DEFAULTS.items():
        if k not in state:
            state[k] = v


# ----------------------------------------------------------------------------- loading data
def _clear_ingest_error(state: State) -> None:
    state["ingest_error"] = None
    state["ingest_error_details"] = None


def load_synthetic(state: State, n_signals: int = 2000, seed: int = 7, errors: int = 6) -> tuple[bool, str | None]:
    """Generate a synthetic MDB (+ a matching synthetic Rev B) and make it the active dataset."""
    ensure_session(state)
    try:
        g = generate(int(n_signals), seed=int(seed), inject_errors=int(errors))
        p = Path(tempfile.mkdtemp()) / f"SYNTHETIC_MDB_{int(n_signals)}_s{int(seed)}.xlsx"
        g.df.to_excel(p, index=False)
        revb = make_revision(g.df, seed=int(seed) + 1)
    except Exception as e:  # defensive: never crash the page
        return False, f"Could not generate the synthetic dataset: {e}"
    state["paths"] = [p]
    state["revb"] = revb
    state["dataset"] = {"names": [p.name], "synthetic": True,
                        "label": f"Synthetic benchmark · {int(n_signals):,} signals · seed {int(seed)}"}
    state["revision_source"] = None
    state["cached_mdb"] = None
    state["cached_mdb_fp"] = None
    _clear_ingest_error(state)
    return True, None


def load_uploads(state: State, saved_paths: list[Path]) -> tuple[bool, str | None]:
    """Ingest uploaded files; on failure keep the previous dataset and record a readable error."""
    ensure_session(state)
    mdb, err, details = safe_read_mdb(saved_paths)
    if mdb is None:
        state["ingest_error"] = err
        state["ingest_error_details"] = details
        return False, err
    state["paths"] = list(saved_paths)
    state["cached_mdb"] = mdb
    state["cached_mdb_fp"] = compute_allocation_input_fingerprint(paths=saved_paths)
    state["dataset"] = {"names": [Path(p).name for p in saved_paths], "synthetic": False,
                        "label": ", ".join(Path(p).name for p in saved_paths[:2])
                        + (f" (+{len(saved_paths) - 2})" if len(saved_paths) > 2 else "")}
    state["revb"] = None
    state["revision_source"] = None
    _clear_ingest_error(state)
    return True, None


def get_mdb(state: State):
    """Session-cached MDB for the active dataset (keyed by the input fingerprint)."""
    paths = state.get("paths")
    if not paths:
        return None
    fp = compute_allocation_input_fingerprint(paths=paths)
    if state.get("cached_mdb") is not None and state.get("cached_mdb_fp") == fp:
        return state["cached_mdb"]
    mdb, err, details = safe_read_mdb(paths)
    if mdb is None:
        state["ingest_error"], state["ingest_error_details"] = err, details
        return None
    state["cached_mdb"], state["cached_mdb_fp"] = mdb, fp
    return mdb


# ----------------------------------------------------------------------------- allocation
def run_allocation(state: State) -> tuple[bool, str | None]:
    """Run the engine. A failure never overwrites a previous good result."""
    ensure_session(state)
    paths = state.get("paths")
    if not paths:
        return False, "No dataset is loaded."
    rules: RuleSet = copy.deepcopy(state["rules"])
    out = Path(tempfile.mkdtemp()) / "SlotSmith_allocation.xlsx"
    try:
        res = run(paths, rules, out)
    except Exception as e:
        state["allocation_error"] = f"{type(e).__name__}: {e}"
        return False, state["allocation_error"]
    state["res"] = res
    state["out"] = out
    state["allocated_rule_fp"] = compute_rule_fingerprint(rules)
    state["allocated_input_fp"] = compute_allocation_input_fingerprint(paths=paths)
    state["allocation_error"] = None
    # a new Rev A invalidates any earlier revision
    state["rr"] = None
    state["rev_out"] = None
    state["revision_rule_fp"] = None
    state["revision_input_fp"] = None
    return True, None


# ----------------------------------------------------------------------------- revision
def set_revision_synthetic(state: State) -> bool:
    revb = state.get("revb")
    if revb is None:
        return False
    state["revision_source"] = {"kind": "synthetic", "label": "Synthetic Rev B (created with the benchmark)",
                                "df": revb, "fp": compute_revision_input_fingerprint(rev_b_df=revb)}
    return True


def set_revision_upload(state: State, saved_paths: list[Path]) -> tuple[bool, str | None]:
    mdb, err, details = safe_read_mdb(saved_paths)
    if mdb is None:
        state["revision_error"] = err
        return False, err
    state["revision_source"] = {"kind": "upload", "label": ", ".join(Path(p).name for p in saved_paths),
                                "paths": list(saved_paths), "fp": compute_revision_input_fingerprint(rev_b_paths=saved_paths)}
    state["revision_error"] = None
    return True, None


def run_revision(state: State) -> tuple[bool, str | None]:
    """Revise Rev A with the chosen Rev B and write a verified Rev B workbook for download."""
    ensure_session(state)
    res, src = state.get("res"), state.get("revision_source")
    if res is None:
        return False, "Allocate Rev A first."
    if not src:
        return False, "Choose a Rev B input first."
    rules: RuleSet = copy.deepcopy(state["rules"])
    try:
        if src["kind"] == "upload":
            mdb_b, err, _ = safe_read_mdb(src["paths"])
        else:
            p = Path(tempfile.mkdtemp()) / "SYNTHETIC_RevB.xlsx"
            src["df"].to_excel(p, index=False)
            mdb_b, err, _ = safe_read_mdb([p])
        if mdb_b is None:
            state["revision_error"] = err
            return False, err
        rr = revise(res.rows, mdb_b.df, rules)
        out = Path(tempfile.mkdtemp()) / "SlotSmith_allocation_RevB.xlsx"
        meta = {"tool": "SlotSmith (UI) revise", "rev_a": str(state.get("dataset", {}).get("label", "")),
                "rev_b": src["label"]}
        write_workbook(out, rr.rows, rr.summary, rr.tqs, [], rules, meta, impact=rr.impact)
        rr.check = verify(load_allocation(out), mdb_b.df, rules)     # re-check the file actually written
        rr.metrics["violations"] = total_violations(rr.check)
        write_workbook(out, rr.rows, rr.summary, rr.tqs, rr.check, rules, meta, impact=rr.impact)
    except Exception as e:
        state["revision_error"] = f"{type(e).__name__}: {e}"
        return False, state["revision_error"]
    state["rr"] = rr
    state["rev_out"] = out
    state["revision_rule_fp"] = compute_rule_fingerprint(rules)
    state["revision_input_fp"] = src["fp"]
    state["revision_error"] = None
    return True, None


# ----------------------------------------------------------------------------- reset
def reset_session(state: State) -> None:
    for k in ("paths", "res", "out", "rr", "rev_out", "cached_mdb", "cached_mdb_fp", "dataset", "revb",
              "revision_source", "allocated_rule_fp", "allocated_input_fp", "revision_rule_fp",
              "revision_input_fp", "ingest_error", "ingest_error_details", "revision_error",
              "allocation_error"):
        state[k] = None
    ensure_session(state)


# ----------------------------------------------------------------------------- derived status
@dataclass(frozen=True)
class WorkbenchStatus:
    has_input: bool
    has_allocation: bool
    has_revision: bool
    alloc: StalenessStatus
    rev: StalenessStatus
    lifecycle: AppLifecycleState
    dataset_label: str
    synthetic: bool
    blocking_input_error: bool = False
    stage_flags: dict = field(default_factory=dict)


def compute_status(state: State) -> WorkbenchStatus:
    ensure_session(state)
    rules = state["rules"]
    paths, res, rr = state.get("paths"), state.get("res"), state.get("rr")
    rule_fp = compute_rule_fingerprint(rules)
    input_fp = compute_allocation_input_fingerprint(paths=paths)
    alloc = check_allocation_staleness(state.get("allocated_rule_fp"), rule_fp, state.get("allocated_input_fp"),
                                       input_fp, has_allocation=res is not None)
    src = state.get("revision_source")
    rev = check_revision_staleness(alloc.is_stale, state.get("revision_rule_fp"), rule_fp,
                                   state.get("revision_input_fp"), (src or {}).get("fp", state.get("revision_input_fp") or ""),
                                   has_revision=rr is not None)
    life = get_lifecycle_state(bool(paths), res is not None, alloc.is_stale, rr is not None, rev.is_stale)
    ds = state.get("dataset") or {}
    label = ds.get("label") or (", ".join(Path(p).name for p in paths[:2]) if paths else "")
    return WorkbenchStatus(bool(paths), res is not None, rr is not None, alloc, rev, life, label,
                           bool(ds.get("synthetic")))


# ----------------------------------------------------------------------------- cached pre-flight audit
def get_audit(state: State):
    """Pre-flight audit for the active dataset and rules, cached per (input, rules) fingerprint."""
    from .state import compute_preflight_audit
    mdb = get_mdb(state)
    if mdb is None:
        return None
    key = (state.get("cached_mdb_fp"), compute_rule_fingerprint(state["rules"]))
    cached = state.get("_audit")
    if cached and cached[0] == key:
        return cached[1]
    audit = compute_preflight_audit(mdb, state["rules"])
    state["_audit"] = (key, audit)
    return audit


def run_id(state: State) -> str:
    """Short stable id of the current Rev A run (rule + input fingerprints). Empty when nothing has been allocated."""
    import hashlib
    if state.get("res") is None:
        return ""
    raw = f'{state.get("allocated_rule_fp")}|{state.get("allocated_input_fp")}'
    return hashlib.sha1(raw.encode()).hexdigest()[:8].upper()
