"""Application shell: page registry, header, and the workbench stage rail (design.md B, D)."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

import streamlit as st

from app.core.session import WorkbenchStatus, compute_status, ensure_session, reset_session
from .components import brand, chip, inject_theme, skip_link, status_chip_for


@dataclass(frozen=True)
class Stage:
    key: str
    title: str
    path: str
    group: str
    n: int


STAGES = [
    Stage("input", "Input", "input", "Prepare", 1),
    Stage("review", "Review", "review", "Prepare", 2),
    Stage("allocate", "Allocate", "allocate", "Prepare", 3),
    Stage("results", "Results", "results", "Inspect", 4),
    Stage("cabinets", "Cabinets", "cabinets", "Inspect", 5),
    Stage("revise", "Revise (Rev B)", "revise", "Revise and deliver", 6),
    Stage("deliverables", "Deliverables", "deliverables", "Revise and deliver", 7),
]
STAGE_KEYS = [s.key for s in STAGES]

# Filled by the entry script on every run (st.Page objects are needed by st.page_link).
PAGES: dict[str, object] = {}


def _availability(key: str, s: WorkbenchStatus) -> tuple[bool, str]:
    """(enabled, reason-if-disabled)."""
    if key == "input":
        return True, ""
    if key in ("review", "allocate"):
        return s.has_input, "Load a dataset first (stage 1)."
    if key in ("results", "cabinets", "deliverables"):
        return s.has_allocation, "Run an allocation first (stage 3)."
    if key == "revise":
        if not s.has_allocation:
            return False, "Run an allocation first (stage 3)."
        return True, ""
    return True, ""


def _stage_icon(key: str, s: WorkbenchStatus, enabled: bool) -> str:
    if not enabled:
        return ":material/lock:"
    if key == "input":
        return ":material/check_circle:" if s.has_input else ":material/radio_button_unchecked:"
    if key == "review":
        return ":material/check_circle:" if s.has_allocation else ":material/radio_button_unchecked:"
    if key == "allocate":
        if s.has_allocation and s.alloc.is_stale:
            return ":material/warning:"
        return ":material/check_circle:" if s.has_allocation else ":material/radio_button_unchecked:"
    if key in ("results", "cabinets", "deliverables"):
        return ":material/warning:" if s.alloc.is_stale else ":material/check_circle:"
    if key == "revise":
        if s.has_revision:
            return ":material/warning:" if s.rev.is_stale else ":material/check_circle:"
        return ":material/radio_button_unchecked:"
    return ":material/radio_button_unchecked:"


def begin(page_key: str, max_width: int = 1360) -> WorkbenchStatus:
    """Common start of every workbench page: theme, session, rail, header. Returns derived status."""
    ensure_session(st.session_state)
    inject_theme(max_width)
    skip_link()
    s = compute_status(st.session_state)
    _rail(s)
    _header(s, page_key)
    return s


def _stage_links(s: WorkbenchStatus) -> None:
    """The seven stage links grouped Prepare / Inspect / Revise and deliver (used by the rail and the narrow-screen menu)."""
    group = None
    for stg in STAGES:
        if stg.group != group:
            group = stg.group
            st.html(f'<div class="ss-rail-group">{escape(group)}</div>')
        enabled, reason = _availability(stg.key, s)
        st.page_link(PAGES[stg.key], label=f"{stg.n}. {stg.title}", icon=_stage_icon(stg.key, s, enabled),
                     disabled=not enabled, help=(reason if not enabled else None))


def _rail(s: WorkbenchStatus) -> None:
    with st.sidebar:
        st.page_link(PAGES["landing"], label="Home", icon=":material/home:")
        _stage_links(s)
        st.divider()
        if st.button("Start over", icon=":material/restart_alt:", key="rail_reset", disabled=not s.has_input,
                     help="Clear the dataset and all results from this session."):
            _confirm_reset()


@st.dialog("Start over?")
def _confirm_reset() -> None:
    st.write("This clears the loaded dataset and every result in this session. Your rule settings are kept. "
             "Files you already downloaded are not affected.")
    c1, c2 = st.columns(2)
    if c1.button("Clear session", type="primary", width="stretch"):
        reset_session(st.session_state)
        st.switch_page(PAGES["landing"])
    if c2.button("Cancel", width="stretch"):
        st.rerun()


def appearance_popover() -> None:
    with st.popover("Appearance", icon=":material/contrast:"):
        st.markdown(
            "Light and dark follow your system setting, or choose one in Streamlit's menu: "
            "**⋮ (top right) → Settings → Theme**. Changing it does not reload the page or clear your data."
        )


def _header(s: WorkbenchStatus, page_key: str) -> None:
    c1, c2 = st.columns([5, 1.3], vertical_alignment="center")
    with c1:
        bits = [brand()]
        if s.has_input:
            bits.append(f'<span class="ss-chip neutral">{escape(s.dataset_label)}</span>')
            if s.synthetic:
                bits.append(chip("info", "Synthetic data", "info"))
            bits.append(status_chip_for(s))
        st.html('<div class="ss-header" style="padding-bottom:6px">' + "".join(bits) + "</div>")
    with c2:
        appearance_popover()
        with st.container(key="stages_menu"):
            with st.popover("Stages", icon=":material/menu:"):
                st.page_link(PAGES["landing"], label="Home", icon=":material/home:")
                _stage_links(s)
