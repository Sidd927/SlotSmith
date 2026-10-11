"""Plain-language summary of a RuleSet, generated from its values (never static text)."""
from __future__ import annotations

from slotsmith.rules import RuleSet

GROUP_WORDS = {"cioc": "Each IO group gets its own CIOC.", "cabinet": "Each IO group gets its own cabinet.",
               "none": "IO groups may share CIOCs and cabinets."}
SEG_WORDS = {"cioc": "A and B signals never share a CIOC.", "cabinet": "A and B signals never share a cabinet."}


def example_names(rules: RuleSet) -> dict[str, str]:
    n = rules.naming
    return {
        "Marshalling cabinet": n.marshalling_cabinet.format(area=n.area, unit=n.unit, seq=1),
        "CIOC": n.cioc.format(area=n.area, unit=n.unit, seq=1),
        "Baseplate": n.baseplate.format(cioc_no=1, n=1),
        "CHARM slot": n.charm_slot.format(cioc_no=1, n=1, slot=1),
    }


def rule_summary(rules: RuleSet) -> list[str]:
    slots = rules.ciocs_per_cabinet * rules.baseplates_per_cioc * rules.charms_per_baseplate
    out = [
        f"A cabinet holds up to {rules.ciocs_per_cabinet} CIOCs × {rules.baseplates_per_cioc} baseplates × "
        f"{rules.charms_per_baseplate} CHARM slots = {slots} slots.",
    ]
    if rules.enabled("R5-spare"):
        out.append(f"Spare room: {rules.spare_percent:g}% means {rules.reserved_baseplates_per_cabinet} of "
                   f"{rules.baseplates_per_cabinet} baseplates are kept empty in every cabinet "
                   f"({rules.usable_baseplates_per_cabinet} usable).")
    else:
        out.append("Spare-room reservation is switched off.")
    out.append(GROUP_WORDS[rules.group_isolation_level] if rules.enabled("R1-grouping")
               else "Grouping rule is switched off.")
    out.append(SEG_WORDS[rules.segregation_level] if rules.enabled("R2-segregation")
               else "A/B separation is switched off.")
    out.append(f"{len(rules.hardware)} rows in the hardware table choose the CHARM and terminal block for each I/O type."
               if rules.enabled("R6-hardware") else "Hardware matching is switched off.")
    off = [t.description for t in rules.toggles if not t.enabled and t.id not in
           ("R5-spare", "R1-grouping", "R2-segregation", "R6-hardware")]
    if off:
        out.append("Also switched off: " + "; ".join(off) + ".")
    return out
