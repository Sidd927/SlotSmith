"""Stage 3: Allocate (rules + run). design.md section E3."""
from __future__ import annotations

import json
from html import escape

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from slotsmith.rules import RuleSet

from app.core.rules_view import GROUP_WORDS, SEG_WORDS, example_names, rule_summary, skipped_families
from app.core.session import get_audit, run_allocation
from app.ui import shell
from app.core.status import run_status
from app.ui.components import banner, icon, kv, status_chip_for
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


# Switches the engine really reads when placing, validating and verifying (checked against src/slotsmith).
SWITCHABLE = {"R1-grouping": "Keep logical groups together",
              "R2-segregation": "Keep A and B signals apart"}
_PLAIN = {"R1-grouping": "Cables of one IO group are placed together, in sequence, and a group never shares a CIOC with another group.",
          "R2-segregation": "A-side and B-side signals never share a CIOC (or cabinet, if you choose that level), so one failure cannot take out both."}
# Rules the engine always applies. A switch for these would not change the result, so none is offered.
ALWAYS = [("Capacity", "12 CHARM slots per baseplate, 8 baseplates per CIOC, 4 CIOCs per cabinet."),
          ("Cable integrity", "A cable is never split: its pairs stay together and in pair order."),
          ("Hardware selection", "Each I/O type gets the CHARM and terminal block from the hardware table below."),
          ("Names", "Cabinet, CIOC, baseplate and slot names come from the naming patterns.")]
_UNSUPPORTED_OFF = {"R3-capacity", "R4-cable", "R5-spare", "R6-hardware", "R7-naming"}


def _widgets(rules: RuleSet) -> None:
    off = [t.id for t in rules.toggles if not t.enabled and t.id in _UNSUPPORTED_OFF]
    if off:
        notes = {"R3-capacity": "capacity", "R4-cable": "cable integrity", "R7-naming": "naming",
                 "R5-spare": "the spare-room reservation (still applied by the allocator; only its check is skipped)",
                 "R6-hardware": "hardware selection"}
        st.html(banner("warn", "This rule set switches rules off",
                       f"{', '.join(off)} {'is' if len(off) == 1 else 'are'} disabled in the loaded rule set. "
                       "The engine always applies " + ", ".join(notes[o] for o in off) + ". "
                       "What a disabled rule changes is the independent check: its family is reported as SKIPPED, never PASS, and the "
                       "run is shown as an incomplete verification. Disabling a rule does not make a violation or an unknown hardware "
                       "assignment valid: a signal whose I/O type has no CHARM / terminal-block mapping is held as a technical "
                       "query either way (no hardware is invented)."))
    with st.container(border=True):
        st.markdown("#### Grouping and separation")
        st.caption("Who may share a CIOC. These settings change where cables are placed and which checks (G-1, S-1) run. "
                   "Turning a switch off skips its check: it never makes a violation or unknown hardware valid.")
        k1, k2 = f"{K}group_isolation_level", f"{K}segregation_level"
        c1, c2 = st.columns(2)
        c1.selectbox("Keep IO groups apart by", ["cioc", "cabinet", "none"],
                     index=["cioc", "cabinet", "none"].index(rules.group_isolation_level), key=k1,
                     format_func=lambda v: {"cioc": "CIOC", "cabinet": "Cabinet", "none": "Nothing (no isolation)"}[v],
                     on_change=_on_rule, args=("group_isolation_level", k1))
        c2.selectbox("Keep A and B apart by", ["cioc", "cabinet"], index=["cioc", "cabinet"].index(rules.segregation_level),
                     key=k2, format_func=lambda v: {"cioc": "CIOC", "cabinet": "Cabinet"}[v],
                     on_change=_on_rule, args=("segregation_level", k2))
        for t in rules.toggles:
            if t.id in SWITCHABLE:
                kk = f"{K}toggle:{t.id}"
                st.toggle(SWITCHABLE[t.id], value=t.enabled, key=kk, on_change=_on_rule, args=(f"toggle:{t.id}", kk))
                st.caption(_PLAIN[t.id])
    with st.container(border=True):
        st.markdown("#### Spare room")
        ks = f"{K}spare_percent"
        st.slider("Spare per cabinet (%)", 0.0, 40.0, float(rules.spare_percent), 1.0, key=ks,
                  on_change=_on_rule, args=("spare_percent", ks),
                  help="Share of a cabinet's baseplates kept empty for future growth.")
        st.caption(f"{rules.spare_percent:g}% → {rules.reserved_baseplates_per_cabinet} of {rules.baseplates_per_cabinet} "
                   f"baseplates kept empty per cabinet.")
    with st.container(border=True):
        st.markdown("#### Always applied")
        st.caption("Fixed by the project rulebook. They are shown so you know what is enforced; there is nothing to switch.")
        st.html('<ul class="ss-fixed">' + "".join(
            f'<li>{icon("ok")}<span><b>{escape(t)}</b>. {escape(d)}</span></li>' for t, d in ALWAYS) + "</ul>")
        st.html(kv([("CHARM slots per baseplate", str(rules.charms_per_baseplate)),
                    ("Baseplates per CIOC", str(rules.baseplates_per_cioc)),
                    ("CIOCs per marshalling cabinet", str(rules.ciocs_per_cabinet))]))
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
    shell.header("allocate", "Configure and allocate",
                 "Set the project rules, then place every cable. Changing a rule or the dataset marks existing results out of date.")
    if not s.has_input:
        return empty_state("No dataset loaded", "Load a workbook first.", "Go to Input", "input")
    rules = st.session_state["rules"]
    audit = get_audit(st.session_state)

    left, right = st.columns([3, 2], gap="large")
    with left:
        _widgets(rules)
    with right, st.container(key="runcard", border=True):
        st.markdown("#### Run")
        blocked = audit is None or audit.readiness_status == "blocked"
        st.html(status_chip_for(run_status(st.session_state)))
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
        st.html('<p class="ss-cap">Editing any rule here, or loading a different dataset, marks the current results, the cabinet map, '
                'the deliverables and any Rev B comparison out of date. Re-run Allocate to refresh them.</p>')
        if s.has_allocation and s.alloc.is_stale:
            st.html(banner("warn", "Current results no longer match", s.alloc.reason))
        elif not s.has_allocation:
            st.caption("Allocating replaces nothing yet. Results, cabinet maps and exports appear after the run.")
        else:
            st.caption("Allocating again replaces the current results and clears any Rev B comparison.")
        if audit is not None and audit.readiness_status == "ready_with_warnings":
            st.html(banner("warn", "Some rows will be held",
                           f"{audit.blocking_tqs} data issue(s) will leave affected rows unplaced as technical queries."))
        elif blocked:
            st.html(banner("bad", "Allocation is blocked", "No valid cable could be formed from this data."))
        skipped = skipped_families(rules)
        if skipped:
            st.html(banner("info", "Some checks will be skipped",
                           "The independent check will report " + ", ".join(f"{r} ({w})" for r, w in skipped) +
                           " as SKIPPED, not PASS, so the result is an incomplete verification."))
        st.html('<p class="ss-h" style="margin-top:14px">Rules in force</p><ul class="ss-conseq">' +
                "".join(f"<li>{escape(x)}</li>" for x in rule_summary(rules)) + "</ul>")
        if s.has_allocation and not s.alloc.is_stale:
            st.caption("The current results match these rules and this data.")
            if st.button("Open results", key="go_results", icon=":material/arrow_forward:", width="stretch"):
                st.switch_page(shell.PAGES["results"])
