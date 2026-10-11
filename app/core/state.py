"""Pure application logic for the SlotSmith UI (no rendering).

Fingerprinting, staleness, lifecycle, ingest safety, pre-flight audit, KPI and TQ helpers.
Behaviour is unchanged from the previous UI revision (covered by tests/test_ui_core.py).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from slotsmith.ingest import CANONICAL, REQUIRED, ColumnMapping, MDB, read_mdb
from slotsmith.rules import RuleSet, default_ruleset
from slotsmith.validate import validate

class AppLifecycleState(str, Enum):
    """Lifecycle states of the application."""
    NO_INPUT = "no_input"
    INPUT_LOADED = "input_loaded"
    ALLOCATED = "allocated"
    STALE = "stale"
    REVISED = "revised"


@dataclass(frozen=True)
class StalenessStatus:
    """Staleness evaluation result with human-readable reason."""
    is_stale: bool
    rules_changed: bool
    inputs_changed: bool
    reason: str


def serialize_ruleset(rules: RuleSet) -> str:
    """Deterministically serialize a RuleSet to a canonical JSON string."""
    d = rules.model_dump()
    return json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)


def compute_rule_fingerprint(rules: RuleSet) -> str:
    """Compute a deterministic SHA-256 hex digest for a RuleSet configuration."""
    canonical_json = serialize_ruleset(rules)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_file_fingerprint(path: Path | str) -> str:
    """Compute SHA-256 hash of file content if it exists, otherwise hash the path string."""
    p = Path(path)
    if p.exists() and p.is_file():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    return hashlib.sha256(str(p).encode("utf-8")).hexdigest()


def compute_dataframe_fingerprint(df: pd.DataFrame | None) -> str:
    """Compute a deterministic SHA-256 fingerprint for a pandas DataFrame."""
    if df is None or df.empty:
        return ""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(csv_bytes).hexdigest()


def compute_inputs_fingerprint(paths: list[Path | str] | None) -> str:
    """Compute a composite SHA-256 fingerprint for a list of input files."""
    if not paths:
        return ""
    sorted_paths = sorted([Path(p) for p in paths], key=lambda x: str(x))
    combined = "|".join(f"{p.name}:{compute_file_fingerprint(p)}" for p in sorted_paths)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_allocation_input_fingerprint(
    paths: list[Path | str] | None = None,
    df: pd.DataFrame | None = None,
    mapping_override: dict[str, str] | None = None,
) -> str:
    """Compute a composite fingerprint for allocation inputs (files, DataFrame, mapping overrides)."""
    parts = []
    if paths:
        parts.append(f"files:{compute_inputs_fingerprint(paths)}")
    if df is not None and not df.empty:
        parts.append(f"df:{compute_dataframe_fingerprint(df)}")
    if mapping_override:
        mapping_json = json.dumps(mapping_override, sort_keys=True, separators=(",", ":"))
        parts.append(f"mapping:{mapping_json}")
    if not parts:
        return ""
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_revision_input_fingerprint(
    rev_b_df: pd.DataFrame | None = None,
    rev_b_paths: list[Path | str] | None = None,
    rev_b_files: list[Any] | None = None,
) -> str:
    """Compute a composite fingerprint for the Rev B revision input dataset."""
    parts = []
    if rev_b_df is not None and not rev_b_df.empty:
        parts.append(f"df:{compute_dataframe_fingerprint(rev_b_df)}")
    if rev_b_paths:
        parts.append(f"files:{compute_inputs_fingerprint(rev_b_paths)}")
    if rev_b_files:
        file_hashes = []
        for f in sorted(rev_b_files, key=lambda x: getattr(x, "name", str(x))):
            name = getattr(f, "name", "file")
            content = f.getvalue() if hasattr(f, "getvalue") else (f.getbuffer() if hasattr(f, "getbuffer") else b"")
            if isinstance(content, memoryview):
                content = content.tobytes()
            elif isinstance(content, str):
                content = content.encode("utf-8")
            h = hashlib.sha256(content).hexdigest()
            file_hashes.append(f"{name}:{h}")
        parts.append(f"uploads:{'|'.join(file_hashes)}")
    if not parts:
        return ""
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def check_allocation_staleness(
    allocated_rule_fp: str | None,
    current_rule_fp: str,
    allocated_input_fp: str | None,
    current_input_fp: str,
    has_allocation: bool,
) -> StalenessStatus:
    """Determine whether displayed allocation results are stale relative to current rules/inputs."""
    if not has_allocation:
        return StalenessStatus(is_stale=False, rules_changed=False, inputs_changed=False, reason="")

    rules_changed = allocated_rule_fp is not None and allocated_rule_fp != current_rule_fp
    inputs_changed = allocated_input_fp is not None and allocated_input_fp != current_input_fp

    if rules_changed and inputs_changed:
        reason = "Both rule configuration and input data have changed since the last allocation."
    elif rules_changed:
        reason = "Rule configuration has changed (e.g. spare %, segregation, or toggles) since the last allocation."
    elif inputs_changed:
        reason = "Input files or source data have changed since the last allocation."
    else:
        reason = ""

    return StalenessStatus(
        is_stale=rules_changed or inputs_changed,
        rules_changed=rules_changed,
        inputs_changed=inputs_changed,
        reason=reason,
    )


def check_revision_staleness(
    is_allocation_stale: bool,
    revision_rule_fp: str | None,
    current_rule_fp: str,
    revision_input_fp: str | None = None,
    current_rev_b_fp: str = "",
    has_revision: bool = True,
) -> StalenessStatus:
    """Determine whether revision results are stale relative to rules, Rev A allocation, or Rev B input."""
    if not has_revision:
        return StalenessStatus(is_stale=False, rules_changed=False, inputs_changed=False, reason="")

    if is_allocation_stale:
        return StalenessStatus(
            is_stale=True,
            rules_changed=True,
            inputs_changed=False,
            reason="Rev A allocation is stale. Re-run Allocate in Tab 1 before revising.",
        )

    rules_changed = revision_rule_fp is not None and revision_rule_fp != current_rule_fp
    inputs_changed = revision_input_fp is not None and revision_input_fp != current_rev_b_fp

    if rules_changed and inputs_changed:
        reason = "Both rule configuration and Rev B input have changed since the last revision."
    elif rules_changed:
        reason = "Rule configuration has changed since Rev B was computed. Re-run Compare + re-allocate."
    elif inputs_changed:
        reason = "Rev B input dataset has changed since Rev B was computed. Re-run Compare + re-allocate."
    else:
        reason = ""

    return StalenessStatus(
        is_stale=rules_changed or inputs_changed,
        rules_changed=rules_changed,
        inputs_changed=inputs_changed,
        reason=reason,
    )


def get_lifecycle_state(
    has_input: bool,
    has_allocation: bool,
    is_stale: bool,
    has_revision: bool,
    is_revision_stale: bool = False,
) -> AppLifecycleState:
    """Evaluate current application lifecycle state."""
    if not has_input:
        return AppLifecycleState.NO_INPUT
    if not has_allocation:
        return AppLifecycleState.INPUT_LOADED
    if is_stale or is_revision_stale:
        return AppLifecycleState.STALE
    if has_revision:
        return AppLifecycleState.REVISED
    return AppLifecycleState.ALLOCATED


def get_lifecycle_badge(state: AppLifecycleState) -> tuple[str, str]:
    """Return human-readable label and status level ('info', 'success', 'warning') for status display."""
    badges = {
        AppLifecycleState.NO_INPUT: ("No Input Loaded", "info"),
        AppLifecycleState.INPUT_LOADED: ("Input Ready (Not Allocated)", "info"),
        AppLifecycleState.ALLOCATED: ("Allocation Current", "success"),
        AppLifecycleState.STALE: ("Results Stale (Re-run Needed)", "warning"),
        AppLifecycleState.REVISED: ("Revision Current", "success"),
    }
    return badges[state]


@dataclass(frozen=True)
class PreflightAudit:
    """Pre-flight audit results derived strictly from the backend validation engine."""
    n_files: int
    n_sheets: int
    n_rows: int
    n_cables: int
    n_signals_valid: int
    n_blocked_tags: int
    blocking_tqs: int
    warning_tqs: int
    info_tqs: int
    tqs: list[Any]
    readiness_status: str  # "ready", "ready_with_warnings", "blocked"
    readiness_label: str
    summary_message: str


def safe_read_mdb(
    paths: list[str | Path] | None,
    mapping_override: dict[str, str] | None = None,
) -> tuple[MDB | None, str | None, str | None]:
    """Safely ingest customer IO MDB workbooks with defensive exception handling.

    Returns:
        (mdb, user_error_message, technical_details)
        If successful: (mdb, None, None)
        If failed: (None, human_readable_error, technical_exception_str)
    """
    if not paths:
        return None, "No input files provided.", None
    try:
        mdb = read_mdb(paths, mapping_override=mapping_override)
        return mdb, None, None
    except ValueError as e:
        msg = str(e)
        if "No sheet with the required columns" in msg:
            user_msg = (
                "No sheet with required IO columns found. Each workbook must contain "
                "at least one sheet with columns for: Tag, IO Type, Cable, and Pair."
            )
        else:
            user_msg = f"Input validation error: {msg}"
        return None, user_msg, f"ValueError: {e}"
    except FileNotFoundError as e:
        return None, f"Input file not found: {e.filename or 'specified path'}.", f"FileNotFoundError: {e}"
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        return None, f"Unable to parse file as tabular data: {e}", f"{type(e).__name__}: {e}"
    except Exception as e:
        err_type = type(e).__name__
        if "BadZipFile" in err_type or "Zip" in err_type:
            user_msg = "The uploaded file appears to be corrupted or not a valid Excel (.xlsx) archive."
        else:
            user_msg = f"Failed to ingest workbook ({err_type}): {e}"
        return None, user_msg, f"{err_type}: {e}"


def build_mapping_review_rows(cm: ColumnMapping) -> list[dict[str, Any]]:
    """Build structured, human-readable review rows for a ColumnMapping."""
    rows = []
    for canon in CANONICAL:
        is_req = canon in REQUIRED
        mapped_hdr = cm.mapping.get(canon)
        conf = cm.confidence.get(canon)

        if mapped_hdr:
            conf_str = f"{int(conf * 100)}%" if conf is not None else "100%"
            status = "✅ Mapped (High)" if (conf is None or conf >= 0.90) else "⚠️ Mapped (Fuzzy)"
        else:
            conf_str = "—"
            status = "❌ Missing (Required)" if is_req else "⚪ Unmapped (Optional)"

        rows.append({
            "Target Field": canon,
            "Required": "Yes" if is_req else "Optional",
            "Matched Header": mapped_hdr or "—",
            "Confidence": conf_str,
            "Status": status,
        })
    return rows


def compute_preflight_audit(mdb: MDB, rules: RuleSet) -> PreflightAudit:
    """Compute a data-backed pre-flight audit using the backend validate() engine."""
    df = mdb.df
    n_rows = len(df)
    n_files = len(set(df["src_file"].dropna())) if "src_file" in df and not df.empty else (1 if n_rows > 0 else 0)
    n_sheets = len(mdb.mapping)

    if n_rows == 0:
        return PreflightAudit(
            n_files=n_files,
            n_sheets=n_sheets,
            n_rows=0,
            n_cables=0,
            n_signals_valid=0,
            n_blocked_tags=0,
            blocking_tqs=0,
            warning_tqs=0,
            info_tqs=0,
            tqs=[],
            readiness_status="blocked",
            readiness_label="Allocation Blocked",
            summary_message="No rows found in the ingested IO sheets.",
        )

    val = validate(df, rules)
    n_cables = len(val.blocks)
    n_signals_valid = sum(len(b.signals) for b in val.blocks)
    n_blocked_tags = len(val.blocked_tags)
    blocking_tqs = sum(1 for t in val.tqs if t.severity == "blocking")
    warning_tqs = sum(1 for t in val.tqs if t.severity == "warning")
    info_tqs = sum(1 for t in val.tqs if t.severity == "info")

    if n_cables == 0:
        readiness_status = "blocked"
        readiness_label = "Allocation Blocked"
        summary_message = f"All {n_rows} rows have blocking issues ({blocking_tqs} blocking TQs). No valid cables to allocate."
    elif blocking_tqs > 0:
        readiness_status = "ready_with_warnings"
        readiness_label = "Ready with Issues (Partial Allocation)"
        summary_message = (
            f"{n_cables} cables ({n_signals_valid} signals) ready to allocate. "
            f"{blocking_tqs} blocking data issues will leave affected rows unplaced as TQs."
        )
    else:
        readiness_status = "ready"
        readiness_label = "Ready to Allocate"
        summary_message = (
            f"All pre-flight checks passed ({n_cables} cables, {n_signals_valid} signals). "
            f"{n_rows} rows ready for allocation."
        )

    return PreflightAudit(
        n_files=n_files,
        n_sheets=n_sheets,
        n_rows=n_rows,
        n_cables=n_cables,
        n_signals_valid=n_signals_valid,
        n_blocked_tags=n_blocked_tags,
        blocking_tqs=blocking_tqs,
        warning_tqs=warning_tqs,
        info_tqs=info_tqs,
        tqs=val.tqs,
        readiness_status=readiness_status,
        readiness_label=readiness_label,
        summary_message=summary_message,
    )


def init_session_state(state: dict | Any) -> None:
    """Initialize default session state keys if not present."""
    defaults = {
        "rules": default_ruleset,
        "paths": None,
        "res": None,
        "out": None,
        "revb": None,
        "rr": None,
        "allocated_rule_fp": None,
        "allocated_input_fp": None,
        "revision_rule_fp": None,
        "revision_input_fp": None,
        "cached_mdb": None,
        "cached_mdb_fp": None,
        "ingest_error": None,
        "ingest_error_details": None,
    }
    for k, v in defaults.items():
        if k not in state:
            state[k] = v() if callable(v) else v


def compute_kpi_metrics(res: Any, rules: RuleSet) -> dict[str, Any]:
    """Compute verified KPI metrics from RunResult and RuleSet."""
    if res is None:
        return {}
    m = getattr(res, "metrics", {}) or {}
    allocated = m.get("signals_allocated", 0)
    tq_signals = m.get("signals_with_tq", 0)
    total_signals = allocated + tq_signals
    baseplates = m.get("baseplates", 0)
    slots_per_bp = getattr(rules, "charms_per_baseplate", 12)
    total_slots = baseplates * slots_per_bp
    utilization = round(100.0 * allocated / max(1, total_slots), 1) if total_slots > 0 else 0.0

    tqs = getattr(res, "tqs", []) or []
    blocking_tqs = sum(1 for t in tqs if getattr(t, "severity", "") == "blocking")
    warning_tqs = sum(1 for t in tqs if getattr(t, "severity", "") == "warning")
    info_tqs = sum(1 for t in tqs if getattr(t, "severity", "") == "info")

    return {
        "signals_allocated": allocated,
        "signals_with_tq": tq_signals,
        "total_signals": total_signals,
        "coverage_pct": m.get("coverage_pct", 0.0),
        "violations": m.get("violations", 0),
        "cabinets": m.get("cabinets", 0),
        "ciocs": m.get("ciocs", 0),
        "baseplates": baseplates,
        "total_slots": total_slots,
        "baseplate_utilization_pct": utilization,
        "tqs_total": len(tqs),
        "blocking_tqs": blocking_tqs,
        "warning_tqs": warning_tqs,
        "info_tqs": info_tqs,
    }


def filter_tqs(tqs: list[Any], severity: str = "All", search: str = "") -> list[Any]:
    """Filter TQs by severity and search query string."""
    if not tqs:
        return []
    filtered = list(tqs)
    if severity and severity.lower() != "all":
        target = severity.lower()
        filtered = [t for t in filtered if getattr(t, "severity", "").lower() == target]

    if search:
        s = search.strip().lower()

        def matches(t: Any) -> bool:
            msg = getattr(t, "message", "").lower()
            tid = getattr(t, "id", "").lower()
            cat = getattr(t, "category", "").lower()
            rule = getattr(t, "rule_ref", "").lower()
            action = getattr(t, "suggested_action", "").lower()
            cables = " ".join(getattr(t, "cables", []) or []).lower()
            tags = " ".join(getattr(t, "tags", []) or []).lower()
            return s in msg or s in tid or s in cat or s in rule or s in action or s in cables or s in tags

        filtered = [t for t in filtered if matches(t)]

    return filtered


def is_verifier_certified(res: Any) -> tuple[bool, str, list[str]]:
    """Determine whether the independent verifier reports no violations (all 11 rule families PASS).

    Returns:
        (certified, summary_message, list_of_failed_rule_refs)
    """
    if res is None:
        return False, "No allocation results available.", []
    check = getattr(res, "check", None)
    if not check or not isinstance(check, list):
        return False, "Independent verification check report is missing.", []
    if len(check) < 11:
        return False, f"Incomplete verification report ({len(check)} of 11 checks recorded).", []

    failed = [c for c in check if c.get("Result") != "PASS" or c.get("Violations", 0) > 0]
    if failed:
        rule_refs = [str(c.get("Rule", "?")) for c in failed]
        return False, f"Rule violations detected in {len(failed)} rule family/families: {', '.join(rule_refs)}.", rule_refs

    return True, "Verified: all 11 rule families passed the independent check on the exported rows.", []
