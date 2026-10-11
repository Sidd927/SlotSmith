"""Stage 7: Deliverables. design.md section E7."""
from __future__ import annotations

from html import escape
from pathlib import Path

import openpyxl
import streamlit as st

from app.ui import shell
from app.ui.components import banner, chip, kv, page_title
from app.views._common import empty_state, stale_banner

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _sheets(path: Path) -> list[tuple[str, int]]:
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return [(ws.title, max(0, (ws.max_row or 1) - 1)) for ws in wb.worksheets]
    finally:
        wb.close()


def _card(title: str, path: Path, name: str, key: str, ready: bool, why: str) -> None:
    size = Path(path).stat().st_size
    sheets = _sheets(Path(path))
    status = chip("ok", "Ready", "ok") if ready else chip("warn", "Out of date", "stale")
    st.html(f'<div class="ss-panel"><h4>{escape(title)} {status}</h4>' +
            kv([("File", name), ("Size", f"{size / 1024:,.0f} KB")] +
               [(f"Sheet: {n}", f"{r:,} rows") for n, r in sheets]) + "</div>")
    st.download_button(f"Download {name}", data=Path(path).read_bytes(), file_name=name, mime=XLSX, disabled=not ready,
                       key=key, icon=":material/download:", type="primary" if key == "dl_a" else "secondary")
    if not ready:
        st.caption(why)


def render() -> None:
    s = shell.begin("deliverables")
    page_title("Deliverables", "Everything you can take away from this session.")
    if not s.has_allocation or not st.session_state.get("out"):
        return empty_state("Nothing to export yet", "Run an allocation first.", "Go to Allocate", "allocate")
    stale_banner(s, "deliverables")
    ss = st.session_state
    st.html(banner("info", "Layout note", "The workbook layout follows the problem statement's description. "
                   "The organiser's allocation template has not been released, so it may need re-mapping."))
    a, b = st.columns(2, gap="large")
    with a:
        _card("Rev A allocation workbook", ss["out"], "SlotSmith_allocation.xlsx", "dl_a", not s.alloc.is_stale,
              "Run Allocate again to export an up-to-date workbook.")
    with b:
        if ss.get("rev_out") and ss.get("rr") is not None:
            _card("Rev B allocation workbook", ss["rev_out"], "SlotSmith_allocation_RevB.xlsx", "dl_b",
                  not s.rev.is_stale, "Run the revision again to export an up-to-date workbook.")
        else:
            st.html('<div class="ss-panel"><h4>Rev B allocation workbook</h4><p>Not created yet. Apply a Rev B on the Revise page to generate it, including the Revision Impact sheet.</p></div>')
            if st.button("Go to Revise", key="del_rev"):
                st.switch_page(shell.PAGES["revise"])
    st.write("")
    with st.container(border=True):
        st.markdown("#### Rule set")
        st.caption("The rules used for this session, as a reusable file.")
        st.download_button("Download rule set (JSON)", ss["rules"].model_dump_json(indent=2), "slotsmith_ruleset.json",
                           mime="application/json", key="dl_rules", icon=":material/download:")
