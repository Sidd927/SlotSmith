"""Stage 1: Input. design.md section E1."""
from __future__ import annotations

from html import escape

import streamlit as st

from app.core.session import get_mdb, load_synthetic, load_uploads
from app.ui import shell
from app.ui.components import banner, chip, kv, page_title, tiles
from app.views._common import save_uploads


def render() -> None:
    s = shell.begin("input")
    page_title("Input", "Load a customer I/O workbook, or generate a synthetic benchmark to try the workflow.")
    ss = st.session_state

    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown("#### Upload a workbook")
            st.caption("Excel (.xlsx) or CSV. Each file needs a sheet with tag, I/O type, cable and pair columns.")
            files = st.file_uploader("I/O list files", type=["xlsx", "csv"], accept_multiple_files=True,
                                     key="input_files", label_visibility="collapsed")
            if files:
                sig = tuple((f.name, f.size) for f in files)
                if sig != ss.get("_upload_sig"):
                    ss["_upload_sig"] = sig
                    ok, _ = load_uploads(ss, save_uploads(files))
                    st.rerun()   # redraw header, rail and summary with the new dataset (or the error)
    with b:
        with st.container(border=True):
            st.markdown("#### Generate a synthetic benchmark")
            st.caption("Seeded, reproducible, with injected data errors so the technical-query flow has something to show.")
            c1, c2, c3 = st.columns(3)
            n = c1.number_input("Signals", 100, 30000, 2000, 100, key="syn_n")
            seed = c2.number_input("Seed", 0, 9999, 7, key="syn_seed")
            errs = c3.number_input("Injected errors", 0, 50, 6, key="syn_errs")
            if st.button("Generate dataset", key="syn_go", icon=":material/science:"):
                ok, err = load_synthetic(ss, n, seed, errs)
                ss["_upload_sig"] = None
                if not ok:
                    st.error(err)
                else:
                    st.rerun()

    # ---- outcome of the last ingest attempt
    if ss.get("ingest_error"):
        st.html(banner("bad", "That file could not be read", ss["ingest_error"] +
                       (" The previous dataset is still loaded." if s.has_input else "")))
        if ss.get("ingest_error_details"):
            with st.expander("Technical detail"):
                st.code(ss["ingest_error_details"])

    mdb = get_mdb(ss) if s.has_input else None
    if mdb is None:
        st.html(banner("info", "No dataset loaded", "Upload a workbook or generate a synthetic benchmark to begin."))
        return

    st.markdown("#### Loaded dataset")
    synth = chip("info", "Synthetic data", "info") if s.synthetic else chip("neutral", "Your data")
    st.html(f'<div class="ss-panel"><p>{synth}</p>' + kv([
        ("Source", ", ".join((ss.get("dataset") or {}).get("names", []))),
        ("Rows read", f"{len(mdb.df):,}"),
        ("Sheets used", str(len(mdb.mapping))),
    ]) + "</div>")
    st.write("")
    if st.button("Review data", type="primary", icon=":material/arrow_forward:", key="input_next"):
        st.switch_page(shell.PAGES["review"])
