"""Landing page (public-facing experience). design.md section E: Landing."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import streamlit as st

from app.core.demo import DemoBundle, build_demo
from app.core.session import ensure_session, load_synthetic
from app.ui import shell
from app.ui.components import banner, brand, chip, icon, inject_theme, ledger, severity_chip, skip_link, tiles
from app.ui.flow import flow_html

BENCH = Path(__file__).resolve().parents[2] / "artifacts" / "benchmarks.json"


@st.cache_resource(show_spinner=False)
def _demo() -> DemoBundle | None:
    try:
        return build_demo()
    except Exception:  # the page must still work without the preview
        return None


def _bench_sentence() -> str | None:
    try:
        b = json.loads(BENCH.read_text())
        s, runs = b["summary"], b["scale"]
        sizes = sorted({r["signals_target"] for r in runs})
        big = [r for r in runs if r["signals_target"] == sizes[-1]]
        return (f"On {len(runs)} synthetic runs ({sizes[0]:,} to {big[0]['mdb_rows']:,} signals) the independent "
                f"verifier reported {s['max_violations']} violations and every row was either allocated or covered by a "
                f"technical query. {big[0]['mdb_rows']:,} signals took about {s['wall_20k_median_s']:.0f} s end to end on one laptop. "
                f"This is a consistency check on synthetic data, not evidence about customer projects.")
    except Exception:
        return None


@st.fragment
def _figure(bundle: DemoBundle) -> None:
    opts = [s.tag for s in bundle.signals]
    labels = {s.tag: f"{s.tag} · {s.row['CHARM Type'].split(' ')[0]}" for s in bundle.signals}
    pick = st.pills("Follow a signal", opts, selection_mode="single", default=opts[0], key="landing_signal",
                    format_func=lambda t: labels[t],
                    help="Each signal below was allocated by the real engine from the synthetic demo MDB.")
    sig = next((s for s in bundle.signals if s.tag == pick), bundle.signals[0])
    st.html(flow_html(bundle, sig))


def _header(s) -> None:
    c1, c2, c3 = st.columns([6, 1.4, 1.1], vertical_alignment="center")
    with c1:
        st.html('<div class="ss-header">' + brand() +
                '<nav class="ss-nav" aria-label="Sections"><a href="#how">How it works</a>'
                '<a href="#inspect">What it produces</a><a href="#method">Method and limits</a></nav></div>')
    with c2:
        shell.appearance_popover()
    with c3:
        st.page_link(shell.PAGES["input"], label="Workbench", icon=":material/arrow_forward:")


def _go_demo() -> None:
    ok, err = load_synthetic(st.session_state, 2000, 7, 6)
    if ok:
        st.switch_page(shell.PAGES["review"])
    st.error(err)


def render() -> None:
    ensure_session(st.session_state)
    inject_theme(1200)
    skip_link()
    bundle = _demo()
    _header(None)

    # ---- hero
    st.html('<section class="ss-hero"><h1>Turn a customer I/O list into a rule-checked CHARM allocation.</h1>'
            '<p class="lead">SlotSmith places each cable into a marshalling cabinet, CIOC, baseplate and CHARM slot under '
            'your project rules, raises a technical query for anything it cannot place, and re-checks its own Excel '
            'export with an independent verifier.</p></section>')
    b1, b2, _ = st.columns([1.5, 1.7, 4])
    if b1.button("Open the workbench", type="primary", key="hero_open", width="stretch"):
        st.switch_page(shell.PAGES["input"])
    if b2.button("Run the synthetic demo", key="hero_demo", width="stretch",
                 help="Generates a 2,000-signal synthetic workbook and opens the review stage."):
        _go_demo()
    st.html('<p class="ss-cap">Runs in your own Python environment. No customer data is needed to try it.</p>')

    if bundle is not None:
        _figure(bundle)
    else:
        st.html(banner("info", "Preview unavailable", "The demo preview could not be computed. The workbench is unaffected."))

    # ---- how it works
    st.html('<section class="ss-section" id="how"><h2>How it works</h2>'
            '<p class="sub">The same five stages you will see in the workbench.</p>'
            '<ol class="ss-steps">'
            '<li><h4>Import</h4><p>Upload Excel (.xlsx) or CSV I/O lists. Columns are matched automatically and every row keeps its file, sheet and row number.</p></li>'
            '<li><h4>Review</h4><p>A pre-flight check lists missing, duplicate and conflicting data before anything is placed.</p></li>'
            '<li><h4>Allocate</h4><p>Cables are packed whole, in pair order, into baseplates, CIOCs and cabinets under rules you set: grouping, A/B separation, spare room, hardware and names.</p></li>'
            '<li><h4>Verify and export</h4><p>An independent checker re-reads the exported workbook and tests 11 rule families. Anything it could not place becomes a technical query.</p></li>'
            '<li><h4>Revise</h4><p>Load Rev B. Unchanged cables stay where they are, and a CP-SAT repair works on the affected cabinets and reports how many signals had to move.</p></li>'
            '</ol></section>')

    # ---- what it produces
    st.html('<section class="ss-section" id="inspect"><h2>What it produces</h2>'
            '<p class="sub">These three panels come from the synthetic demo run above, not from mock-ups.</p></section>')
    if bundle is not None:
        left, right = st.columns([1.35, 1], gap="large")
        q = bundle.sample_tq
        with left:
            rows = [[c["Rule"], c["Check"], chip("ok", "Pass", "ok") if c["Result"] == "PASS" else chip("bad", "Fail", "bad")]
                    for c in bundle.check]
            st.html('<div class="ss-panel"><h4>An independent rule check</h4>'
                    '<p>Eleven rule families, re-checked from the exported rows.</p>'
                    + ledger(["Rule", "Check", "Result"], rows, raw=True) + '</div>')
        with right:
            if q is not None:
                st.html('<div class="ss-panel"><h4>A technical query</h4>'
                        f'<p>{severity_chip(q.severity)} <span class="ss-mono">{escape(q.id)}</span> · rule {escape(q.rule_ref)}</p>'
                        f'<p><b>{escape(q.message)}</b></p>'
                        f'<p class="ss-mono" style="font-size:12px">{escape(", ".join(q.sources[:3]))}</p>'
                        f'<p>Suggested action: {escape(q.suggested_action)}</p></div>')
            st.write("")
            rv = bundle.revision
            tl = [dict(label="Moved", value=str(rv["moved"])), dict(label="Added", value=str(rv["added"])),
                  dict(label="Deleted", value=str(rv["deleted"])), dict(label="Unchanged", value=str(rv["unchanged"]))]
            note = ("No CP-SAT repair window was needed for this small revision." if rv["cpsat_windows"] == 0
                    else f'{rv["cpsat_windows"]} CP-SAT repair window(s) were searched.')
            st.html('<div class="ss-panel"><h4>A revision impact</h4>' + tiles(tl) +
                    f'<p>{escape(note)} Verifier violations on Rev B: {rv["violations"]}.</p></div>')
        st.html('<p class="ss-cap">All three panels: synthetic demo data.</p>')

    # ---- method and limits
    bench = _bench_sentence()
    st.html('<section class="ss-section" id="method"><h2>Method and limits</h2>'
            '<p class="sub">What the tool does, and what has not been shown yet.</p></section>')
    m1, m2 = st.columns(2)
    with m1:
        st.html('<div class="ss-panel"><h4>How it decides</h4><ul>'
                '<li>Placement is deterministic first-fit-decreasing packing of whole cables.</li>'
                '<li>CP-SAT is used only to repair revisions, inside a window of cabinets, with a 10-second limit per window. Each window is reported as proven exact or best found, and results can differ between runs.</li>'
                '<li>The verifier shares no code with the allocator and checks the exported workbook, not the solver\'s internal state.</li>'
                '</ul></div>')
    with m2:
        items = []
        if bench:
            items.append(f"<li>{escape(bench)}</li>")
        items.append("<li>Not yet tested on the organiser's sample MDB or allocation template (not released), so the workbook layout follows the problem statement.</li>")
        items.append("<li>Rules are parameters (grouping, A/B scope, spare room, hardware table, names). A new kind of rule still needs code.</li>")
        st.html('<div class="ss-panel"><h4>What is and is not shown</h4><ul>' + "".join(items) + "</ul></div>")

    # ---- closing
    st.html('<section class="ss-section"><h2>Try it on your own list</h2>'
            '<p class="sub">Load a workbook with tag, I/O type, cable and pair columns, or generate a synthetic benchmark.</p></section>')
    if st.button("Open the workbench", type="primary", key="close_open"):
        st.switch_page(shell.PAGES["input"])
    st.html('<footer class="ss-foot">Team Mac_Enthu · VIT Code Apex 3.0 · Track 1 (Emerson) · PS 1.2 Project IO Signal Sudoku.<br>'
            'SlotSmith complements DeltaV engineering tools; it does not replace them. Every example on this page is synthetic.</footer>')
