import pytest

from battery_arbitrage.battery import BatterySpec
from battery_arbitrage.optimizer import optimize_day


def test_optimizer_charges_low_and_discharges_high():
    """Two-period toy case: price doubles [10, 100], battery starts empty.

    With 90% charge/discharge efficiency, 1 MWh capacity and 1 MW power, the
    optimal strategy charges fully in period 0 (1 MWh stored -> 0.9 MWh after
    losses) then discharges as much as the SOC allows in period 1
    (0.9 * 0.9 = 0.81 MWh), for a profit of 100*0.81 - 10*1 = 71.
    """
    battery = BatterySpec(
        capacity_mwh=1,
        max_power_mw=1,
        charge_efficiency=0.9,
        discharge_efficiency=0.9,
    )

    result = optimize_day([10, 100], battery, initial_soc=0.0, period_hours=1.0)

    assert result.charge_mw[0] == pytest.approx(1.0, abs=1e-4)
    assert result.discharge_mw[1] == pytest.approx(0.81, abs=1e-4)
    assert result.profit == pytest.approx(71.0, abs=1e-4)


def test_soc_never_exceeds_capacity_or_goes_negative():
    battery = BatterySpec(
        capacity_mwh=2,
        max_power_mw=5,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )
    prices = [20, 80, 30, 90, 10, 100]

    result = optimize_day(prices, battery, initial_soc=0.5, period_hours=1.0)

    assert all(0 <= soc <= battery.capacity_mwh + 1e-6 for soc in result.soc_mwh)
