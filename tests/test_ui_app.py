"""Headless journeys through the real pages (Streamlit AppTest). No mocks of the engine."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.core.session import (compute_status, ensure_session, load_synthetic, run_allocation,  # noqa: E402
                              run_revision, set_revision_synthetic)

ENTRY = str(ROOT / "app" / "streamlit_app.py")
HARNESS = str(ROOT / "tests" / "_page_harness.py")


def page(target: str, state: dict | None = None) -> AppTest:
    os.environ["SS_TARGET"] = target
    at = AppTest.from_file(HARNESS, default_timeout=120)
    at.run()
    if state is not None:
        for k, v in state.items():
            at.session_state[k] = v
        at.run()
    return at


@pytest.fixture(scope="module")
def loaded_state():
    d: dict = {}
    ensure_session(d)
    load_synthetic(d, 300, 3, 2)
    return d


@pytest.fixture(scope="module")
def allocated_state():
    d: dict = {}
    ensure_session(d)
    load_synthetic(d, 300, 3, 2)
    assert run_allocation(d)[0]
    return d


@pytest.fixture(scope="module")
def revised_state():
    d: dict = {}
    ensure_session(d)
    load_synthetic(d, 300, 3, 2)
    assert run_allocation(d)[0]
    assert set_revision_synthetic(d)
    assert run_revision(d)[0]
    return d


def texts(at: AppTest) -> str:
    return " ".join([m.value for m in at.markdown] + [e.value for e in at.error] + [b.label for b in at.button])


def html_blob(at: AppTest) -> str:
    return " ".join(getattr(e, "value", "") or "" for e in at.get("html")) if hasattr(at, "get") else ""


# ----------------------------------------------------------------------------- landing
def test_landing_renders_without_exception_and_without_sidebar_navigation():
    at = page("landing")
    assert not at.exception
    labels = [b.label for b in at.button]
    assert "Open the workbench" in labels and "Run the synthetic demo" in labels
    assert len(at.sidebar.children) == 0          # no workbench chrome on the landing page


def test_landing_demo_cta_loads_dataset_and_opens_review():
    os.environ["SS_TARGET"] = "landing"
    at = AppTest.from_file(HARNESS, default_timeout=120).run()
    at.button(key="hero_demo").click().run()
    assert not at.exception
    ds = at.session_state["dataset"]
    assert ds["synthetic"] is True and "2,000" in ds["label"]
    assert at.session_state["paths"]
    assert "Review the data" in html_blob(at)   # landed on the Review page


# ----------------------------------------------------------------------------- empty states and routes
@pytest.mark.parametrize("target", ["review", "allocate", "results", "cabinets", "revise", "deliverables"])
def test_every_workbench_page_has_an_empty_state_without_data(target):
    at = page(target)
    assert not at.exception
    assert at.button, "empty state must offer an action"


def test_input_page_renders_with_defaults():
    at = page("input")
    assert not at.exception
    assert [n.value for n in at.number_input] == [2000, 7, 6]


# ----------------------------------------------------------------------------- pages with data
def test_review_page_shows_findings_and_next_action(loaded_state):
    at = page("review", loaded_state)
    assert not at.exception
    assert any(b.label == "Set up allocation" for b in at.button)


def test_allocate_page_has_no_duplicate_widget_keys_and_generates_summary(loaded_state):
    # regression: the previous UI crashed here with StreamlitDuplicateElementKey in a real browser
    at = page("allocate", loaded_state)
    assert not at.exception
    keys = [t.key for t in at.toggle]
    assert len(keys) == len(set(keys)) == 2   # only the switches the engine honours (R1, R2)
    summary = " ".join(h.value for h in at.get("html"))
    assert "4 of 32 baseplates" in summary        # computed from the default rules, not static text


def test_changing_spare_percent_changes_summary_and_marks_results_stale(allocated_state):
    at = page("allocate", allocated_state)
    at.slider(key="rule::spare_percent").set_value(25.0).run()
    assert not at.exception
    html = " ".join(h.value for h in at.get("html"))
    assert "8 of 32 baseplates" in html           # 25% of 32
    assert compute_status(at.session_state).alloc.is_stale is True
    assert "Results stale" in html


def test_results_page_reports_verification_and_counts(allocated_state):
    at = page("results", allocated_state)
    assert not at.exception
    html = " ".join(h.value for h in at.get("html"))
    assert "no violations" in html.lower() and "Held as queries" in html
    assert "certified" not in html.lower() and "guarantee" not in html.lower()


def test_results_page_flags_stale_results(allocated_state):
    state = dict(allocated_state)
    import copy
    rules = copy.deepcopy(state["rules"]); rules.spare_percent = 30.0
    state["rules"] = rules
    at = page("results", state)
    html = " ".join(h.value for h in at.get("html"))
    assert "out of date" in html


def test_cabinets_page_renders_grid_with_labels(allocated_state):
    at = page("cabinets", allocated_state)
    assert not at.exception
    html = " ".join(h.value for h in at.get("html"))
    assert html.count("ss-slot") >= 96
    assert 'aria-label="' in html and "Free slot" in html


def test_revise_page_shows_solver_status_and_download(revised_state):
    at = page("revise", revised_state)
    assert not at.exception
    html = " ".join(h.value for h in at.get("html"))
    assert "Rev B verification" in html
    assert any(w in html for w in ("No solver repair was needed", "proven exact", "best-found", "fully re-allocated"))


def test_deliverables_lists_real_sheets(revised_state):
    at = page("deliverables", revised_state)
    assert not at.exception
    html = " ".join(h.value for h in at.get("html"))
    for sheet in ("IO Allocation", "Cabinet Summary", "TQ List", "Rule Check", "Revision Impact"):
        assert sheet in html


def test_deliverables_disabled_when_stale(allocated_state):
    import copy
    state = dict(allocated_state)
    rules = copy.deepcopy(state["rules"]); rules.spare_percent = 33.0
    state["rules"] = rules
    at = page("deliverables", state)
    assert any(b.disabled for b in at.get("download_button"))


# ----------------------------------------------------------------------------- state hygiene
def test_failed_ingest_keeps_previous_dataset(tmp_path, loaded_state):
    from app.core.session import load_uploads
    d = dict(loaded_state)
    before = list(d["paths"])
    bad = tmp_path / "broken.xlsx"
    bad.write_bytes(b"not an excel file")
    ok, err = load_uploads(d, [bad])
    assert ok is False and err
    assert d["paths"] == before and d["ingest_error"]


def test_failed_allocation_keeps_previous_results(allocated_state, monkeypatch):
    import app.core.session as sess
    d = dict(allocated_state)
    prev = d["res"]
    monkeypatch.setattr(sess, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    ok, err = run_allocation(d)
    assert ok is False and "boom" in err
    assert d["res"] is prev


def test_leaving_and_returning_keeps_session(allocated_state):
    at = page("results", allocated_state)
    at.run()
    assert at.session_state["res"] is allocated_state["res"]
    at2 = page("landing", {k: allocated_state[k] for k in allocated_state})
    assert at2.session_state["res"] is allocated_state["res"]
