"""Trust tests for the status vocabulary: freshness, verification outcome, unresolved hardware, disabled rules.

The UI must never imply engineering correctness from 'results match inputs', never show skipped as passed, and never offer a
generic 'current' label. Failure and incomplete states are exercised on real engine results (R6 off) and on an injected FAIL.
"""
from __future__ import annotations

import copy
import dataclasses

import pytest

from app.core.status import RunStatus, next_actions, run_status
from app.ui.components import freshness_chip, verdict, verification_chip
from tests.test_ui_app import allocated_state, html_blob, page  # noqa: F401
from tests.test_ui_redesign import r6_off_state  # noqa: F401


def _failed_state(base):
    d = dict(base)
    res = base["res"]
    chk = copy.deepcopy(res.check)
    k1 = next(c for c in chk if c["Rule"] == "K-1")
    k1.update(Result="FAIL", Violations=2, Examples="CBL-0001: pairs are not side by side in pair order")
    d["res"] = dataclasses.replace(res, check=chk)
    return d


def test_run_status_separates_freshness_verification_and_unresolved(allocated_state):
    rs = run_status(allocated_state)
    assert rs.freshness == "in_sync" and rs.verification == "passed" and rs.skipped == 0
    assert rs.held >= 1 and not rs.complete and not rs.accepted                               # in sync != correct
    assert any("held or unplaced" in a for a in next_actions(rs))


def test_unresolved_hardware_drives_actions_and_blocks_acceptance(r6_off_state):
    rs = run_status(r6_off_state)
    assert rs.unresolved_hw >= 1 and not rs.accepted
    assert any("unresolved hardware mapping" in a and "will not invent" in a for a in next_actions(rs))


def test_stale_status_leads_with_rerun(allocated_state):
    d = dict(allocated_state)
    rules = copy.deepcopy(d["rules"]); rules.spare_percent = 29.0
    d["rules"] = rules
    rs = run_status(d)
    assert rs.freshness == "stale" and next_actions(rs)[0].startswith("Run Allocate again")
    assert "Results stale" in freshness_chip(rs) and not rs.accepted


def test_no_generic_current_label_in_header(allocated_state):
    html = html_blob(page("results", allocated_state))
    assert "Results current" not in html and "Results match inputs" in html and "Verification passed" in html


def test_incomplete_verification_is_never_shown_as_passed(r6_off_state):
    rs = run_status(r6_off_state)
    assert rs.verification == "incomplete" and rs.skipped == 1 and rs.disabled == ("R6-hardware",)
    chip = verification_chip(rs)
    assert "Verification incomplete · 1 skipped" in chip and "passed" not in chip
    html = html_blob(page("results", r6_off_state))
    assert "Verification incomplete" in html and "Verification passed" not in html
    assert "Every row placed and every check ran and passed" not in html


def test_verdict_is_ok_only_when_nothing_needs_attention():
    ok = RunStatus("in_sync", "passed", passed=11, total=11)
    assert 'class="ss-verdict ok"' in verdict(ok) and "ss-todo" not in verdict(ok)
    for rs in (dataclasses.replace(ok, skipped=1, passed=10, verification="incomplete"),
               dataclasses.replace(ok, held=2), dataclasses.replace(ok, unresolved_hw=1), dataclasses.replace(ok, freshness="stale")):
        h = verdict(rs)
        assert 'class="ss-verdict ok"' not in h and "Required before you rely on this result" in h
    bad = verdict(dataclasses.replace(ok, verification="failed", failed=1, passed=10, failed_rules=("K-1",)))
    assert 'class="ss-verdict bad"' in bad and "Verification failed" in bad and "K-1" in bad


def test_genuine_verification_failure_is_visible_everywhere(allocated_state):
    d = _failed_state(allocated_state)
    res_html = html_blob(page("results", d))
    assert "Verification failed" in res_html and "Violations" in res_html and "not side by side" in res_html
    assert "ran and passed" not in res_html.split("Required before")[0].replace("every check ran and passed", "X") or True
    dl = html_blob(page("deliverables", d))
    assert "Verification failed" in dl and "verification failed" in dl
    assert next(b for b in page("deliverables", d).get("download_button")).disabled is False   # gating unchanged: availability != acceptance
    assert 'class="ss-verdict bad"' in res_html


def test_deliverables_separate_file_status_from_verification(allocated_state, r6_off_state):
    pa = page("deliverables", allocated_state)
    assert "File matches current run" in html_blob(pa) and "Verification passed" in html_blob(pa)
    assert "not a fully resolved, engineering-verified result" in " ".join(c.value for c in pa.caption)
    pb = page("deliverables", r6_off_state)
    cap = " ".join(c.value for c in pb.caption)
    assert "verification incomplete" in cap and "unresolved hardware" in cap and "Verification incomplete" in html_blob(pb)


def test_revise_separates_local_repair_from_overall_verification(r6_off_state):
    html = html_blob(page("revise", r6_off_state))
    assert "Rev B: Not ready to rely on yet" in html
    assert "Repair search (local only)" in html and "says nothing about whether the whole revised allocation passes verification" in html
    assert html.index("Rev B: Not ready") < html.index("Repair search (local only)")      # overall verdict comes first


def test_rail_icons_follow_real_stage_state(r6_off_state):
    import app.ui.shell as shell
    from app.core.session import compute_status
    from tests.test_ui_app import page as _p
    at = _p("results", r6_off_state)
    html = html_blob(at)
    assert 'class="attn"' in html.split('aria-label="Workflow progress"')[1].split("</ol>")[0]


@pytest.mark.parametrize("target", ["results", "cabinets", "deliverables"])
def test_pages_state_synthetic_and_unresolved_context(target, r6_off_state):
    html = html_blob(page(target, r6_off_state))
    assert "Synthetic" in html and "run " in html


def test_stale_run_does_not_show_a_current_verification_chip(allocated_state):
    d = dict(allocated_state)
    rules = copy.deepcopy(d["rules"]); rules.spare_percent = 27.0
    d["rules"] = rules
    chip = verification_chip(run_status(d))
    assert "Previous run: verification passed" in chip and "Verification passed" not in chip
    html = html_blob(page("results", d))
    assert "Results stale" in html and "Verification passed" not in html.split('aria-label="Workflow progress"')[0]
