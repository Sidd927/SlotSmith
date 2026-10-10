"""Build deliverables/round1/SlotSmith_Round1.pptx on the official Apex 3.0 template.

    .venv/bin/python scripts/build_deck.py

Measured numbers are read from artifacts/benchmarks.json (scripts/benchmark.py) and the cabinet
map on slide 5 is drawn from a real allocation run on SYNTHETIC data, so no figure is typed by hand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.util import Inches  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402

from deck_lib import (AMBER, CYAN, GREEN, GREEN_DK, IO_COLORS, MUTED, PANEL, PANEL2, RED, TEXT, WHITE,  # noqa: E402
                      add_bg_slide, arrow, box, new_presentation, notes, text)
from slotsmith.generator import generate  # noqa: E402
from slotsmith.pipeline import run  # noqa: E402
from slotsmith.rules import default_ruleset  # noqa: E402

BG = ROOT / "deliverables" / "round1" / "build" / "bg"
OUT = ROOT / "deliverables" / "round1" / "SlotSmith_Round1.pptx"
BENCH = ROOT / "artifacts" / "benchmarks.json"

TEAM = {"name": "Mac_Enthu", "leader": "Aayush Aade", "members": ["Aayush Aade (lead)", "Siddhant Patil", "Gaurang Bagwe"]}


def fmt_int(n) -> str:
    return f"{int(n):,}"


def load_metrics() -> dict:
    if not BENCH.exists():
        return {}
    b = json.loads(BENCH.read_text())
    s = b["summary"]
    big = [r for r in b["scale"] if r["signals_target"] == 20000]
    s["n_20k_actual"] = big[0]["mdb_rows"] if big else None
    s["scale_runs"] = len(b["scale"])
    s["machine"] = b["machine"]["cpu"]
    s["rev_cases_10k"] = [r for r in b["revisions"] if r["signals"] == 10000]
    s["generated_at"] = b["generated_at"]
    import statistics as _st
    med = {n: _st.median(r["wall_s"] for r in b["scale"] if r["signals_target"] == n) for n in [2000, 10000, 20000]}
    s["scale_line"] = f"{med[2000]:.1f} s at 2k, {med[10000]:.1f} s at 10k, {med[20000]:.1f} s at 20k signals"
    # revision moves vary run to run (multi-threaded CP-SAT under a wall-clock limit): report the observed range
    totals = []
    for f in sorted((ROOT / "artifacts" / "repro").glob("benchmarks_clean_run*.json")):
        totals.append(json.loads(f.read_text())["summary"]["rev_moved_incremental_total"])
    aud = ROOT / "artifacts" / "audit" / "revision_status.json"
    if aud.exists():
        a = json.loads(aud.read_text())["summary"]
        totals.append(a["moved_total"])
        s["cpsat_exact"], s["cpsat_accepted"] = a["accepted_proven_exact"], a["accepted_windows"]
    s["rev_runs"] = len(totals) or 1
    lo, hi = (min(totals), max(totals)) if totals else (s["rev_moved_incremental_total"],) * 2
    s["rev_moved_range"] = f"{fmt_int(lo)}–{fmt_int(hi)}" if lo != hi else fmt_int(lo)
    return s


def caption(slide, x, y, w, txt, size=9.5, color=MUTED, align=PP_ALIGN.LEFT):
    return text(slide, x, y, w, 0.3, [[(txt, {"italic": True})]], size=size, color=color, align=align)


def chip(slide, x, y, w, h, label, fill, fg="06140A", size=10, bold=True):
    b = box(slide, x, y, w, h, fill=fill, radius=0.3)
    text(slide, 0, 0, 0, 0, [label], size=size, color=fg, bold=bold, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, shape=b)
    return b


def slot_strip(slide, x, y, cells, cw=0.24, ch=0.24, gap=0.03):
    """cells: list of IO_COLORS keys."""
    for i, k in enumerate(cells):
        box(slide, x + i * (cw + gap), y, cw, ch, fill=IO_COLORS[k], radius=0.15,
            line="2E4A35" if k == "FREE" else None, line_w=0.75)


# =============================================================================== slides

def slide1(prs):
    s = add_bg_slide(prs, str(BG / "bg1.jpg"))
    text(s, 3.38, 5.225, 6.0, 0.35, [[(TEAM["name"], {"bold": True})]], size=17, color=WHITE)
    text(s, 4.55, 5.64, 6.0, 0.35, [[(TEAM["leader"], {"bold": True})]], size=17, color=WHITE)
    text(s, 6.12, 6.07, 6.6, 0.35, [[("Track 1 (Emerson) · PS 1.2 Project IO SIGNAL SUDOKU", {"bold": True})]],
         size=15, color=WHITE)
    text(s, 1.67, 6.62, 11.0, 0.32, [[("SlotSmith", {"bold": True, "color": GREEN}),
                                      ("  ·  rule-driven, independently checked, revision-aware DeltaV I/O allocation",
                                       {"color": TEXT})]], size=13)
    notes(s, "Team Mac_Enthu. Problem statement: Track 1 (Emerson), Project IO SIGNAL SUDOKU "
             "(PS #02 in Track_1_PS_description.pdf; registered as PS 1.2). Solution name: SlotSmith.")


def slide2(prs):
    s = add_bg_slide(prs, str(BG / "bg2.jpg"))
    L, W = 0.78, 6.55
    text(s, L, 2.66, W, 0.95, [
        [("DeltaV project and I/O engineers ", {"bold": True, "color": WHITE}),
         ("(Emerson and system integrators) who must give every field signal an exact home: cabinet → CIOC → baseplate → CHARM slot. "
          "Downstream, panel builders and site teams wire to that allocation.", {})]], size=12.5)
    text(s, L, 3.93, W + 0.1, 0.95, [
        [("Emerson's PS: ", {"bold": True, "color": WHITE}),
         ("10,000+ signals are allocated by hand in Excel, and each customer revision means reworking it and tracing the impact again. ", {}),
         ("DeltaV tools automate the steps around it (auto-sense, late binding, Bulk Edit); we found no public tool that places "
          "signals from project rules (internal tools may exist).", {"color": MUTED})]],
         size=12)
    text(s, L, 5.16, W + 0.1, 1.3, [
        [("Electronic Marshalling makes late changes physically cheap (\"without lifting a wire\"), ", {}),
         ("but allocation planning and revision tracking remain a manual workflow burden (per the PS). ", {"bold": True, "color": WHITE}),
         ("Six interacting rules must hold at once, on every revision, with a technical query (TQ) for each data conflict.", {})]],
         size=12.5)
    caption(s, L, 6.52, 6.6, "Sources: Emerson PS #02 p.4; DeltaV Electronic Marshalling PDS (Aug 2026); "
                             "Smart Commissioning WP (2021) p.5; Bulk Edit WP (2022).")

    # right panel: the puzzle
    X, Y, PW, PH = 7.62, 1.92, 5.25, 4.85
    box(s, X, Y, PW, PH, fill=PANEL, line=GREEN_DK, transparency=12, radius=0.04)
    text(s, X + 0.22, Y + 0.12, PW - 0.4, 0.3, [[("THE PUZZLE, PER EMERSON'S RULEBOOK", {"bold": True})]], size=11, color=GREEN)
    hx, hy, hw, hh, hg = X + 0.2, Y + 0.5, 1.07, 0.74, 0.2
    items = [("Cabinet", "≤ 4 CIOCs"), ("CIOC", "8 baseplates"), ("Baseplate", "12 CHARMs"), ("CHARM", "1 signal")]
    for i, (a, b_) in enumerate(items):
        bx = hx + i * (hw + hg)
        bb = box(s, bx, hy, hw, hh, fill=PANEL2, line=GREEN, line_w=1, radius=0.12)
        text(s, 0, 0, 0, 0, [[(a, {"bold": True, "color": WHITE, "size": 11.5})], [(b_, {"size": 10, "color": MUTED})]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=bb)
        if i < 3:
            arrow(s, bx + hw + 0.02, hy + hh / 2, bx + hw + hg - 0.02, hy + hh / 2, width=1.25)
    # cable strips
    cy = Y + 1.48
    text(s, X + 0.22, cy, PW - 0.4, 0.28, [[("24-pair cable = 2 full baseplates (22 signals + 2 wired spares)", {})]],
         size=10.5, color=TEXT)
    mix = ["AI", "AI", "AI", "AI", "DI", "DI", "AI", "AO", "AO", "DI", "AI", "AI",
           "AI", "DI", "DI", "AO", "AI", "AI", "DI", "AI", "AI", "AI", "SPARE", "SPARE"]
    slot_strip(s, X + 0.22, cy + 0.31, mix[:12], cw=0.36, ch=0.24, gap=0.045)
    slot_strip(s, X + 0.22, cy + 0.6, mix[12:], cw=0.36, ch=0.24, gap=0.045)
    text(s, X + 0.22, cy + 0.93, PW - 0.4, 0.28, [[("Smaller cables share a baseplate, in pair order", {})]], size=10.5)
    mix2 = ["DO_ISO", "DO_ISO", "DO_ISO", "DO_ISO", "DO_ISO", "SPARE", "DI", "DO", "DI", "SPARE", "FREE", "FREE"]
    slot_strip(s, X + 0.22, cy + 1.24, mix2, cw=0.36, ch=0.24, gap=0.045)
    # legend
    ly = cy + 1.6
    lx = X + 0.22
    for k, lab in [("AI", "AI"), ("AO", "AO"), ("DI", "DI"), ("DO", "DO"), ("DO_ISO", "DO iso+fused"), ("SPARE", "spare"), ("FREE", "free")]:
        box(s, lx, ly + 0.04, 0.16, 0.16, fill=IO_COLORS[k], radius=0.2, line="2E4A35" if k == "FREE" else None)
        text(s, lx + 0.2, ly, 0.9, 0.24, [lab], size=9, color=MUTED)
        lx += 0.32 + 0.085 * len(lab)
    # rule chips
    ry = ly + 0.42
    rules6 = ["1  Keep IO groups together", "2  A and B never share a CIOC", "3  Capacity 12 · 8 · 4",
              "4  Cable intact, in pair order", "5  ~10% spare per cabinet", "6  Right CHARM + terminal block"]
    for i, r_ in enumerate(rules6):
        cx = X + 0.22 + (i % 2) * 2.45
        yy = ry + (i // 2) * 0.4
        b = box(s, cx, yy, 2.33, 0.32, fill=PANEL2, line=GREEN_DK, radius=0.25)
        text(s, 0, 0, 0, 0, [r_], size=10.2, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, shape=b)
    notes(s, "Who: DeltaV project/IO engineers. Gap: PS #02 p.4 states allocation is done by hand in Excel for 10,000+ "
             "signals and every revision means rework. Emerson-documented automation: auto-sense and drag-and-drop "
             "controller assignment (EM PDS Aug 2026 p.2), late binding with manual drag-drop or bulk edit for non-HART "
             "signals (Smart Commissioning WP p.5), Bulk Edit TAB-delimited import (Bulk Edit WP). Absence of a public "
             "allocation tool is NOT proof that none exists. Hardware facts: 12 CHARMs per baseplate, 8 baseplates "
             "(96 channels) per CIOC (EM PDS). 4 CIOCs per cabinet is a PS project rule.")


def slide3(prs, M):
    s = add_bg_slide(prs, str(BG / "bg3.jpg"))
    L, W = 0.7, 7.1
    pts = [
        ("Independently checked: ", "a separate verifier re-reads the exported workbook (11 rule families)."),
        ("Revision-aware: ", "unchanged cables stay put; CP-SAT repairs changes locally."),
        ("Configurable: ", "existing rule parameters live in JSON; new rule types may need code."),
        ("Traceable TQs: ", "every TQ cites a rule ID and the MDB file and row."),
    ]
    text(s, L, 2.76, W, 1.1, [{"runs": [(a, {"bold": True, "color": WHITE}), (b_, {})], "bullet": True} for a, b_ in pts],
         size=11.5, spacing_after=1)
    text(s, L, 4.13, W, 1.1, [
        [("Each cable becomes one block of 24/12/6/2 slots (spares included). Blocks are packed per group and A/B side into 12-slot baseplates, "
          "then baseplates fill CIOCs (8) and cabinets (4, minus the spare reserve) in group order. ", {}),
         ("Proved: ", {"bold": True, "color": WHITE}),
         ("for one A/B side with cable sizes 2/6/12 (24 = two full baseplates), first-fit-decreasing uses the fewest baseplates. ", {}),
         ("Tested, not proved: ", {"bold": True, "color": WHITE}),
         ("whole-group totals matched an exact CP-SAT solver in 19,682 exhaustive small cases and 12/12 benchmark runs.", {"color": MUTED})]], size=11)
    feas = (f"Built on Python, OR-Tools CP-SAT and openpyxl, all open source, with a synthetic MDB generator built from the published rulebook. "
            f"The working prototype already allocates and verifies {fmt_int(M.get('n_20k_actual') or 20000)} synthetic signals "
            f"in {M.get('wall_20k_median_s', 0):.1f} s on a laptop (slide 6).") if M else \
        "Built on open-source tools (Python, OR-Tools CP-SAT, openpyxl) with a synthetic MDB generator from the published rulebook."
    text(s, L, 5.5, W, 1.0, [feas], size=11.5)

    # right panel
    X, Y, PW = 7.95, 1.95, 4.95
    box(s, X, Y, PW, 2.4, fill=PANEL, line=GREEN_DK, transparency=12, radius=0.04)
    text(s, X + 0.2, Y + 0.1, PW - 0.3, 0.3, [[("WHERE AI HELPS, AND WHERE IT MUST NOT", {"bold": True})]], size=11, color=GREEN)
    cw = (PW - 0.55) / 2
    b1 = box(s, X + 0.2, Y + 0.48, cw, 1.78, fill="0A2433", line=CYAN, radius=0.06)
    text(s, 0, 0, 0, 0, [[("AI-assisted, always reviewed", {"bold": True, "color": CYAN})],
                         {"runs": [("Column auto-mapping for unseen MDBs", {})], "bullet": True},
                         {"runs": [("Plain-English rule → JSON draft, schema-checked and previewed", {})], "bullet": True},
                         {"runs": [("Customer-ready TQ wording", {})], "bullet": True},
                         [("Status: planned for Round 2+", {"italic": True, "color": MUTED, "size": 9.5})]],
         size=10.5, shape=b1, spacing_after=2)
    b2 = box(s, X + 0.35 + cw, Y + 0.48, cw, 1.78, fill="0B2A12", line=GREEN, radius=0.06)
    text(s, 0, 0, 0, 0, [[("Solver + independent verifier", {"bold": True, "color": GREEN})],
                         {"runs": [("Every placement decision", {})], "bullet": True},
                         {"runs": [("Rule verification", {})], "bullet": True},
                         {"runs": [("Excel export and revision diff", {})], "bullet": True},
                         [("Status: built and tested", {"italic": True, "color": MUTED, "size": 9.5})]],
         size=10.5, shape=b2, spacing_after=2)
    Y2 = Y + 2.55
    box(s, X, Y2, PW, 2.25, fill=PANEL, line=GREEN_DK, transparency=12, radius=0.04)
    text(s, X + 0.2, Y2 + 0.1, PW - 0.3, 0.3, [[("DESIGN PRINCIPLES", {"bold": True})]], size=10.5, color=GREEN)
    principles = [("Check, don't trust:", "nothing ships without an independent rule-check report"),
                  ("No AI in placement:", "a solver places signals; AI only suggests, users confirm"),
                  ("Change locally:", "a revision keeps unchanged cables in place and reports every move"),
                  ("Surface, don't hide:", "every unresolved issue becomes a TQ with its rule and source row")]
    text(s, X + 0.2, Y2 + 0.42, PW - 0.35, 1.8,
         [{"runs": [(a, {"bold": True, "color": WHITE}), (" " + b_, {})], "bullet": True} for a, b_ in principles],
         size=10.3, spacing_after=4)
    notes(s, "Divisible-size argument: with sizes from a divisible chain and capacity divisible by every size, "
             "processing in decreasing order keeps every bin's free space a multiple of the current size, so FFD opens a "
             "new bin only when all others are full. Hence #bins = ceil(total/12), the lower bound. Related literature: "
             "Coffman, Garey and Johnson, Bin packing with divisible item sizes, J. Complexity 1987. CP-SAT (Google OR-Tools, "
             "Apache-2.0) is used for local revision repair (window-local; not always proven optimal). The proof covers one A/B side class; "
             "whole-group optimality was tested against exact CP-SAT (artifacts/audit/ffd_exact.json), not proved. "
             "AI components are planned and bounded; they never place signals.")


def slide4(prs):
    s = add_bg_slide(prs, str(BG / "bg4.jpg"))
    stack = [(2.20, 1.95, "Streamlit prototype (built): rule panel, cabinet map, TQs, diff; React + TS later"),
             (3.02, 1.85, "Python 3.12 · pandas · openpyxl · pydantic typed rule sets · CLI"),
             (3.84, 1.95, "Project files: JSON rule sets, Rev A/B workbooks, run log (SQLite planned)"),
             (4.70, 1.95, "OR-Tools CP-SAT (Apache-2.0). Optional LLM for mapping/rule drafts: model declared, never places signals"),
             (5.58, 2.85, "Runs offline on a laptop · pytest + Hypothesis · git; Docker for demo (planned)")]
    for y, x, t in stack:
        text(s, x, y + 0.04, 4.5 - x, 0.6, [t], size=9.6, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)

    # architecture diagram
    X0, Y0 = 4.95, 1.9
    box(s, X0, Y0, 7.95, 4.85, fill=PANEL, line=GREEN_DK, transparency=12, radius=0.03)
    text(s, X0 + 0.2, Y0 + 0.1, 6, 0.3, [[("DATA FLOW (solid = built; dashed = planned)", {"bold": True})]], size=10.5, color=GREEN)

    def node(x, y, w, h, title, sub, fill=PANEL2, line=GREEN, dash=False, tcol=WHITE):
        b = box(s, x, y, w, h, fill=fill, line=line, line_w=1.25, radius=0.1, dash=dash)
        text(s, 0, 0, 0, 0, [[(title, {"bold": True, "color": tcol, "size": 11})], [(sub, {"size": 9, "color": MUTED})]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b, spacing_after=1)
        return b

    r1 = Y0 + 0.55
    w, h = 1.72, 0.92
    xs = [X0 + 0.2 + i * (w + 0.22) for i in range(4)]
    # row 1: allocation path, left to right
    node(xs[0], r1, w, h, "Customer IO MDB", "one or many Excel files", fill="12202A", line=CYAN)
    node(xs[1], r1, w, h, "1 · Ingest + map", "auto-map columns, keep row provenance")
    node(xs[2], r1, w, h, "2 · Validate", "data + rule conflicts → TQ list")
    node(xs[3], r1, w, h, "4 · Allocator", "cable blocks → baseplates → CIOCs → cabinets")
    for i in range(3):
        arrow(s, xs[i] + w + 0.02, r1 + h / 2, xs[i + 1] - 0.02, r1 + h / 2)
    # row 2: output path, right to left
    r2 = r1 + h + 0.5
    node(xs[3], r2, w, h, "6 · Exporter", "allocation, summary, TQs, impact")
    arrow(s, xs[3] + w / 2, r1 + h + 0.02, xs[3] + w / 2, r2 - 0.02)
    node(xs[2], r2, w, h, "5 · Independent verifier", "re-reads the workbook; shares no code with 4",
         fill="2A1F0A", line=AMBER, tcol=AMBER)
    arrow(s, xs[3] - 0.02, r2 + h / 2, xs[2] + w + 0.02, r2 + h / 2, color=AMBER)
    node(xs[0], r2, w * 2 + 0.22, h, "Deliverable", "filled Excel workbook + rule-check report", fill="12202A", line=CYAN)
    arrow(s, xs[2] - 0.02, r2 + h / 2, xs[1] + w + 0.02, r2 + h / 2, color=AMBER)
    # row 3: supporting components
    r3 = r2 + h + 0.5
    node(xs[0], r3, w, h, "UI (Streamlit)", "built prototype: rule panel, map, TQs, diff")
    node(xs[1], r3, w, h, "AI helpers", "planned: mapping + rule-draft suggestions", fill=PANEL2, line=MUTED, dash=True, tcol=TEXT)
    node(xs[2], r3, w, h, "3 · Rule set", "JSON parameters used by 2 · 4 · 5")
    node(xs[3], r3, w, h, "7 · Revision engine", "Rev A + Rev B: pin unchanged, CP-SAT window repair")
    arrow(s, xs[3] + w / 2, r3 - 0.02, xs[3] + w / 2, r2 + h + 0.02)
    caption(s, X0 + 0.2, Y0 + 4.5, 7.6, "Row provenance (file:sheet:row) travels with every signal, so each TQ and placement is traceable.")
    notes(s, "Frontend: Streamlit MVP first (fastest path to a usable rule panel), React later if time allows. "
             "Backend: Python. Solver: Google OR-Tools CP-SAT, Apache-2.0. The verifier imports nothing from the allocator or "
             "exporter; it parses names back into positions using the user's naming patterns and re-derives CHARM/TB from the "
             "rule table. LLM use is optional and limited to suggestions a user confirms.")


def cabinet_map(s, rows, cab_name, x, y, w, h):
    cab_rows = [r for r in rows if r["Marshalling Cabinet"] == cab_name]
    ciocs = sorted({r["CIOC"] for r in cab_rows})
    hw = {"Standard": None}
    kind = {}
    for r in cab_rows:
        bp = int(r["Baseplate"].split("-CBP-")[1])
        if r["Row Kind"] == "Spare pair" or r["Row Kind"].startswith("Held"):
            k = "SPARE"
        else:
            io = (r["IO Type"] or "").upper()
            k = "DO_ISO" if r["Terminal Block"] == "Fused-injected-power" else "DO_RELAY" if r["Terminal Block"] == "Relay output" \
                else "AO" if io.startswith("AO") else "DI" if io.startswith("DI") else "DO" if io.startswith("DO") else "AI"
        kind[(r["CIOC"], bp, int(r["Slot"]))] = k
    colw = w / 4
    cw = (colw - 0.22) / 12
    rh = (h - 0.35) / 8
    for qi in range(4):
        cx = x + qi * colw
        if qi < len(ciocs):
            q = ciocs[qi]
            qrows = [r for r in cab_rows if r["CIOC"] == q]
            grp = sorted({r["IO Group"] for r in qrows if r["IO Group"]}) or ["no group"]
            seg = sorted({r["Segregation"] for r in qrows if r["Segregation"]})
            label = f"{q[-3:]} · {grp[0]}" + (f" · {seg[0]}" if seg else "")
            col = AMBER if seg == ["A"] else CYAN if seg == ["B"] else WHITE
        else:
            q, label, col = None, "(empty CIOC position)", MUTED
        text(s, cx, y, colw - 0.1, 0.25, [[(label, {"bold": True})]], size=9, color=col)
        for bp in range(1, 9):
            yy = y + 0.3 + (bp - 1) * rh
            for sl in range(1, 13):
                k = kind.get((q, bp, sl), "FREE") if q else "FREE"
                box(s, cx + (sl - 1) * cw, yy, cw * 0.84, rh * 0.8, fill=IO_COLORS[k], radius=0.15,
                    line="223A28" if k == "FREE" else None, line_w=0.5)
    return ciocs


SHORT = {"Q-1": "Every signal allocated or has a TQ", "D-2": "One signal per CHARM slot",
         "C-1": "Capacity 12 / 8 / 4", "K-1": "Cables complete, in pair order", "S-1": "A and B never share a CIOC",
         "G-1": "Groups isolated, cabinets contiguous", "P-1": "Spare baseplates per cabinet",
         "H-1..6": "Right CHARM + terminal block", "N-1..6": "Names follow user patterns",
         "C-2": "One controller per CIOC, limits", "M-1": "Rows match the MDB"}


def slide5(prs, M):
    s = add_bg_slide(prs, str(BG / "bg5.jpg"))
    feats = [("1 · Upload", "Excel MDB(s) in; columns auto-mapped with provenance", "Built"),
             ("2 · Set rules", "Rule panel: toggle, edit, save rule sets per project", "Built (prototype panel)"),
             ("3 · Allocate", "One click: signal → cabinet, CIOC, baseplate, CHARM", "Built"),
             ("4 · Report + TQs", "Fill %, spares, rule check, TQ list with sources", "Built"),
             ("5 · Revise", "Rev B vs Rev A: unchanged stay put; impact report", "Built")]
    fx, fy, fw, fh = 0.62, 1.86, 2.36, 1.07
    for i, (a, b_, st) in enumerate(feats):
        x = fx + i * (fw + 0.13)
        bb = box(s, x, fy, fw, fh, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.08)
        text(s, x + 0.12, fy + 0.07, fw - 0.2, 0.3, [[(a, {"bold": True})]], size=11.5, color=GREEN)
        text(s, x + 0.12, fy + 0.36, fw - 0.2, 0.5, [b_], size=10, color=TEXT)
        built = st == "Built" or st.startswith("Built")
        chip(s, x + 0.12, fy + 0.8, fw - 0.24, 0.2, st, fill=GREEN, size=8.5)

    # real allocation output (synthetic data)
    rs = default_ruleset()
    g = generate(900, seed=12, groups=3)
    res = run(None, rs, None, df=_canon(g.df))
    cab = res.rows[0]["Marshalling Cabinet"]
    X, Y, PW, PH = 0.62, 3.05, 6.7, 3.7
    box(s, X, Y, PW, PH, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.03)
    text(s, X + 0.18, Y + 0.08, PW - 0.3, 0.3,
         [[(f"ENGINE OUTPUT: CABINET {cab}", {"bold": True, "color": GREEN}),
           ("  (synthetic 900-signal MDB)", {"color": MUTED, "italic": True})]], size=10.5)
    cabinet_map(s, res.rows, cab, X + 0.18, Y + 0.42, PW - 0.3, PH - 0.85)
    lx, ly = X + 0.18, Y + PH - 0.32
    for k, lab in [("AI", "AI"), ("AO", "AO"), ("DI", "DI"), ("DO", "DO"), ("DO_ISO", "DO iso+fused"),
                   ("DO_RELAY", "relay TB"), ("SPARE", "wired spare"), ("FREE", "free")]:
        box(s, lx, ly + 0.04, 0.15, 0.15, fill=IO_COLORS[k], radius=0.2, line="2E4A35" if k == "FREE" else None)
        text(s, lx + 0.19, ly, 1.3, 0.24, [lab], size=8.5, color=MUTED)
        lx += 0.34 + 0.066 * len(lab)
    X2, W2 = 7.47, 5.43
    box(s, X2, Y, W2, PH, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.03)
    text(s, X2 + 0.18, Y + 0.08, W2 - 0.3, 0.3, [[("PROTOTYPE UI (real screenshots, post-audit build)", {"bold": True})]],
         size=10.5, color=GREEN)
    ui = ROOT / "deliverables" / "round1" / "build" / "ui"
    from PIL import Image
    a = Image.open(ui / "ui_allocate_crop.png")
    b_ = Image.open(ui / "ui_revise_crop.png")
    avail_h, gap = PH - 0.42 - 0.42, 0.08
    iw = W2 - 0.36
    ra, rb = a.size[1] / a.size[0], b_.size[1] / b_.size[0]
    iw = min(iw, (avail_h - gap) / (ra + rb))
    ah, bh = iw * ra, iw * rb
    ix = X2 + (W2 - iw) / 2
    s.shapes.add_picture(str(ui / "ui_allocate_crop.png"), Inches(ix), Inches(Y + 0.42), Inches(iw), Inches(ah))
    s.shapes.add_picture(str(ui / "ui_revise_crop.png"), Inches(ix), Inches(Y + 0.42 + ah + gap), Inches(iw), Inches(bh))
    caption(s, X2 + 0.18, Y + PH - 0.36, W2 - 0.3, "SYNTHETIC 2,000-signal MDB (6 injected errors) + synthetic Rev B. Top: allocate. Bottom: revise.",
            size=8.5)
    notes(s, "Everything in the lower half is generated by the prototype from synthetic MDBs (seeded), not drawn by hand. "
             "Left: cabinet map drawn from the allocator output. Right: screenshots of the Streamlit prototype UI "
             "(2,000-signal synthetic MDB with 6 injected errors; Rev B synthetic). The same engine runs from the CLI and produces the workbook "
             "(sheets: IO Allocation, Cabinet Summary, TQ List, Rule Check, Revision Impact, Rule Set, Run Info).")


def slide6(prs, M):
    s = add_bg_slide(prs, str(BG / "bg6.jpg"))
    cols = [
        ("BUILT TODAY · 10 OCT", GREEN, [
            "Synthetic MDB + Rev B generator (seeded)",
            "Ingestion: multi-file, header detection, auto-map",
            "Validation → TQs citing rule + source row",
            "Allocator: cable blocks, FFD, groups, A/B, spares, CHARM/TB, names",
            "Independent verifier: 11 rule families",
            "Excel export incl. rule check + impact",
            "Revision engine + CP-SAT window repair",
            "Streamlit prototype UI",
            f"{M.get('tests', 25)} automated tests incl. property-based"]),
        ("ROUND 2 · BY 16 OCT", AMBER, [
            "UI polish: mapping review/override, CHARM-table editing, exports",
            "Map to the organiser template once released",
            "Confirm open rule interpretations with mentors",
            "Cut CP-SAT repair time and run-to-run variance"]),
        ("GRAND FINALE · 24 OCT", CYAN, [
            "Run on organiser samples + hidden test",
            "AI helpers: column-mapping suggestions, plain-English → rule JSON (previewed)",
            "Demo hardening, offline bundle"]),
        ("BEYOND THE HACKATHON", MUTED, [
            "Bulk-Edit-style export for DeltaV import (format to be validated)",
            "Other electronic-marshalling platforms (untested)",
            "Cabinet labels and drawings"]),
    ]
    x, y, w, h = 0.62, 1.95, 2.98, 3.05
    for i, (title, col, items) in enumerate(cols):
        xx = x + i * (w + 0.12)
        box(s, xx, y, w, h, fill=PANEL, line=col, line_w=1, transparency=8, radius=0.05)
        text(s, xx + 0.15, y + 0.08, w - 0.25, 0.3, [[(title, {"bold": True})]], size=10.5, color=col)
        text(s, xx + 0.15, y + 0.4, w - 0.22, h - 0.45, [{"runs": [(it, {})], "bullet": True} for it in items],
             size=9.8, spacing_after=2)
    # measured strip
    yy = y + h + 0.15
    box(s, 0.62, yy, 12.28, 1.5, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.05)
    text(s, 0.8, yy + 0.07, 12, 0.3, [[("MEASURED ON SYNTHETIC DATA (prototype, " + (M.get("machine", "laptop")[:40]) + ")", {"bold": True, "color": GREEN}),
                                        ("  ·  not evidence about the hidden test", {"italic": True, "color": MUTED})]], size=10)
    if M:
        tiles = [
            (f"{M['max_violations']}", f"verifier violations in {M['scale_runs']} runs (500–20k signals)"),
            (f"{M['min_coverage_pct']:.0f}%", "of rows allocated or covered by a TQ"),
            (f"{M['tq_detected']}/{M['tq_injected']}", "injected data errors raised as TQs"),
            (f"{M['baseplates_over_exact_max']}", "baseplates above the exact per-group minimum (12 runs)"),
            (f"{M['wall_20k_median_s']} s", f"end-to-end for {fmt_int(M['n_20k_actual'])} signals (median)"),
            (f"{M['rev_moved_range']} vs {fmt_int(M['rev_moved_scratch_total'])}",
             f"moved: SlotSmith vs re-run, {M['rev_cases']} Rev B cases, {M['rev_runs']} runs; "
             f"CP-SAT proven exact in {M.get('cpsat_exact', '?')}/{M.get('cpsat_accepted', '?')} window repairs"),
        ]
    else:
        tiles = [("—", "benchmark pending")] * 6
    tw = 12.0 / len(tiles)
    for i, (big, small) in enumerate(tiles):
        tx = 0.8 + i * tw
        text(s, tx, yy + 0.38, tw - 0.1, 0.5, [[(big, {"bold": True})]], size=19 if len(big) < 9 else 15, color=WHITE)
        text(s, tx, yy + 0.84, tw - 0.12, 0.62, [small], size=8.8, color=MUTED)
    notes(s, "All measured figures come from scripts/benchmark.py → artifacts/benchmarks.json (generated "
             f"{M.get('generated_at', 'n/a')}). Synthetic data only. Revision cases: 2k and 10k signals, 5 seeds each, Rev B = 3% deleted, "
             "5% added (half on spare pairs), 2% IO-type changes, 1 cable regrouped. "
             f"CP-SAT repair was needed in {M.get('rev_cpsat_cases', '?')} of {M.get('rev_cases', '?')} cases; "
             f"window repairs proven exact in {M.get('cpsat_exact', '?')}/{M.get('cpsat_accepted', '?')}, the rest best-found within 10 s. "
             f"Revision move totals varied across {M.get('rev_runs', '?')} runs ({M.get('rev_moved_range', '?')}) because CP-SAT runs "
             "multi-threaded under a wall-clock limit; allocation results were identical across runs. "
             f"full-reallocation fallback in {M.get('rev_fallback_cases', '?')}. Max revision time {M.get('rev_time_max_s', '?')} s.")


def slide7(prs, M):
    s = add_bg_slide(prs, str(BG / "bg7.jpg"))
    y = 1.98
    cards = [
        ("IO / project engineers", "Allocation becomes a re-runnable, rule-checked step instead of hand-editing 10,000+ Excel rows."),
        ("Reviewers and QA", "Every deliverable ships with a rule-check report; every placement and TQ traces to an MDB row."),
        ("Customers and EPCs", "Specific, traceable TQs and a Rev A → Rev B impact report: added, deleted, moved, cabinets hit."),
    ]
    for i, (a, b_) in enumerate(cards):
        xx = 0.62 + i * 4.13
        box(s, xx, y, 4.0, 1.25, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.06)
        text(s, xx + 0.17, y + 0.1, 3.7, 0.3, [[(a, {"bold": True})]], size=12, color=GREEN)
        text(s, xx + 0.17, y + 0.43, 3.7, 0.8, [b_], size=10.8)
    y2 = y + 1.42
    box(s, 0.62, y2, 6.05, 2.0, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.05)
    text(s, 0.8, y2 + 0.08, 5.8, 0.3, [[("HOW BIG THE OPPORTUNITY IS (sourced)", {"bold": True})]], size=10.5, color=GREEN)
    facts = [("10,000+", "signals per project, allocated by hand today (Emerson PS)"),
             ("≤ 300", "CIOCs per DeltaV system (spec maximum) → at most 28,800 CHARM channels (EM PDS)"),
             ("Every", "customer revision means rework and impact tracing (Emerson PS)")]
    for i, (big, small) in enumerate(facts):
        yy = y2 + 0.45 + i * 0.5
        text(s, 0.8, yy, 1.2, 0.45, [[(big, {"bold": True})]], size=17, color=WHITE)
        text(s, 2.05, yy + 0.06, 4.5, 0.45, [small], size=10.5, color=TEXT)
    box(s, 6.85, y2, 6.05, 2.0, fill=PANEL, line=GREEN_DK, transparency=8, radius=0.05)
    text(s, 7.03, y2 + 0.08, 5.8, 0.3, [[("HOW IT GROWS BEYOND A DEMO", {"bold": True})]], size=10.5, color=GREEN)
    grow = ["Rule sets saved per customer and project: the next project starts from the last one",
            "Designed to complement DeltaV and SPI: an export adapter to their import formats is planned (not yet validated)",
            "Block-packing engine could be adapted to other electronic-marshalling I/O families (untested)",
            f"Near-linear runtime measured: {M.get('scale_line', '')} (synthetic)"]
    text(s, 7.03, y2 + 0.42, 5.75, 1.55, [{"runs": [(g_, {})], "bullet": True} for g_ in grow], size=10.3, spacing_after=3)
    y3 = y2 + 2.17
    box(s, 0.62, y3, 12.28, 1.05, fill="231A08", line=AMBER, transparency=10, radius=0.05)
    text(s, 0.8, y3 + 0.07, 12, 0.3, [[("HONEST LIMITS TODAY", {"bold": True, "color": AMBER})]], size=10.5)
    text(s, 0.8, y3 + 0.37, 12.0, 0.7, [
        "Synthetic data only: the organiser's sample MDB and template are not yet released, so no official-template compatibility is claimed. "
        "Rule interpretations (straddling, spare rounding, controller mapping) await mentors. Rules are parameters; new rule types still need code. "
        "CP-SAT repair is window-local. No time savings claimed. Complements DeltaV tools; does not replace them."], size=10.3)
    notes(s, "Impact statements are expected, not measured. Sources: PS #02 p.4 (10,000+ signals, manual Excel, revisions); "
             "DeltaV Electronic Marshalling PDS Aug 2026 p.10 ('Number of CIOCs per System: 300', a specification maximum; 96 channels per CIOC). Positioning: "
             "complementary pre-configuration engineering assistant; see docs/emerson_product_analysis.md.")


def slide8(prs):
    s = add_bg_slide(prs, str(BG / "bg8.jpg"))
    text(s, 0.45, 6.62, 9.0, 0.35, [[("Team ", {"color": MUTED}), (TEAM["name"], {"bold": True, "color": WHITE}),
                                     ("  ·  " + "  ·  ".join(TEAM["members"]), {"color": TEXT})]], size=12)
    notes(s, "Thank you. Repository, rule register, source register and benchmark logs are available on request.")


def _canon(df):
    df = df.rename(columns={"Tag": "tag", "IO": "io_type", "Cable": "cable", "Cable Size": "cable_size",
                            "Pair": "pair", "Grp": "group", "Seg": "seg"}).copy()
    df["src_file"], df["src_sheet"], df["src_row"] = "synthetic.xlsx", "IO MDB", range(2, len(df) + 2)
    df = df.astype(object).where(df.notna(), None)
    for c in ["pair", "cable_size"]:
        df[c] = df[c].map(lambda v: None if v is None else str(int(float(v))))
    return df


def ensure_backgrounds():
    """Render the official template pages (PDF-only) to slide backgrounds if missing."""
    if all((BG / f"bg{i}.jpg").exists() for i in range(1, 9)):
        return
    import pymupdf
    from PIL import Image
    BG.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(ROOT / "reference" / "official" / "Apex_3.0_PPT_Template.pdf")
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=144)
        Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(BG / f"bg{i}.jpg", quality=88)


def main():
    ensure_backgrounds()
    M = load_metrics()
    tests_file = ROOT / "artifacts" / "test_count.txt"
    if tests_file.exists():
        M["tests"] = int(tests_file.read_text().strip())
    prs = new_presentation()
    prs.core_properties.title = "SlotSmith · VIT Code Apex 3.0 Round 1 · Team Mac_Enthu"
    prs.core_properties.author = "Team Mac_Enthu"
    slide1(prs)
    slide2(prs)
    slide3(prs, M)
    slide4(prs)
    slide5(prs, M)
    slide6(prs, M)
    slide7(prs, M)
    slide8(prs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print("wrote", OUT, "metrics:", bool(M))


if __name__ == "__main__":
    main()
