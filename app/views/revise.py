"""Stage 6: Revise (Rev B). design.md section E6."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.revision_view import solver_summary
from app.core.session import run_revision, set_revision_synthetic, set_revision_upload
from app.ui import shell
from app.ui.components import banner, page_title, tiles
from app.views._common import empty_state, save_uploads, stale_banner


def render() -> None:
    s = shell.begin("revise")
    page_title("Revise (Rev B)", "Apply a new revision to the current allocation. Unchanged cables stay where they are.")
    if not s.has_allocation:
        return empty_state("No Rev A allocation yet", "A revision is applied on top of an allocation.", "Go to Allocate", "allocate")
    ss = st.session_state
    if s.alloc.is_stale:
        stale_banner(s, "Rev A results")
        st.html(banner("warn", "Revision is paused", "Re-run Allocate so Rev B is compared against current results."))
        return

    with st.container(border=True):
        st.markdown("#### Rev B input")
        options = (["Synthetic Rev B"] if ss.get("revb") is not None else []) + ["Upload Rev B"]
        mode = st.segmented_control("Source", options, default=options[0], key="rev_mode", label_visibility="collapsed")
        if mode == "Synthetic Rev B":
            if (ss.get("revision_source") or {}).get("kind") != "synthetic":
                set_revision_synthetic(ss)
            st.caption("Created together with the synthetic benchmark: some signals added, deleted and modified.")
        else:
            files = st.file_uploader("Rev B workbook(s)", type=["xlsx", "csv"], accept_multiple_files=True, key="revb_files")
            if files:
                sig = tuple((f.name, f.size) for f in files)
                if sig != ss.get("_revb_sig"):
                    ss["_revb_sig"] = sig
                    set_revision_upload(ss, save_uploads(files))
                    st.rerun()
            if ss.get("revision_error"):
                st.html(banner("bad", "Rev B could not be read", ss["revision_error"]))
        src = ss.get("revision_source")
        if src:
            st.caption(f"Selected: {src['label']}")
        go = st.button("Compare and re-allocate", type="primary", disabled=not src, key="rev_go", icon=":material/play_arrow:")
    if go:
        with st.status("Pinning unchanged cables and repairing the rest…", expanded=True) as stt:
            st.write("Large revisions can take up to a minute: the solver searches each affected window for up to 10 seconds.")
            ok, err = run_revision(ss)
            stt.update(label="Revision finished" if ok else "Revision failed", state="complete" if ok else "error")
        if ok:
            st.rerun()   # redraw the rail and header with the new revision status
        st.error(f"The revision did not finish: {err}. Previous revision results, if any, are unchanged.")
        s = shell.compute_status(ss)

    rr = ss.get("rr")
    if rr is None:
        return
    if s.rev.is_stale:
        st.html(banner("warn", "These revision results are out of date", s.rev.reason + " Compare again to refresh."))
    m = rr.metrics
    sm = solver_summary(m)
    st.html(banner(sm["kind"], sm["headline"], sm["detail"]))
    if sm["capacity_unplaced"]:
        st.html(banner("warn", f"{len(sm['capacity_unplaced'])} cable(s) could not be placed",
                       "They are listed as technical queries in the workbook: " + ", ".join(sm["capacity_unplaced"][:8])))
    stale = s.rev.is_stale
    st.html(tiles([
        dict(label="Moved", value=str(m["moved"]), stale=stale, qualifier="signals that changed slot"),
        dict(label="Added", value=str(m["added"]), stale=stale),
        dict(label="Deleted", value=str(m["deleted"]), stale=stale),
        dict(label="Modified in place", value=str(m["modified_in_place"]), stale=stale, qualifier="same slot, new CHARM or terminal block"),
        dict(label="Unchanged", value=f"{m['unchanged']:,}", stale=stale),
        dict(label="Verifier violations", value=str(m["violations"]), stale=stale,
             tone="good" if m["violations"] == 0 else "bad", qualifier=f"{len(m['cabinets_hit'])} cabinet(s) touched"),
    ]))
    df = pd.DataFrame(rr.impact)
    if df.empty:
        st.html(banner("info", "No differences", "Rev B matches Rev A."))
    else:
        kinds = sorted(df["Change"].unique())
        pick = st.pills("Show", kinds, selection_mode="multi", default=kinds, key="rev_kinds",
                        format_func=lambda k: f"{k} ({(df['Change'] == k).sum()})")
        shown = df[df["Change"].isin(pick or kinds)]
        st.caption(f"Showing {len(shown):,} of {len(df):,} changes.")
        st.dataframe(shown, hide_index=True, width="stretch")
    out = ss.get("rev_out")
    if out and not stale:
        st.download_button("Download Rev B workbook", data=open(out, "rb").read(), file_name="SlotSmith_allocation_RevB.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           icon=":material/download:", key="rev_dl")
