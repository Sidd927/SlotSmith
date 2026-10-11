"""Shared helpers for workbench pages."""
from __future__ import annotations

import tempfile
from pathlib import Path
from html import escape

import streamlit as st

from app.ui import shell
from app.ui.components import banner


def save_uploads(files) -> list[Path]:
    d = Path(tempfile.mkdtemp())
    out = []
    for f in files:
        p = d / f.name
        p.write_bytes(f.getbuffer())
        out.append(p)
    return out


def empty_state(title: str, body: str, action_label: str, target: str) -> None:
    """Empty state: what is missing, why, and one action."""
    st.html(banner("info", title, body))
    if st.button(action_label, key=f"empty_{target}", type="primary"):
        st.switch_page(shell.PAGES[target])


def stale_banner(status, what: str = "results") -> None:
    if status.alloc.is_stale:
        st.html(banner("warn", f"These {what} are out of date",
                       status.alloc.reason + " Run Allocate again to refresh them."))
        if st.button("Go to Allocate", key=f"stale_go_{what}", icon=":material/arrow_forward:"):
            st.switch_page(shell.PAGES["allocate"])
