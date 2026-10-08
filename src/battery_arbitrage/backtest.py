"""Multi-day backtest: run the optimizer day by day, carrying the battery's
state of charge forward from one day to the next.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .battery import BatterySpec
from .data import DayPrices
from .optimizer import DispatchResult, optimize_day


@dataclass
class BacktestResult:
    daily_profits: list[float]
    daily_dispatch: list[DispatchResult]

    @property
    def total_profit(self) -> float:
        return sum(self.daily_profits)


def run_backtest(days: Sequence[DayPrices], battery: BatterySpec, initial_soc: float) -> BacktestResult:
    daily_profits = []
    daily_dispatch = []
    current_soc = initial_soc

    for day in days:
        if not day.prices:
            continue
        result = optimize_day(day.prices, battery, current_soc, day.period_hours)
        current_soc = result.soc_mwh[-1] / battery.capacity_mwh
        daily_profits.append(result.profit)
        daily_dispatch.append(result)

    return BacktestResult(daily_profits=daily_profits, daily_dispatch=daily_dispatch)
