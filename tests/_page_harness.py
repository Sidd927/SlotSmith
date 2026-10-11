"""AppTest harness: runs the real pages with the real shell, starting on the page named by $SS_TARGET."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st  # noqa: E402

from app.ui import shell  # noqa: E402
from app.views import (allocate, cabinets, deliverables, input as input_view, landing, results, review,  # noqa: E402
                       revise)

target = os.environ.get("SS_TARGET", "landing")
fns = {"landing": landing.render, "input": input_view.render, "review": review.render, "allocate": allocate.render,
       "results": results.render, "cabinets": cabinets.render, "revise": revise.render,
       "deliverables": deliverables.render}
pages = {k: st.Page(fn, title=k, url_path=("" if k == target else k), default=(k == target)) for k, fn in fns.items()}
shell.PAGES.update(pages)
st.navigation(list(pages.values()), position="hidden").run()
