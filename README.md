# Battery Arbitrage Optimizer

An algorithmic trading engine for a battery storage asset on the French
day-ahead power market: it decides, for each pricing period, how much to
charge or discharge to maximize profit, subject to the battery's physical
constraints (capacity, max power, round-trip efficiency).

## How it works

Given a day of prices, `optimize_day` solves a linear program (via
[PuLP](https://github.com/coin-or/pulp) + CBC) with perfect foresight:

- **Decision variables**: `charge[t]` and `discharge[t]` (MW) for each period `t`
- **Objective**: maximize `Σ period_hours * price[t] * (discharge[t] - charge[t])`
- **State-of-charge constraint**: `soc[t] = soc[t-1] + period_hours * (charge[t] * charge_efficiency - discharge[t] / discharge_efficiency)`
- **Bounds**: `0 <= charge[t], discharge[t] <= max_power_mw` and `0 <= soc[t] <= capacity_mwh`

Market data comes from [RTE's Wholesale Market API](https://data.rte-france.com),
which publishes EPEX day-ahead prices for France at 15-minute resolution.

## Project layout

```
src/battery_arbitrage/
    battery.py      # BatterySpec: physical battery parameters
    optimizer.py     # optimize_day(): the LP optimizer
    data.py          # RTE OAuth2 auth + day-ahead price fetching
scripts/
    run_single_day.py  # end-to-end example: fetch prices, optimize, plot
tests/
    test_optimizer.py
```

## Setup

```bash
conda create -n battery-arbitrage python=3.11
conda activate battery-arbitrage
pip install -e ".[dev]"
```

On Apple Silicon, PuLP's bundled CBC solver is built for Intel and fails with
`Bad CPU type in executable`. Install a native one via conda-forge:

```bash
conda install -c conda-forge coincbc -y
```

`optimize_day` automatically prefers a system CBC (found via `shutil.which`)
over PuLP's bundled binary when available.

### Credentials

Get a free `client_id`/`client_secret` from
[data.rte-france.com](https://data.rte-france.com) (subscribe to the
"Wholesale Market" API), then create a `.env` file at the repo root:

```
RTE_CLIENT_ID=...
RTE_CLIENT_SECRET=...
```

## Usage

```bash
python scripts/run_single_day.py
```

## Tests

```bash
pytest
```
