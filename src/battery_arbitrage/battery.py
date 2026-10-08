from dataclasses import dataclass


@dataclass
class BatterySpec:
    capacity_mwh: float
    max_power_mw: float
    charge_efficiency: float
    discharge_efficiency: float
