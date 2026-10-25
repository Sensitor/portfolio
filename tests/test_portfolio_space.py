"""
The « Portefeuille et risque » space inside the platform: the analyzer's pages,
the building page, the shared working portfolio, and the separate app's
navigation translated into the platform's.

    python tests/test_portfolio_space.py

Prices are never downloaded: the analysis is the test suite's synthetic
portfolio (`test_sensitor_pages.make_portfolio`), put in the session the way a
finished analysis is.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SENSITOR_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="sensitor-portfolio-space-"), "space.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_TOOLS_URL", None)

from streamlit.testing.v1 import AppTest  # noqa: E402

from test_sensitor_pages import SCENARIOS, make_portfolio  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensitor_app.py")
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def store():
    from sensitor.database import Store
    return Store(os.environ["SENSITOR_DB_PATH"])


def token(email: str) -> str:
    from sensitor.core.auth import Auth
    auth = Auth(store(), mode="multi")
    result = auth.sign_up(email, "un-mot-de-passe-solide")
    return result.token if result else auth.sign_in(email, "un-mot-de-passe-solide").token


def run(route: dict, tok: str | None = None, *, analyzer=None, state: dict | None = None) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=180)
    app.session_state["ac_route"] = route
    if tok:
        app.session_state["session_token"] = tok
    if analyzer is not None:
        app.session_state["current_portfolio"] = analyzer
        app.session_state["selected_tickers"] = list(analyzer.weights)
        app.session_state["weights"] = dict(analyzer.weights)
    for key, value in (state or {}).items():
        app.session_state[key] = value
    app.run()
    return app


def text(app: AppTest) -> str:
    return "\n".join(m.value for m in app.markdown)


def error(app: AppTest) -> str:
    return str(app.exception[0].value)[:300] if app.exception else ""


def offline(tickers, weights, start, **kwargs):
    """
    The analyzer, without the network: the synthetic portfolio, already « fetched ».
    Like the real one, it keeps only the lines with a price history (here, the
    asset library's) and spreads the weight of the others over them.
    """
    from sensitor.investment import assets
    known = {t: w for t, w in dict(weights).items() if t in assets.ASSET_INFO}
    total = sum(known.values()) or 1.0
    analyzer = make_portfolio({t: w / total for t, w in known.items()}, base_currency=kwargs.get("base_currency", "USD"))
    analyzer.user_profile = kwargs.get("user_profile", "balanced")
    analyzer.fetch_data = lambda **_: bool(known)
    return analyzer


def offline_prices(tickers, base="USD", *, manual=None, on_error=None, **_):
    """Today's prices, without the network: 500 for a library line, the typed price otherwise."""
    from sensitor.investment import assets
    report = {"base": base, "converted": {}, "dropped": {}, "missing": [], "manual": {}, "previous": {}}
    prices = {}
    for t in tickers:
        if t in assets.ASSET_INFO:
            prices[t] = 500.0
        elif (manual or {}).get(t, {}).get("price"):
            prices[t] = float(manual[t]["price"])
            report["manual"][t] = manual[t].get("at")
        else:
            report["missing"].append(t)
    return prices, report


def main() -> int:
    from sensitor.platform import spaces
    from sensitor.platform.ui import portfolio_space as PS

    # AppTest runs the app in this process: the space prices portfolios offline.
    PS.UltimatePortfolioAnalyzer = offline
    PS.latest_prices = offline_prices

    print("\nValuing holdings: the one rule both apps use")
    from sensitor.investment import holdings as H
    v = H.value({"SPY": 10, "FLAT": 1, "NONE": 3}, {"SPY": 500.0, "FLAT": 250_000.0})
    check("quantity times price, a total and weights; a line without price is named, not zero",
          v.values == {"SPY": 5000.0, "FLAT": 250000.0} and v.total == 255000.0
          and abs(v.weights["SPY"] - 5000 / 255000) < 1e-12 and v.unpriced == ("NONE",))
    covered, excluded = H.split_analysed(v.values, ["SPY"])
    check("a line the analyzer leaves out takes its money with it",
          covered == 5000.0 and excluded == {"FLAT": 250000.0})
    check("an empty portfolio is worth nothing and has no weights",
          H.value({}, {}).total == 0 and H.value({"SPY": 1}, {}).weights == {})

    print("\nThe space in the registry")
    space = spaces.space("tools")
    check("Portefeuille et risque is live, entered on the building page",
          space.is_live and space.entry == "portfolio" and set(space.pages) == set(PS.PAGES))
    check("the old address of the link page opens the space", spaces.resolve_page("tools") == "portfolio")

    analyzer = make_portfolio(SCENARIOS["diversified (7 assets)"])
    alice = token("alice@example.com")

    print("\nEvery analysis page renders, for a member and a visitor")
    dashed = []
    for page, label, _render in PS.TABS:
        for who, tok in (("member", alice), ("visitor", None)):
            app = run({"page": page}, tok, analyzer=analyzer)
            body = text(app)
            check(f"{who} · {label}", not app.exception and "snr-page-head" in body, error(app))
            if any(d in m.value for m in app.markdown if not m.value.startswith("<style") for d in ("\u2014", "\u2013")):
                dashed.append(f"{who} · {label}")
    check("no long dash on the space's pages", not dashed, str(dashed))

    overview = run({"page": "pf_overview"}, alice, analyzer=analyzer)
    body = text(overview)
    check("the overview carries its « Lecture » margin, in French",
          'class="snr-reading"' in body and "Lecture" in body and "sur la période" in body)
    check("the space's navigation lists the eleven pages and the building page",
          {b.label for b in overview.button} >= {"Construire"} | {label for _p, label, _r in PS.TABS})
    check("the analyzer's component styles are there, its sidebar styles are not",
          any(".snr-card" in m.value for m in overview.markdown)
          and not any("background-image: repeating-linear-gradient(30deg" in m.value and "stSidebar" in m.value
                      and ".snr-card" in m.value for m in overview.markdown))

    print("\nWithout an analysis")
    empty = run({"page": "pf_risk"}, token("neuf@example.com"))
    check("an analysis page without a portfolio asks to compose one, and draws nothing",
          "Aucun portefeuille analysé" in text(empty) and not empty.get("plotly_chart") and not empty.exception,
          error(empty))
    build = run({"page": "portfolio"})
    check("the building page renders for a visitor, and says nothing is kept",
          "Composer le portefeuille" in text(build) and "Sans compte" in text(build) and not build.exception, error(build))
    check("it says what stays in the full app, and that its address is not configured",
          "portefeuilles modèles" in text(build) and "pas renseignée" in text(build))
    built = run({"page": "portfolio"}, alice, analyzer=analyzer)
    check("with an analysis, the building page shows it and offers to read it",
          "Portefeuille analysé" in text(built) and any(b.label == "Lire la vue d'ensemble" for b in built.button))
    check("a free account composes five lines; a larger allocation stays whole, and the page says so",
          any("au plus 7" in m.label for m in built.multiselect) and "un compte gratuit en compose 5" in text(built))
    fresh = run({"page": "portfolio"}, token("carol@example.com"))
    check("a new free account is capped at five lines", any("au plus 5" in m.label for m in fresh.multiselect))

    print("\nThe working portfolio is the member's, shared with the full app")
    run({"page": "pf_overview"}, alice, analyzer=analyzer)
    saved = store().load_workspace("alice@example.com")
    check("analysing in the space writes the member's working portfolio",
          saved is not None and set(saved.holdings) == set(analyzer.weights))
    bob = token("bob@example.com")
    other = run({"page": "portfolio"}, bob)
    mine = store().load_workspace("bob@example.com")
    check("another member does not get it", (mine is None or mine.is_empty)
          and "Portefeuille analysé" not in text(other)
          and all(not (m.value or []) for m in other.multiselect))
    restored = run({"page": "portfolio"}, alice, state={"_workspace_resume_pending": False})
    check("the member finds their allocation back on the building page",
          set(restored.multiselect[0].value) == set(analyzer.weights), str(restored.multiselect[0].value))

    print("\nBuilding and analysing, end to end")
    dave = token("dave@example.com")
    app = run({"page": "portfolio"}, dave)
    app.multiselect(key="pf_tickers").set_value(["SPY", "GLD"]).run()
    app.number_input(key="pf_w_SPY").set_value(70.0).run()
    app.number_input(key="pf_w_GLD").set_value(30.0).run()
    app.selectbox(key="pf_currency").set_value("EUR").run()
    [b for b in app.button if b.label == "Analyser le portefeuille"][0].click().run()
    ws = store().load_workspace("dave@example.com")
    check("« Analyser » prices the allocation and opens the overview",
          not app.exception and app.session_state["ac_route"]["page"] == "pf_overview"
          and app.session_state["current_portfolio"] is not None, error(app))
    check("the allocation is written as the member's working portfolio, in its currency",
          ws is not None and ws.holdings == {"SPY": 0.7, "GLD": 0.3} and ws.base_currency == "EUR",
          str(ws))

    print("\nA real portfolio, in quantities, with a price typed by hand")
    erin = token("erin@example.com")
    app = run({"page": "portfolio"}, erin)
    app.radio(key="pf_mode").set_value("real").run()
    app.selectbox(key="pf_add_pick").set_value("SPY").run()
    app.number_input(key="pf_add_qty").set_value(10.0).run()
    [b for b in app.button if b.key == "pf_add"][0].click().run()
    app.text_input(key="pf_add_custom").set_value("Appartement Lyon").run()
    [b for b in app.button if b.key == "pf_add_custom_btn"][0].click().run()
    check("a library line and a line outside it are added",
          app.session_state["real_portfolio_holdings"] == {"SPY": 10.0, "APPARTEMENT-LYON": 1.0},
          str(app.session_state["real_portfolio_holdings"]))
    app.number_input(key="pf_mp_APPARTEMENT-LYON").set_value(250000.0).run()
    [b for b in app.button if b.label == "Valoriser et analyser"][0].click().run()
    state = app.session_state
    check("valued and analysed: the overview opens in real mode", not app.exception
          and state["ac_route"]["page"] == "pf_overview" and state["analysis_mode"] == "real", error(app))
    check("the hand-priced line is valued, named, and left out of the analysis with its money",
          state["unanalysed_holdings"] == {"APPARTEMENT-LYON": 250000.0} and state["real_portfolio_total_value"] == 5000.0)
    ws = store().load_workspace("erin@example.com")
    check("quantities and the typed price are the member's working portfolio",
          ws is not None and ws.mode == "real" and ws.quantities == {"SPY": 10.0, "APPARTEMENT-LYON": 1.0}
          and ws.manual_prices.get("APPARTEMENT-LYON", {}).get("price") == 250000.0, str(ws))
    page = run({"page": "pf_overview"}, erin)
    check("a new session restores the real portfolio, values it again and analyses it",
          page.session_state["analysis_mode"] == "real" and page.session_state["current_portfolio"] is not None
          and page.session_state["real_portfolio_total_value"] == 5000.0)
    check("the analysis pages say which lines are valued but not analysed",
          "Lignes valorisées, non analysées" in text(page) and "APPARTEMENT-LYON" in text(page) and not page.exception,
          error(page))
    back = run({"page": "portfolio"}, erin)
    body = text(back)
    check("back on the building page, the member's wealth: each line, its source, the total",
          "Portefeuille réel" in body and "saisi le" in body and "cours du marché" in body
          and "255\u202f000" in body, body[-600:] if "Portefeuille réel" not in body else "")
    other = run({"page": "portfolio"}, token("frank@example.com"))
    check("another member sees none of it", "APPARTEMENT" not in text(other) and "255\u202f000" not in text(other))

    print("\nThe separate app's navigation, translated")
    hop = run({"page": "pf_copilot"}, alice, analyzer=analyzer, state={"page": "simulator"})
    check("a copilot change opens the simulator page", not hop.exception and hop.session_state["ac_route"]["page"] == "pf_simulator",
          str(hop.session_state["ac_route"]))
    load = run({"page": "pf_portfolios"}, alice, analyzer=analyzer, state={"page": "new_analysis"})
    check("loading a saved portfolio opens the building page for a new analysis",
          load.session_state["ac_route"]["page"] == "portfolio" and load.session_state["current_portfolio"] is None)

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
