"""Stage 4: Results. design.md section E4."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.state import compute_kpi_metrics, filter_tqs, unresolved_hardware, verification_status
from app.core.status import run_status
from app.ui import shell
from app.ui.components import banner, chip, composition_bar, kv, ledger, severity_chip, tiles, verdict, verify_readout
from app.views._common import empty_state, stale_banner


def render() -> None:
    s = shell.begin("results")
    shell.header("results", "Allocation results",
                 "What was placed, what was held back and why, and whether the independent check found any violations.")
    if not s.has_allocation:
        return empty_state("No allocation yet", "Run an allocation first.", "Go to Allocate", "allocate")
    res, rules = st.session_state["res"], st.session_state["rules"]
    stale_banner(s)
    k = compute_kpi_metrics(res, rules)
    rs = run_status(st.session_state)
    vs = verification_status(res)
    hw = unresolved_hardware(res)
    n_tq = k["tqs_total"]
    unplaced = sum(1 for r in res.rows if r.get("Status") == "Not allocated")
    held = k["signals_with_tq"]
    st.html(verdict(rs))
    c_out, c_ver = st.columns([1.15, 1], gap="medium")
    c_out.html('<div class="ss-panel" style="height:100%;box-sizing:border-box"><h4>Where every row went</h4>' +
               composition_bar(k["signals_allocated"], held, unplaced) +
               f'<p class="ss-cap" style="margin-top:8px">{k["signals_allocated"]:,} of {k["total_signals"]:,} rows placed · '
               f'{n_tq} technical queries ({k["blocking_tqs"]} blocking, {k["warning_tqs"]} warning, {k["info_tqs"]} info). '
               'Placed means a slot was assigned; it does not mean the engineering requirements are met.</p></div>')
    c_ver.html(verify_readout(res.check))
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
        bad = [c for c in res.check if c["Result"] == "FAIL" or c.get("Violations", 0) > 0]
        skp = [c for c in res.check if c["Result"] == "SKIPPED"]
        if bad:
            st.html('<div class="ss-panel" style="border-left:4px solid var(--ss-bad)"><h4>Violations</h4><p>Each family below ran and found a violation. '
                    'Examples are the first five the checker recorded; the count is the total.</p>' +
                    "".join(f'<p><b class="ss-mono">{escape(c["Rule"])}</b> · {escape(c["Check"])} · <b>{c["Violations"]}</b> violation(s)<br>'
                            f'<span class="ss-mono" style="font-size:12.5px">{escape(c.get("Examples") or "")}</span></p>' for c in bad) + "</div>")
        if skp:
            st.html(banner("warn", f"{len(skp)} check(s) were skipped, not passed",
                           "; ".join(f"{c['Rule']}: {c.get('Note') or 'not run'}" for c in skp)))
        with st.expander("Allocation success is not verification success"):
            st.markdown("**Allocation** means each signal was given a slot or a technical query. **Verification** is a separate program that re-reads "
                        "the exported workbook and re-checks 11 rule families. A run can place every row and still fail or skip checks, "
                        "and a clean verification only covers the rules that were switched on and the data that was loaded. Neither is engineering sign-off.")
        has_ex = any(c.get("Examples") or c.get("Note") for c in res.check)
        res_chip = {"PASS": chip("ok", "Pass", "ok"), "FAIL": chip("bad", "Fail", "bad"), "SKIPPED": chip("neutral", "Skipped", "idle")}
        rows = [[c["Rule"], c["Check"], res_chip.get(c["Result"], chip("bad", c["Result"], "bad")), str(c["Violations"])]
                + ([escape(c.get("Examples") or c.get("Note") or "")] if has_ex else []) for c in res.check]
        st.html(ledger(["Rule", "What is checked", "Result", "Violations"] + (["Examples / note"] if has_ex else []), rows,
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
                    hit = next((r for r in res.rows if r.get("Slot") and r.get("Marshalling Cabinet") and
                                (r.get("Tag") in tq.tags or r.get("Cable") in tq.cables) and r.get("Status") == "Allocated"), None)
                    if hit is not None:
                        if st.button("Find it in the cabinets", key="tq_jump", icon=":material/location_searching:"):
                            st.session_state["cab_jump"] = {"cab": hit["Marshalling Cabinet"],
                                                            "q": hit.get("Tag") or hit.get("Cable")}
                            st.switch_page(shell.PAGES["cabinets"])
                    else:
                        st.caption("Nothing was placed for this query, so there is no slot to show.")
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

    shell.next_action("results", "Next", "Inspect where every signal landed", "Inspect cabinets", "cabinets",
                      disabled=s.alloc.is_stale, why_disabled="Re-run Allocate first: these results are out of date.")
    a, b, _ = st.columns([1, 1, 2])
    if a.button("Revise with Rev B", key="res_rev", width="stretch"):
        st.switch_page(shell.PAGES["revise"])
    if b.button("Go to deliverables", key="res_del", width="stretch"):
        st.switch_page(shell.PAGES["deliverables"])
