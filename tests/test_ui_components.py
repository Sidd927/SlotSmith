"""Pure tests for the design system: tokens, contrast, escaping, cabinet model and renderers."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.core.cabinet import build_cabinet, cabinet_names, find_slots, type_code  # noqa: E402
from app.core.demo import build_demo  # noqa: E402
from app.core.revision_view import solver_summary  # noqa: E402
from app.core.rules_view import example_names, rule_summary  # noqa: E402
from app.ui.cabinet import cabinet_html, legend_html  # noqa: E402
from app.ui.components import banner, chip, kv, ledger, tile  # noqa: E402
from app.ui.flow import flow_html  # noqa: E402
from app.ui.theme import TOKENS, stylesheet  # noqa: E402
from slotsmith.pipeline import run  # noqa: E402
from slotsmith.rules import default_ruleset  # noqa: E402


def _lum(hexc: str) -> float:
    h = hexc.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def tok(name: str, mode: int) -> str:
    return TOKENS[name][mode]


MODES = [(0, "light"), (1, "dark")]


# ----------------------------------------------------------------------------- stylesheet
def test_stylesheet_is_small_self_contained_and_has_reduced_motion():
    css = stylesheet()
    assert len(css) < 20_000
    assert "@import" not in css and "http://" not in css and "https://" not in css and "base64" not in css
    assert "prefers-reduced-motion" in css and "animation:none" in css.replace(" ", "")


def test_every_var_used_is_defined():
    css = stylesheet()
    used = set(re.findall(r"var\((--ss-[a-z0-9-]+)", css))
    defined = set(re.findall(r"(--ss-[a-z0-9-]+)\s*:", css))
    assert used <= defined, used - defined


def test_each_colour_token_has_fallback_and_light_dark_pair():
    css = stylesheet()
    for name, (light, dark) in TOKENS.items():
        assert f"--ss-{name}:{light};--ss-{name}:light-dark({light},{dark});" in css


# ----------------------------------------------------------------------------- contrast (design.md section G)
@pytest.mark.parametrize("mode,label", MODES)
def test_text_contrast_on_surfaces(mode, label):
    for surf in ("surface", "bg", "surface-2"):
        assert contrast(tok("text", mode), tok(surf, mode)) >= 7, (label, surf)
        assert contrast(tok("text-2", mode), tok(surf, mode)) >= 4.5, (label, surf, "text-2")
    assert contrast(tok("text-3", mode), tok("surface", mode)) >= 4.5, label
    assert contrast(tok("text-3", mode), tok("bg", mode)) >= 4.5, label


@pytest.mark.parametrize("mode,label", MODES)
def test_accent_and_status_contrast(mode, label):
    assert contrast(tok("accent-fg", mode), tok("accent", mode)) >= 4.5, label
    assert contrast(tok("accent", mode), tok("surface", mode)) >= 4.5, label
    assert contrast(tok("accent", mode), tok("bg", mode)) >= 4.5, label
    for s in ("ok", "warn", "bad", "info"):
        assert contrast(tok(s, mode), tok(f"{s}-soft", mode)) >= 4.5, (label, s)
        assert contrast(tok(s, mode), tok("surface", mode)) >= 4.5, (label, s, "on surface")


@pytest.mark.parametrize("mode,label", MODES)
def test_signal_type_text_contrast(mode, label):
    for t in ("ai", "ao", "di", "do", "df", "rl"):
        assert contrast(tok(f"t-{t}-fg", mode), tok(f"t-{t}", mode)) >= 4.5, (label, t)


@pytest.mark.parametrize("mode,label", MODES)
def test_signal_types_are_distinguishable_from_each_other(mode, label):
    # colour is never the only cue (two-letter codes), but the tints should also differ visibly in luminance or hue
    fills = [tok(f"t-{t}", mode) for t in ("ai", "ao", "di", "do", "df", "rl")]
    assert len(set(fills)) == 6


# ----------------------------------------------------------------------------- escaping (no injected markup)
EVIL = '<img src=x onerror=alert(1)>"&'


def test_components_escape_data():
    for html in (chip("ok", EVIL), banner("info", EVIL, EVIL), tile(EVIL, EVIL, EVIL), kv([(EVIL, EVIL)]),
                 ledger([EVIL], [[EVIL]])):
        assert "<img" not in html and "&lt;img" in html     # escaped text, never a live tag


# ----------------------------------------------------------------------------- cabinet model and renderer
@pytest.fixture(scope="module")
def run_rows():
    d = build_demo()
    from app.core.demo import _canon
    from slotsmith.generator import generate
    g = generate(200, seed=8, inject_errors=3)
    res = run(None, default_ruleset(), None, df=_canon(g.df), verify_from_file=False)
    return res.rows


def test_cabinet_model_matches_engine_rows(run_rows):
    names = cabinet_names(run_rows)
    assert names
    model = build_cabinet(run_rows, names[0])
    n_rows = sum(1 for r in run_rows if r["Marshalling Cabinet"] == names[0] and r.get("Slot"))
    assert sum(1 for _ in model.all_slots()) == n_rows
    sig = next(s for s in model.all_slots() if s.kind == "signal")
    assert sig.address and sig.code in {"AI", "AO", "DI", "DO", "DF", "RL"}


def test_type_codes_follow_terminal_block_and_io_type():
    assert type_code({"Terminal Block": "Fused-injected-power", "IO Type": "DO-SOV"}) == "DF"
    assert type_code({"Terminal Block": "Relay output", "IO Type": "DO-RELAY"}) == "RL"
    assert type_code({"Terminal Block": "Standard", "IO Type": "AI-RTD"}) == "AI"
    assert type_code({"Terminal Block": "Standard", "IO Type": "AO"}) == "AO"
    assert type_code({"Terminal Block": "Standard", "IO Type": "DI"}) == "DI"


def test_search_finds_exactly_the_tag_and_filters_by_type(run_rows):
    model = build_cabinet(run_rows, cabinet_names(run_rows)[0])
    tag = next(s.tag for s in model.all_slots() if s.kind == "signal")
    hits = find_slots(model, tag)
    assert len(hits) == 1 and hits[0].tag == tag
    only_ai = find_slots(model, "", ["AI"])
    assert only_ai and all(s.code == "AI" for s in only_ai)


def test_cabinet_html_cells_labels_selection_and_dimming(run_rows):
    model = build_cabinet(run_rows, cabinet_names(run_rows)[0])
    html = cabinet_html(model)
    assert html.count('class="ss-slot') == len(model.ciocs) * 8 * 12
    assert 'role="img"' in html and 'aria-label="Free slot"' in html
    first = next(s for s in model.all_slots() if s.kind == "signal")
    sel = cabinet_html(model, selected=first.key, matches={first.key})
    assert sel.count(" sel") == 1 and " dim" in sel
    assert "<script" not in html.lower()
    assert "Free slot" in legend_html() and "Wired spare pair" in legend_html()


# ----------------------------------------------------------------------------- generated summaries
def test_rule_summary_is_computed_from_values():
    r = default_ruleset()
    assert any("10% means 4 of 32" in s for s in rule_summary(r))
    r.spare_percent = 25.0
    assert any("25% means 8 of 32" in s for s in rule_summary(r))
    r.group_isolation_level = "cabinet"
    assert any("own cabinet" in s for s in rule_summary(r))
    for t in r.toggles:
        if t.id == "R2-segregation":
            t.enabled = False
    assert any("A/B separation is switched off" in s for s in rule_summary(r))
    r.naming.area = "ZZ9"
    assert example_names(r)["Marshalling cabinet"].startswith("ZZ9-DCM")


def test_solver_summary_is_honest_about_exactness():
    none = solver_summary({"cpsat_repairs": []})
    assert none["headline"] == "No solver repair was needed" and none["kind"] == "ok"
    mixed = solver_summary({"cpsat_repairs": [{"status": "OPTIMAL", "proven_exact": True},
                                              {"status": "FEASIBLE", "proven_exact": False},
                                              {"status": "INFEASIBLE"}]})
    assert (mixed["exact"], mixed["best_found"], mixed["rejected"]) == (1, 1, 1)
    assert "not proven minimal" in mixed["headline"] and "optimal" not in mixed["detail"].lower()
    fb = solver_summary({"cpsat_repairs": [{"status": "INFEASIBLE"}], "fallback_full_reallocation": True})
    assert fb["kind"] == "warn" and fb["fallback"] is True


# ----------------------------------------------------------------------------- demo and signal-flow figure use real output
def test_demo_bundle_is_real_engine_output():
    d = build_demo()
    assert d.metrics["violations"] == 0 and all(c["Result"] == "PASS" for c in d.check)
    assert len(d.signals) == 4 and len({s.row["CHARM Address"] for s in d.signals}) == 4
    assert d.sample_tq is not None and d.sample_tq.sources


def test_flow_figure_shows_real_values_and_label():
    d = build_demo()
    for s in d.signals:
        html = flow_html(d, s)
        assert s.row["CHARM Address"] in html and s.tag in html
        assert "synthetic" in html.lower() and "Not a live connection" in html
        assert html.count("ss-fstep") >= 5
