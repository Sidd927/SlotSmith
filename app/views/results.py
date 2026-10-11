"""Stage 4: Results. design.md section E4."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.state import compute_kpi_metrics, filter_tqs, is_verifier_certified
from app.ui import shell
from app.ui.components import banner, chip, kv, ledger, page_title, severity_chip, tiles
from app.views._common import empty_state, stale_banner


def render() -> None:
    s = shell.begin("results")
    page_title("Results", "What was placed, what was held, and whether the independent check found any violations.")
    if not s.has_allocation:
        return empty_state("No allocation yet", "Run an allocation first.", "Go to Allocate", "allocate")
    res, rules = st.session_state["res"], st.session_state["rules"]
    stale_banner(s)
    k = compute_kpi_metrics(res, rules)
    ok, _, failed = is_verifier_certified(res)
    if ok:
        st.html(banner("ok", "Independent check: no violations",
                       "The verifier re-read the exported rows and found no violation in any of the 11 rule families. "
                       "This applies to this dataset and these rules only."))
    else:
        st.html(banner("bad", "Independent check: violations found",
                       f"Rule families with violations: {', '.join(failed) or 'report incomplete'}. See the Rule check tab."))

    n_tq = k["tqs_total"]
    st.html(tiles([
        dict(label="Signals allocated", value=f"{k['signals_allocated']:,}", stale=s.alloc.is_stale),
        dict(label="Held as queries", value=f"{k['signals_with_tq']:,}", stale=s.alloc.is_stale,
             tone="attn" if k["signals_with_tq"] else "", qualifier="held, not placed"),
        dict(label="Rows total", value=f"{k['total_signals']:,}", stale=s.alloc.is_stale,
             qualifier=f"{k['coverage_pct']:g}% allocated or covered by a query"),
        dict(label="Cabinets / CIOCs", value=f"{k['cabinets']} / {k['ciocs']}", stale=s.alloc.is_stale),
        dict(label="Baseplates used", value=f"{k['baseplates']:,}", stale=s.alloc.is_stale,
             qualifier=f"{k['baseplate_utilization_pct']:g}% of their slots hold signals"),
        dict(label="Technical queries", value=f"{n_tq:,}", stale=s.alloc.is_stale,
             qualifier=f"{k['blocking_tqs']} blocking, {k['warning_tqs']} warning, {k['info_tqs']} info"),
    ]))
    t = getattr(res, "timings", {}) or {}
    if t:
        st.caption("Measured in this run: " + " · ".join(f"{n.replace('_s', '')} {v:.2f} s" for n, v in t.items()))

    t1, t2, t3 = st.tabs(["Rule check", f"Technical queries ({n_tq})", "Cabinets"])
    with t1:
        has_ex = any(c.get("Examples") for c in res.check)
        rows = [[c["Rule"], c["Check"], chip("ok", "Pass", "ok") if c["Result"] == "PASS" else chip("bad", "Fail", "bad"),
                 str(c["Violations"])] + ([escape(c.get("Examples", ""))] if has_ex else []) for c in res.check]
        st.html(ledger(["Rule", "What is checked", "Result", "Violations"] + (["Examples"] if has_ex else []), rows,
                       numeric={3}, raw=True))
    with t2:
        if not res.tqs:
            st.html(banner("ok", "No technical queries", "Every row was placed."))
        else:
            c1, c2 = st.columns([2, 3])
            sev = c1.segmented_control("Severity", ["All", "Blocking", "Warning", "Info"], default="All", key="res_sev")
            q = c2.text_input("Search", placeholder="Tag, cable, rule ID or text", key="res_q")
            shown = filter_tqs(res.tqs, sev or "All", q)
            st.caption(f"Showing {len(shown)} of {n_tq}. Select a row for details.")
            if shown:
                df = pd.DataFrame([{"ID": t.id, "Severity": t.severity.title(), "Rule": t.rule_ref,
                                    "Category": t.category, "Message": t.message} for t in shown])
                ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun",
                                  selection_mode="single-row", key="res_tq_table")
                rows_sel = ev.selection.rows if ev and ev.selection else []
                if rows_sel:
                    tq = shown[rows_sel[0]]
                    st.html('<div class="ss-panel"><h4>' + escape(tq.id) + " " + severity_chip(tq.severity) + "</h4>" +
                            f"<p><b>{escape(tq.message)}</b></p>" + kv([
                                ("Rule", tq.rule_ref), ("Category", tq.category),
                                ("Tags", ", ".join(tq.tags[:12])), ("Cables", ", ".join(tq.cables[:12])),
                                ("Source rows", ", ".join(tq.sources[:6])),
                                ("Suggested action", tq.suggested_action)]) + "</div>")
            else:
                st.html(banner("info", "No queries match", "Clear the search or choose another severity."))
    with t3:
        sm = pd.DataFrame(res.summary)
        if not sm.empty:
            st.dataframe(sm, hide_index=True, width="stretch", column_config={
                "Fill % (signals / cabinet slots)": st.column_config.ProgressColumn(
                    "Signals / cabinet slots", min_value=0, max_value=100, format="%.1f%%"),
                "Fill % (occupied / cabinet slots)": st.column_config.ProgressColumn(
                    "Occupied / cabinet slots", min_value=0, max_value=100, format="%.1f%%")})
        st.caption("Occupied counts signals, wired spare pairs and slots held for a query.")

    a, b, c = st.columns(3)
    if a.button("Inspect cabinets", type="primary", icon=":material/arrow_forward:", key="res_cab", width="stretch"):
        st.switch_page(shell.PAGES["cabinets"])
    if b.button("Revise with Rev B", key="res_rev", width="stretch"):
        st.switch_page(shell.PAGES["revise"])
    if c.button("Deliverables", key="res_del", width="stretch"):
        st.switch_page(shell.PAGES["deliverables"])
