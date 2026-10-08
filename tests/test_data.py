from unittest.mock import Mock, patch

from battery_arbitrage.data import fetch_entsoe_day_ahead_prices

# Two TimeSeries for the same day (a duplicate, as ENTSO-E's archive sometimes
# republishes), plus one TimeSeries for a second, distinct day.
SAMPLE_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<Publication_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3">
    <TimeSeries>
        <Period>
            <timeInterval><start>2026-08-31T22:00Z</start><end>2026-09-01T22:00Z</end></timeInterval>
            <resolution>PT15M</resolution>
            <Point><position>1</position><price.amount>50.0</price.amount></Point>
            <Point><position>2</position><price.amount>55.0</price.amount></Point>
        </Period>
    </TimeSeries>
    <TimeSeries>
        <Period>
            <timeInterval><start>2026-08-31T22:00Z</start><end>2026-09-01T22:00Z</end></timeInterval>
            <resolution>PT15M</resolution>
            <Point><position>1</position><price.amount>50.0</price.amount></Point>
            <Point><position>2</position><price.amount>55.0</price.amount></Point>
        </Period>
    </TimeSeries>
    <TimeSeries>
        <Period>
            <timeInterval><start>2026-09-01T22:00Z</start><end>2026-09-02T22:00Z</end></timeInterval>
            <resolution>PT60M</resolution>
            <Point><position>1</position><price.amount>60.0</price.amount></Point>
        </Period>
    </TimeSeries>
</Publication_MarketDocument>"""


def test_fetch_entsoe_day_ahead_prices_deduplicates_and_keeps_native_resolution():
    mock_response = Mock()
    mock_response.text = SAMPLE_RESPONSE
    mock_response.raise_for_status = Mock()

    with patch("battery_arbitrage.data.requests.get", return_value=mock_response):
        days = fetch_entsoe_day_ahead_prices("fake_key", "202608312200", "202609022200")

    assert len(days) == 2  # the duplicate first day was dropped
    assert days[0].start == "2026-08-31T22:00Z"
    assert days[0].prices == [50.0, 55.0]
    assert days[0].period_hours == 0.25
    assert days[1].start == "2026-09-01T22:00Z"
    assert days[1].prices == [60.0]
    assert days[1].period_hours == 1.0
