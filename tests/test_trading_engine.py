"""
Trading engine tests.

Runs with `streamlit` poisoned, like the investment suite: the trading engine is
pure computation and must stay that way.

Most assertions are on hand-built trades with known answers rather than on
generated data, because the point is to pin the arithmetic — a P&L or an R
multiple computed the wrong way still produces plausible-looking numbers.

Run with:  python tests/test_trading_engine.py
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["streamlit"] = None  # type: ignore[assignment]

from sensitor.trading import (  # noqa: E402
    Direction, Trade, TradeFilter, TradeJournal,
)
from sensitor.trading import analytics as TA  # noqa: E402
from sensitor.trading import models as TM  # noqa: E402
from sensitor.trading import performance as TP  # noqa: E402
from sensitor.trading import psychology as TPsy  # noqa: E402
from sensitor.trading import risk as TR  # noqa: E402
from sensitor.trading import setups as TS  # noqa: E402

FAILURES: list[str] = []
UTC = timezone.utc


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def near(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(a - b) < tol


def make(id_="T", *, direction=Direction.LONG, entry=100.0, exit_=None, stop=None,
         size=1.0, commission=0.0, swap=0.0, opened=None, minutes=60, **extra) -> Trade:
    opened = opened or datetime(2026, 1, 5, 13, 0, tzinfo=UTC)
    return Trade(
        id=id_, symbol=extra.pop("symbol", "XAUUSD"), direction=direction,
        entry_price=entry, exit_price=exit_, size=size, stop_loss=stop,
        opened_at=opened,
        closed_at=(opened + timedelta(minutes=minutes)) if exit_ is not None else None,
        commission=commission, swap=swap, **extra,
    )


# =============================================================================
# ARITHMETIC
# =============================================================================

def test_pnl_and_r() -> None:
    print("\np&l and R multiple")

    long_win = make(entry=100, exit_=110, stop=95, size=2, commission=-3)
    check("long P&L is net of costs", near(long_win.pnl, 17.0), str(long_win.pnl))
    check("risk is stop distance times size", near(long_win.risk_amount, 10.0))
    check("net R divides net P&L by risk", near(long_win.r_multiple, 1.7))
    check("gross R excludes costs", near(long_win.r_multiple_gross, 2.0))

    short_win = make(direction=Direction.SHORT, entry=100, exit_=90, stop=105, size=1)
    check("short profits when price falls", near(short_win.pnl, 10.0), str(short_win.pnl))
    check("short risk uses the same distance", near(short_win.risk_amount, 5.0))
    check("short R is positive on a win", near(short_win.r_multiple, 2.0))

    no_stop = make(entry=100, exit_=110)
    check("no stop leaves risk undefined", no_stop.risk_amount is None)
    check("no stop leaves R undefined (not 0)", no_stop.r_multiple is None)

    zero_stop = make(entry=100, exit_=110, stop=100)
    check("stop at entry leaves R undefined", zero_stop.r_multiple is None)

    broker_pnl = make(entry=100, exit_=110, stop=95, gross_pnl=42.0, commission=-2)
    check("broker P&L wins over recomputation", near(broker_pnl.pnl, 40.0),
          str(broker_pnl.pnl))

    open_trade = make(entry=100, stop=95)
    check("open trade has no P&L", open_trade.pnl is None)
    check("open trade is not closed", open_trade.is_closed is False)

    planned = make(entry=100, exit_=110, stop=95, take_profit=115)
    check("planned R:R from stop and target", near(planned.planned_rr, 3.0))

    check("duration in minutes", near(make(entry=100, exit_=110, minutes=90).duration_minutes, 90.0))


def test_direction_and_session() -> None:
    print("\ndirection and session")

    for value, expected in ((0, Direction.LONG), (1, Direction.SHORT),
                            ("BUY", Direction.LONG), ("sell", Direction.SHORT),
                            ("B", Direction.LONG), ("Short", Direction.SHORT)):
        check(f"parses {value!r}", Direction.parse(value) is expected)

    raised = False
    try:
        Direction.parse("sideways")
    except ValueError:
        raised = True
    check("rejects an unknown side instead of guessing", raised)

    for hour, expected in ((2, "asia"), (9, "london"), (13, "overlap"),
                           (18, "new_york"), (23, "off_hours")):
        got = TM.session_for(datetime(2026, 1, 5, hour, tzinfo=UTC)).value
        check(f"{hour:02d}:00 UTC is {expected}", got == expected, got)

    naive = TM.session_for(datetime(2026, 1, 5, 13, 0))
    check("naive timestamps still resolve", naive.value == "overlap")
    check("missing timestamp is off hours", TM.session_for(None).value == "off_hours")


def test_validation() -> None:
    print("\nvalidation")

    good = make(entry=100, exit_=110, stop=95, take_profit=115)
    check("a sane trade has no problems", TM.validate(good) == [], str(TM.validate(good)))

    inverted = make(entry=100, exit_=110, stop=105)
    check("stop on the wrong side is caught",
          any("stop loss" in p for p in TM.validate(inverted)))

    backwards = Trade(id="x", symbol="X", direction=Direction.LONG, entry_price=100,
                      exit_price=110, size=1,
                      opened_at=datetime(2026, 1, 5, 15, tzinfo=UTC),
                      closed_at=datetime(2026, 1, 5, 13, tzinfo=UTC))
    check("closing before opening is caught",
          any("closed before" in p for p in TM.validate(backwards)))

    check("out-of-range rating is caught",
          any("discipline" in p for p in TM.validate(make(entry=100, exit_=110, discipline=9))))


# =============================================================================
# METRICS
# =============================================================================

def test_metrics() -> None:
    print("\nmetrics")

    start = datetime(2026, 1, 5, 13, tzinfo=UTC)
    # Three wins of +2, two losses of -1. Known answers throughout.
    book = [make(f"W{i}", entry=100, exit_=102, stop=99, opened=start + timedelta(days=i))
            for i in range(3)]
    book += [make(f"L{i}", entry=100, exit_=99, stop=99, opened=start + timedelta(days=10 + i))
             for i in range(2)]

    m = TA.compute_metrics(book)
    check("counts every closed trade", m["n"] == 5, str(m["n"]))
    check("net P&L sums", near(m["net_pnl"], 4.0), str(m["net_pnl"]))
    check("win rate", near(m["win_rate"], 0.6), str(m["win_rate"]))
    check("gross profit", near(m["gross_profit"], 6.0))
    check("gross loss is negative", near(m["gross_loss"], -2.0))
    check("profit factor", near(m["profit_factor"], 3.0), str(m["profit_factor"]))
    check("expectancy", near(m["expectancy"], 0.8), str(m["expectancy"]))
    check("average R", near(m["avg_r"], 0.8), str(m["avg_r"]))
    check("best and worst", near(m["best_trade"], 2.0) and near(m["worst_trade"], -1.0))
    check("R coverage is total here", near(m["r_coverage"], 1.0))

    no_losses = TA.compute_metrics(book[:3])
    check("profit factor undefined with no losses", no_losses["profit_factor"] is None)

    check("empty input returns n=0", TA.compute_metrics([])["n"] == 0)
    check("open trades are excluded", TA.compute_metrics([make(entry=100, stop=95)])["n"] == 0)

    scratch = book + [make("S", entry=100, exit_=100, stop=99,
                           opened=start + timedelta(days=30))]
    ms = TA.compute_metrics(scratch)
    check("a scratch counts in n but not in the win rate",
          ms["n"] == 6 and ms["n_decided"] == 5 and near(ms["win_rate"], 0.6),
          f"n={ms['n']} decided={ms['n_decided']} wr={ms['win_rate']}")


def test_r_coverage() -> None:
    print("\nR coverage")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)
    mixed = [make(f"R{i}", entry=100, exit_=102, stop=99, opened=start + timedelta(days=i))
             for i in range(3)]
    mixed += [make(f"N{i}", entry=100, exit_=90, opened=start + timedelta(days=5 + i))
              for i in range(7)]

    m = TA.compute_metrics(mixed)
    check("R stats cover only trades with a stop", m["n_with_r"] == 3, str(m["n_with_r"]))
    check("coverage is reported", near(m["r_coverage"], 0.3), str(m["r_coverage"]))
    check("average R ignores the stopless trades", near(m["avg_r"], 2.0), str(m["avg_r"]))
    check("but net P&L counts them all", near(m["net_pnl"], 6.0 - 70.0),
          str(m["net_pnl"]))


def test_curves_and_streaks() -> None:
    print("\ncurves, drawdown and streaks")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)
    pattern = [2, 2, -1, -1, -1, 3]
    book = [make(f"T{i}", entry=100, exit_=100 + p, stop=99,
                 opened=start + timedelta(days=i)) for i, p in enumerate(pattern)]

    curve = TA.equity_curve(book)
    check("one point per closed trade", len(curve) == 6)
    check("equity ends at the net total", near(curve[-1]["equity"], 4.0),
          str(curve[-1]["equity"]))
    check("curve is ordered by close time",
          all(curve[i]["at"] <= curve[i + 1]["at"] for i in range(len(curve) - 1)))

    dd = TA.max_drawdown(curve)
    check("drawdown depth", near(dd["depth"], -3.0), str(dd["depth"]))
    check("drawdown percentage from the peak", near(dd["depth_pct"], -0.75),
          str(dd["depth_pct"]))

    negative_peak = TA.max_drawdown([{"at": start, "equity": -5.0},
                                     {"at": start, "equity": -9.0}])
    check("no percentage drawdown from a negative peak",
          negative_peak["depth_pct"] is None)

    streaks = TA.compute_streaks(book)
    check("longest win streak", streaks["max_wins"] == 2, str(streaks))
    check("longest loss streak", streaks["max_losses"] == 3, str(streaks))
    check("current streak is a single win", streaks["current"] == 1, str(streaks))

    # Win, win, scratch, win — the scratch must stop the run at two rather than
    # letting it continue to three.
    with_scratch = [
        make("A", entry=100, exit_=102, stop=99, opened=start),
        make("B", entry=100, exit_=102, stop=99, opened=start + timedelta(days=1)),
        make("S", entry=100, exit_=100, stop=99, opened=start + timedelta(days=2)),
        make("C", entry=100, exit_=102, stop=99, opened=start + timedelta(days=3)),
    ]
    streaks_with_scratch = TA.compute_streaks(with_scratch)
    check("a scratch breaks a streak", streaks_with_scratch["max_wins"] == 2,
          str(streaks_with_scratch))

    check("daily P&L buckets by day", len(TA.daily_pnl(book)) == 6)


def test_stop_discipline() -> None:
    print("\nstop discipline")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)

    # Stopped out exactly, with a commission that pushes net R past -1.
    clean = [make(f"C{i}", entry=100, exit_=99, stop=99, commission=-0.2,
                  opened=start + timedelta(days=i)) for i in range(10)]
    result = TR.stop_discipline(clean)
    check("costs alone do not count as a broken stop",
          result["n_beyond_stop"] == 0, str(result["n_beyond_stop"]))
    check("the measure says it is gross", result.get("measured_on") == "gross")

    blown = clean + [make("B", entry=100, exit_=97, stop=99,
                          opened=start + timedelta(days=50))]
    result = TR.stop_discipline(blown)
    check("a genuinely blown stop is flagged", result["n_beyond_stop"] == 1,
          str(result["n_beyond_stop"]))
    check("the offending trade is named", result["beyond_stop_trades"] == ["B"])


def test_risk() -> None:
    print("\nrisk")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)

    steady = [make(f"S{i}", entry=100, exit_=102, stop=99,
                   opened=start + timedelta(days=i)) for i in range(20)]
    profile = TR.risk_profile(steady)
    check("full stop coverage", near(profile["coverage"], 1.0))
    check("consistent sizing scores near zero", near(profile["consistency"], 0.0, 1e-9),
          str(profile["consistency"]))

    erratic = steady + [make("BIG", entry=100, exit_=110, stop=90, size=5,
                             opened=start + timedelta(days=40))]
    check("an outsized trade raises dispersion",
          TR.risk_profile(erratic)["consistency"] > 0.1)
    check("largest vs median is reported",
          TR.risk_profile(erratic)["largest_vs_median"] > 10)

    tiny = [make("A", entry=100, exit_=102, stop=99)]
    check("dispersion withheld on a tiny sample",
          TR.risk_profile(tiny)["consistency"] is None)

    overlapping = [
        make("O1", entry=100, exit_=102, stop=99, opened=start, minutes=600),
        make("O2", entry=100, exit_=102, stop=99, opened=start + timedelta(minutes=10), minutes=600),
        make("O3", entry=100, exit_=102, stop=99, opened=start + timedelta(minutes=20), minutes=600),
    ]
    exposure = TR.concurrent_exposure(overlapping)
    check("concurrent positions counted", exposure["max_concurrent"] == 3,
          str(exposure["max_concurrent"]))
    check("simultaneous risk summed", near(exposure["max_simultaneous_risk"], 3.0))

    expected = TR.expected_loss_streak(0.45, 200)
    check("expected losing run is computed", expected["expected_max_streak"] > 5,
          str(expected))
    check("no expectation from a 100% win rate", TR.expected_loss_streak(1.0, 200) == {})


# =============================================================================
# BREAKDOWNS
# =============================================================================

def test_breakdowns() -> None:
    print("\nbreakdowns")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)

    book = []
    for i in range(12):
        book.append(make(f"G{i}", symbol="XAUUSD", entry=100, exit_=102, stop=99,
                         setups=["bos", "fvg"], opened=start + timedelta(days=i)))
    for i in range(12):
        book.append(make(f"E{i}", symbol="EURUSD", entry=100, exit_=99, stop=99,
                         setups=["breakout"], opened=start + timedelta(days=20 + i)))

    by_symbol = TP.by_symbol(book)
    check("one bucket per symbol", len(by_symbol) == 2, str(len(by_symbol)))
    check("buckets sort by net P&L", by_symbol[0]["key"] == "XAUUSD")
    check("sample size travels", all("n" in r for r in by_symbol))
    check("reliability flag set", all(r["reliable"] for r in by_symbol))

    by_setup = TP.by_setup(book)
    keys = {r["key"] for r in by_setup}
    check("a multi-tag trade counts in each tag", {"bos", "fvg", "breakout"} <= keys,
          str(keys))
    check("bos and fvg have the same count",
          next(r for r in by_setup if r["key"] == "bos")["n"] ==
          next(r for r in by_setup if r["key"] == "fvg")["n"])

    combos = TP.by_setup_combination(book)
    combo_keys = {r["key"] for r in combos}
    check("combination view keeps tags together", "bos + fvg" in combo_keys,
          str(combo_keys))

    # A two-trade bucket must never be promoted as "best".
    lucky = book + [make("LUCK1", symbol="NAS100", entry=100, exit_=150, stop=99,
                         opened=start + timedelta(days=90)),
                    make("LUCK2", symbol="NAS100", entry=100, exit_=150, stop=99,
                         opened=start + timedelta(days=91))]
    rows = TP.by_symbol(lucky)
    top = max(rows, key=lambda r: r["net_pnl"])
    check("the two-trade bucket does lead on raw P&L", top["key"] == "NAS100")
    best = TP.best(rows, "expectancy")
    check("but best() refuses to promote it", best["key"] != "NAS100",
          str(best["key"]))

    check("weekday breakdown is chronological",
          [r["key"] for r in TP.by_weekday(book)] ==
          sorted(r["key"] for r in TP.by_weekday(book)))

    con = TP.concentration(by_symbol)
    check("concentration reports the busiest bucket", con["busiest"] in {"XAUUSD", "EURUSD"})


# =============================================================================
# PSYCHOLOGY
# =============================================================================

def test_psychology() -> None:
    print("\npsychology")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)

    book = []
    for i in range(20):
        book.append(make(f"OK{i}", entry=100, exit_=102, stop=99, discipline=5,
                         emotion_before="calm", opened=start + timedelta(days=i)))
    for i in range(20):
        book.append(make(f"BAD{i}", entry=100, exit_=99, stop=99, discipline=2,
                         emotion_before="impatient", mistakes=["fomo"],
                         opened=start + timedelta(days=30 + i)))

    rows = TPsy.by_mistake(book)
    check("mistake comparison produced", len(rows) == 1, str(len(rows)))
    check("both sample sizes carried",
          rows[0]["group"]["n"] == 20 and rows[0]["rest"]["n"] == 20)
    check("labelled as correlation", rows[0]["interpretation"] == "correlation")

    discipline = TPsy.by_discipline(book)
    check("discipline bands compared", len(discipline) >= 2, str(len(discipline)))

    emotions = TPsy.by_emotion(book, "before")
    check("emotions compared", len(emotions) == 2, str(len(emotions)))

    small = book[:6]
    check("a group below the threshold is withheld", TPsy.by_mistake(small) == [])

    findings = TPsy.findings(book, "en")
    check("findings are produced", len(findings) >= 1)

    # The framing is the product here, so it is asserted rather than trusted:
    # every finding must name itself a correlation in both languages, carry its
    # sample size in the sentence, and avoid causal verbs.
    banned = ("causes", "because of", "caused by", "proves", "leads to")
    for finding in findings:
        check(f"{finding['key']}: states correlation (en)",
              "correlation" in finding["en"].lower(), finding["en"][:90])
        check(f"{finding['key']}: states correlation (fr)",
              "corrélation" in finding["fr"].lower(), finding["fr"][:90])
        check(f"{finding['key']}: no causal language",
              not any(b in (finding["en"] + finding["fr"]).lower() for b in banned),
              finding["en"][:90])
        check(f"{finding['key']}: sample size in the sentence",
              str(finding["n"]) in finding["en"], finding["en"][:90])


# =============================================================================
# JOURNAL
# =============================================================================

def test_journal() -> None:
    print("\njournal")
    start = datetime(2026, 1, 5, 13, tzinfo=UTC)
    rnd = random.Random(3)

    book = []
    for i in range(60):
        won = rnd.random() < 0.5
        book.append(make(
            f"J{i}",
            symbol=rnd.choice(["XAUUSD", "EURUSD"]),
            entry=100, exit_=102 if won else 99, stop=99,
            setups=[rnd.choice(["bos", "fvg", "breakout"])],
            timeframe=rnd.choice(["M15", "H1"]),
            opened=start + timedelta(days=i),
        ))

    journal = TradeJournal(book)
    check("length", len(journal) == 60)
    check("metrics delegate", journal.metrics()["n"] == 60)
    check("symbols listed", journal.symbols() == ["EURUSD", "XAUUSD"])
    check("setups listed", set(journal.setups()) == {"bos", "fvg", "breakout"})

    filtered = journal.filter(TradeFilter(symbols=["XAUUSD"]))
    check("filter narrows", all(t.symbol == "XAUUSD" for t in filtered))
    check("filter returns a new journal, original intact", len(journal) == 60)

    wins = journal.filter(TradeFilter(only_wins=True))
    check("only_wins", all(t.is_win for t in wins))

    r_filter = journal.filter(TradeFilter(min_r=1.0))
    check("min_r excludes losers", all(t.r_multiple >= 1.0 for t in r_filter))

    check("empty filter is inactive", TradeFilter().is_active is False)
    check("populated filter is active", TradeFilter(symbols=["X"]).is_active is True)

    merged = journal.merge(TradeJournal([book[0].annotated(notes="edited")]))
    check("merge deduplicates by id", len(merged) == 60, str(len(merged)))
    check("merge takes the incoming version", merged.get("J0").notes == "edited")

    annotated = journal.annotate("J5", discipline=4, notes="hello")
    check("annotate updates one trade", annotated.get("J5").discipline == 4)
    check("annotate leaves the original alone", journal.get("J5").discipline is None)

    rows = journal.to_dicts()
    restored = TradeJournal.from_dicts(rows)
    check("round-trips through dicts", len(restored) == 60)
    check("round-trip preserves P&L",
          near(restored.metrics()["net_pnl"], journal.metrics()["net_pnl"]))

    check("breakdown by name works", len(journal.breakdown("setup")) == 3)
    check("unknown breakdown returns empty", journal.breakdown("nonsense") == [])
    check("validate finds nothing wrong", journal.validate() == [])


def test_setups() -> None:
    print("\nsetup taxonomy")
    check("folds spellings",
          {TS.canonical_setup(x) for x in ("FVG", "fair value gap", "Fair Value Gap")} == {"fvg"})
    check("folds order block aliases", TS.canonical_setup("OB") == "order_block")
    check("keeps a custom tag", TS.canonical_setup("my edge") == "my edge")
    check("custom tags are marked", TS.is_custom_setup("my edge") is True)
    check("combination is order-independent",
          TS.combination_key(["fvg", "bos"]) == TS.combination_key(["BOS", "FVG"]))
    check("untagged has its own key", TS.combination_key([]) == "untagged")
    check("labels translate", TS.setup_label("fvg", "fr") == "Fair Value Gap")
    check("mistakes fold too", TS.canonical_mistake("fear of missing out") == "fomo")


def main() -> int:
    test_pnl_and_r()
    test_direction_and_session()
    test_validation()
    test_metrics()
    test_r_coverage()
    test_curves_and_streaks()
    test_stop_discipline()
    test_risk()
    test_breakdowns()
    test_psychology()
    test_journal()
    test_setups()

    print(f"\n{len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
