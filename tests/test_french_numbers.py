"""
Figures in French typography on the analysis pages read in French.

    python tests/test_french_numbers.py

The rewriting itself (`core.numbers`), then the pages that use it: the journal's
performance page and the portfolio overview in the platform, and the separate
app, which stays in English typography when it is read in English.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SENSITOR_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="sensitor-french-numbers-"), "n.db")
os.environ["SENSITOR_AUTH"] = "multi"

from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "sensitor_app.py")
ANALYTICS_APP = os.path.join(ROOT, "portfolio_optimizer_saas.py")
NNBSP, NBSP = " ", " "
ENGLISH_MONEY = re.compile(r"[€$£]-?\d")             # « €1,709 », the currency in front
ENGLISH_DECIMAL = re.compile(r"(?<![\w.,])\d+\.\d+(?![\d.])")
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


def run(route: dict, tok: str | None = None, *, app_file: str = APP, state: dict | None = None) -> AppTest:
    app = AppTest.from_file(app_file, default_timeout=180)
    app.session_state["ac_route"] = route
    if tok:
        app.session_state["session_token"] = tok
    for key, value in (state or {}).items():
        app.session_state[key] = value
    app.run()
    return app


def visible(app: AppTest) -> str:
    """The page's text, outside tags, styles and drawings, as a reader sees it."""
    out = []
    for m in app.markdown:
        if m.value.lstrip().startswith("<style"):
            continue
        text = re.sub(r"<(style|svg|script)[\s\S]*?</\1>", " ", m.value)
        out.append(unescape(re.sub(r"<[^>]+>", " ", text)))
    return "\n".join(out)


def charts(app: AppTest) -> list[dict]:
    return [json.loads(c.proto.spec) for c in app.get("plotly_chart")]


def main() -> int:
    from sensitor.core.numbers import french_figure, french_html, french_text

    print("\nThe rewriting")
    cases = {
        "€1,709.00": f"1{NNBSP}709,00{NBSP}€",
        "€-1,492.00 (-14.60R)": f"-1{NNBSP}492,00{NBSP}€ (-14,60{NBSP}R)",
        "35.5%": f"35,5{NNBSP}%",
        "+25.1% sur la période": f"+25,1{NNBSP}% sur la période",
        "Ratio 2.24x": "Ratio 2,24x",
        "$1.20M": f"1,20{NBSP}M{NBSP}$",
        "12,345,678.9": f"12{NNBSP}345{NNBSP}678,9",
    }
    for given, expected in cases.items():
        check(f"« {given} » becomes « {expected} »", french_text(given) == expected, repr(french_text(given)))
    untouched = ("En 2026, sur 499 jours.", "Le 2025.03.10 à 09:30.", "NAS100, Web3, S&P 500", "n = 5. Les",
                 "5, 10, 20", "v1.2.3", "38W / 69L")
    check("years, dates, tickers, lists and versions are left alone", all(french_text(x) == x for x in untouched),
          str([french_text(x) for x in untouched if french_text(x) != x]))
    markup = ('<div style="width:1.5px" data-v="2.5">€1,709.00<svg><path d="M1.5 2.5"/><text>3.5</text></svg>'
              '</div><style>.a{opacity:.5}</style>')
    out = french_html(markup)
    check("in HTML, only the text changes: attributes, drawings and styles keep their decimal points",
          f"1{NNBSP}709,00{NBSP}€" in out and 'width:1.5px' in out and 'data-v="2.5"' in out
          and 'd="M1.5 2.5"' in out and "<text>3.5</text>" in out and "opacity:.5" in out, out)
    import plotly.graph_objects as go
    fig = go.Figure(go.Scatter(x=[1, 2], y=[1, 2], hovertemplate="€%{y:,.2f} · %{x:.1f}%<extra></extra>",
                               text=["€1,000.00", "2.5%"]))
    fig.update_layout(yaxis=dict(tickprefix="€", tickformat=",.0f"), xaxis=dict(ticksuffix="%"))
    french_figure(fig)
    check("a chart: decimal comma and narrow spaces, the currency after the value, a space before « % »",
          fig.layout.separators == "," + NNBSP and fig.layout.yaxis.ticksuffix == NBSP + "€"
          and not fig.layout.yaxis.tickprefix and fig.layout.xaxis.ticksuffix == NNBSP + "%"
          and fig.data[0].hovertemplate.startswith("%{y:,.2f}" + NBSP + "€")
          and f"%{{x:.1f}}{NNBSP}%" in fig.data[0].hovertemplate
          and list(fig.data[0].text) == [f"1{NNBSP}000,00{NBSP}€", f"2,5{NNBSP}%"])

    print("\nThe journal's performance page, in French")
    from sensitor.trading import demo
    email = "chiffres@example.com"
    tok = token(email)
    store().save_trades(email, demo.trades())
    perf = run({"page": "journal_performance"}, tok)
    text = visible(perf)
    check("renders", not perf.exception and "Votre trading, sur un seul écran." in text,
          str(perf.exception[0].value)[:200] if perf.exception else "")
    check("no amount with its currency in front", not ENGLISH_MONEY.search(text), str(ENGLISH_MONEY.findall(text)[:5]))
    check("no decimal point left in the text", not ENGLISH_DECIMAL.search(text), str(ENGLISH_DECIMAL.findall(text)[:8]))
    check("amounts read « 1 234,56 € » and rates « 35,5 % »",
          re.search(rf"\d,\d\d{NBSP}€", text) and re.search(rf"\d,\d{NNBSP}%", text))
    specs = charts(perf)
    check("every chart has French separators", specs and all(s["layout"].get("separators") == "," + NNBSP
                                                              for s in specs), str(len(specs)))
    check("the period control reads « 7 j, 30 j, Tout »",
          any(set(r.options) >= {"7 j", "30 j", "Tout"} for r in perf.radio), str([r.options for r in perf.radio]))

    print("\nThe portfolio overview, in French")
    from test_sensitor_pages import SCENARIOS, make_portfolio
    analyzer = make_portfolio(SCENARIOS["diversified (7 assets)"])
    overview = run({"page": "pf_overview"}, tok, state={"current_portfolio": analyzer,
                                                        "selected_tickers": list(analyzer.weights),
                                                        "weights": dict(analyzer.weights)})
    text = visible(overview)
    check("renders", not overview.exception, str(overview.exception[0].value)[:200] if overview.exception else "")
    check("no amount with its currency in front, no decimal point", not ENGLISH_MONEY.search(text)
          and not ENGLISH_DECIMAL.search(text), str((ENGLISH_MONEY.findall(text)[:4], ENGLISH_DECIMAL.findall(text)[:6])))
    check("the period control is in French", any("Max" in r.options and "1 an" in r.options for r in overview.radio),
          str([r.options for r in overview.radio]))

    print("\nThe separate app in English keeps English typography")
    english = run({}, tok, app_file=ANALYTICS_APP, state={"page": "trading_overview", "language": "en"})
    text = visible(english)
    check("an English page still writes « 35.5% » and the currency in front",
          not english.exception and ENGLISH_DECIMAL.search(text) and ENGLISH_MONEY.search(text),
          str(english.exception[0].value)[:200] if english.exception else "")
    check("and its charts keep the default separators", all("separators" not in s["layout"] for s in charts(english)))

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
