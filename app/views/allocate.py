"""Stage 3: Allocate (rules + run). design.md section E3."""
from __future__ import annotations

import json
from html import escape

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from slotsmith.rules import RuleSet

from app.core.rules_view import GROUP_WORDS, SEG_WORDS, example_names, rule_summary
from app.core.session import get_audit, run_allocation
from app.ui import shell
from app.ui.components import banner, chip, kv, page_title, status_chip_for
from app.views._common import empty_state

K = "rule::"


def _on_rule(path: str, key: str) -> None:
    rules = st.session_state["rules"]
    val = st.session_state[key]
    if path.startswith("toggle:"):
        for t in rules.toggles:
            if t.id == path.split(":", 1)[1]:
                t.enabled = bool(val)
    elif path.startswith("naming."):
        setattr(rules.naming, path.split(".", 1)[1], val)
    else:
        setattr(rules, path, val)


def _clear_rule_widgets() -> None:
    for k in [k for k in st.session_state if str(k).startswith(K)]:
        del st.session_state[k]


def _widgets(rules: RuleSet) -> None:
    with st.container(border=True):
        st.markdown("#### Capacity")
        st.caption("Project rules from the problem statement. Shown for reference; the engine reads them from the rule set file.")
        st.html(kv([("CHARM slots per baseplate", str(rules.charms_per_baseplate)),
                    ("Baseplates per CIOC", str(rules.baseplates_per_cioc)),
                    ("CIOCs per marshalling cabinet", str(rules.ciocs_per_cabinet))]))
    with st.container(border=True):
        st.markdown("#### Separation and grouping")
        k1, k2 = f"{K}group_isolation_level", f"{K}segregation_level"
        c1, c2 = st.columns(2)
        c1.selectbox("Keep IO groups apart by", ["cioc", "cabinet", "none"],
                     index=["cioc", "cabinet", "none"].index(rules.group_isolation_level), key=k1,
                     format_func=lambda v: {"cioc": "CIOC", "cabinet": "Cabinet", "none": "Nothing (no isolation)"}[v],
                     on_change=_on_rule, args=("group_isolation_level", k1))
        c2.selectbox("Keep A and B apart by", ["cioc", "cabinet"], index=["cioc", "cabinet"].index(rules.segregation_level),
                     key=k2, format_func=lambda v: {"cioc": "CIOC", "cabinet": "Cabinet"}[v],
                     on_change=_on_rule, args=("segregation_level", k2))
        st.markdown("**Rule switches**")
        for t in rules.toggles:
            kk = f"{K}toggle:{t.id}"
            st.toggle(t.description, value=t.enabled, key=kk, on_change=_on_rule, args=(f"toggle:{t.id}", kk))
    with st.container(border=True):
        st.markdown("#### Spare room")
        ks = f"{K}spare_percent"
        st.slider("Spare per cabinet (%)", 0.0, 40.0, float(rules.spare_percent), 1.0, key=ks,
                  on_change=_on_rule, args=("spare_percent", ks),
                  help="Share of a cabinet's baseplates kept empty for future growth.")
        st.caption(f"{rules.spare_percent:g}% → {rules.reserved_baseplates_per_cabinet} of {rules.baseplates_per_cabinet} "
                   f"baseplates kept empty per cabinet.")
    with st.container(border=True):
        st.markdown("#### Names")
        c1, c2 = st.columns(2)
        ka, ku = f"{K}naming.area", f"{K}naming.unit"
        c1.text_input("Area", rules.naming.area, key=ka, on_change=_on_rule, args=("naming.area", ka))
        c2.text_input("Unit", rules.naming.unit, key=ku, on_change=_on_rule, args=("naming.unit", ku))
        st.html(kv(list(example_names(rules).items())))
        st.caption("Examples generated from the current patterns. Patterns are edited in the rule set file.")
    with st.expander("CHARM and terminal-block table"):
        st.dataframe(pd.DataFrame([{"ID": h.id, "I/O types": ", ".join(h.io_types), "CHARM": h.charm,
                                    "Terminal block": h.terminal_block} for h in rules.hardware]),
                     hide_index=True, width="stretch")
    with st.expander("Rule set file"):
        st.download_button("Download rule set (JSON)", rules.model_dump_json(indent=2), "slotsmith_ruleset.json",
                           mime="application/json", key="rules_dl")
        up = st.file_uploader("Load a rule set", type=["json"], key="rules_upl")
        if up is not None:
            sig = (up.name, up.size)
            if sig != st.session_state.get("_rules_sig"):
                st.session_state["_rules_sig"] = sig
                try:
                    st.session_state["rules"] = RuleSet.model_validate(json.loads(up.getvalue()))
                except (ValueError, ValidationError) as e:
                    st.session_state["_rules_err"] = f"That rule set could not be loaded: {str(e)[:300]}"
                else:
                    st.session_state["_rules_err"] = None
                    _clear_rule_widgets()
                    st.rerun()
        if st.session_state.get("_rules_err"):
            st.error(st.session_state["_rules_err"])


def render() -> None:
    s = shell.begin("allocate")
    page_title("Allocate", "Set the project rules, then place every cable. Changing a rule marks existing results out of date.")
    if not s.has_input:
        return empty_state("No dataset loaded", "Load a workbook first.", "Go to Input", "input")
    rules = st.session_state["rules"]
    audit = get_audit(st.session_state)

    left, right = st.columns([3, 2], gap="large")
    with left:
        _widgets(rules)
    with right:
        with st.container(border=True):
            st.markdown("#### Run")
            st.html(status_chip_for(s))
            st.html('<ul>' + "".join(f"<li>{escape(x)}</li>" for x in rule_summary(rules)) + "</ul>")
            blocked = audit is None or audit.readiness_status == "blocked"
            if audit is not None and audit.readiness_status == "ready_with_warnings":
                st.html(banner("warn", "Some rows will be held",
                               f"{audit.blocking_tqs} data issue(s) will leave affected rows unplaced as technical queries."))
            elif blocked:
                st.html(banner("bad", "Allocation is blocked", "No valid cable could be formed from this data."))
            label = "Allocate again" if s.has_allocation else "Allocate"
            if st.button(label, type="primary", disabled=blocked, key="run_alloc", width="stretch",
                         icon=":material/play_arrow:"):
                with st.status("Allocating cables…", expanded=True) as stt:
                    st.write("Validating, packing cables into baseplates and CIOCs, then re-checking the exported workbook.")
                    ok, err = run_allocation(st.session_state)
                    if ok:
                        stt.update(label="Allocation finished", state="complete")
                    else:
                        stt.update(label="Allocation failed", state="error")
                if ok:
                    st.switch_page(shell.PAGES["results"])
                st.error(f"The allocation did not finish: {err}. Previous results, if any, are unchanged.")
            if s.has_allocation and not s.alloc.is_stale:
                st.caption("The current results match these rules and this data.")
                if st.button("Open results", key="go_results", icon=":material/arrow_forward:", width="stretch"):
                    st.switch_page(shell.PAGES["results"])
