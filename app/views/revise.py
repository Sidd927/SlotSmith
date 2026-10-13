"""Stage 6: Revise (Rev B). design.md section E6."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.revision_view import solver_summary
from app.core.state import unresolved_hardware, verification_status
from app.core.status import revision_status
from app.core.session import run_revision, set_revision_synthetic, set_revision_upload
from app.ui import shell
from app.ui.components import banner, change_kind, tiles, verdict, verify_readout
from app.views._common import empty_state, save_uploads, stale_banner


def render() -> None:
    s = shell.begin("revise")
    shell.header("revise", "Revise against Rev B",
                 "Apply a new revision on top of the current allocation. Unchanged cables are pinned where they are; "
                 "only what the revision touches is re-placed.")
    if not s.has_allocation:
        return empty_state("No Rev A allocation yet", "A revision is applied on top of an allocation.", "Go to Allocate", "allocate")
    ss = st.session_state
    if s.alloc.is_stale:
        stale_banner(s, "Rev A results")
        st.html(banner("warn", "Revision is paused", "Re-run Allocate so Rev B is compared against current results."))
        return

    with st.expander("How a revision is applied, and what it does not promise"):
        st.html('<ul class="ss-conseq"><li>Rev B is compared with Rev A row by row. Cables that did not change keep their slots.</li>'
                '<li>Added and changed cables are placed into the cabinets they affect. Where a window of cabinets must be re-solved, '
                'a CP-SAT solver searches it for up to 10 seconds and reports whether the result is proven exact or best found.</li>'
                '<li>The tool does not claim a globally optimal or minimal-movement result; it reports exactly how many signals moved.</li>'
                '<li>The independent verifier then re-checks the Rev B workbook.</li></ul>')
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
    st.html(verdict(revision_status(ss), subject="Rev B"))
    st.html(verify_readout(rr.check))
    rej = sm["rejected"]
    st.html('<div class="ss-panel" style="margin-top:12px"><h4>Repair search (local only)</h4>'
            f'<p><b>{escape(sm["headline"])}.</b> {escape(sm["detail"])}</p>'
            '<p>This describes only the cabinet windows the solver searched. It says nothing about whether the whole revised '
            'allocation passes verification; that is the Rev B verdict above.</p>'
            + (f'<p>{rej} window(s) were tried and <b>not accepted</b>, so no change from them was applied. Review the moved and added signals below; '
               'if the result is not what you need, adjust capacity or spare-room rules and run the comparison again.</p>' if rej and not sm["fallback"] else "")
            + ('<p><b>No local repair was accepted.</b> Rev B was fully re-allocated, so unchanged signals may have moved; check the Moved rows below.</p>' if sm["fallback"] else "")
            + "</div>")
    if sm["capacity_unplaced"]:
        st.html(banner("warn", f"{len(sm['capacity_unplaced'])} cable(s) could not be placed",
                       "They are listed as technical queries in the workbook: " + ", ".join(sm["capacity_unplaced"][:8])))
    stale = s.rev.is_stale
    vs = verification_status(rr)
    hw = unresolved_hardware(rr)
    st.html(tiles([
        dict(label="Moved", value=str(m["moved"]), stale=stale, qualifier="signals that changed slot"),
        dict(label="Added", value=str(m["added"]), stale=stale),
        dict(label="Deleted", value=str(m["deleted"]), stale=stale),
        dict(label="Modified in place", value=str(m["modified_in_place"]), stale=stale, qualifier="same slot, new CHARM or terminal block"),
        dict(label="Unchanged", value=f"{m['unchanged']:,}", stale=stale),
        dict(label="Rev B verification", value={"passed": "Passed", "incomplete": "Incomplete", "failed": "Failed"}.get(vs["outcome"], "Missing"), stale=stale,
             tone="good" if vs["outcome"] == "passed" else "bad" if vs["outcome"] == "failed" else "attn",
             qualifier=f"{vs['passed']} passed · {vs['failed']} failed · {vs['skipped']} skipped · {len(m['cabinets_hit'])} cabinet(s) touched"),
    ]))
    kept = m["unchanged"] + m["modified_in_place"]
    st.html('<div class="ss-tiles" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">'
            '<div class="ss-panel"><h4>Preserved</h4>'
            f'<p><b>{kept:,}</b> signals keep their slot ({m["unchanged"]:,} unchanged, {m["modified_in_place"]:,} updated in place).</p></div>'
            '<div class="ss-panel"><h4>Needs your attention</h4>'
            f'<p><b>{m["moved"]:,}</b> moved, <b>{m["added"]:,}</b> added, <b>{m["deleted"]:,}</b> deleted'
            f'{", <b>" + str(len(sm["capacity_unplaced"])) + "</b> could not be placed" if sm["capacity_unplaced"] else ""}. '
            f'{"The verifier reports " + str(m["violations"]) + " violation(s)." if m["violations"] else "The verifier found no violations in the families it ran."}'
            f'{" " + str(vs["skipped"]) + " famil" + ("y was" if vs["skipped"] == 1 else "ies were") + " skipped (rules switched off), so this is not a full verification." if vs["skipped"] else ""}'
            f'{" " + str(len(hw)) + " signal(s) remain unresolved: no hardware mapping, held as technical queries (not preserved as valid)." if hw else ""}</p></div></div>')
    df = pd.DataFrame(rr.impact)
    if df.empty:
        st.html(banner("info", "No differences", "Rev B matches Rev A."))
    else:
        kinds = sorted(df["Change"].unique())
        pick = st.pills("Show", kinds, selection_mode="multi", default=kinds, key="rev_kinds",
                        format_func=lambda k: f"{k} ({(df['Change'] == k).sum()})")
        shown = df[df["Change"].isin(pick or kinds)]
        st.html('<div class="ss-art">' + "".join(change_kind(k) for k in (pick or kinds)) + "</div>")
        st.caption(f"Showing {len(shown):,} of {len(df):,} changes.")
        st.dataframe(shown, hide_index=True, width="stretch")
    out = ss.get("rev_out")
    if out and not stale:
        st.download_button("Download Rev B workbook", data=open(out, "rb").read(), file_name="SlotSmith_allocation_RevB.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           icon=":material/download:", key="rev_dl")
