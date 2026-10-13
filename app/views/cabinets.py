"""Stage 5: Cabinets (inspector). design.md section E5."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.cabinet import TYPE_WORDS, build_cabinet, cabinet_names, find_slots
from app.core.state import unresolved_hardware
from app.ui import shell
from app.ui.cabinet import cabinet_html, legend_html
from app.ui.components import banner, kv, tiles
from app.views._common import empty_state, stale_banner


def render() -> None:
    s = shell.begin("cabinets")
    shell.header("cabinets", "Cabinet inspection",
                 "Every CIOC, baseplate and CHARM slot as placed. Search a tag or cable, filter by signal type, and select a row to inspect that slot.")
    if not s.has_allocation:
        return empty_state("No allocation yet", "Run an allocation first.", "Go to Allocate", "allocate")
    res = st.session_state["res"]
    stale_banner(s, "cabinet maps")
    names = cabinet_names(res.rows)
    if not names:
        return st.html(banner("info", "Nothing was placed", "No signal could be placed, so there is no cabinet to show."))

    jump = st.session_state.pop("cab_jump", None)
    if jump and jump.get("cab") in names:   # arrive from Results with the cabinet and search already set
        st.session_state["cab_sel"], st.session_state["cab_q"] = jump["cab"], jump.get("q", "")
    c1, c2, c3 = st.columns([1.2, 1.6, 2.2])
    cab = c1.selectbox("Marshalling cabinet", names, key="cab_sel")
    q = c2.text_input("Search tag, cable or address", key="cab_q", placeholder="e.g. 10-FT-1001A or CBL-0001")
    codes = c3.pills("Signal types", list(TYPE_WORDS), selection_mode="multi", key="cab_types",
                     format_func=lambda c: f"{c}", help=" · ".join(f"{k}: {v}" for k, v in TYPE_WORDS.items()))
    hw_tqs = unresolved_hardware(res)
    hw_ids = {t.id for t in hw_tqs}
    hw_pairs = {}
    for r in res.rows:
        if r.get("TQ Ref") in hw_ids:
            try:
                hw_pairs[(str(r.get("Cable")), int(float(r.get("Pair"))))] = r["TQ Ref"]
            except (TypeError, ValueError):
                pass
    model = build_cabinet(res.rows, cab, hw_pairs)
    matches_list = find_slots(model, q, codes or ())
    filtering = bool(q.strip() or codes)
    match_keys = {m.key for m in matches_list} if filtering else None

    table_rows = [m for m in matches_list if m.kind != "free"]
    table_key = f"cab_tbl_{cab}_{q}_{'-'.join(codes or [])}"
    # Read the table selection *before* drawing the map so the ring follows the click in the same run.
    prev = st.session_state.get(table_key)
    rows_prev = list(prev.selection.rows) if prev is not None and getattr(prev, "selection", None) else []
    sel_key = table_rows[rows_prev[0]].key if rows_prev and rows_prev[0] < len(table_rows) else None
    if sel_key is None and filtering and len(table_rows) == 1:   # a search that finds exactly one slot locates it
        sel_key = table_rows[0].key
    sel_slot = next((m for m in model.all_slots() if m.key == sel_key), None)
    if sel_slot is not None:
        sel = sel_slot
        st.html('<div class="ss-panel rise ss-selpanel"><h4>' + escape(sel.address or "Slot") + " · selected slot</h4>" + kv([
            ("Tag", sel.tag), ("I/O type", sel.io_type), ("Cable / pair", f"{sel.cable} / {sel.pair}"),
            ("CHARM", sel.charm or ("UNRESOLVED: no mapping" if sel.reason == "hardware" else "")),
            ("Terminal block", sel.terminal_block or ("UNRESOLVED" if sel.reason == "hardware" else "")),
            ("Technical query", sel.tq_ref), ("Baseplate", sel.baseplate_name),
            ("Controller", sel.controller), ("Group / side", f"{sel.group or '—'} / {sel.seg or '—'}"),
            ("Status", sel.status), ("Source row", sel.source)]) + "</div>")
    all_slots = list(model.all_slots())
    n_sig = sum(1 for m in all_slots if m.kind == "signal")
    n_sp = sum(1 for m in all_slots if m.kind == "spare")
    n_held = sum(1 for m in all_slots if m.kind == "held")
    cap = len(model.ciocs) * 96
    n_unres = sum(1 for m in all_slots if m.kind == "held" and m.reason == "hardware")
    if hw_tqs:
        st.html(banner("warn", f"{len(hw_tqs)} signal(s) have unresolved hardware",
                       "Their I/O type has no CHARM or terminal-block mapping, so they are held (red ? slots, in the cabinet that holds their cable) instead of being assigned "
                       "hardware. This applies whether or not the hardware rule is switched on. Tags: "
                       + ", ".join(sorted({x for t in hw_tqs for x in t.tags}))[:240]))
    st.html(tiles([dict(label="CIOCs", value=str(len(model.ciocs)), qualifier=f"{cap:,} CHARM slots"),
                   dict(label="Signals", value=f"{n_sig:,}", qualifier=f"{100 * n_sig / max(cap, 1):.0f}% of slots"),
                   dict(label="Wired spare pairs", value=f"{n_sp:,}"),
                   dict(label="Held for a query", value=f"{n_held:,}", tone="attn" if n_held else "",
                        qualifier=f"{n_unres} with unresolved hardware" if n_unres else ""),
                   dict(label="Free slots", value=f"{cap - len(all_slots):,}", qualifier="not wired")]))
    st.html(legend_html())

    st.html(cabinet_html(model, sel_key if sel_key in {m.key for m in model.all_slots()} else None, match_keys))
    used = sum(1 for m in model.all_slots() if m.kind == "signal")
    st.caption(f"{cab}: {len(model.ciocs)} CIOC(s), {used} signals. "
               + (f"{len(matches_list)} slot(s) match; the rest are dimmed." if filtering else "Each CIOC has 8 baseplates (BP) of 12 slots. Hover a slot for its tag and address."))
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.markdown("**Matching slots**" if filtering else "**All occupied slots**")
        if table_rows:
            def _tag(m):
                return m.tag or ("(unresolved hardware)" if m.reason == "hardware" else "(held for a query)" if m.kind == "held" else "(wired spare)")

            df = pd.DataFrame([{"Address": m.address, "Tag": _tag(m),
                                "Type": m.code or ("unresolved" if m.reason == "hardware" else m.kind),
                                "Cable": m.cable, "Pair": m.pair, "Query": m.tq_ref} for m in table_rows])
            ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun",
                              selection_mode="single-row", key=table_key, height=300)
        else:
            st.html(banner("info", "No slots match", "Clear the search or the type filter."))
    with right:
        st.markdown("**Selected slot**")
        if sel_slot is None:
            st.caption("Select a row in the table to see its details here. The slot is ringed in the map above.")
        else:
            st.caption("Details are shown above the map so they stay in view.")
