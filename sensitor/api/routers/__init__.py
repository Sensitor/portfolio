"""
Route modules.

Each one is a translation layer and nothing more: read the caller from the
bearer token, ask the engine, serialise. No router computes a financial figure,
and `tests/test_api.py` asserts it by parsing these files for arithmetic and for
imports of numpy, pandas and scipy.

The reason is not tidiness. A metric implemented twice diverges, and the version
that diverges is the one with fewer readers — so the app and the phone would
quietly disagree about a trader's expectancy, and only one of them would be
wrong in a way anyone noticed.
"""
