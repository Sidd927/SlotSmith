"""SlotSmith: entry point and router.

    .venv/bin/streamlit run app/streamlit_app.py

Two experiences share one identity (design.md): the public landing page and the engineering workbench.
Native `st.navigation` pages provide real routes; the default navigation is hidden and replaced by our own
header and stage rail (app/ui/shell.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st  # noqa: E402

st.set_page_config(page_title="SlotSmith · DeltaV I/O allocation", page_icon=":material/grid_view:",
                   layout="wide", initial_sidebar_state="auto")

from app.ui import shell  # noqa: E402
from app.views import (allocate, cabinets, deliverables, input as input_view, landing, results, review,  # noqa: E402
                       revise)

_pages = {
    "landing": st.Page(landing.render, title="SlotSmith · DeltaV I/O allocation", default=True),
    "input": st.Page(input_view.render, title="Input · SlotSmith", url_path="input"),
    "review": st.Page(review.render, title="Review · SlotSmith", url_path="review"),
    "allocate": st.Page(allocate.render, title="Allocate · SlotSmith", url_path="allocate"),
    "results": st.Page(results.render, title="Results · SlotSmith", url_path="results"),
    "cabinets": st.Page(cabinets.render, title="Cabinets · SlotSmith", url_path="cabinets"),
    "revise": st.Page(revise.render, title="Revise · SlotSmith", url_path="revise"),
    "deliverables": st.Page(deliverables.render, title="Deliverables · SlotSmith", url_path="deliverables"),
}
shell.PAGES.update(_pages)
st.navigation(list(_pages.values()), position="hidden").run()
