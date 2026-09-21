"""
HTTP API over the analysis engine.

    uvicorn sensitor.api.app:app

Nothing is imported here. `app.py` pulls in FastAPI, which is not a dependency
of the Streamlit application and need not be installed to use it — the same
reason `integrations/__init__` does not import the MetaTrader connector. Import
what you need:

    from sensitor.api.app import create_app

The layering rule this package exists to honour: it computes nothing. Every
number it serves comes from `sensitor.trading` and `sensitor.investment`,
reached through the same `Store` and the same `Auth` the Streamlit pages use.
"""
