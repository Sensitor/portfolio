"""
The trading journal's review: the plan, the rules checked on each trade, the
period report, trade entry and import, and the coach review requests.

    python tests/test_journal.py

Pure modules only: no Streamlit, no database. Every expected figure below is
worked out by hand in the comment next to it.
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensitor.platform.ui import trade_visuals as V  # noqa: E402
from sensitor.trading import coaching as C  # noqa: E402
from sensitor.trading import demo  # noqa: E402
from sensitor.trading import entry as E  # noqa: E402
from sensitor.trading import review as R  # noqa: E402
from sensitor.trading.models import Direction, Trade  # noqa: E402

CHECKS: list[tuple[str, bool, str]] = []
UTC = timezone.utc


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def raises(call) -> bool:
    try:
        call()
    except ValueError:
        return True
    return False


def trade(id_: str, *, hour: int = 9, minute: int = 0, day: int = 20, result_r: float = 2.0,
          risk: float = 100.0, rr: float | None = 2.0, stop: bool = True, setups=("fvg",), mistakes=(),
          held: int = 30) -> Trade:
    """A long EURUSD trade with an exact R: stop 0.0010 below 1.1000, size from the risk."""
    entry, distance = 1.1000, 0.0010
    size = risk / distance
    opened = datetime(2026, 10, day, hour, minute, tzinfo=UTC)
    exit_price = entry + distance * result_r
    return Trade(id=id_, symbol="EURUSD", direction=Direction.LONG, entry_price=entry, size=size,
                 opened_at=opened, exit_price=exit_price, closed_at=opened + timedelta(minutes=held),
                 stop_loss=entry - distance if stop else None,
                 take_profit=entry + distance * rr if rr else None,
                 gross_pnl=(exit_price - entry) * size, setups=list(setups), mistakes=list(mistakes))


PLAN = R.TradingPlan(capital=10_000, currency="EUR", risk_pct=1.0, require_stop=True, min_rr=2.0,
                     sessions=("london", "new_york"), setups=("fvg", "order_block"),
                     max_trades_per_day=2, daily_loss_r=2.0, pause_after_losses=2)


def status(review: R.TradeReview, rule: str) -> str:
    return next(c.status for c in review.checks if c.rule == rule)


# =============================================================================

def test_plan() -> None:
    print("\nThe plan")
    check("1 % of 10 000 is a maximum risk of 100", PLAN.max_risk == 100)
    check("no capital, no maximum in money", R.TradingPlan(risk_pct=1.0).max_risk is None)
    cleaned = R.clean_plan({"capital": "5000", "risk_pct": 0.5, "sessions": ["london", "london"],
                            "setups": ["FVG", "ob"], "max_trades_per_day": 3, "min_rr": 0})
    check("cleaning reads numbers, folds setup spellings and drops duplicates",
          cleaned.capital == 5000 and cleaned.sessions == ("london",) and cleaned.setups == ("fvg", "order_block"))
    check("a zero leaves the rule unchecked", cleaned.min_rr is None)
    check("a plan survives its dictionary", R.TradingPlan.from_dict(PLAN.to_dict()) == PLAN)
    for label, data in (("a negative capital", {"capital": -1}), ("a risk over 100 %", {"risk_pct": 150}),
                        ("an unknown session", {"sessions": ["tokyo"]}), ("a fractional trade count",
                        {"max_trades_per_day": 2.5}), ("text for a number", {"min_rr": "deux"}),
                        ("an unknown currency", {"currency": "BTC"})):
        check(f"refuses {label}", raises(lambda d=data: R.clean_plan(d)))
    sentences = R.plan_sentences(PLAN)
    check("the plan reads back in French, money included",
          "Je risque au plus 1 % du capital par trade, soit 100 €." in sentences
          and "Au plus 2 trades par jour." in sentences, str(sentences))


def test_rules() -> None:
    print("\nOne trade, rule by rule")
    good = R.review_trade(trade("a"), PLAN, [])
    check("a trade inside every rule follows the plan",
          good.followed is True and good.score == 1.0 and not good.failed, str([(c.rule, c.status) for c in good.checks]))
    check("nine rules, all checkable here", len(good.checks) == 9 and len(good.evaluated) == 9)

    no_stop = R.review_trade(trade("b", stop=False), PLAN, [])
    check("no stop breaks the stop rule", status(no_stop, "stop") == R.FAIL)
    check("and leaves the risk unknown, not passed", status(no_stop, "risk") == R.NA)
    check("and the reward-to-risk unknown", status(no_stop, "rr") == R.NA)

    big = R.review_trade(trade("c", risk=250), PLAN, [])
    check("250 risked for a maximum of 100 is a breach", status(big, "risk") == R.FAIL)
    check("and says by how much", "2,5 fois le maximum" in next(c.detail for c in big.checks if c.rule == "risk"))
    check("104 is a rounding, not a breach", status(R.review_trade(trade("d", risk=104), PLAN, []), "risk") == R.OK)

    check("a target at 1.5 times the risk is under a minimum of 2",
          status(R.review_trade(trade("e", rr=1.5), PLAN, []), "rr") == R.FAIL)
    check("no target, the ratio is unknown", status(R.review_trade(trade("f", rr=None), PLAN, []), "rr") == R.NA)

    check("02:00 UTC is Asia, outside the plan", status(R.review_trade(trade("g", hour=2), PLAN, []), "session") == R.FAIL)
    check("07:30 UTC is London, inside it", status(R.review_trade(trade("h", hour=7, minute=30), PLAN, []), "session") == R.OK)
    check("the London and New York overlap counts as both",
          status(R.review_trade(trade("i", hour=13), PLAN, []), "session") == R.OK)

    check("a setup outside the plan", status(R.review_trade(trade("j", setups=("breakout",)), PLAN, []), "setup") == R.FAIL)
    check("no setup at all", status(R.review_trade(trade("k", setups=()), PLAN, []), "setup") == R.FAIL)
    free = R.TradingPlan(require_setup=False)
    check("a plan without setups does not check them", status(R.review_trade(trade("l", setups=()), free, []), "setup") == R.NA)

    declared = R.review_trade(trade("m", mistakes=("moved_stop",)), PLAN, [])
    check("a mistake the member recorded breaks the plan", status(declared, "declared") == R.FAIL)
    check("and points to the lesson on that mistake",
          next(c.lesson for c in declared.failed) == "lesson:processus-de-trading/executer-seance")
    check("hesitation is a remark, not a breach",
          status(R.review_trade(trade("n", mistakes=("hesitation",)), PLAN, []), "declared") == R.OK)
    check("every failed rule carries its lesson", all(c.lesson for c in big.failed + no_stop.failed))
    check("a passed rule carries none", all(not c.lesson for c in good.checks))

    no_day = R.review_trade(trade("o"), PLAN)
    check("without the day's trades, the daily rules are not checkable",
          {status(no_day, r) for r in ("daily_count", "daily_loss", "pause")} == {R.NA})
    empty = R.review_trade(trade("p", stop=False, rr=None, setups=()), R.TradingPlan(
        risk_pct=None, require_stop=False, min_rr=None, require_setup=False, max_trades_per_day=None,
        daily_loss_r=None, pause_after_losses=None))
    check("a plan with no rule checks only the recorded mistakes", len(empty.evaluated) == 1)
    round_trip = R.TradeReview.from_dict(big.to_dict())
    check("a review survives its dictionary", round_trip.checks == big.checks and round_trip.score == big.score)


def test_daily_rules() -> None:
    print("\nThe day's rules")
    # Three trades on 20 October: a loss at 08:00, a loss at 09:00, a third at 10:00.
    day = [trade("d1", hour=8, result_r=-1.0), trade("d2", hour=9, result_r=-1.0), trade("d3", hour=10)]
    reviews = R.review_journal(day, PLAN)
    check("the third trade of a day with a maximum of two breaks the count",
          status(reviews["d3"], "daily_count") == R.FAIL and status(reviews["d2"], "daily_count") == R.OK)
    check("after −2 R, the daily loss limit of 2 R is reached",
          status(reviews["d3"], "daily_loss") == R.FAIL and status(reviews["d2"], "daily_loss") == R.OK)
    check("after two losses in a row, the pause was due", status(reviews["d3"], "pause") == R.FAIL)
    check("one loss before is under the threshold", status(reviews["d2"], "pause") == R.OK)
    # A trade still open when the next one starts does not count as « earlier ».
    overlap = [trade("o1", hour=8, result_r=-1.0, held=180), trade("o2", hour=9, result_r=-1.0, held=10),
               trade("o3", hour=10)]
    check("a loss closed after the next entry is not before it",
          status(R.review_journal(overlap, PLAN)["o3"], "pause") == R.OK)
    other_day = [trade("x1", day=19, hour=9, result_r=-1.0), trade("x2", day=19, hour=10, result_r=-1.0),
                 trade("x3", day=20, hour=9)]
    check("the day starts afresh", status(R.review_journal(other_day, PLAN)["x3"], "daily_loss") == R.OK)


def test_report() -> None:
    print("\nA period")
    # Four trades: two inside the plan (+2 R and −1 R), one oversized loss (−1 R),
    # one moved stop that lost 1.5 R. Followed: +1 R. Departed: −2.5 R.
    trades = [trade("r1", day=13), trade("r2", day=14, result_r=-1.0), trade("r3", day=15, risk=250, result_r=-1.0),
              trade("r4", day=16, result_r=-1.5, mistakes=("moved_stop",))]
    reviews = R.review_journal(trades, PLAN)
    rep = R.report(trades, reviews)
    check("two trades out of four followed the plan", (rep.n_followed, rep.n_checked) == (2, 4))
    check("compliance is 50 %", rep.compliance == 0.5)
    check("the followed trades made +1 R", abs(rep.followed_r - 1.0) < 1e-9)
    check("the departures cost −2.5 R", abs(rep.departed_r + 2.5) < 1e-9)
    by_rule = {t.rule: t for t in rep.tallies}
    check("each rule counts its breaches over the trades it could check",
          (by_rule["risk"].breaches, by_rule["risk"].checked) == (1, 4)
          and by_rule["declared"].breaches == 1 and by_rule["stop"].breaches == 0)
    check("the priority is the most expensive breach: the moved stop (−1.5 R)",
          rep.priority.rule == "declared" and abs(rep.priority.cost_r + 1.5) < 1e-9)
    curves = R.plan_curves(trades, reviews)
    check("the curve as traded ends at −1.5 R", abs(curves[-1]["realise"] + 1.5) < 1e-9)
    check("the plan's curve counts departures as zero and ends at +1 R", abs(curves[-1]["plan"] - 1.0) < 1e-9)
    check("departures are flagged", [c["ecart"] for c in curves] == [False, False, True, True])
    clean = R.report(trades[:2], R.review_journal(trades[:2], PLAN))
    check("no breach, no priority", clean.priority is None and clean.compliance == 1.0)
    daily = R.daily_r(trades)
    total, n = daily[date(2026, 10, 13)]
    check("R per closing day", abs(total - 2.0) < 1e-9 and n == 1 and len(daily) == 4)


def test_entry() -> None:
    print("\nEntering trades")
    t = E.build_trade(symbol=" eurusd ", direction="achat", opened_at=datetime(2026, 7, 20, 9, 30),
                      closed_at=datetime(2026, 7, 20, 11, 0), entry=1.0850, exit=1.0880, stop=1.0835,
                      target=1.0880, risk=50)
    # 0.0015 of stop distance for 50 risked: size 33 333.33, result 0.0030 × size = 100, so +2 R.
    check("the size comes from the risk and the stop", abs(t.size - 50 / 0.0015) < 1e-6)
    check("so R is exact: +2 R", abs(t.r_multiple - 2.0) < 1e-9 and abs(t.risk_amount - 50) < 1e-9)
    check("the symbol is cleaned", t.symbol == "EURUSD")
    check("9:30 in Paris in July is 7:30 UTC", t.opened_at == datetime(2026, 7, 20, 7, 30, tzinfo=UTC))
    check("which is the London session", t.session.value == "london")
    winter = E.build_trade(symbol="X", direction="vente", opened_at=datetime(2026, 1, 12, 9, 30),
                           closed_at=datetime(2026, 1, 12, 10, 0), entry=100, exit=98, stop=101, risk=10)
    check("9:30 in Paris in January is 8:30 UTC", winter.opened_at.hour == 8 and winter.direction is Direction.SHORT)
    check("a short that fell 2 for a stop 1 above is +2 R", abs(winter.r_multiple - 2.0) < 1e-9)
    net = E.build_trade(symbol="X", direction="long", opened_at=datetime(2026, 1, 12, 9), closed_at=datetime(2026, 1, 12, 10),
                        entry=100, exit=102, stop=99, risk=10, result=17.5)
    check("the broker's net result wins over the prices", abs(net.pnl - 17.5) < 1e-9 and abs(net.r_multiple - 1.75) < 1e-9)
    bare = E.build_trade(symbol="X", direction="long", opened_at=datetime(2026, 1, 12, 9), closed_at=datetime(2026, 1, 12, 10),
                         entry=100, exit=102, result=40)
    check("without a stop, R stays undefined", bare.r_multiple is None and bare.pnl == 40)
    base = dict(symbol="X", direction="long", opened_at=datetime(2026, 1, 12, 9), closed_at=datetime(2026, 1, 12, 10),
                entry=100.0, exit=102.0)
    for label, extra, word in (("a stop without a risk", {"stop": 99}, "risque"),
                               ("no stop and no result", {}, "résultat"),
                               ("a stop above a long entry", {"stop": 101, "risk": 10}, "mauvais côté"),
                               ("an unknown side", {"direction": "peut-être", "stop": 99, "risk": 10}, "sens"),
                               ("no symbol", {"symbol": " ", "stop": 99, "risk": 10}, "symbole"),
                               ("a close before the open", {"closed_at": datetime(2026, 1, 12, 8), "stop": 99, "risk": 10},
                                "fermeture")):
        try:
            E.build_trade(**{**base, **extra})
            message = ""
        except ValueError as exc:
            message = str(exc)
        check(f"refuses {label}, in French", word in message, message)


def test_import() -> None:
    print("\nImporting a spreadsheet")
    trades, errors = E.parse_csv(E.template_csv())
    check("the template imports its example row", len(trades) == 1 and not errors, str(errors))
    check("the example is +2 R with its setup", abs(trades[0].r_multiple - 2.0) < 1e-9 and trades[0].setups == ["fvg"])
    text = ("Ouverture,Fermeture,Symbole,Sens,Entrée,Sortie,Stop,Risque,Erreurs\n"
            "20/10/2026 14:00,20/10/2026 15:00,XAUUSD,vente,2650.5,2640.5,2660.5,150,revenge\n"
            "2026-10-20 15:00,2026-10-20 16:00,EURUSD,achat,1.08,1.09,1.07,\n"
            "2026-10-21 09:00,2026-10-21 10:00,GBPUSD,achat,abc,1.27,1.26,50\n"
            ",,,,,,,,\n")
    trades, errors = E.parse_csv(text)
    check("commas, French headers with accents, and day-first dates are read", len(trades) == 1)
    check("a short gaining 10 for a stop 10 away is +1 R", abs(trades[0].r_multiple - 1.0) < 1e-9)
    check("recorded mistakes are folded", trades[0].mistakes == ["revenge"])
    check("each bad row is reported with its line", [n for n, _ in errors] == [3, 4], str(errors))
    check("an empty row is skipped silently", len(errors) == 2)
    french = "ouverture;fermeture;symbole;sens;entree;sortie;stop;risque\n2026-10-20 09:00;2026-10-20 10:00;DAX;achat;19 250,5;19 270,5;19 240,5;100\n"
    trades, errors = E.parse_csv(french)
    check("semicolons, thousands spaces and decimal commas", len(trades) == 1 and abs(trades[0].r_multiple - 2.0) < 1e-9, str(errors))
    again, _ = E.parse_csv(french)
    check("the same row gets the same id, so a second import updates", again[0].id == trades[0].id)
    check("a file without the needed columns is refused whole",
          E.parse_csv("date;prix\n1;2\n")[1][0][1].startswith("colonnes manquantes"))
    check("an empty file says so", E.parse_csv("")[1] == [(1, "le fichier est vide")])


def test_coaching() -> None:
    print("\nCoach reviews")
    check("a member has one review a month, premium eight",
          C.monthly_quota("free") == 1 and C.monthly_quota("premium") == 8 and C.monthly_quota(None) == 1)
    check("the month starts on the first", C.month_start(datetime(2026, 10, 21, 15, tzinfo=UTC)).startswith("2026-10-01T00:00"))
    name = C.pseudonym("Alice@Example.com ")
    check("a pseudonym is stable and hides the address",
          name == C.pseudonym("alice@example.com") and "alice" not in name.lower() and name.startswith("Membre "))
    check("two members, two pseudonyms", C.pseudonym("bob@example.com") != name)
    t = trade("c1")
    t.raw = {"broker": "secret"}
    snap = C.snapshot(t)
    check("the coach's copy drops the broker payload", "raw" not in snap and snap["symbol"] == "EURUSD")
    check("a closed trade may be sent", C.can_request(t, used=0, quota=1, already_open=False) is None)
    check("not over the quota", "1er du mois" in C.can_request(t, used=1, quota=1, already_open=False))
    check("not twice", "déjà" in C.can_request(t, used=0, quota=1, already_open=True))
    open_ = Trade(id="o", symbol="X", direction=Direction.LONG, entry_price=1, size=1, opened_at=datetime(2026, 10, 1, tzinfo=UTC))
    check("not an open trade", "clôturé" in C.can_request(open_, used=0, quota=1, already_open=False))
    check("not a demonstration trade", "exemple" in C.can_request(demo.trades(date(2026, 10, 21))[0], used=0, quota=1,
                                                                   already_open=False))
    check("a question is required", raises(lambda: C.clean_question("   ")))
    feedback = C.clean_feedback({"improve": " La taille. ", "scores": {"risque": 2, "contexte": None},
                                 "lessons": ["lesson:premiers-pas/budget-de-risque"] * 2})
    check("feedback is cleaned, empty marks dropped, lessons deduplicated",
          feedback == {"strengths": "", "improve": "La taille.", "comment": "", "scores": {"risque": 2},
                       "lessons": ["lesson:premiers-pas/budget-de-risque"]}, str(feedback))
    for label, data in (("an empty answer", {"strengths": "Bien."}), ("a mark of 6", {"comment": "x", "scores": {"risque": 6}}),
                        ("a link that is not a lesson", {"comment": "x", "lessons": ["https://exemple.com"]}),
                        ("five lessons", {"comment": "x", "lessons": [f"lesson:a/b{i}" for i in range(5)]})):
        check(f"refuses {label}", raises(lambda d=data: C.clean_feedback(d)))


def test_demo() -> None:
    print("\nThe demonstration journal")
    first, again = demo.trades(date(2026, 10, 21)), demo.trades(date(2026, 10, 21))
    check("the same day gives the same journal", [t.to_dict() for t in first] == [t.to_dict() for t in again])
    check("about fifty to seventy trades over nine weeks", 40 <= len(first) <= 80, str(len(first)))
    check("every trade is marked as demonstration", all(t.source == "demo" and t.id.startswith("demo-") for t in first))
    check("all before the day", all(t.closed_at.date() <= date(2026, 10, 21) for t in first))
    check("R is exact on the trades inside the plan: 1 % of 10 000 is 100 risked",
          all(abs(t.risk_amount - 100) < 1e-6 for t in first if "oversized" not in t.mistakes))
    reviews = R.review_journal(first, demo.PLAN)
    rep = R.report(first, reviews)
    check("the construction shows departures that cost R", rep.departed_r < 0 < rep.followed_r)
    check("and most trades inside the plan", rep.compliance > 0.6)


def test_visuals() -> None:
    print("\nDrawings")
    ring = V.score_ring(0.75, center="3/4")
    check("a ring is an SVG with its centre text", ring.startswith("<svg") and "3/4" in ring and 'aria-hidden="true"' in ring)
    check("an empty ring draws no arc", V.score_ring(0).count("<circle") == 1)
    ladder = V.price_ladder(trade("v1").to_dict())
    check("the ladder names its levels in French", all(w in ladder for w in ("STOP", "ENTRÉE", "OBJECTIF")))
    check("and gives them in R", "+2,0 R" in ladder and "−1,0 R" in ladder)
    check("a trade without a stop draws without R", "R<" not in V.price_ladder(trade("v2", stop=False).to_dict()))
    cal = V.calendar({date(2026, 10, 20): (2.0, 1)}, end=date(2026, 10, 21), weeks=4)
    check("the calendar labels each day", "20 octobre : +2,00 R, 1 trade" in cal)
    check("a day without trades says so", "aucun trade" in cal)
    check("R reads in French", V.r_text(-1.5) == "−1,50 R" and V.r_text(None) == "n.d.")
    dashes = [s for s in (ring, ladder, cal) if "\u2014" in s or "\u2013" in s]
    check("no long dash in any drawing", not dashes)


def main() -> int:
    for test in (test_plan, test_rules, test_daily_rules, test_report, test_entry, test_import,
                 test_coaching, test_demo, test_visuals):
        test()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
