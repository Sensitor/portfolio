"""
External data sources and broker connectors.

    market_data  price and benchmark history
    mt5          MetaTrader 5 — deals normalised into Sensitor trades
    sync         broker-agnostic synchronisation into the journal

Nothing above this package knows what platform a trade came from: a connector
normalises into `trading.models.Trade` and everything else only ever sees that.

**Nothing is imported here**, deliberately. `market_data` caches through
Streamlit and `mt5` reaches for the Windows-only `MetaTrader5` package inside
`connect()`. Re-exporting either would mean that importing one pulled in the
other's dependencies — a broker sync would require Streamlit, and the layering
test that poisons `streamlit` before importing the connector would fail on a
module the connector never uses. Import submodules by name:

    from sensitor.integrations import mt5, sync
"""
