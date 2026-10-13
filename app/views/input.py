"""Stage 1: Input (Import). Supported formats, expected columns, and what happens to a file."""
from __future__ import annotations

from html import escape

import streamlit as st

from slotsmith.ingest import CANONICAL, REQUIRED, SYNONYMS

from app.core.session import get_audit, get_mdb, load_synthetic, load_uploads
from app.ui import shell
from app.ui.components import banner, chip, kv, tiles
from app.views._common import save_uploads

_FIELD_WORDS = {"tag": "Instrument or signal tag", "io_type": "AI, AO, DI, DO (and variants)", "cable": "Multicore cable id",
                "pair": "Pair / core number in the cable", "group": "Logical IO group (keeps cables together)",
                "seg": "A/B side (redundancy separation)", "cable_size": "Pairs in the cable (2, 6, 12, 24)"}


def _expected_columns() -> str:
    items = "".join(
        f'<li>{"<span class=req>required</span>" if f in REQUIRED else ""}<b>{escape(f)}</b>'
        f'<em>{escape(_FIELD_WORDS[f])}. Also read as: {escape(", ".join(SYNONYMS[f][1:4]))}</em></li>' for f in CANONICAL)
    return f'<ul class="ss-cols">{items}</ul>'


def _recovery(err: str) -> list[str]:
    tips = ["Use an .xlsx workbook or a .csv file. Legacy .xls is not supported: re-save it as .xlsx.",
            "Check that a header row names the four required columns: tag, I/O type, cable and pair.",
            "Remove password protection, and make sure the file is not open in another program."]
    if "required" in err.lower() or "column" in err.lower():
        tips.insert(0, "A required column was not recognised. Rename the header to one of the accepted names listed above.")
    return tips


def render() -> None:
    s = shell.begin("input")
    shell.header("input", "Import an I/O list",
                 "Load a customer I/O workbook, or generate a synthetic benchmark to try the whole workflow first.")
    ss = st.session_state

    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown("#### Upload a workbook")
            st.caption("Accepted: Excel (.xlsx) and CSV (.csv). Several files can be combined into one dataset.")
            files = st.file_uploader("I/O list files", type=["xlsx", "csv"], accept_multiple_files=True,
                                     key="input_files", label_visibility="collapsed")
            if files:
                sig = tuple((f.name, f.size) for f in files)
                if sig != ss.get("_upload_sig"):
                    ss["_upload_sig"] = sig
                    with st.spinner("Reading the workbook and matching columns…"):
                        ok, _ = load_uploads(ss, save_uploads(files))
                    st.rerun()   # redraw header, rail and summary with the new dataset (or the error)
    with b:
        with st.container(border=True):
            st.markdown("#### Generate a synthetic benchmark")
            st.caption("Seeded and reproducible, with injected data errors so the technical-query flow has something to show.")
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

    with st.expander("What a valid file looks like, and what happens next"):
        st.html('<p class="ss-h" style="margin-top:4px">Columns SlotSmith looks for</p>' + _expected_columns() +
                '<p class="ss-cap">Headers are matched by name and similarity (80% or better), so "Tag No" or "Multicore" work. '
                'Manual remapping is not available yet; rename the header in the file if a column is not recognised.</p>'
                '<p class="ss-h">What happens to your file</p><ol class="ss-how">'
                '<li>Every sheet is read and each row keeps its file, sheet and row number.</li>'
                '<li>Missing, duplicate and conflicting data is listed on the Review step. Nothing is changed or deleted.</li>'
                '<li>Rows that cannot be placed safely are held as technical queries instead of being guessed.</li></ol>')

    # ---- outcome of the last ingest attempt
    if ss.get("ingest_error"):
        st.html(banner("bad", "That file could not be read", ss["ingest_error"] +
                       (" The previous dataset is still loaded." if s.has_input else "")))
        st.html('<div class="ss-panel"><h4>How to fix it</h4><ul>' +
                "".join(f"<li>{escape(t)}</li>" for t in _recovery(ss["ingest_error"])) + "</ul></div>")
        if ss.get("ingest_error_details"):
            with st.expander("Technical detail"):
                st.code(ss["ingest_error_details"])

    mdb = get_mdb(ss) if s.has_input else None
    if mdb is None:
        st.html(banner("info", "No dataset loaded", "Upload a workbook or generate a synthetic benchmark to begin."))
        return

    audit = get_audit(ss)
    st.html('<p class="ss-h">Loaded dataset</p>')
    synth = chip("info", "Synthetic data", "info") if s.synthetic else chip("neutral", "Your data")
    st.html(f'<div class="ss-panel rise"><p>{synth}</p>' + kv([
        ("Source", ", ".join((ss.get("dataset") or {}).get("names", []))),
        ("Rows read", f"{len(mdb.df):,}"),
        ("Sheets used", str(len(mdb.mapping))),
    ]) + "</div>")
    if audit is not None:
        kind = {"ready": "ok", "ready_with_warnings": "warn", "blocked": "bad"}[audit.readiness_status]
        st.html(banner(kind, audit.readiness_label, audit.summary_message))
    shell.next_action("input", "Next", "Review the data before anything is placed", "Review data", "review")
