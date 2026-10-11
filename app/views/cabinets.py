"""Stage 5: Cabinets (inspector). design.md section E5."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.cabinet import TYPE_WORDS, build_cabinet, cabinet_names, find_slots
from app.ui import shell
from app.ui.cabinet import cabinet_html, legend_html
from app.ui.components import banner, chip, kv, page_title
from app.views._common import empty_state, stale_banner


def render() -> None:
    s = shell.begin("cabinets")
    page_title("Cabinets", "Find any slot. Search a tag or cable, filter by signal type, and select a row to inspect it.")
    if not s.has_allocation:
        return empty_state("No allocation yet", "Run an allocation first.", "Go to Allocate", "allocate")
    res = st.session_state["res"]
    stale_banner(s, "cabinet maps")
    names = cabinet_names(res.rows)
    if not names:
        return st.html(banner("info", "Nothing was placed", "No signal could be placed, so there is no cabinet to show."))

    c1, c2, c3 = st.columns([1.2, 1.6, 2.2])
    cab = c1.selectbox("Marshalling cabinet", names, key="cab_sel")
    q = c2.text_input("Search tag, cable or address", key="cab_q", placeholder="e.g. 10-FT-1001A or CBL-0001")
    codes = c3.pills("Signal types", list(TYPE_WORDS), selection_mode="multi", key="cab_types",
                     format_func=lambda c: f"{c}", help=" · ".join(f"{k}: {v}" for k, v in TYPE_WORDS.items()))
    model = build_cabinet(res.rows, cab)
    matches_list = find_slots(model, q, codes or ())
    filtering = bool(q.strip() or codes)
    match_keys = {m.key for m in matches_list} if filtering else None

    table_rows = [m for m in matches_list if m.kind != "free"]
    table_key = f"cab_tbl_{cab}_{q}_{'-'.join(codes or [])}"
    # Read the table selection *before* drawing the map so the ring follows the click in the same run.
    prev = st.session_state.get(table_key)
    rows_prev = list(prev.selection.rows) if prev is not None and getattr(prev, "selection", None) else []
    sel_key = table_rows[rows_prev[0]].key if rows_prev and rows_prev[0] < len(table_rows) else None
    st.html(legend_html())

    st.html(cabinet_html(model, sel_key if sel_key in {m.key for m in model.all_slots()} else None, match_keys))
    used = sum(1 for m in model.all_slots() if m.kind == "signal")
    st.caption(f"{cab}: {len(model.ciocs)} CIOC(s), {used} signals. "
               + (f"{len(matches_list)} slot(s) match; the rest are dimmed." if filtering else "Each CIOC has 8 baseplates of 12 slots. Wide cabinets scroll sideways."))
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.markdown("**Matching slots**" if filtering else "**All occupied slots**")
        if table_rows:
            df = pd.DataFrame([{"Address": m.address, "Tag": m.tag or "(spare)", "Type": m.code or m.kind,
                                "Cable": m.cable, "Pair": m.pair} for m in table_rows])
            ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun",
                              selection_mode="single-row", key=table_key, height=300)
        else:
            st.html(banner("info", "No slots match", "Clear the search or the type filter."))
    with right:
        sel = next((m for m in model.all_slots() if m.key == sel_key), None)
        st.markdown("**Selected slot**")
        if sel:
            st.html('<div class="ss-panel"><h4>' + escape(sel.address or "Slot") + "</h4>" + kv([
                ("Tag", sel.tag), ("I/O type", sel.io_type), ("Cable / pair", f"{sel.cable} / {sel.pair}"),
                ("CHARM", sel.charm), ("Terminal block", sel.terminal_block), ("Baseplate", sel.baseplate_name),
                ("Controller", sel.controller), ("Group / side", f"{sel.group or '—'} / {sel.seg or '—'}"),
                ("Status", sel.status), ("Source row", sel.source)]) + "</div>")
        else:
            st.caption("Select a row in the table to see its details here. The slot is ringed in the map above.")
