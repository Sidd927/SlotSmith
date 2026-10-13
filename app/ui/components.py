"""Reusable UI components (design.md section D).

HTML builders are pure functions returning strings (unit-tested, no Streamlit needed); `render_*` helpers
place them. All data-derived text is escaped. Icons are inline SVG (no emoji, no network).
"""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from .theme import maxw_override, stylesheet

# Streamlit's HTML sanitiser strips <svg>, so status icons are CSS glyphs (see .ss-ic in base.css), not inline SVG.
ICONS = {"ok": "✓", "warn": "!", "bad": "✕", "info": "i", "stale": "↻", "idle": "·"}


def icon(name: str) -> str:
    return f'<span class="ss-ic {name}" aria-hidden="true">{ICONS[name]}</span>'


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
    from .fx import inject_fx
    inject_fx()


def skip_link() -> None:
    st.html('<a class="ss-skip" href="#ss-main">Skip to content</a><span id="ss-main"></span>')


def page_title(title: str, sub: str = "") -> None:
    st.html(f'<h2 class="ss-ph-title">{escape(title)}</h2>' + (f'<p class="ss-ph-sub">{escape(sub)}</p>' if sub else ""))


def stage_strip(items: list[tuple[str, str, str, str]]) -> str:
    """Workflow progress strip. items = (label, state, glyph, note); state in done|cur|attn|bad|todo|lock.

    Non-interactive (navigation lives in the rail): it shows where the user is and what needs attention."""
    parts = []
    for label, state, glyph, note in items:
        cur = ' aria-current="step"' if state == "cur" else ""
        parts.append(f'<li class="{state}"{cur} title="{escape(note)}"><span class="g" aria-hidden="true">{glyph}</span>'
                     f'{escape(label)}<span class="ss-sr">: {escape(note)}</span></li>')
    lis = "".join(parts)
    return f'<ol class="ss-prog" aria-label="Workflow progress">{lis}</ol>'


def page_header(eyebrow: str, title: str, sub: str, strip: str = "", num: str = "") -> None:
    st.html(f'{strip}<header class="ss-ph" data-n="{escape(num)}"><p class="ss-ph-eyebrow">{escape(eyebrow)}</p>'
            f'<h2 class="ss-ph-title">{escape(title)}</h2><p class="ss-ph-sub">{escape(sub)}</p></header>')


def composition_bar(placed: int, held: int, unplaced: int) -> str:
    total = max(1, placed + held + unplaced)
    pct = lambda n: f"{100 * n / total:.2f}%"
    return (f'<div class="ss-comp" role="img" aria-label="{placed} placed, {held} held, {unplaced} not placed">'
            f'<i class="p" style="width:{pct(placed)}"></i><i class="h" style="width:{pct(held)}"></i>'
            f'<i class="u" style="width:{pct(unplaced)}"></i></div>'
            f'<div class="ss-complegend"><span>Placed <b>{placed:,}</b></span><span>Held for a query <b>{held:,}</b></span>'
            f'<span>Not placed (capacity) <b>{unplaced:,}</b></span></div>')


def change_kind(kind: str) -> str:
    k = kind.lower()
    cls, g = (("moved", "→") if "move" in k else ("added", "+") if "add" in k
              else ("deleted", "−") if "delet" in k or "remov" in k
              else ("modified", "~") if "modif" in k else ("unchanged", "="))
    return f'<span class="ss-kind {cls}"><i aria-hidden="true">{g}</i>{escape(kind)}</span>'


def freshness_chip(rs) -> str:
    """Whether results match the current data and rules. Deliberately neutral when in sync: in sync is not correct."""
    if rs.freshness == "none":
        return chip("neutral", "Not allocated yet", "idle")
    if rs.freshness == "stale":
        return chip("warn", "Results stale", "stale").replace("ss-chip warn", "ss-chip warn ss-stalechip", 1)
    return chip("neutral", "Results match inputs", "idle")


def verification_chip(rs) -> str:
    """Outcome of the independent check, in words: passed / incomplete / failed. Skipped is never shown as passed."""
    if rs.verification in ("none",):
        return ""
    if rs.freshness == "stale":      # a stale result's verification no longer describes the current inputs
        return chip("neutral", f"Previous run: verification {rs.verification}", "stale")
    if rs.verification == "failed":
        return chip("bad", f"Verification failed · {rs.failed} family" if rs.failed == 1 else f"Verification failed · {rs.failed} families", "bad")
    if rs.verification == "incomplete":
        return chip("warn", f"Verification incomplete · {rs.skipped} skipped", "warn")
    if rs.verification == "missing":
        return chip("warn", "Verification report missing", "warn")
    return chip("ok", f"Verification passed · {rs.passed}/{rs.total}", "ok")


def status_chip_for(rs) -> str:
    """Freshness and verification together (used where space is tight)."""
    return freshness_chip(rs) + verification_chip(rs)


def verify_readout(check: list[dict]) -> str:
    """Compact dark 'instrument' for the independent check: one cell per rule family with its real state.

    PASS = ran and found nothing, FAIL = ran and found a violation, SKIPPED = not run because its rule is switched off.
    The headline never says everything passed unless every family ran."""
    passed = sum(1 for c in check if c["Result"] == "PASS")
    failed = sum(1 for c in check if c["Result"] == "FAIL" or c.get("Violations", 0) > 0)
    skipped = sum(1 for c in check if c["Result"] == "SKIPPED")
    state = "bad" if failed else "inc" if skipped else "ok"
    cls = {"PASS": "p", "FAIL": "f", "SKIPPED": "s"}
    cells = "".join(f'<i class="{cls.get(c["Result"], "f")}" style="--j:{j}" title="{escape(c["Rule"])}: {escape(c["Check"])} '
                    f'({c["Result"]}{": " + escape(c.get("Note", "")) if c.get("Note") else ""})">{escape(c["Rule"])}</i>'
                    for j, c in enumerate(check))
    if failed:
        verdict = f"{failed} rule famil{'y' if failed == 1 else 'ies'} with violations"
    elif skipped:
        verdict = f"Not a full verification: {skipped} skipped"
    else:
        verdict = "No violations found"
    counts = f"{passed} passed" + (f" · {failed} failed" if failed else "") + (f" · {skipped} skipped" if skipped else "")
    return (f'<div class="ss-vread {state}" role="group" aria-label="Independent verification: {counts} of {len(check)} rule families">'
            f'<div class="n"><b>{passed}</b><span>/{len(check)}</span></div><div class="t"><p class="k">Independent check · {len(check)} rule families</p>'
            f'<p class="v">{verdict}</p><p class="c">{counts}</p><div class="cells">{cells}</div></div></div>')


def verdict(rs, headline_ok_note: str = "", subject: str = "") -> str:
    """Overall outcome first (one sentence), then the separate facts. 'ok' only if nothing needs attention."""
    from app.core.status import next_actions
    if rs.freshness == "stale":
        kind, title, lead = "warn", "Results are out of date", "The data or rules changed after this run, so nothing below describes the current inputs."
    elif rs.verification == "failed":
        kind, title, lead = "bad", "Verification failed", "The independent check found violations. Do not use this allocation until they are resolved."
    elif not rs.accepted:
        kind, title = "warn", "Not ready to rely on yet"
        lead = ("Placement finished, but " + "; ".join(x for x in (
            f"{rs.held} row(s) are held or unplaced" if rs.held else "",
            f"{rs.unresolved_hw} signal(s) have unresolved hardware" if rs.unresolved_hw else "",
            f"{rs.skipped} verification check(s) were skipped" if rs.skipped else "",
            "the verification report is incomplete" if rs.verification == "missing" else "") if x)
                 + ". Allocation success is not verification success." + (" A skipped check is not a pass." if rs.skipped else ""))
    else:
        kind, title = "ok", "Every row placed and every check ran and passed"
        lead = headline_ok_note or "This applies to this dataset and these rules only. It is a consistency result, not engineering sign-off."
    alloc = ("warn", "Partial", f"{rs.held} held or unplaced") if rs.held else ("ok", "Complete", "every row placed")
    ver = {"passed": ("ok", "Passed", f"{rs.passed} of {rs.total} ran and passed"),
           "incomplete": ("warn", "Incomplete", f"{rs.passed} passed · {rs.skipped} skipped · {rs.failed} failed"),
           "failed": ("bad", "Failed", f"{rs.passed} passed · {rs.failed} failed · {rs.skipped} skipped"),
           "missing": ("warn", "Missing", "no usable report"), "none": ("", "Not run", "")}[rs.verification]
    hw = ("bad", f"{rs.unresolved_hw} unresolved", "no hardware mapping; held, never invented") if rs.unresolved_hw else ("ok", "None", "every signal has a mapping")
    off = ("warn", ", ".join(rs.disabled), "their checks are skipped") if rs.disabled else ("ok", "None", "all rules enforced")
    fr = ("warn", "Stale", "re-run Allocate") if rs.freshness == "stale" else ("", "Matches inputs", "says nothing about correctness")
    cells = "".join(f'<div class="ss-fact {k}"><div class="k">{escape(n)}</div><div class="v">{escape(v)}</div><div class="d">{escape(d)}</div></div>'
                    for n, (k, v, d) in (("Allocation", alloc), ("Verification", ver), ("Hardware", hw), ("Disabled rules", off), ("Freshness", fr)))
    todo = next_actions(rs)
    tl = ('<p class="ss-todo-h">Required before you rely on this result</p><ol class="ss-todo">' + "".join(f"<li><span>{escape(x)}</span></li>" for x in todo) + "</ol>") if todo else ""
    title = f"{subject}: {title}" if subject else title
    return f'<section class="ss-verdict {kind}" role="status"><h3>{escape(title)}</h3><p>{escape(lead)}</p><div class="ss-facts">{cells}</div>{tl}</section>'
