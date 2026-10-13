"""Stage 7: Deliverables. design.md section E7."""
from __future__ import annotations

from html import escape
from pathlib import Path

import openpyxl
import streamlit as st

from app.ui import shell
from app.core.session import run_id
from app.core.state import unresolved_hardware, verification_status
from app.core.status import revision_status, run_status
from app.ui.components import banner, chip, kv, verification_chip
from app.views._common import empty_state, stale_banner

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _sheets(path: Path) -> list[tuple[str, int]]:
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return [(ws.title, max(0, (ws.max_row or 1) - 1)) for ws in wb.worksheets]
    finally:
        wb.close()


def _check_text(vs: dict) -> str:
    if vs["outcome"] == "missing":
        return "report missing"
    t = f"{vs['passed']} passed, {vs['failed']} failed, {vs['skipped']} skipped of {vs['total']}"
    return t + {"passed": " (all ran)", "incomplete": " (incomplete: rules switched off)", "failed": " (violations)"}[vs["outcome"]]


def _card(title: str, path: Path, name: str, key: str, ready: bool, why: str, facts: list[tuple[str, str]], rs) -> None:
    """A deliverable: file availability and verification outcome are separate facts, shown separately.

    Download gating is unchanged (only an out-of-date file is blocked); a file with failed or incomplete verification
    stays downloadable but is labelled as not engineering-verified."""
    size = Path(path).stat().st_size
    sheets = _sheets(Path(path))
    file_chip = chip("neutral", "File matches current run", "idle") if ready else chip("warn", "File out of date", "stale")
    sheet_chips = "".join(f"<li>{escape(n)} <b>{r:,}</b></li>" for n, r in sheets)
    st.html(f'<div class="ss-panel rise"><h4>{escape(title)}</h4><div class="ss-art">{file_chip}{verification_chip(rs)}</div>' +
            kv([("File", name), ("Size", f"{size / 1024:,.0f} KB")] + facts) +
            f'<p class="ss-h" style="margin:14px 0 4px">Sheets (rows)</p><ul class="ss-sheets">{sheet_chips}</ul></div>')
    st.download_button(f"Download {name}", data=Path(path).read_bytes(), file_name=name, mime=XLSX, disabled=not ready,
                       key=key, icon=":material/download:", type="primary" if key == "dl_a" and rs.accepted else "secondary")
    if not ready:
        st.caption(why)
    else:
        reasons = ([("verification failed" if rs.verification == "failed" else "verification incomplete")] if rs.verification != "passed" else []) \
            + ([f"{rs.unresolved_hw} signal(s) with unresolved hardware"] if rs.unresolved_hw else []) \
            + ([f"{rs.held - rs.unresolved_hw} other row(s) held or unplaced"] if rs.held - rs.unresolved_hw > 0 else [])
        if reasons:
            st.caption("Downloadable, but not a fully resolved, engineering-verified result: " + "; ".join(reasons) +
                       ". The Rule Check, TQ List and Run Info sheets in the file say so.")

def render() -> None:
    s = shell.begin("deliverables")
    shell.header("deliverables", "Deliverables",
                 "The files from this session, each tied to the run that produced it. A download means the file exists, not that its contents were verified: the verification outcome is shown beside every file.")
    if not s.has_allocation or not st.session_state.get("out"):
        return empty_state("Nothing to export yet", "Run an allocation first.", "Go to Allocate", "allocate")
    stale_banner(s, "deliverables")
    ss = st.session_state
    vs = verification_status(ss["res"])
    hw = unresolved_hardware(ss["res"])
    off = [t.id for t in ss["rules"].toggles if not t.enabled]
    rid = run_id(ss)
    n_tq = len(ss["res"].tqs)
    facts_a = [("Run", rid), ("Dataset", s.dataset_label or "—"), ("Rule set", ss["rules"].name),
               ("Independent check", _check_text(vs)), ("Disabled rules", ", ".join(off) if off else "none"),
               ("Unresolved hardware", f"{len(hw)} signal(s) held" if hw else "none"),
               ("Technical queries listed", f"{n_tq:,}")]
    if hw or vs["outcome"] != "passed":
        bits = ([f"{len(hw)} signal(s) have unresolved hardware and are not assigned a CHARM or terminal block"] if hw else []) + \
               ([f"{vs['skipped']} verification famil{'y was' if vs['skipped'] == 1 else 'ies were'} skipped because rules are switched off"]
                if vs["skipped"] else []) + ([f"violations in {', '.join(vs['failed_rules'])}"] if vs["failed"] else [])
        st.html(banner("warn" if not vs["failed"] else "bad", "This workbook is not a fully resolved, fully verified result",
                       "; ".join(bits) + ". The Rule Check, TQ List, Rule Set and Run Info sheets record this."))
    st.html(banner("info", "Layout note", "The workbook layout follows the problem statement's description. "
                   "The organiser's allocation template has not been released, so it may need re-mapping."))
    a, b = st.columns(2, gap="large")
    with a:
        _card("Rev A allocation workbook", ss["out"], "SlotSmith_allocation.xlsx", "dl_a", not s.alloc.is_stale,
              "Run Allocate again to export an up-to-date workbook.", facts_a, run_status(ss))
    with b:
        if ss.get("rev_out") and ss.get("rr") is not None:
            _card("Rev B allocation workbook", ss["rev_out"], "SlotSmith_allocation_RevB.xlsx", "dl_b",
                  not s.rev.is_stale, "Run the revision again to export an up-to-date workbook.",
                  [("Run", rid + " (Rev A) + Rev B"), ("Rule set", ss["rules"].name),
                   ("Disabled rules", ", ".join(off) if off else "none"), ("Technical queries listed", f"{len(ss['rr'].tqs):,}"), ("Revision source", (ss.get("revision_source") or {}).get("label", "—")),
                   ("Independent check", _check_text(verification_status(ss["rr"]))),
                   ("Unresolved hardware", f"{len(unresolved_hardware(ss['rr']))} signal(s) held" if unresolved_hardware(ss["rr"]) else "none"),
                   ("Moved / added / deleted", f"{ss['rr'].metrics['moved']} / {ss['rr'].metrics['added']} / {ss['rr'].metrics['deleted']}")],
                  revision_status(ss))
        else:
            st.html('<div class="ss-panel"><h4>Rev B allocation workbook</h4><p>Not created yet. Apply a Rev B on the Revise page to generate it, including the Revision Impact sheet.</p></div>')
            if st.button("Go to Revise", key="del_rev"):
                st.switch_page(shell.PAGES["revise"])
    st.write("")
    with st.container(border=True):
        st.markdown("#### Rule set")
        st.caption("The rules used for this session, as a reusable file.")
        st.download_button("Download rule set (JSON)", ss["rules"].model_dump_json(indent=2), "slotsmith_ruleset.json",
                           mime="application/json", key="dl_rules", icon=":material/download:")
