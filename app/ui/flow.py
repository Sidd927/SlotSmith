"""Landing signature: the signal-flow figure (design.md section F).

Pure HTML builder over real engine output (`app.core.demo.DemoBundle`). Content is real; it is labelled synthetic.
"""
from __future__ import annotations

from html import escape

from app.core.cabinet import type_code
from app.core.demo import DemoBundle, DemoSignal

_CHECKS_SHOWN = [("K-1", "Cable stays whole, in pair order"), ("S-1", "A and B never share a CIOC"),
                 ("H-1..6", "Right CHARM and terminal block")]


def _row(k: str, v: str, mono: bool = False) -> str:
    return f'<div class="row"><span>{escape(k)}</span><span class="{"mono" if mono else ""}">{escape(v)}</span></div>'


def _bp_cells(sig: DemoSignal) -> str:
    cells = []
    by_slot = {int(float(r["Slot"])): r for r in sig.neighbours}
    sel = int(float(sig.row["Slot"]))
    for n in range(1, 13):
        r = by_slot.get(n)
        if r is None:
            cells.append('<i title="Free slot"></i>')
            continue
        sel_cls = " sel" if n == sel else ""
        if r["Row Kind"] == "Signal":
            code = type_code(r)
            cells.append(f'<i class="t-{code.lower()}{sel_cls}" title="{escape(r["Tag"])} ({code})">{code}</i>')
        elif r["Row Kind"] == "Spare pair":
            cells.append(f'<i class="spare{sel_cls}" title="Wired spare pair"></i>')
        else:
            cells.append(f'<i class="held{sel_cls}" title="Held for a technical query">!</i>')
    return "".join(cells)


def flow_html(bundle: DemoBundle, sig: DemoSignal) -> str:
    r, m = sig.row, sig.mdb
    chk = {c["Rule"]: c for c in bundle.check}
    passed = sum(1 for c in bundle.check if c["Result"] == "PASS")
    verify_rows = "".join(
        _row(rid, "PASS" if chk.get(rid, {}).get("Result") == "PASS" else "FAIL") for rid, _ in _CHECKS_SHOWN)
    side = m.get("seg") or "none"
    steps = [
        ("Import", "source row", [
            f'<div class="mono">{escape(sig.source_line)}</div>',
            _row("Tag", sig.tag, True), _row("IO type", str(m["io_type"])),
            _row("Cable / pair", f'{m["cable"]} / {m["pair"]}', True),
            _row("Group / side", f'{m.get("group") or "none"} / {side}')]),
        ("Validate", "technical queries", [
            _row("Queries on this signal", str(sig.tqs_touching)),
            _row("Queries in this MDB", str(bundle.n_tqs)),
            '<div class="ss-cap" style="margin-top:6px">Checks required fields, duplicates, pair range, and A/B or group mixing per cable.</div>']),
        ("Allocate", "rules applied", [
            _row("Cabinet", r["Marshalling Cabinet"], True), _row("CIOC", r["CIOC"], True),
            _row("Baseplate / slot", f'{r["Baseplate"]} / {int(float(r["Slot"]))}', True),
            _row("CHARM", r["CHARM Type"]), _row("Terminal block", r["Terminal Block"])]),
        ("Verify", "independent check", [
            verify_rows, _row("All families", f"{passed} of {len(bundle.check)} pass")]),
        ("Slot", "where it lands", [
            f'<div class="mono">{escape(r["CHARM Address"])}</div>',
            f'<div class="ss-bp" role="img" aria-label="Baseplate {escape(r["Baseplate"])}: 12 slots, '
            f'slot {int(float(r["Slot"]))} highlighted">{_bp_cells(sig)}</div>']),
    ]
    items = ""
    for i, (title, sub, rows) in enumerate(steps):
        act = " act" if i == 4 else ""
        items += (f'<li class="ss-fstep{act}"><h4>{title} <span>{sub}</span></h4>{"".join(rows)}</li>')
    return (f'<figure class="ss-flow" aria-label="How one signal moves from an I/O list row to a CHARM slot">'
            f'<ol>{items}</ol>'
            f'<figcaption class="ss-cap">Illustrative. Computed by SlotSmith when this page loaded, from a seeded '
            f'<b>synthetic</b> MDB of {bundle.n_rows} rows. Not a live connection and not customer data.</figcaption></figure>')


_LETTERS = "abcd"


def _lane(i: int, sig: DemoSignal) -> str:
    r, m = sig.row, sig.mdb
    by_slot = {int(float(x["Slot"])): x for x in sig.neighbours}
    land = int(float(r["Slot"]))
    cells = ""
    for n in range(1, 13):
        k = (i - 1) * 12 + (n - 1)
        x = by_slot.get(n)
        if x is None:
            cells += '<div class="ss-vc"></div>'
            continue
        badge = f'<em>{_LETTERS[i - 1]}</em>' if n == land else ""
        cls = " land" if n == land else ""
        if x["Row Kind"] == "Signal":
            code = type_code(x)
            cells += (f'<div class="ss-vc t-{code.lower()}{cls}" style="--i:{k}" title="{escape(x["Tag"])} ({code})">'
                      f'<b>{code}</b>{badge}</div>')
        elif x["Row Kind"] == "Spare pair":
            cells += f'<div class="ss-vc spare{cls}" style="--i:{k}" title="Wired spare pair"><b></b>{badge}</div>'
        else:
            cells += f'<div class="ss-vc held{cls}" style="--i:{k}" title="Held for a technical query"><b>!</b>{badge}</div>'
    code = type_code(r)
    label = (f"Signal {_LETTERS[i - 1]}: {sig.tag}, {code}, {sig.source_line}, lands at {r['CHARM Address']}")
    return (f'<div class="ss-lane l{i}" style="--l:{i}">'
            f'<div class="src s{i}" tabindex="0" role="group" aria-label="{escape(label)}">'
            f'<span class="bd">{_LETTERS[i - 1]}</span><span class="rw">{escape(sig.source_line.split("· ")[-1])}</span>'
            f'<span class="tg">{escape(sig.tag)}</span><span class="ty">{code}</span></div>'
            f'<span class="wire" aria-hidden="true"></span>'
            f'<div class="bp"><span class="bpn">{escape(r["Baseplate"])}</span><div class="ss-viz-cells">{cells}</div></div></div>')


def _trace(i: int, sig: DemoSignal) -> str:
    r, m = sig.row, sig.mdb
    return (f'<p class="tr s{i}"><span class="bd">{_LETTERS[i - 1]}</span> <b>{escape(sig.tag)}</b> '
            f'<span class="ar">→</span> {escape(r["Marshalling Cabinet"])} <span class="ar">›</span> {escape(r["CIOC"])} '
            f'<span class="ar">›</span> {escape(r["Baseplate"])} <span class="ar">›</span> slot {int(float(r["Slot"]))} '
            f'<span class="dim">· {escape(r["CHARM Type"])} · cable {escape(str(m["cable"]))} pair {escape(str(m["pair"]))} · '
            f'{escape(sig.source_line)}</span></p>')


def bench_html(bundle: DemoBundle, mode: str = "hero") -> str:
    """The product in miniature: source rows -> constrained allocation -> independent verification -> export.

    Everything shown is real output of the seeded synthetic demo run (`app.core.demo.build_demo`). `mode` is "hero"
    (plays once on load) or "story" (stages are revealed by the scroll-driven story)."""
    sigs = bundle.signals[:4]
    cab = sigs[0].row["Marshalling Cabinet"] if sigs else ""
    passed = sum(1 for c in bundle.check if c["Result"] == "PASS")
    lanes = "".join(_lane(i, s) for i, s in enumerate(sigs, 1))
    traces = "".join(_trace(i, s) for i, s in enumerate(sigs, 1))
    checks = "".join(f'<span class="{"ok" if c["Result"] == "PASS" else "no"}" style="--j:{j}" title="{escape(c["Check"])}">'
                     f'{escape(c["Rule"])}</span>' for j, c in enumerate(bundle.check))
    rv = bundle.revision
    export = (f'<span>IO Allocation <b>{bundle.n_rows:,}</b></span><span>Cabinet Summary</span>'
              f'<span>TQ List <b>{bundle.n_tqs}</b></span><span>Rule Check <b>{len(bundle.check)}</b></span>'
              f'<span class="rev">Rev B <b>{rv["moved"]}</b> moved · <b>{rv["added"]}</b> added · <b>{rv["deleted"]}</b> deleted</span>')
    return (
        f'<figure class="ss-bench {mode}" aria-label="Synthetic demonstration: four signals from an I/O list placed into CHARM slots, '
        f'then checked by {passed} of {len(bundle.check)} independent rules">'
        f'<header class="ss-bench-h"><span class="ss-bench-t">Synthetic run · <b>{escape(cab)}</b></span>'
        f'<ol class="ss-st4" aria-hidden="true"><li class="s1">Source</li><li class="s2">Allocate</li>'
        f'<li class="s3">Verify</li><li class="s4">Export</li></ol></header>'
        f'<div class="ss-lanes"><div class="ss-lane-h"><span>I/O list row</span><span>Cabinet · CIOC · baseplate · 12 CHARM slots</span></div>{lanes}</div>'
        f'<div class="ss-trace" aria-live="off">{traces}</div>'
        f'<div class="ss-verify"><span class="lb">Independent check · {passed}/{len(bundle.check)} rule families</span>'
        f'<div class="chk">{checks}</div></div>'
        f'<div class="ss-export"><span class="lb">Workbook</span><div class="chips">{export}</div></div>'
        f'<figcaption class="ss-cap">Synthetic demo data, real engine output. Hover or focus a row to trace it.</figcaption></figure>')


CHAPTERS = [
    ("01", "Import", "Your list, exactly as written.",
     "Excel or CSV in. Columns are matched automatically and every row keeps its file, sheet and row number, so any result can be traced back to its source."),
    ("02", "Allocate", "Whole cables, in pair order, into slots.",
     "Each cable lands in a cabinet, CIOC, baseplate and CHARM slot under your rules. What cannot be placed safely is held as a technical query, not guessed."),
    ("03", "Verify", "A second opinion that shares no code.",
     "An independent checker re-reads the exported rows and tests 11 rule families. It reports what it checked and any violation it found."),
    ("04", "Deliver", "A workbook you can hand over.",
     "Allocation, cabinet summary, technical queries and the rule check, tied to the run that produced them. A revision keeps unchanged cables where they are."),
]


def story_html(bundle: DemoBundle) -> str:
    """Scroll-driven product story: one connected stage that is transformed chapter by chapter.

    Without scroll-timeline support, with reduced motion, or below 1000 px it is a plain stacked section in which every
    stage is already visible."""
    ch = "".join(f'<article class="ss-ch c{i}"><span class="k">{n} · {k}</span><h3>{escape(h)}</h3><p>{escape(p)}</p></article>'
                 for i, (n, k, h, p) in enumerate(CHAPTERS, 1))
    rail = "".join(f'<li class="r{i}"><span>{n}</span>{k}</li>' for i, (n, k, _, _) in enumerate(CHAPTERS, 1))
    return (f'<section class="ss-story" id="how"><div class="ss-story-pin">'
            f'<div class="ss-chcol"><ol class="ss-rail4" aria-label="Chapters">{rail}</ol><div class="ss-chs">{ch}</div></div>'
            f'<div class="ss-stage">{bench_html(bundle, "story")}</div></div></section>')


def viz_html(bundle: DemoBundle) -> str:   # kept for callers that want the hero stage
    return bench_html(bundle, "hero")
