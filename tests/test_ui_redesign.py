"""Tests for the v3 redesign: workflow strip state, composition bar, honest rule switches, landing story, cabinet jump."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.core.demo import build_demo  # noqa: E402
from app.ui.components import change_kind, composition_bar, stage_strip  # noqa: E402
from app.ui.flow import story_html, viz_html  # noqa: E402
from app.views.allocate import SWITCHABLE  # noqa: E402
from tests.test_ui_app import allocated_state, html_blob, loaded_state, page  # noqa: E402,F401


def test_stage_strip_marks_current_and_escapes():
    html = stage_strip([("Import", "done", "✓", "dataset loaded"), ("Review", "cur", "●", "<b>x</b>")])
    assert 'aria-current="step"' in html and "&lt;b&gt;" in html and "<b>x</b>" not in html


def test_composition_bar_counts_and_labels():
    html = composition_bar(90, 8, 2)
    assert "90 placed, 8 held, 2 not placed" in html and "width:90.00%" in html


def test_change_kind_uses_symbol_not_only_colour():
    assert "→" in change_kind("Moved") and "+" in change_kind("Added") and "−" in change_kind("Deleted / not allocated in Rev B")


def test_only_engine_honoured_rules_are_switchable():
    # R3/R4/R7 are never read by the engine; R5 and R6 only change which checks the verifier runs. A UI switch is offered
    # only for R1/R2, which change the allocation itself.
    assert set(SWITCHABLE) == {"R1-grouping", "R2-segregation"}


def test_workflow_strip_reflects_real_state(loaded_state, allocated_state):
    at = page("review", loaded_state)
    html = html_blob(at)
    assert "Step 2 of 7" in html and 'aria-current="step"' in html
    assert "needs an allocation" in html          # downstream stages are locked until a run exists
    at2 = page("results", allocated_state)
    assert "verified" in html_blob(at2) or "blocking quer" in html_blob(at2)


def test_results_never_calls_a_partial_allocation_complete(allocated_state):
    html = html_blob(page("results", allocated_state))
    assert "Not ready to rely on yet" in html and "Allocation success is not verification success" in html
    assert "Every row placed and every check ran and passed" not in html


def test_landing_story_is_real_engine_output_and_labelled_synthetic():
    b = build_demo()
    story, viz = story_html(b), viz_html(b)
    assert "Synthetic demo" in viz and f"{len(b.check)}" in viz
    assert story.count("ss-ch c") == 4 and "<script" not in story.lower()
    assert f"{b.n_rows:,}" in story


def test_cabinet_jump_preselects_cabinet_and_search(allocated_state):
    rows = allocated_state["res"].rows
    hit = next(r for r in rows if r.get("Slot") and r.get("Status") == "Allocated")
    state = dict(allocated_state)
    state["cab_jump"] = {"cab": hit["Marshalling Cabinet"], "q": hit["Tag"]}
    at = page("cabinets", state)
    assert not at.exception
    assert at.text_input(key="cab_q").value == hit["Tag"]
    assert at.selectbox(key="cab_sel").value == hit["Marshalling Cabinet"]


def test_loaded_ruleset_with_unsupported_switch_off_warns(allocated_state):
    import copy
    state = dict(allocated_state)
    rules = copy.deepcopy(state["rules"])
    next(t for t in rules.toggles if t.id == "R3-capacity").enabled = False
    state["rules"] = rules
    html = html_blob(page("allocate", state))
    assert "switches rules off" in html and "R3-capacity" in html and "SKIPPED, never PASS" in html


# ----------------------------------------------------------------------------- v4: bench, cursor, links, icons, readout
def test_bench_traces_real_engine_rows_and_escapes():
    from app.ui.flow import bench_html
    b = build_demo()
    html = bench_html(b, "hero")
    assert html.count('class="ss-lane ') == len(b.signals[:4]) == 4
    for sig in b.signals[:4]:
        assert sig.row["CHARM Address"].split("-")[0] in html          # addresses come from the engine row
        assert sig.tag in html and sig.source_line.split("· ")[-1] in html
        assert f'<b>{sig.tag}</b>' in html                              # trace readout for each signal
    assert "<script" not in html.lower() and "Synthetic demo data" in html
    assert 'class="ss-bench story"' in bench_html(b, "story")


def test_project_links_are_configurable_and_never_invented():
    from app.core.links import configured_links
    assert all(url is None for _, url in configured_links({}))
    got = dict(configured_links({"SLOTSMITH_REPO_URL": "https://example.org/r", "SLOTSMITH_DOCS_URL": "javascript:alert(1)",
                                 "SLOTSMITH_VIDEO_URL": "http://insecure.example"}))
    assert got["Repository"] == "https://example.org/r"
    assert got["Documentation"] is None and got["Demo video"] is None


def test_footer_has_no_placeholders_and_no_competition_branding(monkeypatch):
    for v in ("SLOTSMITH_REPO_URL", "SLOTSMITH_DOCS_URL", "SLOTSMITH_VIDEO_URL"):
        monkeypatch.delenv(v, raising=False)
    from app.views.landing import _footer
    f = _footer()
    assert "not configured" not in f and "github.com" not in f and "youtube" not in f.lower()
    assert "VIT" not in f and "Mac_Enthu" not in f and "Back to top" in f
    monkeypatch.setenv("SLOTSMITH_REPO_URL", "https://example.org/repo")
    assert 'href="https://example.org/repo"' in _footer()


def test_cursor_layer_is_isolated_and_respects_preferences():
    from app.ui import fx
    from app.ui.theme import stylesheet
    js, css = fx._JS, stylesheet()
    assert "(pointer: fine)" in js and "prefers-reduced-motion: reduce" in js and "window.__ssFx" in js
    assert "<" not in js.replace("=>", "").replace("<=", "").replace("< ", "")   # Streamlit's sanitiser breaks HTML literals in scripts
    assert "pointer-events:none" in css.split(".ss-cursor{")[1].split("}")[0]
    assert "cursor:none" not in css.replace(" ", "")                              # the native cursor is never hidden
    assert "(pointer:coarse),(prefers-reduced-motion:reduce){.ss-cursor{display:none;}" in css
    assert ".ss-cursor.text b,.ss-cursor.text i{opacity:0;}" in css               # text fields keep only the native I-beam


def test_scroll_story_only_animates_without_reduced_motion():
    import re
    from app.ui.theme import stylesheet
    css = stylesheet()
    start = css.index("@media (prefers-reduced-motion:no-preference) and (min-width:1000px){")
    end = css.index("@keyframes ss-ch{")
    spots = [m.start() for m in re.finditer(r"animation-timeline:--story", css)]
    assert spots and all(start < i < end for i in spots)          # every scroll-linked rule sits inside the guarded block
    assert "view-timeline:--story" in css[start:end]
    assert "@media (prefers-reduced-motion:reduce){" in css and "animation:none !important" in css


def test_status_icons_are_css_glyphs_not_svg():
    from app.ui.components import banner, chip, icon
    assert "<svg" not in icon("ok") + chip("ok", "x", "ok") + banner("warn", "t", "b")   # st.html strips <svg>


def test_run_id_is_stable_and_tracks_the_run(allocated_state):
    from app.core.session import run_id
    assert run_id({}) == ""
    a, b = run_id(allocated_state), run_id(dict(allocated_state))
    assert a == b and len(a) == 8
    changed = dict(allocated_state, allocated_rule_fp="different")
    assert run_id(changed) != a


def test_verify_readout_shows_failures_honestly():
    from app.ui.components import verify_readout
    ok = verify_readout([{"Rule": "K-1", "Check": "c", "Result": "PASS"}])
    bad = verify_readout([{"Rule": "K-1", "Check": "c", "Result": "PASS"}, {"Rule": "S-1", "Check": "c", "Result": "FAIL"}])
    assert "No violations found" in ok and 'class="ss-vread ok"' in ok
    assert 'class="ss-vread bad"' in bad and "1 rule family with violations" in bad and "1</b><span>/2" in bad


def test_results_page_shows_the_verification_readout(allocated_state):
    html = html_blob(page("results", allocated_state))
    assert "ss-vread" in html and "Independent check" in html


def test_workbench_header_has_breadcrumb_and_run_id(allocated_state):
    html = html_blob(page("results", allocated_state))
    assert 'aria-label="Breadcrumb"' in html and "run " in html and "Synthetic" in html


def test_single_search_match_is_located_automatically(allocated_state):
    rows = allocated_state["res"].rows
    hit = next(r for r in rows if r.get("Slot") and r.get("Status") == "Allocated")
    state = dict(allocated_state, cab_jump={"cab": hit["Marshalling Cabinet"], "q": hit["Tag"]})
    at = page("cabinets", state)
    html = html_blob(at)
    assert " sel" in html and "selected slot" in html


def test_cabinet_find_survives_stale_state(allocated_state):
    # a stale allocation must still show the stale banner on the cabinets page (no silent success)
    import copy
    state = dict(allocated_state)
    rules = copy.deepcopy(state["rules"]); rules.spare_percent = 31.0
    state["rules"] = rules
    assert "out of date" in html_blob(page("cabinets", state))


# ----------------------------------------------------------------------------- unresolved hardware / skipped checks in the UI
@pytest.fixture(scope="module")
def r6_off_state():
    import copy
    from app.core.session import ensure_session, load_synthetic, run_allocation, run_revision, set_revision_synthetic
    d: dict = {}
    ensure_session(d)
    load_synthetic(d, 300, 3, 6)
    rules = copy.deepcopy(d["rules"])
    next(t for t in rules.toggles if t.id == "R6-hardware").enabled = False
    d["rules"] = rules
    assert run_allocation(d)[0]
    assert set_revision_synthetic(d) and run_revision(d)[0]
    return d


def test_cabinet_marks_unresolved_hardware_distinctly(r6_off_state):
    from app.core.cabinet import build_cabinet, cabinet_names, type_code
    from app.core.state import unresolved_hardware
    from app.ui.cabinet import cabinet_html, legend_html
    res = r6_off_state["res"]
    ids = {t.id for t in unresolved_hardware(res)}
    pairs = {(r["Cable"], int(float(r["Pair"]))): r["TQ Ref"] for r in res.rows if r["TQ Ref"] in ids}
    assert pairs
    found = []
    for cab in cabinet_names(res.rows):
        found += [s for s in build_cabinet(res.rows, cab, pairs).all_slots() if s.reason == "hardware"]
    assert found and all(s.kind == "held" and s.code == "" and s.tq_ref in ids for s in found)
    html = cabinet_html(build_cabinet(res.rows, cabinet_names(res.rows)[0], pairs))
    assert "ss-slot" in html
    assert type_code({"IO Type": "PULSE-XYZ", "Terminal Block": ""}) == ""        # never the AI tint
    assert type_code({"IO Type": float("nan"), "Terminal Block": ""}) == ""
    assert "Unresolved hardware" in legend_html() and "t-ai" not in legend_html().split("Unresolved")[1]


def test_signal_row_without_hardware_is_never_drawn_as_a_normal_slot():
    from app.core.cabinet import build_cabinet
    row = {"Marshalling Cabinet": "C1", "Slot": 1, "CIOC": "I1", "_cioc": 1, "_bp": 1, "Row Kind": "Signal", "Tag": "T1",
           "IO Type": "AI", "CHARM Type": "", "Terminal Block": "", "Cable": "CB", "Pair": 1, "Status": "Allocated"}
    s = next(iter(build_cabinet([row], "C1").all_slots()))
    assert s.kind == "held" and s.reason == "hardware" and s.code == ""


def test_results_page_tells_the_incomplete_story(r6_off_state):
    html = html_blob(page("results", r6_off_state))
    assert "unresolved hardware" in html.lower() and "skipped" in html.lower()
    assert "Not a full verification" in html and "A skipped check is not a pass" in html
    assert "all 11 rule families ran and passed" not in html and "Every row was placed" not in html
    assert "Disabled rules" in html and "R6-hardware" in html and "10 passed" in html and "1 skipped" in html


def test_deliverables_disclose_unresolved_and_disabled(r6_off_state):
    html = html_blob(page("deliverables", r6_off_state))
    assert "not a fully resolved, fully verified result" in html
    assert "R6-hardware" in html and "1 signal(s) held" in html and "10 passed, 0 failed, 1 skipped" in html
    assert "incomplete: rules switched off" in html


def test_revise_page_keeps_unresolved_visible(r6_off_state):
    html = html_blob(page("revise", r6_off_state))
    assert "remain unresolved" in html and "skipped" in html and "not a full verification" in html


def test_allocate_page_explains_disabled_rule_semantics(r6_off_state):
    html = html_blob(page("allocate", r6_off_state))
    assert "does not make a violation or an unknown hardware" in html
    assert "SKIPPED, not PASS" in html


def test_workflow_strip_flags_unresolved_hardware(r6_off_state):
    assert "unresolved hardware" in html_blob(page("review", r6_off_state))


def test_verify_readout_marks_skipped_honestly():
    from app.ui.components import verify_readout
    chk = [{"Rule": "K-1", "Check": "c", "Result": "PASS", "Violations": 0}, {"Rule": "H-1..6", "Check": "h", "Result": "SKIPPED",
           "Violations": 0, "Note": "not run: rule R6-hardware is switched off"}]
    html = verify_readout(chk)
    assert 'class="ss-vread inc"' in html and "Not a full verification: 1 skipped" in html and "1 passed · 1 skipped" in html
    assert "No violations found" not in html and 'class="s"' in html
