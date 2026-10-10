"""SlotSmith minimal UI (prototype).

    .venv/bin/streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slotsmith.export import write_workbook  # noqa: E402
from slotsmith.generator import generate, make_revision  # noqa: E402
from slotsmith.ingest import read_mdb  # noqa: E402
from slotsmith.pipeline import run  # noqa: E402
from slotsmith.revision import revise  # noqa: E402
from slotsmith.rules import RuleSet, default_ruleset  # noqa: E402

st.set_page_config(page_title="SlotSmith", layout="wide")
COL = {"AI": "#4FA3FF", "AO": "#B98CFF", "DI": "#7BD88F", "DO": "#FFD54F", "DO_ISO": "#FF8A50",
       "DO_RELAY": "#FF6FA8", "SPARE": "#5B6B5F", "FREE": "#16241A"}

st.title("SlotSmith · DeltaV I/O allocation (prototype)")
st.caption("Rule-driven allocation · independent verifier · revision-aware re-allocation. Synthetic demo data is labelled as such.")

if "rules" not in st.session_state:
    st.session_state.rules = default_ruleset()
rules: RuleSet = st.session_state.rules

# ------------------------------------------------------------------ sidebar: rule panel
with st.sidebar:
    st.header("Rule panel")
    for t in rules.toggles:
        t.enabled = st.toggle(t.description, value=t.enabled, key=f"tg_{t.id}")
    rules.spare_percent = st.slider("Spare per cabinet (%)", 0.0, 40.0, float(rules.spare_percent), 1.0)
    st.caption(f"→ {rules.reserved_baseplates_per_cabinet} of {rules.baseplates_per_cabinet} baseplates kept empty per cabinet")
    rules.group_isolation_level = st.selectbox("Group isolation", ["cioc", "cabinet", "none"],
                                               index=["cioc", "cabinet", "none"].index(rules.group_isolation_level))
    rules.segregation_level = st.selectbox("A/B segregation scope", ["cioc", "cabinet"],
                                           index=["cioc", "cabinet"].index(rules.segregation_level))
    rules.naming.area = st.text_input("Area", rules.naming.area)
    rules.naming.unit = st.text_input("Unit", rules.naming.unit)
    with st.expander("CHARM / terminal-block table"):
        hw = pd.DataFrame([{"id": h.id, "io_types": ", ".join(h.io_types), "charm": h.charm, "terminal_block": h.terminal_block}
                           for h in rules.hardware])
        st.dataframe(hw, hide_index=True, use_container_width=True)
    st.download_button("Save rule set (JSON)", rules.model_dump_json(indent=2), "ruleset.json")
    up_rules = st.file_uploader("Load rule set", type=["json"], key="rules_up")
    if up_rules is not None:
        st.session_state.rules = RuleSet.model_validate(json.loads(up_rules.read()))
        st.rerun()

tab1, tab2, tab3 = st.tabs(["1 · Upload + allocate", "2 · Cabinet map", "3 · Revise (Rev B)"])


def _save_uploads(files) -> list[Path]:
    d = Path(tempfile.mkdtemp())
    out = []
    for f in files:
        p = d / f.name
        p.write_bytes(f.getbuffer())
        out.append(p)
    return out


with tab1:
    c1, c2 = st.columns([2, 1])
    files = c1.file_uploader("Customer IO MDB (one or many Excel/CSV files)", type=["xlsx", "xls", "csv"],
                             accept_multiple_files=True)
    n_demo = c2.number_input("…or generate a SYNTHETIC MDB (signals)", 100, 30000, 2000, 100)
    seed = c2.number_input("seed", 0, 9999, 7)
    errs = c2.number_input("injected data errors", 0, 50, 6)
    if c2.button("Generate synthetic MDB"):
        g = generate(int(n_demo), seed=int(seed), inject_errors=int(errs))
        p = Path(tempfile.mkdtemp()) / f"SYNTHETIC_MDB_{n_demo}_s{seed}.xlsx"
        g.df.to_excel(p, index=False)
        st.session_state.paths = [p]
        st.session_state.revb = make_revision(g.df, seed=int(seed) + 1)
    if files:
        st.session_state.paths = _save_uploads(files)
    paths = st.session_state.get("paths")
    if paths:
        mdb = read_mdb(paths)
        st.subheader("Column mapping (auto)")
        st.dataframe(pd.DataFrame([{"sheet": k, **v.mapping} for k, v in mdb.mapping.items()]), hide_index=True)
        if st.button("Allocate", type="primary"):
            out = Path(tempfile.mkdtemp()) / "SlotSmith_allocation.xlsx"
            res = run(paths, rules, out)
            st.session_state.res = res
            st.session_state.out = out
    res = st.session_state.get("res")
    if res:
        m = res.metrics
        k = st.columns(6)
        k[0].metric("Signals allocated", f"{m['signals_allocated']:,}")
        k[1].metric("Covered by TQ", m["signals_with_tq"])
        k[2].metric("Verifier violations", m["violations"])
        k[3].metric("Cabinets", m["cabinets"])
        k[4].metric("CIOCs", m["ciocs"])
        k[5].metric("Baseplates used", f"{m['baseplates']}")
        a, b = st.columns(2)
        a.subheader("Rule-check report")
        a.dataframe(pd.DataFrame(res.check), hide_index=True, use_container_width=True)
        b.subheader("TQ list")
        b.dataframe(pd.DataFrame([{"TQ": q.id, "Sev": q.severity, "Rule": q.rule_ref, "Message": q.message,
                                   "Rows": ", ".join(q.sources[:3])} for q in res.tqs]), hide_index=True,
                    use_container_width=True)
        st.subheader("Cabinet summary")
        st.dataframe(pd.DataFrame(res.summary), hide_index=True, use_container_width=True)
        st.download_button("Download allocation workbook", Path(st.session_state.out).read_bytes(),
                           "SlotSmith_allocation.xlsx")


def cabinet_html(rows, cab):
    cr = [r for r in rows if r["Marshalling Cabinet"] == cab]
    ciocs = sorted({r["CIOC"] for r in cr})
    kind = {}
    for r in cr:
        bp = int(r["Baseplate"].split("-CBP-")[1])
        if r["Row Kind"] != "Signal":
            k = "SPARE"
        else:
            io_ = (r["IO Type"] or "").upper()
            k = "DO_ISO" if r["Terminal Block"] == "Fused-injected-power" else "DO_RELAY" if r["Terminal Block"] == "Relay output" \
                else "AO" if io_.startswith("AO") else "DI" if io_.startswith("DI") else "DO" if io_.startswith("DO") else "AI"
        kind[(r["CIOC"], bp, int(r["Slot"]))] = (k, r["Tag"] or f"spare {r['Cable']}/{r['Pair']}")
    html = "<div style='display:flex;gap:18px'>"
    for q in ciocs:
        qr = [r for r in cr if r["CIOC"] == q]
        g = sorted({r["IO Group"] for r in qr if r["IO Group"]}) or ["no group"]
        s = sorted({r["Segregation"] for r in qr if r["Segregation"]})
        html += f"<div><div style='font:600 12px sans-serif;margin-bottom:4px'>{q} · {g[0]}{' · ' + s[0] if s else ''}</div>"
        for bp in range(1, 9):
            html += "<div style='display:flex;gap:2px;margin-bottom:3px'>"
            for sl in range(1, 13):
                k, tag = kind.get((q, bp, sl), ("FREE", "free"))
                html += f"<div title='{tag}' style='width:12px;height:22px;border-radius:2px;background:{COL[k]}'></div>"
            html += "</div>"
        html += "</div>"
    return html + "</div>"


with tab2:
    res = st.session_state.get("res")
    if not res:
        st.info("Allocate first.")
    else:
        cabs = [s["Marshalling Cabinet"] for s in res.summary]
        cab = st.selectbox("Marshalling cabinet", cabs)
        st.markdown(cabinet_html(res.rows, cab), unsafe_allow_html=True)
        st.caption("Hover a CHARM to see its tag. Colours: AI blue · AO violet · DI green · DO yellow · DO iso+fused orange · "
                   "relay pink · wired spare grey · free dark")

with tab3:
    res = st.session_state.get("res")
    if not res:
        st.info("Allocate Rev A first.")
    else:
        fb = st.file_uploader("Rev B MDB", type=["xlsx", "csv"], accept_multiple_files=True, key="revb_up")
        use_demo = st.session_state.get("revb") is not None and st.checkbox("Use the synthetic Rev B generated with Rev A", True)
        if st.button("Compare + re-allocate (keep unchanged in place)", type="primary"):
            if fb:
                mdb_b = read_mdb(_save_uploads(fb)).df
            elif use_demo:
                p = Path(tempfile.mkdtemp()) / "SYNTHETIC_RevB.xlsx"
                st.session_state.revb.to_excel(p, index=False)
                mdb_b = read_mdb([p]).df
            else:
                st.stop()
            with st.spinner("Pinning unchanged cables, repairing with CP-SAT if needed…"):
                rr = revise(res.rows, mdb_b, rules)
            st.session_state.rr = rr
        rr = st.session_state.get("rr")
        if rr:
            m = rr.metrics
            k = st.columns(6)
            for i, (lab, key) in enumerate([("Moved", "moved"), ("Added", "added"), ("Deleted", "deleted"),
                                            ("Modified in place", "modified_in_place"), ("Unchanged", "unchanged"),
                                            ("Violations", "violations")]):
                k[i].metric(lab, f"{m[key]:,}")
            st.caption(f"Cabinets hit: {len(m['cabinets_hit'])} · CP-SAT repairs: {len(m['cpsat_repairs'])} · "
                       f"full re-allocation fallback: {m['fallback_full_reallocation']}")
            st.dataframe(pd.DataFrame(rr.impact), hide_index=True, use_container_width=True)
