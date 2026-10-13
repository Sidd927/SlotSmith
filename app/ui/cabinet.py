"""Cabinet slot grid renderer (design.md D: Cabinet slot grid, Legend). Pure HTML over `CabinetModel`."""
from __future__ import annotations

from html import escape
from typing import Collection

from app.core.cabinet import BP_PER_CIOC, SLOTS_PER_BP, TYPE_WORDS, CabinetModel, Slot


def legend_html() -> str:
    items = "".join(
        f'<span role="listitem"><span class="ss-slot t-{c.lower()}" aria-hidden="true">{c}</span>{escape(w)}</span>'
        for c, w in TYPE_WORDS.items())
    items += ('<span role="listitem"><span class="ss-slot spare" aria-hidden="true"></span>Wired spare pair</span>'
              '<span role="listitem"><span class="ss-slot held" aria-hidden="true">!</span>Held for a technical query</span>'
              '<span role="listitem"><span class="ss-slot held unres" aria-hidden="true">?</span>Unresolved hardware (no CHARM mapping)</span>'
              '<span role="listitem"><span class="ss-slot free" aria-hidden="true" style="color:transparent"></span>Free slot</span>')
    return f'<div class="ss-legend" role="list" aria-label="Slot legend">{items}</div>'


def _cell(s: Slot, selected: str | None, matches: Collection[str] | None) -> str:
    cls = ["ss-slot"]
    text = ""
    if s.kind == "signal":
        cls.append(f"t-{s.code.lower()}")
        text = s.code
    elif s.kind == "spare":
        cls.append("spare")
    elif s.kind == "held":
        cls.append("held")
        text = "!"
        if s.reason == "hardware":
            cls.append("unres")     # distinct from every signal-type tint: red, dashed, "?" glyph
            text = "?"
    else:
        cls.append("free")
    if selected and s.key == selected:
        cls.append("sel")
    if matches is not None and s.kind != "free" and s.key not in matches:
        cls.append("dim")
    label = escape(s.label + (f" at {s.address}" if s.address else ""))
    return f'<div class="{" ".join(cls)}" role="img" aria-label="{label}" title="{label}">{text}</div>'


def cabinet_html(model: CabinetModel, selected: str | None = None, matches: Collection[str] | None = None) -> str:
    head = "".join(f'<span class="ss-sn">{n}</span>' for n in range(1, SLOTS_PER_BP + 1))
    cards = ""
    for c in model.ciocs:
        meta = " · ".join(x for x in (c.group and f"group {c.group}", c.seg and f"side {c.seg}") if x) or "no group"
        n_sig = sum(1 for s in c.slots.values() if s.kind == "signal")
        n_sp = sum(1 for s in c.slots.values() if s.kind == "spare")
        n_held = sum(1 for s in c.slots.values() if s.kind == "held")
        cap = BP_PER_CIOC * SLOTS_PER_BP
        pct = 100 * len(c.slots) / cap
        occ = (f'<div class="ss-cioc-occ"><span>{n_sig} signals · {n_sp} spare · {n_held} held · '
               f'{cap - len(c.slots)} free of {cap}</span><span class="ss-bar" aria-hidden="true"><i style="width:{pct:.0f}%"></i></span></div>')
        rows = f'<div class="ss-bphead"><span class="ss-bpn" aria-hidden="true">BP</span>{head}</div>'
        for bp in range(1, BP_PER_CIOC + 1):
            cells = "".join(_cell(c.slot(bp, n), selected, matches) for n in range(1, SLOTS_PER_BP + 1))
            rows += f'<div class="ss-bprow"><span class="ss-bpn" aria-hidden="true">{bp}</span>{cells}</div>'
        cards += (f'<section class="ss-cioc" tabindex="0" aria-label="CIOC {escape(c.name)}"><div class="ss-cioc-top"><p class="ss-cioc-h">{escape(c.name)}</p>'
                  f'<p class="ss-cioc-s">{escape(meta)}</p></div>{occ}{rows}</section>')
    return (f'<div class="ss-cabwrap" role="group" aria-label="Cabinet {escape(model.name)}: {len(model.ciocs)} CIOC(s)">{cards}</div>')
