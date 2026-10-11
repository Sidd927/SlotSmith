"""Reusable UI components (design.md section D).

HTML builders are pure functions returning strings (unit-tested, no Streamlit needed); `render_*` helpers
place them. All data-derived text is escaped. Icons are inline SVG (no emoji, no network).
"""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from .theme import maxw_override, stylesheet

ICONS = {
    "ok": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
    "warn": '<path d="M12 4l9 16H3z"/><path d="M12 10v4"/><path d="M12 17.4v.2"/>',
    "bad": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 7.9v.2"/>',
    "stale": '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4v5h-5"/>',
    "idle": '<circle cx="12" cy="12" r="9" stroke-dasharray="3 3"/>',
}


def icon(name: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


def chip(kind: str, text: str, icon_name: str | None = None) -> str:
    """Status chip: symbol + word + colour. kind in ok|warn|bad|info|neutral."""
    ic = icon(icon_name) if icon_name else ""
    return f'<span class="ss-chip {kind}">{ic}{escape(text)}</span>'


def banner(kind: str, title: str, body: str = "", *, raw_body: bool = False) -> str:
    ic = {"ok": "ok", "warn": "warn", "bad": "bad", "info": "info"}[kind]
    b = body if raw_body else escape(body)
    return (f'<div class="ss-banner {kind}" role="status">{icon(ic)}<div><b>{escape(title)}</b>'
            f'{f"<p>{b}</p>" if body else ""}</div></div>')


def tile(label: str, value: str, qualifier: str = "", *, tone: str = "", stale: bool = False) -> str:
    cls = " ".join(x for x in ("ss-tile", tone, "stale" if stale else "") if x)
    q = f'<div class="q">{escape(qualifier)}</div>' if qualifier else ""
    return f'<div class="{cls}"><div class="l">{escape(label)}</div><div class="v">{escape(value)}</div>{q}</div>'


def tiles(items: Iterable[dict]) -> str:
    return '<div class="ss-tiles">' + "".join(tile(**i) for i in items) + "</div>"


def kv(pairs: Iterable[tuple[str, str]]) -> str:
    return '<dl class="ss-kv">' + "".join(
        f"<dt>{escape(k)}</dt><dd>{escape(v) if v else '—'}</dd>" for k, v in pairs) + "</dl>"


def brand() -> str:
    cells = "".join("<i></i>" for _ in range(12))
    return f'<span class="ss-brand"><span class="ss-mark" aria-hidden="true">{cells}</span>SlotSmith</span>'


def ledger(headers: list[str], rows: list[list[str]], numeric: set[int] = frozenset(), *, raw: bool = False,
           caption: str = "") -> str:
    th = "".join(f'<th class="{"n" if i in numeric else ""}" scope="col">{escape(h)}</th>' for i, h in enumerate(headers))
    body = ""
    for r in rows:
        tds = "".join(f'<td class="{"n" if i in numeric else ""}">{c if raw else escape(c)}</td>' for i, c in enumerate(r))
        body += f"<tr>{tds}</tr>"
    cap = f"<caption class='ss-cap' style='text-align:left'>{escape(caption)}</caption>" if caption else ""
    return f'<div class="ss-ledger-wrap"><table class="ss-ledger">{cap}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def severity_chip(sev: str) -> str:
    s = (sev or "").lower()
    return {"blocking": chip("bad", "Blocking", "bad"), "warning": chip("warn", "Warning", "warn"),
            "info": chip("info", "Info", "info")}.get(s, chip("neutral", sev))


# ----------------------------------------------------------------------------- rendering helpers
def inject_theme(max_width: int = 1360) -> None:
    """Inject the design-system stylesheet (style-only HTML takes no layout space)."""
    st.html(f"<style>{stylesheet()}{maxw_override(max_width)}</style>")


def skip_link() -> None:
    st.html('<a class="ss-skip" href="#ss-main">Skip to content</a><span id="ss-main"></span>')


def page_title(title: str, sub: str = "") -> None:
    st.markdown(f"## {title}")
    if sub:
        st.html(f'<p class="ss-page-sub">{escape(sub)}</p>')


def status_chip_for(status) -> str:
    """Chip describing whether the displayed allocation is current."""
    if not status.has_allocation:
        return chip("neutral", "Not allocated yet", "idle")
    if status.alloc.is_stale:
        return chip("warn", "Results stale", "stale")
    return chip("ok", "Results current", "ok")
