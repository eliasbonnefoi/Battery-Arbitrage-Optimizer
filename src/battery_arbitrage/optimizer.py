"""Day-ahead battery arbitrage optimizer (linear program, solved with PuLP/CBC)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Sequence

import pulp

from .battery import BatterySpec


@dataclass
class DispatchResult:
    charge_mw: list[float]
    discharge_mw: list[float]
    soc_mwh: list[float]
    profit: float


def _cbc_solver() -> pulp.LpSolver:
    """Prefer a system-installed CBC (e.g. via conda-forge) over PuLP's bundled
    binary, which is built for Intel macOS and fails with "Bad CPU type" on
    Apple Silicon. Falls back to PuLP's default if no system CBC is found.
    """
    cbc_path = shutil.which("cbc")
    if cbc_path:
        return pulp.COIN_CMD(path=cbc_path, msg=False)
    return pulp.PULP_CBC_CMD(msg=False)


def optimize_day(
    day_prices: Sequence[float],
    battery: BatterySpec,
    initial_soc: float,
    period_hours: float,
) -> DispatchResult:
    """Solve the optimal charge/discharge schedule for one day of prices.

    `day_prices` holds one price (€/MWh) per period of length `period_hours`
    (e.g. 24 hourly prices with period_hours=1, or 96 prices with
    period_hours=0.25 for RTE's 15-minute day-ahead resolution).
    """
    n = len(day_prices)

    prob = pulp.LpProblem("battery_arbitrage", pulp.LpMaximize)

    charge = [pulp.LpVariable(f"charge_{t}", lowBound=0, upBound=battery.max_power_mw) for t in range(n)]
    discharge = [pulp.LpVariable(f"discharge_{t}", lowBound=0, upBound=battery.max_power_mw) for t in range(n)]
    soc = [pulp.LpVariable(f"soc_{t}", lowBound=0, upBound=battery.capacity_mwh) for t in range(n)]

    profit = pulp.lpSum(period_hours * day_prices[t] * (discharge[t] - charge[t]) for t in range(n))
    prob += profit

    prob += soc[0] == initial_soc * battery.capacity_mwh + period_hours * (
        charge[0] * battery.charge_efficiency - discharge[0] / battery.discharge_efficiency
    )
    for t in range(1, n):
        prob += soc[t] == soc[t - 1] + period_hours * (
            charge[t] * battery.charge_efficiency - discharge[t] / battery.discharge_efficiency
        )

    prob.solve(_cbc_solver())

    return DispatchResult(
        charge_mw=[charge[t].varValue for t in range(n)],
        discharge_mw=[discharge[t].varValue for t in range(n)],
        soc_mwh=[soc[t].varValue for t in range(n)],
        profit=pulp.value(profit),
    )
