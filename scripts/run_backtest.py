"""Backtest the battery arbitrage strategy over several weeks of ENTSO-E day-ahead prices.

Usage:
    python scripts/run_backtest.py

Requires ENTSOE_API_KEY in a .env file at the repo root.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
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

    # Continuous price/SOC trace over the whole backtest, stitching each day's
    # own (possibly partial) period count and resolution end to end.
    traded_days = [day for day in days if day.prices]
    hours, prices, soc = [], [], []
    t0 = 0.0
    for day, dispatch in zip(traded_days, result.daily_dispatch):
        n = len(day.prices)
        hours.extend(t0 + np.arange(n) * day.period_hours)
        prices.extend(day.prices)
        soc.extend(dispatch.soc_mwh)
        t0 += n * day.period_hours
    days_axis = np.array(hours) / 24

    fig2, ax1 = plt.subplots(figsize=(14, 5))
    ax1.plot(days_axis, prices, color="gray", linewidth=0.8, label="Prix (€/MWh)")
    ax1.set_xlabel("Jour")
    ax1.set_ylabel("Prix (€/MWh)", color="gray")
    ax1.tick_params(axis="y", labelcolor="gray")

    ax2 = ax1.twinx()
    ax2.plot(days_axis, soc, color="tab:blue", linewidth=1.2, label="SOC (MWh)")
    ax2.set_ylabel("Énergie stockée (MWh)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax1.set_title("Prix et état de charge de la batterie sur tout le backtest")
    ax1.grid(alpha=0.3)
    fig2.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
