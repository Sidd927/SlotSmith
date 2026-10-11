"""Hand-laid-out SVG diagrams for docs/SlotSmith_Technical_Dossier.md (Figures B, D, H). PNG via PyMuPDF.

    .venv/bin/python scripts/dossier_diagrams.py

Fig D numbers come from docs/assets/slotsmith/data/examples_fast.json (scripts/dossier_examples.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from dossier_figures import FONT, Svg, esc  # noqa: E402
import dossier_figures as F  # noqa: E402

OUT = ROOT / "docs" / "assets" / "slotsmith" / "diagrams"
F.OUT = OUT          # reuse Svg.save() for this folder

STYLE = {  # fill, stroke, text
    "core": ("#e8f4ea", "#2f7d4a", "#0f2a18"), "chk": ("#fff4d6", "#b07a00", "#3a2900"),
    "file": ("#e8f1fb", "#3a6ea5", "#0d2238"), "surf": ("#f1ecfa", "#6a4fa5", "#241a3a"),
    "plan": ("#f6f6f6", "#8a8a8a", "#555555"), "bad": ("#fde8e8", "#b03030", "#3a0f0f"),
    "rule": ("#eef3f7", "#4a6a85", "#10202c"),
}


def node(s: Svg, x, y, w, h, title, lines=(), kind="core", dash=False, tsize=14, lsize=11.5):
    fill, stroke, tc = STYLE[kind]
    d = ' stroke-dasharray="6 4"' if dash else ""
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')
    tl = [title] if isinstance(title, str) else list(title)
    lh = lsize + 4
    th = tsize + 3
    total = len(tl) * th + (6 if lines else 0) + len(lines) * lh
    ty = y + (h - total) / 2 + tsize
    for j, t in enumerate(tl):
        s.text(x + w / 2, ty + j * th, t, tsize, tc, "middle", "bold")
    for i, ln in enumerate(lines):
        s.text(x + w / 2, ty + (len(tl) - 1) * th + 8 + (i + 1) * lh - 3, ln, lsize, tc, "middle")


def arrow(s: Svg, pts, color="#444", dash=False, w=1.8, label=None, lpos=None, lsize=10.5):
    """Polyline with an arrowhead at the end. pts = [(x, y), ...]."""
    d = ' stroke-dasharray="6 4"' if dash else ""
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    s.add(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="{w}"{d}/>')
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L, W = 10, 5
    p1 = (x2 - L * math.cos(ang) + W * math.sin(ang), y2 - L * math.sin(ang) - W * math.cos(ang))
    p2 = (x2 - L * math.cos(ang) - W * math.sin(ang), y2 - L * math.sin(ang) + W * math.cos(ang))
    s.add(f'<polygon points="{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')
    if label:
        lx, ly = lpos or ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2 - 6)
        s.text(lx, ly, label, lsize, "#333", "middle")


def lane_label(s, x, y, w, text):
    s.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="13" font-weight="bold" fill="#333">{esc(text)}</text>')
    s.line(x, y + 6, x + w, y + 6, "#bbb", 1)


def fig_b():
    W, H = 1240, 820
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure B. End-to-end SlotSmith architecture (what the code does today)", 17, anchor="middle", weight="bold")
    s.text(W / 2, 48, "Solid boxes are implemented in src/slotsmith or app/. Amber = independent verification. Dashed = conditional or planned. Files are blue.", 11.5, "#555", "middle")
    # rule set bar
    node(s, 20, 58, W - 40, 50, "Rule set (rules.py: RuleSet, JSON, pydantic)", ["read by validate, allocate, revise, repair and verify: hardware table, capacities, spare %, naming patterns, rule switches"], "rule", tsize=13, lsize=11)
    bw, bh, gap = 138, 96, 14
    xs = [20 + i * (bw + gap) for i in range(8)]
    # lane 1
    y1 = 150
    lane_label(s, 20, y1 - 18, W - 40, "Lane 1  Initial allocation: pipeline.run() (used by the CLI and by the Streamlit 'Allocate' button)")
    n1 = [(["Customer", "I/O list(s)"], ["xlsx / csv, many", "files and sheets"], "file"), ("ingest.py", ["read_mdb", "auto_map", "file:sheet:row"], "core"),
          ("validate.py", ["validate", "cable blocks", "TQs"], "core"), ("allocator.py", ["allocate", "FFD + Placer", "capacity TQs"], "core"),
          ("export.py", ["build_rows", "write_workbook"], "core"), (["Allocation", "workbook"], ["IO Allocation, Cabinet", "Summary, TQ List, ..."], "file"),
          ("verifier.py", ["load_allocation", "verify: 11 checks"], "chk"), (["Workbook with", "Rule Check"], ["rewritten with the", "Rule Check sheet"], "file")]
    for i, (t, ls, k) in enumerate(n1):
        node(s, xs[i], y1, bw, bh, t, ls, k, tsize=13, lsize=11)
        if i < 7:
            arrow(s, [(xs[i] + bw + 1, y1 + bh / 2), (xs[i + 1] - 1, y1 + bh / 2)], "#b07a00" if i == 5 else "#444")
    s.text(xs[5] + bw + gap / 2, y1 + bh / 2 - 8, "re-read", 10, "#8a5a00", "middle")
    # lane 2
    y2 = 330
    lane_label(s, 20, y2 - 18, W - 40, "Lane 2  Revision: revision.revise() (CLI 'revise' and the Streamlit 'Compare and re-allocate' button)")
    n2 = [(["Rev A rows +", "Rev B list"], ["Rev A: run() rows or", "the Rev A workbook"], "file"), (["ingest.py +", "validate.py"], ["Rev B cable blocks", "and TQs"], "core"),
          ("revision.py", ["pin unchanged cables", "greedy fill of the rest", "impact_report"], "core"), ("(next box)", [], "core"),
          ("export.py", ["build_rows", "write_workbook", "+ Revision Impact"], "core"), (["Rev B", "workbook"], ["same sheets", "+ Revision Impact"], "file"),
          ("verifier.py", ["same 11 checks on", "the written file"], "chk"), (["Rev B workbook", "with Rule Check"], ["rewritten after", "re-verification"], "file")]
    n2[3] = ("repair_cpsat.py", ["CP-SAT window repair", "only if greedy fails"], "core")
    pos = [0, 1, 2, 3, 4, 5, 6, 7]
    for i, (t, ls, k) in enumerate(n2):
        if i == 3:
            continue
        node(s, xs[i], y2, bw, bh, t, ls, k, tsize=13, lsize=11)
    node(s, xs[2] + 10, y2 + bh + 38, 2 * bw + gap - 20, 66, "repair_cpsat.py (OR-Tools CP-SAT)", ["conditional: window of cabinets, 10 s per solve", "fallback: full re-allocation + warning TQ"], "core", dash=True, tsize=12.5, lsize=10.5)
    arrow(s, [(xs[0] + bw + 1, y2 + bh / 2), (xs[1] - 1, y2 + bh / 2)])
    arrow(s, [(xs[1] + bw + 1, y2 + bh / 2), (xs[2] - 1, y2 + bh / 2)])
    arrow(s, [(xs[2] + bw + 1, y2 + bh / 2), (xs[4] - 1, y2 + bh / 2)], label="Rev B rows", lpos=(xs[3] + bw / 2 + 12, y2 + bh / 2 - 8))
    cx = xs[2] + bw / 2 + 24
    arrow(s, [(cx, y2 + bh + 1), (cx, y2 + bh + 37)], "#6a6a6a", dash=True)
    arrow(s, [(cx + 60, y2 + bh + 37), (cx + 60, y2 + bh + 1)], "#6a6a6a", dash=True)
    s.text(cx + 76, y2 + bh + 25, "windows, solution", 10, "#555")
    arrow(s, [(xs[4] + bw + 1, y2 + bh / 2), (xs[5] - 1, y2 + bh / 2)])
    arrow(s, [(xs[5] + bw + 1, y2 + bh / 2), (xs[6] - 1, y2 + bh / 2)], "#b07a00", label="re-read", lpos=(xs[5] + bw + gap / 2, y2 + bh / 2 - 8))
    arrow(s, [(xs[6] + bw + 1, y2 + bh / 2), (xs[7] - 1, y2 + bh / 2)], "#b07a00")
    # lane 3: surfaces and evidence
    y3 = 596
    lane_label(s, 20, y3 - 18, W - 40, "Surfaces, data generation and evidence (they call the engine; the engine never imports them)")
    sw = (W - 40 - 3 * 20) / 4
    items = [("cli.py", ["generate, allocate, verify,", "revise, rules (exit code 2", "if violations remain)"], "surf"),
             ("app/ (Streamlit)", ["views/ + core/session.py:", "load, run_allocation, run_revision,", "reset, staleness, downloads"], "surf"),
             ("generator.py", ["synthetic MDB, 9 kinds of", "injected data errors, Rev B", "(demo, tests, benchmarks)"], "core"),
             ("tests/ and scripts/", ["122 pytest tests, benchmark.py,", "audit_*.py exact-solver checks,", "artifacts/ outputs"], "chk")]
    for i, (t, ls, k) in enumerate(items):
        node(s, 20 + i * (sw + 20), y3, sw, 100, t, ls, k, tsize=14, lsize=11.5)
    node(s, 20, 716, W - 40, 56, "Planned, not implemented", ["LLM suggestion helper for column mapping and rule drafts  ·  exporter for the official allocation template (not released)  ·  Docker demo bundle"], "plan", dash=True, tsize=13, lsize=11.5)
    s.text(W / 2, 800, "Row provenance (file:sheet:row) travels with every signal into the TQ list and the 'Source' column of the workbook.", 11, "#555", "middle")
    s.save("figB_architecture")


def fig_d():
    d = json.loads((ROOT / "docs/assets/slotsmith/data/examples_fast.json").read_text())["ab_interaction"]
    W, H = 1100, 500
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure D. Constraint interaction: two 6-pair cables, one on side A and one on side B (same IO group)", 16, anchor="middle", weight="bold")
    s.text(W / 2, 48, "Computed with the real engine on 12 synthetic signals (scripts/dossier_examples.py). Slot numbers are the actual output.", 11.5, "#555", "middle")

    def bp(x, y, cab_a, cab_b, label, lab2):
        cw = 34
        for i in range(12):
            slot = i + 1
            owner = "A" if slot in cab_a else "B" if slot in cab_b else None
            fill = {"A": "#f6dc9b", "B": "#a9dcf3", None: "#ffffff"}[owner]
            stroke = {"A": "#b07a00", "B": "#2d86b3", None: "#bbb"}[owner]
            s.rect(x + i * (cw + 3), y, cw, 40, fill, stroke, 1.5, 4)
            s.text(x + i * (cw + 3) + cw / 2, y + 25, owner or str(slot), 12, "#222" if owner else "#999", "middle", "bold" if owner else "normal")
        s.text(x, y - 8, label, 12, "#222", "start", "bold")
        s.text(x, y + 60, lab2, 11, "#555")

    wa, wo = d["with_A_B_sides"], d["without_sides"]
    s.text(40, 100, "1. If the cables carried no A/B side", 14, "#222", weight="bold")
    s.text(40, 119, f"Result: {wo['metrics']['baseplates']} baseplate, {wo['metrics']['ciocs']} CIOC, 0 violations.", 12, "#333")
    bp(40, 150, set(wo["slots"]["CBL-A"]), set(wo["slots"]["CBL-B"]), f"{wo['cables']['CBL-A'][0][0]} · {wo['cables']['CBL-A'][0][1]}",
       "Both cables fit one 12-slot baseplate (CBL-A slots 1-6, CBL-B slots 7-12).")
    s.line(40, 245, W - 40, 245, "#ddd")
    s.text(40, 280, "2. With CBL-A on side A and CBL-B on side B (rule 2: A and B never share a CIOC)", 14, "#222", weight="bold")
    s.text(40, 299, f"Result: {wa['metrics']['baseplates']} baseplates in {wa['metrics']['ciocs']} CIOCs, 0 violations. Each cable stays whole and in pair order (rule 4).", 12, "#333")
    bp(40, 335, set(wa["slots"]["CBL-A"]), set(), f"{wa['cables']['CBL-A'][0][0]} · {wa['cables']['CBL-A'][0][1]} (side A)", "")
    bp(40, 435, set(), set(wa["slots"]["CBL-B"]), f"{wa['cables']['CBL-B'][0][0]} · {wa['cables']['CBL-B'][0][1]} (side B)", "")
    s.rect(580, 340, 480, 150, "#fff4d6", "#b07a00", 1.3, 8)
    for i, t in enumerate(["What changed: the same 12 signals use 2 baseplates",
                           "instead of 1, and half of each baseplate stays free.",
                           "This waste is forced by rules 2 and 4, so it counts",
                           "against capacity (rule 3) and the spare budget (rule 5).",
                           "Verifier check S-1 fails if A and B share a CIOC."]):
        s.text(596, 366 + i * 24, t, 12.5, "#3a2900", weight="bold" if i == 0 else "normal")
    s.save("figD_constraint_interaction")


def fig_h():
    W, H = 1210, 480
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure H. User journey through the Streamlit workbench (routes in parentheses)", 17, anchor="middle", weight="bold")
    bw, bh = 262, 112
    cols = [20, 322, 624, 926]
    row1 = [("Landing  (/)", ["explains the tool; 'Run the", "synthetic demo' loads data", "and opens Review"], "surf"),
            ("1 Input  (/input)", [".xlsx / .csv upload or a", "synthetic generator;", "read errors keep old data"], "core"),
            ("2 Review  (/review)", ["pre-flight findings (TQs),", "column mapping (read-only)"], "core"),
            ("3 Allocate  (/allocate)", ["edit rule parameters, load or", "save rule JSON, press Allocate"], "core")]
    for x, (t, ls, k) in zip(cols, row1):
        node(s, x, 70, bw, bh, t, ls, k, tsize=14, lsize=12)
    for i in range(3):
        arrow(s, [(cols[i] + bw + 1, 126), (cols[i + 1] - 1, 126)])
    arrow(s, [(cols[3] + bw / 2, 70 + bh + 1), (cols[3] + bw / 2, 248)])
    row2 = [("7 Deliverables  (/deliverables)", ["download Rev A / Rev B workbooks", "and the rule set (disabled when", "results are out of date)"], "file"),
            ("6 Revise  (/revise)", ["choose Rev B, compare and re-allocate;", "moved / added / deleted / modified;", "solver status; Rev B workbook"], "core"),
            ("5 Cabinets  (/cabinets)", ["slot map per cabinet, search,", "type filter, slot detail"], "core"),
            ("4 Results  (/results)", ["verifier banner, tiles, rule check,", "TQ list, cabinet summary"], "chk")]
    for x, (t, ls, k) in zip(cols, row2):
        node(s, x, 250, bw, bh, t, ls, k, tsize=14, lsize=12)
    for i in (3, 2, 1):
        arrow(s, [(cols[i] - 1, 306), (cols[i - 1] + bw + 1, 306)])
    s.text(cols[2] + bw + 20, 296, "next", 10.5, "#333", "middle")
    s.text(cols[1] + bw + 20, 296, "next", 10.5, "#333", "middle")
    s.text(cols[0] + bw + 20, 296, "next", 10.5, "#333", "middle")
    node(s, 322, 372, 560, 76, "Out-of-date handling", ["Changing a rule or the data after a run marks results 'out of date' on every", "result page and disables downloads until Allocate is run again."], "chk", tsize=13, lsize=11.5)
    node(s, 902, 372, 286, 76, "Start over (rail, confirmed)", ["clears data and results,", "keeps the rule settings"], "surf", tsize=13, lsize=11.5)
    s.text(20, 464, "Stages 2-7 stay disabled until their prerequisite exists (data for 2-3, an allocation for 4-7); the rail allows any enabled stage, and Results has buttons to 5, 6 and 7. A browser refresh starts a new session.", 11, "#555")
    s.save("figH_user_journey")


def fig_a():
    W, H = 1100, 600
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure A. Physical context: where the allocation problem sits (conceptual, not an official vendor drawing)", 16, anchor="middle", weight="bold")
    s.text(W / 2, 48, "Capacities from the DeltaV Electronic Marshalling data sheet (12 CHARMs per baseplate, 8 baseplates = 96 channels per CIOC); 4 CIOCs per cabinet is a rule of the problem statement.", 11, "#555", "middle")
    node(s, 30, 80, 250, 80, "Field instruments", ["transmitters, switches,", "solenoid valves, control valves"], "rule", tsize=14)
    node(s, 30, 215, 250, 90, "Multi-pair home-run cable", ["24, 12, 6 or 2 pairs", "1 pair = 1 signal = 1 CHARM"], "rule", tsize=14)
    arrow(s, [(155, 161), (155, 214)], label="wired in the field", lpos=(235, 192), lsize=10.5)
    arrow(s, [(155, 306), (155, 360), (330, 360)], label="landed in pair order", lpos=(150, 342), lsize=10.5)
    s.text(30, 340, "", 1)
    # cabinet nest
    s.rect(330, 80, 740, 400, "#f7f9fb", "#4a6a85", 1.6, 10)
    s.text(350, 106, "Marshalling cabinet  (up to 4 CIOCs: problem-statement rule)", 13.5, "#10202c", weight="bold")
    s.rect(350, 125, 700, 335, "#eef3f7", "#4a6a85", 1.4, 8)
    s.text(370, 150, "CIOC = CHARM I/O Card  (8 baseplates, 96 channels)", 13, "#10202c", weight="bold")
    s.rect(370, 168, 660, 120, "#ffffff", "#4a6a85", 1.2, 6)
    s.text(386, 192, "Baseplate  (12 slots)", 12.5, "#10202c", weight="bold")
    for i in range(12):
        s.rect(386 + i * 50, 205, 44, 56, "#e8f4ea", "#2f7d4a", 1.3, 4)
        s.text(386 + i * 50 + 22, 230, "CHARM", 8.5, "#0f2a18", "middle")
        s.text(386 + i * 50 + 22, 245, f"slot {i + 1}", 8.5, "#0f2a18", "middle")
    s.text(386, 280, "each slot = terminal block + CHARM; type and block depend on the signal type (AI, AO, DI, DO ...)", 11, "#444")
    s.rect(370, 300, 660, 40, "#f1f1f1", "#bbb", 1, 6)
    s.text(700, 325, "... baseplates 2 to 8 of this CIOC", 11.5, "#777", "middle")
    s.rect(370, 352, 660, 40, "#f1f1f1", "#bbb", 1, 6)
    s.text(700, 377, "... other CIOCs of this cabinet (up to 4)", 11.5, "#777", "middle")
    s.rect(370, 404, 660, 44, "#fff4d6", "#b07a00", 1.4, 6)
    s.text(700, 423, "THE ALLOCATION PROBLEM: which cable lands on which baseplate,", 12, "#3a2900", "middle", "bold")
    s.text(700, 439, "CIOC and cabinet, under grouping, A/B, spare and hardware rules", 12, "#3a2900", "middle", "bold")
    node(s, 330, 510, 740, 70, "Controllers", ["electronic marshalling: after installation, each channel is assigned to a controller in software (late binding)"], "rule", tsize=14, lsize=11.5)
    arrow(s, [(700, 481), (700, 509)])
    s.save("figA_physical_context")


def fig_g():
    W, H = 1180, 500
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure G. Technology stack (versions from requirements.lock.txt and the environment used for the tests)", 16, anchor="middle", weight="bold")
    cols = [("Core runtime (pyproject.toml)", "core", [("Python 3.11+", "3.12.13 used"), ("pandas 3.0.6", "tables; Excel and CSV reading"), ("openpyxl 3.1.5", "workbook writing and reading"),
                                                              ("pydantic 2.14.0", "typed rule set, JSON load/save"), ("OR-Tools 9.15 (CP-SAT)", "revision repair only")]),
            ("Optional UI extra", "surf", [("Streamlit 1.65.0", "workbench and landing page")]),
            ("Development and evidence", "chk", [("pytest 9.1.1", "122 tests"), ("Hypothesis 6.168.5", "property-based tests"), ("python-pptx, PyMuPDF", "pitch-deck build only; not the engine")]),
            ("Planned, not implemented", "plan", [("LLM suggestion helper", "mapping and rule drafts"), ("Docker demo bundle", ""), ("Official-template exporter", "template not released")])]
    cw, gap = 275, 20
    for i, (title, kind, items) in enumerate(cols):
        x = 20 + i * (cw + gap)
        fill, stroke, tc = STYLE[kind]
        s.rect(x, 60, cw, 408, "#fafafa", stroke, 1.5, 10)
        s.text(x + cw / 2, 86, title, 13, tc, "middle", "bold")
        for j, (a, b) in enumerate(items):
            node(s, x + 14, 104 + j * 76, cw - 28, 64, a, [b] if b else [], kind, dash=(kind == "plan"), tsize=13.5, lsize=11.5)
    s.text(W / 2, 490, "Where used: pandas in ingest/validate/export/verifier; openpyxl in export.py; pydantic in rules.py; OR-Tools only in repair_cpsat.py; Streamlit only under app/.", 11, "#555", "middle")
    s.save("figG_technology_stack")


def fig_j():
    W, H = 1240, 760
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure J. Source-code map (layers, not every import)", 17, anchor="middle", weight="bold")
    s.text(W / 2, 48, "Each layer calls the layer below it. The engine (src/slotsmith) imports nothing from app/ or tests/.", 11.5, "#555", "middle")

    def row(y, label, items, h=78):
        s.text(20, y - 8, label, 12.5, "#333", weight="bold")
        n = len(items)
        w = (W - 40 - (n - 1) * 14) / n
        for i, (t, ls, k) in enumerate(items):
            node(s, 20 + i * (w + 14), y, w, h, t, ls, k, tsize=13, lsize=11)

    row(88, "Surfaces", [("cli.py", ["generate, allocate, verify,", "revise, rules"], "surf"),
                         ("app/streamlit_app.py, app/views/", ["router and the 8 pages:", "landing, input, review, allocate,", "results, cabinets, revise, deliverables"], "surf"),
                         ("app/core/session.py, state.py", ["load_*, run_allocation, run_revision,", "reset, fingerprints, staleness,", "safe_read_mdb, preflight audit"], "surf"),
                         ("app/ui/, core/cabinet.py, demo.py", ["theme, components, shell,", "slot map, landing flow figure"], "surf")])
    s.text(W / 2 + 24, 186, "calls", 10.5, "#555", "middle"); arrow(s, [(W / 2, 168), (W / 2, 198)], "#777", w=1.6)
    row(222, "Orchestration", [("pipeline.py", ["run: validate, allocate, export, verify", "capacity_tqs"], "core"),
                               ("revision.py", ["revise: pin, greedy fill, impact_report"], "core"),
                               ("generator.py", ["generate, make_revision (synthetic data)"], "core")], h=66)
    arrow(s, [(W / 2, 290), (W / 2, 320)], "#777", w=1.6)
    row(344, "Engine components", [("ingest.py", ["read_mdb, auto_map"], "core"), ("validate.py", ["validate"], "core"),
                                    ("allocator.py", ["ffd_pack, build_units,", "Placer, allocate,", "exact_group_baseplates"], "core"),
                                    ("export.py", ["build_rows, summary,", "write_workbook"], "core"), ("repair_cpsat.py", ["repair_window", "(OR-Tools CP-SAT)"], "core"),
                                    ("verifier.py", ["CHECKS, load_allocation,", "verify"], "chk")], h=84)
    arrow(s, [(W / 2, 430), (W / 2, 460)], "#777", w=1.6)
    row(484, "Foundation", [("model.py", ["Signal, CableBlock, TQ, Placement"], "rule"), ("rules.py", ["RuleSet, HardwareRule, default_ruleset"], "rule")], h=60)
    row(612, "Evidence (imports the engine; UI tests also import app/)", [("tests/test_core.py,", ["test_audit_regressions.py", "31 engine tests"], "chk"), ("tests/test_ui_*.py", ["+ _page_harness.py", "91 UI tests"], "chk"),
                                                                     ("scripts/", ["benchmark.py, audit_*.py:", "measurements, exact-solver checks"], "chk"), ("artifacts/", ["recorded outputs"], "file")], h=78)
    s.text(W / 2, 724, "verifier.py imports only rules.py. revision.py imports allocator, export, validate and verifier, and loads repair_cpsat.py lazily.", 11, "#555", "middle")
    s.text(W / 2, 742, "Line counts: src/slotsmith 2,232; app/ 2,536 (including UI styling); tests 1,652.", 11, "#555", "middle")
    s.save("figJ_source_map")


def fig_e():
    W, H = 1190, 520
    s = Svg(W, H)
    s.text(W / 2, 28, "Figure E. Allocation engine and independent verifier as distinct components", 17, anchor="middle", weight="bold")
    s.text(W / 2, 48, "Only names and slot numbers in the exported workbook cross the boundary. verifier.py imports only rules.py.", 11.5, "#555", "middle")
    # left: allocation side
    s.rect(20, 70, 270, 250, "#f6fbf7", "#2f7d4a", 1.5, 10)
    s.text(36, 94, "Allocation side", 13, "#0f2a18", weight="bold")
    node(s, 40, 110, 230, 80, "allocator.py + export.py", ["placements are objects in memory;", "export turns them into rows and names"], "core", tsize=13, lsize=11)
    node(s, 40, 215, 230, 80, "pipeline.run()", ["writes the workbook, then calls", "the verifier on the file it just wrote"], "core", tsize=13, lsize=11)
    arrow(s, [(155, 191), (155, 214)], w=1.6)
    # workbook
    node(s, 330, 150, 190, 100, "Exported workbook", ["sheet 'IO Allocation':", "names and slot numbers only"], "file", tsize=13, lsize=11)
    arrow(s, [(271, 255), (310, 255), (310, 200), (329, 200)])
    # verifier
    s.rect(560, 70, 330, 330, "#fffaf0", "#b07a00", 1.5, 10)
    s.text(576, 94, "Verifier side (verifier.py)", 13, "#3a2900", weight="bold")
    node(s, 580, 110, 290, 80, "load_allocation + parse names", ["positions re-derived from the strings", "with regexes built from the naming patterns"], "chk", tsize=12.5, lsize=11)
    node(s, 580, 215, 290, 170, "11 check families", ["Q-1  every signal allocated or has a TQ", "D-2  one signal per slot    C-1  capacity", "K-1  cable whole, in pair order", "S-1  A and B apart    G-1  groups", "P-1  spare    H-1..6  CHARM and block", "N-1..6  names    C-2  controllers", "M-1  rows match the MDB"], "chk", tsize=12.5, lsize=10.5)
    arrow(s, [(725, 191), (725, 214)], "#b07a00", w=1.6)
    arrow(s, [(521, 200), (579, 150)], "#b07a00", w=1.8)
    # inputs to verifier
    node(s, 330, 300, 190, 60, "Original MDB rows", ["from ingest.py"], "file", tsize=12.5, lsize=11)
    node(s, 330, 380, 190, 60, "Rule set (rules.py)", ["parameters, hardware table, patterns"], "file", tsize=12.5, lsize=11)
    arrow(s, [(521, 330), (579, 330)], "#b07a00", w=1.6)
    arrow(s, [(521, 410), (545, 410), (545, 360), (579, 360)], "#b07a00", w=1.6)
    # outcomes
    node(s, 930, 110, 230, 80, "Rule Check report", ["PASS / FAIL, violation count,", "first five examples per family"], "chk", tsize=12.5, lsize=11)
    arrow(s, [(871, 300), (905, 300), (905, 150), (929, 150)], "#b07a00", w=1.6)
    node(s, 930, 235, 230, 90, "All 11 PASS", ["UI: 'Independent check: no violations'", "(this dataset, these rules);", "CLI exit code 0"], "core", tsize=12.5, lsize=10.5)
    node(s, 930, 350, 230, 90, "Any FAIL", ["UI: 'violations found' + families;", "CLI exit code 2;", "report is still written into the workbook"], "bad", tsize=12.5, lsize=10.5)
    arrow(s, [(1045, 191), (1045, 234)], w=1.6)
    arrow(s, [(1161, 150), (1172, 150), (1172, 395), (1161, 395)], w=1.6)
    s.text(W / 2, 480, "Shared with the allocator: the RuleSet values, the MDB as read by ingest.py, and the authors' reading of the rules. Not shared: allocator, export and validation code.", 11.5, "#555", "middle")
    s.text(W / 2, 500, "Not checked by any family: group sequence, minimal cabinet span, rules outside the 11 families.", 11.5, "#555", "middle")
    s.save("figE_verifier")


if __name__ == "__main__":
    fig_a()
    fig_e()
    fig_g()
    fig_j()
    fig_b()
    fig_d()
    fig_h()
    print("ok")
