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
