"""Stage 2: Review (pre-flight audit). design.md section E2."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from slotsmith.ingest import CANONICAL, REQUIRED

from app.core.session import get_audit, get_mdb
from app.core.state import filter_tqs
from app.ui import shell
from html import escape

from app.ui.components import banner, kv, severity_chip, tiles
from app.views._common import empty_state


def _mapping_rows(cm) -> list[dict]:
    out = []
    for f in CANONICAL:
        hdr, conf = cm.mapping.get(f), cm.confidence.get(f)
        if hdr:
            status = "Matched" if (conf is None or conf >= 0.9) else "Matched (approximate)"
        else:
            status = "Missing: required" if f in REQUIRED else "Not mapped (optional)"
        out.append({"Field": f, "Required": "Yes" if f in REQUIRED else "No", "Matched header": hdr or "none",
                    "Match": f"{int(conf * 100)}%" if conf is not None and hdr else "", "Status": status})
    return out


def render() -> None:
    s = shell.begin("review")
    shell.header("review", "Review the data",
                 "A pre-flight check before anything is placed. Blockers hold rows back; warnings are noted and do not stop allocation. "
                 "Nothing on this page changes your dataset.")
    if not s.has_input:
        return empty_state("No dataset loaded", "Load a workbook first.", "Go to Input", "input")
    mdb, audit = get_mdb(st.session_state), get_audit(st.session_state)
    if mdb is None or audit is None:
        return empty_state("The dataset could not be read", st.session_state.get("ingest_error") or "Load it again.",
                           "Go to Input", "input")

    kind = {"ready": "ok", "ready_with_warnings": "warn", "blocked": "bad"}[audit.readiness_status]
    st.html(banner(kind, audit.readiness_label, audit.summary_message))
    st.html(tiles([
        dict(label="Rows read", value=f"{audit.n_rows:,}", qualifier=f"{audit.n_files} file(s), {audit.n_sheets} sheet(s)"),
        dict(label="Signals ready to place", value=f"{audit.n_signals_valid:,}", qualifier=f"in {audit.n_cables:,} cables"),
        dict(label="Blocking findings", value=str(audit.blocking_tqs), qualifier="rows held as technical queries",
             tone="bad" if audit.blocking_tqs else "good"),
        dict(label="Warnings and notes", value=str(audit.warning_tqs + audit.info_tqs), qualifier="do not block allocation"),
    ]))

    t1, t2 = st.tabs([f"Findings ({len(audit.tqs)})", f"Column mapping ({len(mdb.mapping)})"])
    with t1:
        if not audit.tqs:
            st.html(banner("ok", "No findings", "No missing, duplicate or conflicting data was found."))
        else:
            c1, c2 = st.columns([2, 3])
            sev = c1.segmented_control("Severity", ["All", "Blocking", "Warning", "Info"], default="All", key="rev_sev")
            q = c2.text_input("Search", placeholder="Tag, cable, rule ID or text", key="rev_q")
            shown = filter_tqs(audit.tqs, sev or "All", q)
            st.caption(f"Showing {len(shown)} of {len(audit.tqs)}.")
            if shown:
                df = pd.DataFrame([{
                    "ID": t.id, "Severity": t.severity.title(), "Rule": t.rule_ref, "What": t.message,
                    "Affected": f"{len(t.tags)} signal(s)" if t.tags else (f"{len(t.cables)} cable(s)" if t.cables else "-"),
                    "First source row": (t.sources[0] + (f"  (+{len(t.sources) - 1})" if len(t.sources) > 1 else "")) if t.sources else "-"}
                    for t in shown])
                ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun",
                                  selection_mode="single-row", key="rev_tbl", column_config={
                                      "ID": st.column_config.TextColumn(width="small"),
                                      "Severity": st.column_config.TextColumn(width="small"),
                                      "Rule": st.column_config.TextColumn(width="small"),
                                      "What": st.column_config.TextColumn(width="large"),
                                      "Affected": st.column_config.TextColumn(width="small"),
                                      "First source row": st.column_config.TextColumn(width="medium")})
                rows_sel = ev.selection.rows if ev and ev.selection else []
                if rows_sel and rows_sel[0] < len(shown):
                    t = shown[rows_sel[0]]
                    effect = ("Blocking: the affected rows are held out of the allocation until this is fixed."
                              if t.severity == "blocking" else "Does not stop allocation; review and decide.")
                    st.html('<div class="ss-panel rise ss-selpanel"><h4>' + escape(t.id) + " " + severity_chip(t.severity) +
                            f"</h4><p><b>{escape(t.message)}</b></p>" + kv([
                                ("Effect", effect), ("Rule", t.rule_ref), ("Category", t.category),
                                ("Affected tags", ", ".join(t.tags[:12])), ("Affected cables", ", ".join(t.cables[:12])),
                                ("Source (file · sheet · row)", ", ".join(t.sources[:8])),
                                ("Recommended fix", t.suggested_action)]) + "</div>")
                else:
                    st.caption("Select a row to see the affected rows, why it matters and the recommended fix.")
            else:
                st.html(banner("info", "No findings match", "Clear the search or choose another severity."))
    with t2:
        st.caption("Columns are matched by name and similarity (80% or better). Manual overrides are not supported by the pipeline yet.")
        for key, cm in mdb.mapping.items():
            st.markdown(f"**Sheet** `{key}`")
            st.dataframe(pd.DataFrame(_mapping_rows(cm)), hide_index=True, width="stretch")
            if cm.unused_headers:
                st.caption(f"Headers not used: {', '.join(cm.unused_headers)}")

    blocked = audit.readiness_status == "blocked"
    held = audit.blocking_tqs
    shell.next_action("review", "Next",
                      "Set the rules and run the allocation" + (f" ({held} row issue(s) will be held as queries)" if held else ""),
                      "Set up allocation", "allocate", disabled=blocked,
                      why_disabled="Allocation is blocked: no valid cable could be formed from this data.")
