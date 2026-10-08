import pulp

from .battery import BatterySpec


def optimize_day(day_prices, battery: BatterySpec, initial_soc):
    capacity_mwh = battery.capacity_mwh
    max_power_mw = battery.max_power_mw
    charge_efficiency = battery.charge_efficiency
    discharge_efficiency = battery.discharge_efficiency

    # créaton de la fonction d'optimisation
    prob = pulp.LpProblem("battery_arbitrage", pulp.LpMaximize)

    # paramètres problème
    charge = [pulp.LpVariable(f"charge_{t}", lowBound=0, upBound=max_power_mw) for t in range(24)]
    discharge = [pulp.LpVariable(f"discharge_{t}", lowBound=0, upBound=max_power_mw) for t in range(24)]
    soc = [pulp.LpVariable(f"soc_{t}", lowBound=0, upBound=capacity_mwh) for t in range(24)]

    profit = pulp.lpSum([(day_prices[t] * (discharge[t] - charge[t])) for t in range(24)])
    prob += profit

    prob += soc[0] == initial_soc * capacity_mwh + charge[0] * charge_efficiency - discharge[0] / discharge_efficiency
    for t in range(1, 24):
        prob += soc[t] == soc[t - 1] + charge[t] * charge_efficiency - discharge[t] / discharge_efficiency

    prob.solve()
    pulp.LpStatus[prob.status]

    # variables fin
    charge_vals = [charge[t].varValue for t in range(24)]
    discharge_vals = [discharge[t].varValue for t in range(24)]
    soc_vals = [soc[t].varValue for t in range(24)]
    profit_total = pulp.value(profit)

    return charge_vals, discharge_vals, soc_vals, profit_total
