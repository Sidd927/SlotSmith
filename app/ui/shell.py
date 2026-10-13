"""Application shell: page registry, header, and the workbench stage rail (design.md B, D)."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

import streamlit as st

from app.core.session import WorkbenchStatus, compute_status, ensure_session, reset_session
from .components import brand, chip, freshness_chip, inject_theme, page_header, skip_link, stage_strip, verification_chip


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


_ICON = {"done": ":material/check_circle:", "attn": ":material/warning:", "bad": ":material/error:",
         "todo": ":material/radio_button_unchecked:", "lock": ":material/lock:", "cur": ":material/radio_button_checked:"}


def _stage_icon(key: str, s: WorkbenchStatus, enabled: bool) -> str:
    """Rail icon derived from the same real stage state as the workflow strip (never 'done' for failed/incomplete work)."""
    if not enabled:
        return _ICON["lock"]
    return _ICON[stage_states(s)[key][0]]


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
    """Compact context bar: brand, breadcrumb, then dataset, run id and result status in one quiet line."""
    from app.core.session import run_id
    hdr = st.container(key="wbhdr")
    c1, c2 = hdr.columns([5, 1.3], vertical_alignment="center")
    with c1:
        stage = next((x for x in STAGES if x.key == page_key), None)
        bits = [brand(), f'<nav class="ss-crumb" aria-label="Breadcrumb"><span>Workbench</span><i aria-hidden="true">/</i>'
                         f'<b aria-current="page">{escape(STRIP_LABELS.get(page_key, stage.title if stage else ""))}</b></nav>']
        ctx = []
        if s.has_input:
            label = s.dataset_label.removeprefix("Synthetic benchmark · ")
            ctx.append(f'<span class="ss-ctx">{"<i class=syn>Synthetic</i>" if s.synthetic else ""}<span>{escape(label)}</span>'
                       + (f'<span class="rid" title="Run id">run {run_id(st.session_state)}</span>' if s.has_allocation else "") + "</span>")
            from app.core.status import run_status
            rs = run_status(st.session_state)
            ctx.append(freshness_chip(rs))
            ctx.append(verification_chip(rs))
        st.html('<div class="ss-header" style="padding-bottom:6px">' + "".join(bits) + '<span class="ss-spacer"></span>' + "".join(ctx) + "</div>")
    with c2:
        appearance_popover()
        with st.container(key="stages_menu"):
            with st.popover("Stages", icon=":material/menu:"):
                st.page_link(PAGES["landing"], label="Home", icon=":material/home:")
                _stage_links(s)


# Short names for the workflow strip: Import, Review, Allocate (configure + run), Results, Inspect, Revise, Deliver.
STRIP_LABELS = {"input": "Import", "review": "Review", "allocate": "Allocate", "results": "Results",
                "cabinets": "Inspect", "revise": "Revise", "deliverables": "Deliver"}
_GLYPH = {"done": "✓", "attn": "!", "bad": "✕", "todo": "○", "lock": "–", "cur": "●"}


def stage_states(s: WorkbenchStatus) -> dict[str, tuple[str, str]]:
    """Derive (state, note) per stage from real state. A stage is 'done' only when its outcome exists and is current."""
    from app.core.session import get_audit
    from app.core.state import unresolved_hardware, verification_status
    out: dict[str, tuple[str, str]] = {}
    out["input"] = ("done", "dataset loaded") if s.has_input else ("todo", "no dataset yet")
    if not s.has_input:
        out["review"] = out["allocate"] = ("lock", "needs a dataset")
    else:
        audit = get_audit(st.session_state)
        if audit is None:
            out["review"] = ("bad", "dataset could not be read")
        elif audit.readiness_status == "blocked":
            out["review"] = ("bad", "blocked: no valid cable")
        elif audit.blocking_tqs:
            out["review"] = ("attn", f"{audit.blocking_tqs} blocking finding(s)")
        elif audit.warning_tqs:
            out["review"] = ("attn", f"{audit.warning_tqs} warning(s)")
        else:
            out["review"] = ("done", "no findings")
        if not s.has_allocation:
            out["allocate"] = ("todo", "not run yet")
        elif s.alloc.is_stale:
            out["allocate"] = ("attn", "results out of date")
        else:
            out["allocate"] = ("done", "allocation current")
    if not s.has_allocation:
        for k in ("results", "cabinets", "revise", "deliverables"):
            out[k] = ("lock", "needs an allocation")
        return out
    res = st.session_state.get("res")
    if s.alloc.is_stale:
        for k in ("results", "cabinets", "deliverables"):
            out[k] = ("attn", "out of date")
        out["revise"] = ("attn", "paused until Allocate is re-run")
        return out
    vs = verification_status(res)
    held = sum(1 for t in res.tqs if t.severity == "blocking")
    hw = len(unresolved_hardware(res))
    if vs["outcome"] == "failed":
        out["results"] = ("bad", "verifier found violations")
    elif hw:
        out["results"] = ("attn", f"{hw} signal(s) with unresolved hardware")
    elif vs["outcome"] != "passed":
        out["results"] = ("attn", f"{vs['skipped']} check(s) skipped: rules switched off")
    elif held:
        out["results"] = ("attn", f"{held} blocking quer{'y' if held == 1 else 'ies'}")
    else:
        out["results"] = ("done", "verified, nothing held")
    out["cabinets"] = ("attn", f"{hw} unresolved-hardware slot(s) held") if hw else ("done", "map matches current results")
    if s.has_revision:
        rr = st.session_state.get("rr")
        rvs = verification_status(rr) if rr is not None else {"outcome": "missing", "skipped": 0}
        if s.rev.is_stale:
            out["revise"] = ("attn", "revision out of date")
        elif rvs["outcome"] == "failed":
            out["revise"] = ("bad", "Rev B verification failed")
        elif rvs["outcome"] != "passed":
            out["revise"] = ("attn", "Rev B verification incomplete")
        else:
            out["revise"] = ("done", "Rev B applied and verified")
    else:
        out["revise"] = ("todo", "optional: no Rev B applied")
    if vs["outcome"] == "failed":
        out["deliverables"] = ("bad", "file exists but verification failed")
    elif vs["outcome"] != "passed" or hw:
        out["deliverables"] = ("attn", "file exists; verification incomplete or hardware unresolved")
    else:
        out["deliverables"] = ("done", "export matches current results")
    return out


def header(page_key: str, title: str, sub: str) -> None:
    """Workflow strip + page title block (eyebrow shows step number and group)."""
    s = compute_status(st.session_state)
    states = stage_states(s)
    items = []
    for stg in STAGES:
        state, note = states[stg.key]
        css = "cur" if stg.key == page_key else state
        items.append((STRIP_LABELS[stg.key], css, _GLYPH[css if css in _GLYPH else state], note))
    stg = next(x for x in STAGES if x.key == page_key)
    page_header(f"Step {stg.n} of {len(STAGES)} · {stg.group}", title, sub, stage_strip(items), num=f"{stg.n:02d}")


def next_action(key: str, kicker: str, text: str, label: str, target: str, *, disabled: bool = False,
                primary: bool = True, why_disabled: str = "") -> None:
    """One clear next step: what comes next, why, and the button that goes there."""
    with st.container(key=f"nextbar_{key}"):
        c1, c2 = st.columns([3, 1.2], vertical_alignment="center")
        c1.html(f'<div class="ss-next"><span class="k">{escape(kicker)}</span><b>{escape(text)}</b>'
                + (f'<span>{escape(why_disabled)}</span>' if disabled and why_disabled else "") + "</div>")
        if c2.button(label, type="primary" if primary else "secondary", key=f"next_{key}", disabled=disabled,
                     icon=":material/arrow_forward:", width="stretch"):
            st.switch_page(PAGES[target])
