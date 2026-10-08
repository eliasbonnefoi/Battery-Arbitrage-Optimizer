"""Day-ahead market data access: RTE (current day only) and ENTSO-E (historical)."""

from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

RTE_TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
RTE_WHOLESALE_MARKET_URL = (
    "https://digital.iservices.rte-france.com/open_api/wholesale_market/v3/france_power_exchanges"
)

ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_FRANCE_DOMAIN = "10YFR-RTE------C"
ENTSOE_NAMESPACE = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
ENTSOE_RESOLUTION_TO_HOURS = {"PT15M": 0.25, "PT30M": 0.5, "PT60M": 1.0}


def get_rte_token(client_id: str, client_secret: str) -> str:
    """Exchange RTE OAuth2 client credentials for a short-lived access token."""
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": "Basic " + encoded,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(RTE_TOKEN_URL, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_rte_prices(token: str) -> list[float]:
    """Fetch the current EPEX day-ahead prices (€/MWh) for France.

    This endpoint takes no query parameters: per RTE's own API guide, it
    always returns today's prices before ~13h00 French time and tomorrow's
    prices after that, regardless of what date range is requested. It is
    therefore only useful for a single "current day" snapshot, not for
    fetching historical data (use fetch_entsoe_day_ahead_prices for that).
    Prices are returned at RTE's native resolution (15 minutes as of 2026).
    """
    headers = {"Authorization": "Bearer " + token}
    response = requests.get(RTE_WHOLESALE_MARKET_URL, headers=headers)
    response.raise_for_status()
    exchanges = response.json()["france_power_exchanges"]
    return [point["price"] for point in exchanges[0]["values"]]


@dataclass
class DayPrices:
    start: str
    prices: list[float]
    period_hours: float


def fetch_entsoe_day_ahead_prices(api_key: str, start_date: str, end_date: str) -> list[DayPrices]:
    """Fetch historical day-ahead prices (€/MWh) for France from ENTSO-E, one entry per day.

    start_date/end_date must be in "YYYYMMDDHHMM" format, UTC, e.g. "202609010000".

    ENTSO-E's archive sometimes republishes the same day as multiple
    near-identical <TimeSeries>/<Period> blocks (e.g. revisions), and some
    days have fewer points than a full day (data gaps in the archive).
    This function deduplicates periods by their start timestamp and keeps
    each day's native point count and resolution rather than assuming a
    fixed length, so run_backtest can optimize each day on its own terms.
    """
    params = {
        "securityToken": api_key,
        "documentType": "A44",
        "in_Domain": ENTSOE_FRANCE_DOMAIN,
        "out_Domain": ENTSOE_FRANCE_DOMAIN,
        "periodStart": start_date,
        "periodEnd": end_date,
    }
    response = requests.get(ENTSOE_URL, params=params)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    days: dict[str, DayPrices] = {}
    for time_series in root.findall(".//ns:TimeSeries", ENTSOE_NAMESPACE):
        for period in time_series.findall("ns:Period", ENTSOE_NAMESPACE):
            start = period.find(".//ns:start", ENTSOE_NAMESPACE).text
            if start in days:
                continue
            resolution = period.find("ns:resolution", ENTSOE_NAMESPACE).text
            prices = [
                float(point.find("ns:price.amount", ENTSOE_NAMESPACE).text)
                for point in period.findall("ns:Point", ENTSOE_NAMESPACE)
            ]
            days[start] = DayPrices(
                start=start,
                prices=prices,
                period_hours=ENTSOE_RESOLUTION_TO_HOURS[resolution],
            )
    return [days[key] for key in sorted(days)]
