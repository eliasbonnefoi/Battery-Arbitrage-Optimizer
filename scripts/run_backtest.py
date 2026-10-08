"""Backtest the battery arbitrage strategy over several weeks of ENTSO-E day-ahead prices.

Usage:
    python scripts/run_backtest.py

Requires ENTSOE_API_KEY in a .env file at the repo root.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
from dotenv import load_dotenv

from battery_arbitrage.backtest import run_backtest
from battery_arbitrage.battery import BatterySpec
from battery_arbitrage.data import fetch_entsoe_day_ahead_prices

START_DATE = "202609010000"
END_DATE = "202609300000"


def main() -> None:
    load_dotenv()
    days = fetch_entsoe_day_ahead_prices(os.environ["ENTSOE_API_KEY"], START_DATE, END_DATE)

    battery = BatterySpec(
        capacity_mwh=8,
        max_power_mw=10,
        charge_efficiency=0.92,
        discharge_efficiency=0.95,
    )
    result = run_backtest(days, battery, initial_soc=0.5)

    n_days = len(result.daily_profits)
    print(f"Profit total sur {n_days} jours : {result.total_profit:.2f} €")
    print(f"Profit moyen par jour : {result.total_profit / n_days:.2f} €")

    fig, ax = plt.subplots(figsize=(12, 5))
    day_numbers = range(1, n_days + 1)
    ax.bar(day_numbers, result.daily_profits, color="tab:blue")
    ax.axhline(
        result.total_profit / n_days,
        color="tab:red",
        linestyle="--",
        label=f"Moyenne : {result.total_profit / n_days:.0f} €",
    )
    ax.set_xlabel("Jour")
    ax.set_ylabel("Profit (€)")
    ax.set_title(f"Profit quotidien — {n_days} jours, total : {result.total_profit:.0f} €")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
