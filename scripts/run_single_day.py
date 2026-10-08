"""Fetch one day of RTE day-ahead prices and plot the optimal battery dispatch.

Usage:
    python scripts/run_single_day.py

Requires RTE_CLIENT_ID and RTE_CLIENT_SECRET in a .env file at the repo root.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

from battery_arbitrage.battery import BatterySpec
from battery_arbitrage.data import fetch_rte_prices, get_rte_token
from battery_arbitrage.optimizer import optimize_day

PERIOD_HOURS = 0.25  # RTE day-ahead prices are published at 15-minute resolution


def main() -> None:
    load_dotenv()
    token = get_rte_token(os.environ["RTE_CLIENT_ID"], os.environ["RTE_CLIENT_SECRET"])
    day_prices = fetch_rte_prices(token)  # RTE's endpoint always returns today's (or tomorrow's) prices

    battery = BatterySpec(
        capacity_mwh=8,
        max_power_mw=10,
        charge_efficiency=0.92,
        discharge_efficiency=0.95,
    )
    result = optimize_day(day_prices, battery, initial_soc=0.5, period_hours=PERIOD_HOURS)

    hours = np.arange(len(day_prices)) * PERIOD_HOURS

    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.plot(hours, day_prices, color="gray", linestyle="--", label="Prix (€/MWh)")
    ax1.set_xlabel("Heure de la journée")
    ax1.set_ylabel("Prix (€/MWh)", color="gray")
    ax1.tick_params(axis="y", labelcolor="gray")

    ax2 = ax1.twinx()
    ax2.plot(hours, result.charge_mw, color="tab:green", label="Charge (MW)")
    ax2.plot(hours, result.discharge_mw, color="tab:red", label="Décharge (MW)")
    ax2.plot(hours, result.soc_mwh, color="tab:blue", label="SOC (MWh)")
    ax2.set_ylabel("Puissance (MW) / Énergie stockée (MWh)")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.title(f"Dispatch optimal — profit journalier : {result.profit:.2f} €")
    ax1.grid(alpha=0.3)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
