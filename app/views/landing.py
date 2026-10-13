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
from app.core.links import configured_links
from app.ui.flow import bench_html, flow_html, story_html

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
    with st.container(key="landhdr"):
        c1, c2, c3 = st.columns([6, 1.4, 1.1], vertical_alignment="center")
        with c1:
            st.html('<div class="ss-header land">' + brand() +
                    '<nav class="ss-nav" aria-label="Sections"><a href="#problem">The problem</a><a href="#how">How it works</a>'
                    '<a href="#inspect">Evidence</a><a href="#status">Status</a></nav></div>')
        with c2:
            shell.appearance_popover()
        with c3:
            st.page_link(shell.PAGES["input"], label="Workbench", icon=":material/arrow_forward:")


def _go_demo() -> None:
    ok, err = load_synthetic(st.session_state, 2000, 7, 6)
    if ok:
        st.switch_page(shell.PAGES["review"])
    st.error(err)


def _readout(bundle: DemoBundle) -> str:
    cells = "".join(
        f'<div class="ss-rc{"" if c["Result"] == "PASS" else " no"}"><b>{escape(c["Rule"])}</b><span>{escape(c["Check"])}</span>'
        f'<i>{"PASS" if c["Result"] == "PASS" else "FAIL"}</i></div>' for c in bundle.check)
    passed = sum(1 for c in bundle.check if c["Result"] == "PASS")
    return ('<div class="ss-readout"><h4>Independent verification</h4>'
            f'<p>{passed} of {len(bundle.check)} rule families pass on the exported rows of the synthetic demo. '
            'The checker shares no code with the allocator.</p>' f'<div class="ss-rgrid">{cells}</div></div>')


def _revision_strip(rv: dict) -> str:
    parts = [("u", "Unchanged", rv["unchanged"]), ("x", "Updated in place", rv["modified_in_place"]), ("m", "Moved", rv["moved"]),
             ("a", "Added", rv["added"]), ("d", "Deleted", rv["deleted"])]
    total = max(1, sum(v for _, _, v in parts))
    bar = "".join(f'<i class="{k}" style="width:{100 * v / total:.2f}%" title="{n}: {v}"></i>' for k, n, v in parts)
    leg = "".join(f"<span>{n} <b>{v:,}</b></span>" for _, n, v in parts)
    return f'<div class="ss-seg" role="img" aria-label="Revision impact">{bar}</div><div class="ss-segl">{leg}</div>'


def _footer() -> str:
    links = "".join(f'<li><a href="{escape(u)}" rel="noopener noreferrer">{escape(n)}</a></li>' for n, u in configured_links() if u)
    return ('<footer class="ss-foot"><div><b>SlotSmith</b> · I/O allocation workbench for DeltaV Electronic Marshalling.<br>'
            'It complements vendor engineering tools and is not affiliated with or endorsed by Emerson. Every example on this page is synthetic. '
            'Project background and credits are in the repository README.</div>'
            f'<ul>{links}<li><a href="#top">Back to top</a></li></ul></footer>')


def render() -> None:
    ensure_session(st.session_state)
    inject_theme(1200)
    skip_link()
    bundle = _demo()
    st.html('<div class="ss-scrollbar" aria-hidden="true"></div><span id="top"></span>')
    _header(None)

    # ---- hero: dark instrument surface carrying the real calls to action
    with st.container(key="cine"):
        left, right = st.columns([0.92, 1.28], gap="large", vertical_alignment="center")
        with left:
            st.html('<p class="ss-eyebrow">DeltaV Electronic Marshalling</p>'
                    '<h1 class="ss-cine-h">From I/O list to <em>checked</em> CHARM slot.</h1>'
                    '<p class="ss-cine-lead">Place every cable into a cabinet, CIOC, baseplate and slot under your project rules. '
                    'What cannot be placed becomes a technical query, and an independent checker re-reads the export.</p>')
            b1, b2 = st.columns(2)
            if b1.button("Open the workbench", type="primary", key="hero_open", width="stretch"):
                st.switch_page(shell.PAGES["input"])
            if b2.button("Run the synthetic demo", key="hero_demo", width="stretch",
                         help="Generates a 2,000-signal synthetic workbook and opens the review stage."):
                _go_demo()
            st.html('<ul class="ss-cine-facts"><li><b>Traceable</b> row to slot</li><li><b>Rule-checked</b> by a second implementation</li>'
                    '<li><b>Revision-aware</b> Rev A to Rev B</li></ul>'
                    '<p class="ss-cine-note">For DeltaV I/O and project engineers. Runs in your own Python environment; no customer data needed.</p>')
        with right:
            if bundle is not None:
                st.html(bench_html(bundle, "hero"))
            else:
                st.html(banner("info", "Preview unavailable", "The demo preview could not be computed. The workbench is unaffected."))

    # ---- the problem, in the rules engineers actually have to satisfy
    st.html('<section class="ss-section" id="problem" style="margin-top:56px"><div class="ss-method"><div><p class="ss-eyebrow">The problem</p>'
            '<h2>A signal list is a puzzle with hard rules.</h2><p class="sub">Electronic marshalling removed cross-wiring, but the allocation moved '
            'into spreadsheets: thousands of signals on multi-pair cables must land in CIOCs, baseplates and CHARM slots, and every revision '
            'tempts a re-run from scratch. These are the rules SlotSmith enforces or checks, as read from the published problem statement.</p></div>'
            '<ol class="ss-principles">'
            '<li><div><b>K-1 Cables stay whole.</b> Every pair of a cable lands side by side, in pair order.</div></li>'
            '<li><div><b>S-1 A and B stay apart.</b> Redundant sides never share a CIOC.</div></li>'
            '<li><div><b>G-1 Groups stay together.</b> A process group occupies contiguous cabinets.</div></li>'
            '<li><div><b>P-1 Room to grow.</b> Each cabinet keeps a share of baseplates empty.</div></li>'
            '<li><div><b>H Right hardware.</b> Each I/O type maps to a CHARM and terminal block, or is held as a query. SlotSmith never guesses a mapping.</div></li></ol></div></section>')

    # ---- scroll-driven story (one connected stage)
    if bundle is not None:
        st.html(story_html(bundle))
        st.html('<section class="ss-section" id="trace"><p class="ss-eyebrow">Trace a signal</p><h2>One row in, one slot out.</h2>'
                '<p class="sub">Pick a signal and follow it from its source row to its CHARM address. Each was allocated by the real engine from the synthetic demo.</p></section>')
        _figure(bundle)

    # ---- evidence: instrument readout + proof cards (varied composition)
    st.html('<section class="ss-section" id="inspect"><p class="ss-eyebrow">What it produces</p><h2>Evidence, not just a layout.</h2>'
            '<p class="sub">From the synthetic demo run above, not from mock-ups.</p></section>')
    if bundle is not None:
        q = bundle.sample_tq
        tq = ""
        if q is not None:
            tq = ('<div class="ss-panel"><h4>A technical query</h4>'
                  f'<p>{severity_chip(q.severity)} <span class="ss-mono">{escape(q.id)}</span> · rule {escape(q.rule_ref)}</p>'
                  f'<p><b>{escape(q.message)}</b></p><p class="ss-mono" style="font-size:12px">{escape(", ".join(q.sources[:3]))}</p>'
                  f'<p>Suggested action: {escape(q.suggested_action)}</p></div>')
        rv = bundle.revision
        note = ("No CP-SAT repair window was needed." if rv["cpsat_windows"] == 0 else f'{rv["cpsat_windows"]} CP-SAT repair window(s) were searched.')
        st.html('<div class="ss-evid">' + _readout(bundle) + '<div class="ss-proof">' + tq +
                '<div class="ss-panel"><h4>A revision impact</h4>' + _revision_strip(rv) +
                f'<p>{escape(note)} Verifier violations on Rev B: {rv["violations"]}.</p></div></div></div>'
                '<p class="ss-cap">All panels: synthetic demo data.</p>')

    # ---- what you receive
    sheets = [["IO Allocation", "One row per signal and spare pair: cabinet, CIOC, baseplate, slot, CHARM, terminal block, status, query reference, source row."],
              ["Cabinet Summary", "Per cabinet: CIOCs, baseplates used, empty baseplates, signals, spares, held slots, fill."],
              ["TQ List", "Every technical query: severity, rule, message, affected tags and cables, source rows, suggested action."],
              ["Rule Check", "The independent check: PASS, FAIL or SKIPPED per rule family, with violation counts and notes."],
              ["Rule Set", "Parameters, hardware table and each rule switch ON or OFF."],
              ["Run Info", "Disabled switches, verification counts and outcome, unresolved hardware, query totals."],
              ["Revision Impact", "Rev B only: every added, deleted, moved and modified signal."]]
    st.html('<section class="ss-section" id="deliver"><p class="ss-eyebrow">What you receive</p><h2>One workbook, with its own evidence.</h2>'
            '<p class="sub">The file records what was checked and what was not, so it can be read without the application. '
            'Its layout follows the problem statement; the organiser\'s template has not been released.</p></section>'
            + ledger(["Sheet", "Contents"], sheets))

    # ---- method, status and limits
    bench = _bench_sentence()
    st.html('<section class="ss-section" id="method"><p class="ss-eyebrow">Method</p><h2>How it decides.</h2></section>'
            '<div class="ss-method"><ol class="ss-principles">'
            '<li><div><b>Deterministic placement.</b> Whole cables are packed first-fit-decreasing, in pair order. The same input and rules give the same placement.</div></li>'
            '<li><div><b>Solver only for revisions.</b> CP-SAT repairs a window of cabinets with a 10-second limit. Each window is reported as proven exact or best found, and a proven window says nothing about the whole project.</div></li>'
            '<li><div><b>Independent verifier.</b> It shares no code with the allocator and re-checks the exported workbook, not the solver\'s internal state.</div></li></ol>'
            '<aside class="ss-limits"><h4>Reading the evidence</h4><ul>'
            '<li>The synthetic demo is generated by SlotSmith itself. Agreement between that generator and the allocator is a <b>consistency check</b>, not independent validation against real engineering data.</li>'
            + (f"<li>{escape(bench)}</li>" if bench else "") +
            '</ul></aside></div>')
    st.html('<section class="ss-section" id="status"><p class="ss-eyebrow">Status</p><h2>What is supported, and what is not.</h2></section>'
            '<div class="ss-status3">'
            '<div class="ss-panel"><h4>Supported today</h4><ul><li>Import of .xlsx and .csv I/O lists with column matching and findings tied to source rows.</li>'
            '<li>Rule-driven allocation, technical queries, 11-family independent verification and a cabinet map.</li>'
            '<li>Rev A to Rev B comparison and repair, with workbook export.</li><li>Single user, local, in-memory session.</li></ul></div>'
            '<div class="ss-panel"><h4>Experimental</h4><ul><li>CP-SAT revision repair: time-limited and multi-threaded, so results can differ between runs.</li>'
            '<li>Behaviour with a rule switched off: unknown hardware stays held, and mixed A/B or mixed-group cables are placed unsided with a warning. These are our interpretations; the organiser has not confirmed them.</li></ul></div>'
            '<div class="ss-panel"><h4>Not validated</h4><ul><li>Real customer I/O lists and the organiser\'s allocation template (not released).</li>'
            '<li>Vendors or platforms other than DeltaV, and any certification.</li>'
            '<li>Security, persistence, multi-user use and assistive-technology support. This is not production software.</li></ul></div></div>')

    # ---- closing
    with st.container(key="cine_end"):
        l2, r2 = st.columns([1.2, 1], gap="large", vertical_alignment="center")
        with l2:
            st.html('<p class="ss-eyebrow">Your turn</p><h2 class="ss-cine-h" style="font-size:clamp(2rem,1.2rem + 2.4vw,3.2rem);max-width:16ch">'
                    'Try it on your own list.</h2><p class="ss-cine-lead">Load a workbook with tag, I/O type, cable and pair columns, '
                    'or generate a synthetic benchmark.</p>')
            if st.button("Open the workbench", type="primary", key="close_open"):
                st.switch_page(shell.PAGES["input"])
        with r2:
            st.html('<ol class="ss-ix" aria-label="Workbench stages"><li><i>01</i><b>Import</b><span>xlsx · csv</span></li>'
                    '<li><i>02</i><b>Review</b><span>findings with source rows</span></li><li><i>03</i><b>Allocate</b><span>rules, then run</span></li>'
                    '<li><i>04</i><b>Results</b><span>verification, queries</span></li><li><i>05</i><b>Inspect</b><span>cabinet and slot map</span></li>'
                    '<li><i>06</i><b>Revise</b><span>Rev A to Rev B</span></li><li><i>07</i><b>Deliver</b><span>workbook, run id</span></li></ol>')
    st.html(_footer())
