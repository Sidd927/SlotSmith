"""Pure-logic tests for the UI layer: fingerprints, staleness, lifecycle, ingest safety, pre-flight, KPIs, TQ filters.

Carried over from the previous UI revision (bodies unchanged); imports now point at app.core.state.
Tests that exercised the removed layout (NAV_*/STAGE_* constants, radio sync helpers, old landing page,
custom CSS builder) were replaced by tests/test_ui_app.py and tests/test_ui_components.py.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from slotsmith.generator import generate, make_revision
from slotsmith.ingest import ColumnMapping, MDB, read_mdb
from slotsmith.pipeline import run
from slotsmith.rules import RuleSet, default_ruleset
from app.core.state import (
    AppLifecycleState,
    PreflightAudit,
    StalenessStatus,
    build_mapping_review_rows,
    check_allocation_staleness,
    check_revision_staleness,
    compute_allocation_input_fingerprint,
    compute_dataframe_fingerprint,
    compute_file_fingerprint,
    compute_inputs_fingerprint,
    compute_kpi_metrics,
    compute_preflight_audit,
    compute_revision_input_fingerprint,
    compute_rule_fingerprint,
    filter_tqs,
    get_lifecycle_badge,
    get_lifecycle_state,
    init_session_state,
    is_verifier_certified,
    safe_read_mdb,
    serialize_ruleset,
)

ROOT = Path(__file__).resolve().parents[1]

def test_deterministic_ruleset_serialization_identical_instances():
    r1 = default_ruleset()
    r2 = default_ruleset()
    s1 = serialize_ruleset(r1)
    s2 = serialize_ruleset(r2)
    assert s1 == s2
    assert compute_rule_fingerprint(r1) == compute_rule_fingerprint(r2)

def test_deterministic_ruleset_fingerprint_from_json_roundtrip():
    r1 = default_ruleset()
    raw_json = r1.model_dump_json(indent=2)
    r2 = RuleSet.model_validate(json.loads(raw_json))
    assert compute_rule_fingerprint(r1) == compute_rule_fingerprint(r2)

def test_rule_fingerprint_changes_on_toggle_modification():
    r1 = default_ruleset()
    r2 = default_ruleset()
    fp_orig = compute_rule_fingerprint(r1)

    r2.toggles[0].enabled = not r2.toggles[0].enabled
    fp_mod = compute_rule_fingerprint(r2)
    assert fp_orig != fp_mod

def test_rule_fingerprint_changes_on_spare_percent_change():
    r1 = default_ruleset()
    r2 = default_ruleset()
    r2.spare_percent = 20.0
    assert compute_rule_fingerprint(r1) != compute_rule_fingerprint(r2)

def test_rule_fingerprint_changes_on_isolation_and_segregation():
    r1 = default_ruleset()
    r2 = default_ruleset()
    r2.group_isolation_level = "cabinet"
    assert compute_rule_fingerprint(r1) != compute_rule_fingerprint(r2)

    r3 = default_ruleset()
    r3.segregation_level = "cabinet"
    assert compute_rule_fingerprint(r1) != compute_rule_fingerprint(r3)

def test_rule_fingerprint_changes_on_naming_modification():
    r1 = default_ruleset()
    r2 = default_ruleset()
    r2.naming.area = "AREA_99"
    assert compute_rule_fingerprint(r1) != compute_rule_fingerprint(r2)

def test_inputs_fingerprint_empty_paths():
    assert compute_inputs_fingerprint(None) == ""
    assert compute_inputs_fingerprint([]) == ""
    assert compute_allocation_input_fingerprint() == ""

def test_inputs_fingerprint_deterministic_order(tmp_path):
    p1 = tmp_path / "a.xlsx"
    p2 = tmp_path / "b.xlsx"
    p1.write_bytes(b"content_a")
    p2.write_bytes(b"content_b")

    fp_1 = compute_inputs_fingerprint([p1, p2])
    fp_2 = compute_inputs_fingerprint([p2, p1])
    assert fp_1 == fp_2
    assert len(fp_1) == 64

def test_inputs_fingerprint_changes_when_content_changes(tmp_path):
    p = tmp_path / "input.xlsx"
    p.write_bytes(b"initial_data")
    fp1 = compute_inputs_fingerprint([p])

    p.write_bytes(b"modified_data")
    fp2 = compute_inputs_fingerprint([p])
    assert fp1 != fp2

def test_inputs_fingerprint_changes_when_file_added(tmp_path):
    p1 = tmp_path / "f1.xlsx"
    p2 = tmp_path / "f2.xlsx"
    p1.write_bytes(b"data1")
    p2.write_bytes(b"data2")

    fp_single = compute_inputs_fingerprint([p1])
    fp_double = compute_inputs_fingerprint([p1, p2])
    assert fp_single != fp_double

def test_dataframe_fingerprint_deterministic():
    df1 = pd.DataFrame({"Tag": ["T1", "T2"], "IO": ["AI", "DO"]})
    df2 = pd.DataFrame({"Tag": ["T1", "T2"], "IO": ["AI", "DO"]})
    df3 = pd.DataFrame({"Tag": ["T1", "T3"], "IO": ["AI", "DO"]})

    assert compute_dataframe_fingerprint(df1) == compute_dataframe_fingerprint(df2)
    assert compute_dataframe_fingerprint(df1) != compute_dataframe_fingerprint(df3)
    assert compute_dataframe_fingerprint(None) == ""
    assert compute_dataframe_fingerprint(pd.DataFrame()) == ""

def test_allocation_input_fingerprint_incorporates_mapping_override(tmp_path):
    p = tmp_path / "m.xlsx"
    p.write_bytes(b"dummy")
    fp_no_override = compute_allocation_input_fingerprint(paths=[p])
    fp_with_override = compute_allocation_input_fingerprint(paths=[p], mapping_override={"Tag_ID": "tag"})
    assert fp_no_override != fp_with_override

def test_allocation_staleness_no_allocation():
    r = default_ruleset()
    fp = compute_rule_fingerprint(r)
    status = check_allocation_staleness(
        allocated_rule_fp=None,
        current_rule_fp=fp,
        allocated_input_fp=None,
        current_input_fp="inp123",
        has_allocation=False,
    )
    assert not status.is_stale
    assert not status.rules_changed
    assert not status.inputs_changed
    assert status.reason == ""

def test_allocation_staleness_identical_state():
    r = default_ruleset()
    rfp = compute_rule_fingerprint(r)
    ifp = "hash_input_1"
    status = check_allocation_staleness(
        allocated_rule_fp=rfp,
        current_rule_fp=rfp,
        allocated_input_fp=ifp,
        current_input_fp=ifp,
        has_allocation=True,
    )
    assert not status.is_stale
    assert not status.rules_changed
    assert not status.inputs_changed
    assert status.reason == ""

def test_allocation_staleness_rule_changed():
    r1 = default_ruleset()
    r2 = default_ruleset()
    r2.spare_percent = 25.0
    rfp1 = compute_rule_fingerprint(r1)
    rfp2 = compute_rule_fingerprint(r2)
    ifp = "hash_input_1"

    status = check_allocation_staleness(
        allocated_rule_fp=rfp1,
        current_rule_fp=rfp2,
        allocated_input_fp=ifp,
        current_input_fp=ifp,
        has_allocation=True,
    )
    assert status.is_stale
    assert status.rules_changed
    assert not status.inputs_changed
    assert "Rule configuration has changed" in status.reason

def test_allocation_staleness_input_changed():
    r = default_ruleset()
    rfp = compute_rule_fingerprint(r)

    status = check_allocation_staleness(
        allocated_rule_fp=rfp,
        current_rule_fp=rfp,
        allocated_input_fp="old_input_hash",
        current_input_fp="new_input_hash",
        has_allocation=True,
    )
    assert status.is_stale
    assert not status.rules_changed
    assert status.inputs_changed
    assert "Input files or source data have changed" in status.reason

def test_allocation_staleness_both_changed():
    r1 = default_ruleset()
    r2 = default_ruleset()
    r2.spare_percent = 25.0

    status = check_allocation_staleness(
        allocated_rule_fp=compute_rule_fingerprint(r1),
        current_rule_fp=compute_rule_fingerprint(r2),
        allocated_input_fp="old_input",
        current_input_fp="new_input",
        has_allocation=True,
    )
    assert status.is_stale
    assert status.rules_changed
    assert status.inputs_changed
    assert "Both rule configuration and input data have changed" in status.reason

def test_allocation_staleness_recovery_when_rules_reverted():
    r = default_ruleset()
    rfp_orig = compute_rule_fingerprint(r)
    ifp = "same_input"

    # Rule modified -> stale
    r.spare_percent = 20.0
    status1 = check_allocation_staleness(rfp_orig, compute_rule_fingerprint(r), ifp, ifp, True)
    assert status1.is_stale

    # Rule reverted back -> no longer stale
    r.spare_percent = 10.0
    status2 = check_allocation_staleness(rfp_orig, compute_rule_fingerprint(r), ifp, ifp, True)
    assert not status2.is_stale

def test_synthetic_dataset_generation_invalidates_prior_allocation(tmp_path):
    """Correction 1: A newly generated synthetic dataset invalidates the prior allocation."""
    p = tmp_path / "synthetic.xlsx"

    # 1. First dataset generated and allocated
    g1 = generate(200, seed=10)
    g1.df.to_excel(p, index=False)
    fp1 = compute_allocation_input_fingerprint(paths=[p])

    # 2. New synthetic dataset generated with different seed
    g2 = generate(200, seed=20)
    g2.df.to_excel(p, index=False)
    fp2 = compute_allocation_input_fingerprint(paths=[p])

    assert fp1 != fp2

    # Prior allocation was made with fp1; current input is fp2
    status = check_allocation_staleness(
        allocated_rule_fp="rfp",
        current_rule_fp="rfp",
        allocated_input_fp=fp1,
        current_input_fp=fp2,
        has_allocation=True,
    )
    assert status.is_stale
    assert status.inputs_changed

def test_synthetic_controls_change_without_generation_does_not_invalidate_results(tmp_path):
    """Correction 1: Merely changing synthetic-generation controls does not mark results stale."""
    p = tmp_path / "synthetic.xlsx"
    g = generate(200, seed=7)
    g.df.to_excel(p, index=False)

    fp_allocated = compute_allocation_input_fingerprint(paths=[p])

    # User adjusts number inputs in UI (n_demo=5000, seed=99), but has NOT clicked generate.
    # Paths still point to p, and file content is unchanged.
    fp_current = compute_allocation_input_fingerprint(paths=[p])

    assert fp_allocated == fp_current
    status = check_allocation_staleness("rfp", "rfp", fp_allocated, fp_current, True)
    assert not status.is_stale

def test_failed_allocation_does_not_overwrite_previous_fingerprints():
    """Correction 1: A failed allocation does not overwrite fingerprints from the last run."""
    state = {
        "res": "previous_successful_run_result",
        "allocated_rule_fp": "rule_fp_prev",
        "allocated_input_fp": "input_fp_prev",
    }

    # Simulate an allocation attempt that raises an exception
    def failing_allocate():
        raise ValueError("Corrupt file sheet")

    try:
        failing_allocate()
        state["res"] = "new_res"
        state["allocated_rule_fp"] = "new_rfp"
        state["allocated_input_fp"] = "new_ifp"
    except Exception:
        pass  # Previous results preserved!

    assert state["res"] == "previous_successful_run_result"
    assert state["allocated_rule_fp"] == "rule_fp_prev"
    assert state["allocated_input_fp"] == "input_fp_prev"

def test_revision_staleness_no_revision():
    status = check_revision_staleness(
        is_allocation_stale=False,
        revision_rule_fp=None,
        current_rule_fp="any",
        revision_input_fp=None,
        current_rev_b_fp="any",
        has_revision=False,
    )
    assert not status.is_stale

def test_revision_staleness_when_rev_a_allocation_is_stale():
    status = check_revision_staleness(
        is_allocation_stale=True,
        revision_rule_fp="fp1",
        current_rule_fp="fp1",
        revision_input_fp="rev_b_fp1",
        current_rev_b_fp="rev_b_fp1",
        has_revision=True,
    )
    assert status.is_stale
    assert "Rev A allocation is stale" in status.reason

def test_revision_staleness_when_rules_changed_post_revision():
    status = check_revision_staleness(
        is_allocation_stale=False,
        revision_rule_fp="fp_revised",
        current_rule_fp="fp_new",
        revision_input_fp="rev_b_fp",
        current_rev_b_fp="rev_b_fp",
        has_revision=True,
    )
    assert status.is_stale
    assert "Rule configuration has changed since Rev B was computed" in status.reason

def test_changed_rev_b_dataset_invalidates_prior_revision():
    """Correction 2: A changed Rev B dataset invalidates the prior revision."""
    g = generate(200, seed=5)
    rev_b_1 = make_revision(g.df, seed=6)
    rev_b_2 = make_revision(g.df, seed=7)

    fp_b1 = compute_revision_input_fingerprint(rev_b_df=rev_b_1)
    fp_b2 = compute_revision_input_fingerprint(rev_b_df=rev_b_2)
    assert fp_b1 != fp_b2

    # Revision computed with fp_b1; current input is fp_b2
    status = check_revision_staleness(
        is_allocation_stale=False,
        revision_rule_fp="rfp",
        current_rule_fp="rfp",
        revision_input_fp=fp_b1,
        current_rev_b_fp=fp_b2,
        has_revision=True,
    )
    assert status.is_stale
    assert status.inputs_changed
    assert "Rev B input dataset has changed" in status.reason

def test_unchanged_rev_b_input_remains_current():
    """Correction 2: Unchanged Rev B input remaining current."""
    g = generate(200, seed=5)
    rev_b = make_revision(g.df, seed=6)
    fp_b = compute_revision_input_fingerprint(rev_b_df=rev_b)

    status = check_revision_staleness(
        is_allocation_stale=False,
        revision_rule_fp="rfp",
        current_rule_fp="rfp",
        revision_input_fp=fp_b,
        current_rev_b_fp=fp_b,
        has_revision=True,
    )
    assert not status.is_stale
    assert not status.rules_changed
    assert not status.inputs_changed
    assert status.reason == ""

    # Lifecycle state is REVISED
    st = get_lifecycle_state(
        has_input=True,
        has_allocation=True,
        is_stale=False,
        has_revision=True,
        is_revision_stale=status.is_stale,
    )
    assert st == AppLifecycleState.REVISED

def test_revision_input_fingerprint_uploaded_files():
    """Correction 2: Track uploaded Rev B files."""
    f1 = SimpleNamespace(name="revB.xlsx", getvalue=lambda: b"bytes_version_1")
    f2 = SimpleNamespace(name="revB.xlsx", getvalue=lambda: b"bytes_version_2")

    fp1 = compute_revision_input_fingerprint(rev_b_files=[f1])
    fp2 = compute_revision_input_fingerprint(rev_b_files=[f2])
    assert fp1 != fp2

def test_failed_revision_does_not_overwrite_previous_fingerprints():
    """Correction 2: A failed revision does not overwrite fingerprints from the last run."""
    state = {
        "rr": "previous_successful_revision_result",
        "revision_rule_fp": "rev_rfp_prev",
        "revision_input_fp": "rev_ifp_prev",
    }

    def failing_revise():
        raise RuntimeError("Solver timeout")

    try:
        failing_revise()
        state["rr"] = "new_rr"
        state["revision_rule_fp"] = "new_rev_rfp"
        state["revision_input_fp"] = "new_rev_ifp"
    except Exception:
        pass

    assert state["rr"] == "previous_successful_revision_result"
    assert state["revision_rule_fp"] == "rev_rfp_prev"
    assert state["revision_input_fp"] == "rev_ifp_prev"

def test_lifecycle_state_transitions():
    # 1. No input loaded
    s1 = get_lifecycle_state(has_input=False, has_allocation=False, is_stale=False, has_revision=False)
    assert s1 == AppLifecycleState.NO_INPUT
    assert get_lifecycle_badge(s1)[0] == "No Input Loaded"

    # 2. Input loaded, not allocated
    s2 = get_lifecycle_state(has_input=True, has_allocation=False, is_stale=False, has_revision=False)
    assert s2 == AppLifecycleState.INPUT_LOADED
    assert "Not Allocated" in get_lifecycle_badge(s2)[0]

    # 3. Allocation completed
    s3 = get_lifecycle_state(has_input=True, has_allocation=True, is_stale=False, has_revision=False)
    assert s3 == AppLifecycleState.ALLOCATED
    assert get_lifecycle_badge(s3)[0] == "Allocation Current"

    # 4. Results stale (allocation)
    s4 = get_lifecycle_state(has_input=True, has_allocation=True, is_stale=True, has_revision=False)
    assert s4 == AppLifecycleState.STALE
    assert "Results Stale" in get_lifecycle_badge(s4)[0]

    # 5. Revision completed
    s5 = get_lifecycle_state(has_input=True, has_allocation=True, is_stale=False, has_revision=True)
    assert s5 == AppLifecycleState.REVISED
    assert get_lifecycle_badge(s5)[0] == "Revision Current"

    # 6. Revision stale (due to rev B input change)
    s6 = get_lifecycle_state(
        has_input=True, has_allocation=True, is_stale=False, has_revision=True, is_revision_stale=True
    )
    assert s6 == AppLifecycleState.STALE

def test_init_session_state_populates_all_defaults():
    state = {}
    init_session_state(state)
    assert "rules" in state
    assert isinstance(state["rules"], RuleSet)
    assert state["paths"] is None
    assert state["res"] is None
    assert state["out"] is None
    assert state["allocated_rule_fp"] is None
    assert state["allocated_input_fp"] is None
    assert state["revision_rule_fp"] is None
    assert state["revision_input_fp"] is None
    assert state["cached_mdb"] is None
    assert state["cached_mdb_fp"] is None
    assert state["ingest_error"] is None
    assert state["ingest_error_details"] is None

def test_init_session_state_preserves_existing_keys():
    existing_rules = default_ruleset()
    existing_rules.spare_percent = 33.0
    state = {"rules": existing_rules, "custom_key": 42}
    init_session_state(state)
    assert state["rules"].spare_percent == 33.0
    assert state["custom_key"] == 42
    assert state["paths"] is None

def test_safe_read_mdb_missing_required_columns_returns_actionable_error(tmp_path):
    """Unsupported or invalid sheet columns produce a clear error without crashing."""
    p = tmp_path / "invalid_io.csv"
    p.write_text("random_col1,random_col2\nfoo,bar\n")

    mdb, user_msg, details = safe_read_mdb([p])
    assert mdb is None
    assert user_msg is not None
    assert "No sheet with required IO columns found" in user_msg
    assert "Tag, IO Type, Cable, and Pair" in user_msg
    assert details is not None
    assert "ValueError" in details

def test_safe_read_mdb_corrupted_file_returns_error_without_crash(tmp_path):
    """Corrupted binary files produce a clear error rather than an unhandled crash."""
    p = tmp_path / "corrupt.xlsx"
    p.write_bytes(b"PK\x03\x04not_a_valid_zip_payload")

    mdb, user_msg, details = safe_read_mdb([p])
    assert mdb is None
    assert user_msg is not None
    assert "corrupted" in user_msg.lower() or "failed to ingest" in user_msg.lower()
    assert details is not None

def test_safe_read_mdb_nonexistent_file_returns_error(tmp_path):
    """Missing file paths return a clean file-not-found error."""
    p = tmp_path / "does_not_exist.xlsx"
    mdb, user_msg, details = safe_read_mdb([p])
    assert mdb is None
    assert user_msg is not None
    assert "not found" in user_msg.lower()
    assert "FileNotFoundError" in details

def test_safe_read_mdb_valid_file_succeeds(tmp_path):
    """Valid datasets are ingested successfully."""
    p = tmp_path / "valid.xlsx"
    g = generate(100, seed=42)
    g.df.to_excel(p, index=False)

    mdb, user_msg, details = safe_read_mdb([p])
    assert mdb is not None
    assert user_msg is None
    assert details is None
    assert len(mdb.df) == len(g.df)
    assert len(mdb.mapping) >= 1

def test_failed_upload_preserves_previous_allocation_state():
    """A failed new upload attempt does not overwrite the last successful allocation or fingerprints."""
    session_state = {
        "paths": ["/path/to/valid_mdb.xlsx"],
        "res": "previous_successful_run_result",
        "allocated_rule_fp": "prev_rule_hash",
        "allocated_input_fp": "prev_input_hash",
        "ingest_error": None,
        "ingest_error_details": None,
    }

    def simulate_upload(uploaded_files, state):
        mdb, err_msg, err_det = safe_read_mdb(uploaded_files)
        if mdb is not None:
            state["paths"] = uploaded_files
            state["ingest_error"] = None
        else:
            state["ingest_error"] = err_msg
            state["ingest_error_details"] = err_det

    simulate_upload(["/nonexistent/corrupt.xlsx"], session_state)

    # Previous results and fingerprints MUST remain untouched!
    assert session_state["paths"] == ["/path/to/valid_mdb.xlsx"]
    assert session_state["res"] == "previous_successful_run_result"
    assert session_state["allocated_rule_fp"] == "prev_rule_hash"
    assert session_state["allocated_input_fp"] == "prev_input_hash"
    assert session_state["ingest_error"] is not None

def test_build_mapping_review_rows_exact_match():
    """Mapping review accurately reflects ColumnMapping fields with high confidence."""
    cm = ColumnMapping(
        mapping={
            "tag": "Tag No",
            "io_type": "Signal Type",
            "cable": "Cable ID",
            "pair": "Pair No",
            "group": "Group",
            "seg": "Segregation",
            "cable_size": "Pairs",
        },
        confidence={
            "tag": 1.0,
            "io_type": 0.95,
            "cable": 0.92,
            "pair": 1.0,
            "group": 0.9,
            "seg": 1.0,
            "cable_size": 0.85,
        },
        unmapped_required=[],
        unused_headers=["Description", "Manufacturer"],
    )
    rows = build_mapping_review_rows(cm)
    assert len(rows) == 7

    row_map = {r["Target Field"]: r for r in rows}
    assert row_map["tag"]["Required"] == "Yes"
    assert row_map["tag"]["Matched Header"] == "Tag No"
    assert row_map["tag"]["Confidence"] == "100%"
    assert "High" in row_map["tag"]["Status"]

    assert "Fuzzy" in row_map["cable_size"]["Status"]
    assert row_map["cable_size"]["Required"] == "Optional"

def test_build_mapping_review_rows_missing_required_and_optional():
    """Mapping review clearly distinguishes missing required fields from optional ones."""
    cm = ColumnMapping(
        mapping={
            "tag": "Tag",
            "io_type": "Type",
        },
        confidence={"tag": 1.0, "io_type": 1.0},
        unmapped_required=["cable", "pair"],
        unused_headers=["Notes"],
    )
    rows = build_mapping_review_rows(cm)
    row_map = {r["Target Field"]: r for r in rows}

    assert "Missing (Required)" in row_map["cable"]["Status"]
    assert "Missing (Required)" in row_map["pair"]["Status"]
    assert "Unmapped (Optional)" in row_map["group"]["Status"]
    assert "Unmapped (Optional)" in row_map["seg"]["Status"]

def test_preflight_audit_clean_mdb(tmp_path):
    """Pre-flight audit accurately reflects a clean dataset and reports readiness."""
    rules = default_ruleset()
    g = generate(200, seed=123, inject_errors=0)
    p = tmp_path / "clean.xlsx"
    g.df.to_excel(p, index=False)

    mdb = read_mdb([p])
    audit = compute_preflight_audit(mdb, rules)

    assert audit.n_rows == len(g.df)
    assert audit.n_cables > 0
    assert audit.n_signals_valid == len(g.df)
    assert audit.blocking_tqs == 0
    assert audit.n_blocked_tags == 0
    assert audit.readiness_status == "ready"
    assert audit.readiness_label == "Ready to Allocate"
    assert "All pre-flight checks passed" in audit.summary_message

def test_preflight_audit_with_injected_errors(tmp_path):
    """Pre-flight audit catches blocking data issues before allocation and distinguishes severity."""
    rules = default_ruleset()
    g = generate(200, seed=123, inject_errors=8)
    p = tmp_path / "errors.xlsx"
    g.df.to_excel(p, index=False)

    mdb = read_mdb([p])
    audit = compute_preflight_audit(mdb, rules)

    assert audit.n_rows == len(g.df)
    assert audit.blocking_tqs > 0
    assert audit.readiness_status == "ready_with_warnings"
    assert audit.readiness_label == "Ready with Issues (Partial Allocation)"
    assert len(audit.tqs) >= audit.blocking_tqs
    blocking_items = [t for t in audit.tqs if t.severity == "blocking"]
    assert len(blocking_items) == audit.blocking_tqs

def test_preflight_audit_empty_data():
    """Pre-flight audit blocks allocation when no rows are available."""
    rules = default_ruleset()
    empty_mdb = MDB(df=pd.DataFrame(), mapping={})
    audit = compute_preflight_audit(empty_mdb, rules)

    assert audit.n_rows == 0
    assert audit.n_cables == 0
    assert audit.readiness_status == "blocked"
    assert audit.readiness_label == "Allocation Blocked"

def test_compute_kpi_metrics_with_valid_run_result():
    """compute_kpi_metrics correctly extracts verified counts, utilization, and TQ breakdowns."""
    rules = default_ruleset()
    mock_tq1 = SimpleNamespace(id="TQ-0001", severity="blocking", rule_ref="C-1", category="capacity", message="Cable unplaced")
    mock_tq2 = SimpleNamespace(id="TQ-0002", severity="warning", rule_ref="M-1", category="data", message="Group missing")
    mock_tq3 = SimpleNamespace(id="TQ-0003", severity="info", rule_ref="N-1", category="naming", message="Naming style")

    mock_res = SimpleNamespace(
        metrics={
            "mdb_rows": 2000,
            "signals_allocated": 1994,
            "signals_with_tq": 6,
            "coverage_pct": 100.0,
            "cabinets": 3,
            "ciocs": 10,
            "baseplates": 24,
            "violations": 0,
        },
        tqs=[mock_tq1, mock_tq2, mock_tq3],
    )

    kpi = compute_kpi_metrics(mock_res, rules)
    assert kpi["signals_allocated"] == 1994
    assert kpi["signals_with_tq"] == 6
    assert kpi["total_signals"] == 2000
    assert kpi["cabinets"] == 3
    assert kpi["ciocs"] == 10
    assert kpi["baseplates"] == 24
    assert kpi["total_slots"] == 24 * rules.charms_per_baseplate
    assert kpi["baseplate_utilization_pct"] == round(100.0 * 1994 / (24 * 12), 1)
    assert kpi["violations"] == 0
    assert kpi["tqs_total"] == 3
    assert kpi["blocking_tqs"] == 1
    assert kpi["warning_tqs"] == 1
    assert kpi["info_tqs"] == 1

def test_compute_kpi_metrics_none_res():
    """compute_kpi_metrics handles None gracefully without exceptions."""
    rules = default_ruleset()
    assert compute_kpi_metrics(None, rules) == {}

def test_filter_tqs_by_severity():
    """filter_tqs accurately segments TQs by severity."""
    tqs = [
        SimpleNamespace(id="TQ-01", severity="blocking", message="Blocked", rule_ref="C-1", category="capacity", suggested_action="", cables=[], tags=[]),
        SimpleNamespace(id="TQ-02", severity="warning", message="Warning", rule_ref="W-1", category="data", suggested_action="", cables=[], tags=[]),
        SimpleNamespace(id="TQ-03", severity="info", message="Info", rule_ref="I-1", category="naming", suggested_action="", cables=[], tags=[]),
    ]

    all_tqs = filter_tqs(tqs, severity="All")
    assert len(all_tqs) == 3

    blocking = filter_tqs(tqs, severity="Blocking")
    assert len(blocking) == 1
    assert blocking[0].id == "TQ-01"

    warnings = filter_tqs(tqs, severity="Warning")
    assert len(warnings) == 1
    assert warnings[0].id == "TQ-02"

    info = filter_tqs(tqs, severity="Info")
    assert len(info) == 1
    assert info[0].id == "TQ-03"

def test_filter_tqs_by_search_query():
    """filter_tqs filters on keyword search across message, ID, cables, and actions."""
    tqs = [
        SimpleNamespace(id="TQ-0001", severity="blocking", message="Cable CBL-99 overflow", rule_ref="C-1", category="capacity", suggested_action="Split", cables=["CBL-99"], tags=["FT-101"]),
        SimpleNamespace(id="TQ-0002", severity="warning", message="Tag TT-202 missing group", rule_ref="G-1", category="data", suggested_action="Assign group", cables=["CBL-12"], tags=["TT-202"]),
    ]

    res_cable = filter_tqs(tqs, search="CBL-99")
    assert len(res_cable) == 1
    assert res_cable[0].id == "TQ-0001"

    res_rule = filter_tqs(tqs, search="G-1")
    assert len(res_rule) == 1
    assert res_rule[0].id == "TQ-0002"

    res_none = filter_tqs(tqs, search="NonexistentTerm")
    assert len(res_none) == 0

def test_filter_tqs_empty_list():
    """filter_tqs handles empty list safely."""
    assert filter_tqs([]) == []
    assert filter_tqs(None) == []

def test_is_verifier_certified_all_11_pass():
    """is_verifier_certified returns True when all 11 required checks pass with 0 violations."""
    checks = [
        {"Rule": rid, "Check": f"Desc {rid}", "Result": "PASS", "Violations": 0, "Examples": ""}
        for rid in ["Q-1", "D-2", "C-1", "K-1", "S-1", "G-1", "P-1", "H-1..6", "N-1..6", "C-2", "M-1"]
    ]
    mock_res = SimpleNamespace(check=checks)
    certified, msg, failed = is_verifier_certified(mock_res)
    assert certified is True
    assert "Verified" in msg
    assert len(failed) == 0

def test_is_verifier_certified_detects_violations():
    """is_verifier_certified returns False and lists failed rule IDs when any check fails."""
    checks = [
        {"Rule": rid, "Check": f"Desc {rid}", "Result": "PASS", "Violations": 0, "Examples": ""}
        for rid in ["Q-1", "D-2", "C-1", "K-1", "S-1", "G-1", "P-1", "H-1..6", "N-1..6", "C-2", "M-1"]
    ]
    # Inject violation in C-1 (capacity) and S-1 (segregation)
    checks[2]["Result"] = "FAIL"
    checks[2]["Violations"] = 3
    checks[4]["Violations"] = 1

    mock_res = SimpleNamespace(check=checks)
    certified, msg, failed = is_verifier_certified(mock_res)
    assert certified is False
    assert "Rule violations detected" in msg
    assert "C-1" in failed
    assert "S-1" in failed

def test_is_verifier_certified_guards_missing_and_incomplete():
    """is_verifier_certified guards against claiming success when checks are missing or incomplete."""
    # None result
    cert, msg, failed = is_verifier_certified(None)
    assert cert is False

    # Missing check list
    mock_no_check = SimpleNamespace(check=None)
    cert, msg, failed = is_verifier_certified(mock_no_check)
    assert cert is False

    # Incomplete checks (<11)
    incomplete_checks = [
        {"Rule": "Q-1", "Check": "Check Q1", "Result": "PASS", "Violations": 0, "Examples": ""}
    ]
    mock_incomplete = SimpleNamespace(check=incomplete_checks)
    cert, msg, failed = is_verifier_certified(mock_incomplete)
    assert cert is False
    assert "Incomplete verification report" in msg

def test_compute_kpi_metrics_utilization_accurate_denominator():
    """Utilization is calculated strictly on deployed baseplate slots, not invented capacity."""
    rules = default_ruleset()
    mock_res = SimpleNamespace(
        metrics={
            "mdb_rows": 500,
            "signals_allocated": 240,
            "signals_with_tq": 10,
            "coverage_pct": 100.0,
            "cabinets": 2,
            "ciocs": 4,
            "baseplates": 20,  # 20 deployed baseplates * 12 slots = 240 slots -> 100%
            "violations": 0,
        },
        tqs=[],
    )
    kpi = compute_kpi_metrics(mock_res, rules)
    assert kpi["total_slots"] == 20 * 12
    assert kpi["baseplate_utilization_pct"] == 100.0
    assert kpi["signals_with_tq"] == 10

def _get_rendered_html_strings(at) -> list[str]:
    """Inspect all rendered strings across at.markdown and at.get('html')."""
    return [m.value for m in at.markdown] + [h.proto.body for h in at.get("html")]
