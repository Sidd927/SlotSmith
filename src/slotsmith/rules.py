"""Typed, user-editable rule set.

Every behaviour that the problem statement leaves open is a parameter here, so
an organiser clarification changes a JSON file, not code (rule register Q-5).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class HardwareRule(BaseModel):
    """One row of the CHARM / terminal-block selection table (PS rule 6)."""

    id: str
    io_types: list[str] = Field(description="Normalised IO-type keys this row applies to, e.g. 'AI', 'DO-SOV'")
    charm: str
    terminal_block: str
    color_key: str = "AI"
    description: str = ""


class NamingRules(BaseModel):
    area: str = "AR1"
    unit: str = "100"
    system_cabinet: str = "{area}-DCS-{unit}-{seq:02d}"
    controller: str = "{area}CTL{unit}{seq:02d}"
    marshalling_cabinet: str = "{area}-DCM-{unit}-{seq:02d}"
    cioc: str = "{area}CIOC{unit}{seq:03d}"
    baseplate: str = "{cioc_no:03d}-CBP-{n}"
    charm_slot: str = "{cioc_no:03d}-CBP-{n}-{slot:02d}"


class RuleToggle(BaseModel):
    id: str
    enabled: bool = True
    description: str = ""


class RuleSet(BaseModel):
    name: str = "Default (PS #02 rulebook)"
    version: str = "1"

    # Capacity (PS rule 3)
    charms_per_baseplate: int = 12
    baseplates_per_cioc: int = 8
    ciocs_per_cabinet: int = 4
    max_ciocs_per_controller: int = 16       # Emerson PDS (S-03); assumption for naming
    controllers_per_system_cabinet: int = 4  # ASM (rule register C-2)

    # Cables (PS rule 4)
    standard_cable_sizes: list[int] = Field(default_factory=lambda: [2, 6, 12, 24])
    allow_cable_straddle: bool = False       # ASM K-3: ≤12-pair cables stay in one baseplate
    multi_baseplate_cables_same_cioc: bool = True

    # Grouping and segregation (PS rules 1, 2)
    group_isolation_level: Literal["cioc", "cabinet", "none"] = "cioc"
    ungrouped_may_share_group_cioc: bool = False
    segregation_level: Literal["cioc", "cabinet"] = "cioc"
    segregation_values: list[str] = Field(default_factory=lambda: ["A", "B"])

    # Spare capacity (PS rule 5)
    spare_percent: float = 10.0
    spare_rounding: Literal["ceil", "round", "floor"] = "ceil"

    # Allocation ordering
    block_order: Literal["ffd", "mdb"] = "ffd"

    # Hardware selection (PS rule 6)
    hardware: list[HardwareRule] = Field(default_factory=list)
    io_type_aliases: dict[str, str] = Field(default_factory=dict)

    naming: NamingRules = Field(default_factory=NamingRules)

    # Rule switches (rule panel on/off)
    toggles: list[RuleToggle] = Field(default_factory=list)

    @field_validator("spare_percent")
    @classmethod
    def _pct(cls, v: float) -> float:
        if not 0 <= v < 100:
            raise ValueError("spare_percent must be in [0, 100)")
        return v

    # ---- derived values -------------------------------------------------
    @property
    def baseplates_per_cabinet(self) -> int:
        return self.baseplates_per_cioc * self.ciocs_per_cabinet

    @property
    def reserved_baseplates_per_cabinet(self) -> int:
        raw = self.spare_percent / 100.0 * self.baseplates_per_cabinet
        fn = {"ceil": math.ceil, "round": round, "floor": math.floor}[self.spare_rounding]
        return int(fn(raw - 1e-9) if self.spare_rounding == "ceil" else fn(raw))

    @property
    def usable_baseplates_per_cabinet(self) -> int:
        return self.baseplates_per_cabinet - self.reserved_baseplates_per_cabinet

    def enabled(self, rule_id: str) -> bool:
        for t in self.toggles:
            if t.id == rule_id:
                return t.enabled
        return True

    def hardware_for(self, io_type_key: str) -> Optional[HardwareRule]:
        for h in self.hardware:
            if io_type_key in h.io_types:
                return h
        return None

    def normalise_io_type(self, raw: str) -> str:
        k = str(raw).strip().upper().replace("_", "-").replace(" ", "-")
        return self.io_type_aliases.get(k, k)

    # ---- persistence ------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path) -> "RuleSet":
        return cls.model_validate(json.loads(Path(path).read_text()))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2))


def default_ruleset() -> RuleSet:
    """The six example rules of PS #02 p.5, as data."""
    hw = [
        HardwareRule(id="H-1", io_types=["AI"], charm="AI 4-20 mA HART CHARM", terminal_block="Standard",
                     color_key="AI", description="AI: pressure, level, flow, temperature"),
        HardwareRule(id="H-1b", io_types=["AI-RTD"], charm="RTD CHARM", terminal_block="Standard",
                     color_key="AI", description="AI: RTD temperature"),
        HardwareRule(id="H-2", io_types=["AO"], charm="AO 4-20 mA HART CHARM", terminal_block="Standard",
                     color_key="AO", description="AO: control valve"),
        HardwareRule(id="H-3", io_types=["DI"], charm="DI 24 V DC low-side CHARM", terminal_block="Standard",
                     color_key="DI", description="DI: switch, status, push-button"),
        HardwareRule(id="H-4", io_types=["DO-SOV", "DO-HORN", "DO-BEACON", "DO-SOUNDER", "DO-ISO"],
                     charm="DO 24 V DC Isolated CHARM", terminal_block="Fused-injected-power",
                     color_key="DO_ISO", description="DO high current: SOV, horn, beacon, sounder"),
        HardwareRule(id="H-5", io_types=["DO"], charm="DO 24 V DC High-side CHARM", terminal_block="Standard",
                     color_key="DO", description="DO normal"),
        HardwareRule(id="H-6", io_types=["DO-RELAY"], charm="DO 24 V DC High-side CHARM", terminal_block="Relay output",
                     color_key="DO_RELAY", description="DO relay output (rule-based)"),
    ]
    aliases = {
        "ANALOG-INPUT": "AI", "ANALOGUE-INPUT": "AI", "AI-HART": "AI",
        "ANALOG-OUTPUT": "AO", "ANALOGUE-OUTPUT": "AO", "AO-HART": "AO",
        "DIGITAL-INPUT": "DI", "DIGITAL-OUTPUT": "DO", "DO-STD": "DO", "DO-NORMAL": "DO",
        "RTD": "AI-RTD", "SOV": "DO-SOV", "HORN": "DO-HORN", "BEACON": "DO-BEACON",
        "SOUNDER": "DO-SOUNDER", "RELAY": "DO-RELAY", "DO-RO": "DO-RELAY",
    }
    toggles = [
        RuleToggle(id="R1-grouping", description="Keep logical groups together, in sequence"),
        RuleToggle(id="R2-segregation", description="Never put A and B in the same CIOC"),
        RuleToggle(id="R3-capacity", description="12 CHARMs/baseplate, 8 baseplates/CIOC, 4 CIOCs/cabinet"),
        RuleToggle(id="R4-cable", description="Keep each cable together, in pair order"),
        RuleToggle(id="R5-spare", description="Leave spare room per cabinet (empty baseplates)"),
        RuleToggle(id="R6-hardware", description="Pick the right CHARM and terminal block"),
        RuleToggle(id="R7-naming", description="Names generated from user-defined patterns"),
    ]
    return RuleSet(hardware=hw, io_type_aliases=aliases, toggles=toggles)
