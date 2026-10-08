"""RTE (Réseau de Transport d'Électricité) day-ahead market data access."""

from __future__ import annotations

import base64

import requests

RTE_TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
RTE_WHOLESALE_MARKET_URL = (
    "https://digital.iservices.rte-france.com/open_api/wholesale_market/v3/france_power_exchanges"
)


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


def fetch_rte_prices(token: str, start_date: str, end_date: str) -> list[float]:
    """Fetch EPEX day-ahead prices (€/MWh) for France between two dates.

    Dates must be RFC3339 timestamps, e.g. "2026-10-01T00:00:00+02:00".
    Prices are returned at RTE's native resolution (15 minutes as of 2026).
    """
    headers = {"Authorization": "Bearer " + token}
    params = {"start_date": start_date, "end_date": end_date}
    response = requests.get(RTE_WHOLESALE_MARKET_URL, headers=headers, params=params)
    response.raise_for_status()
    exchanges = response.json()["france_power_exchanges"]
    return [point["price"] for point in exchanges[0]["values"]]
