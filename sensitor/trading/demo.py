"""
A constructed journal, for the demonstration of the journal and its review.

Visitors and new members see what the journal does before they have entered a
trade. Nothing here is real: the trades are generated from a fixed seed, over
the weeks before a given day, and every page that shows them says « Exemple
synthétique ». The construction is deliberate and stated: trades that follow
the plan win about 45 % of the time at two to three times the risk, and the
departures (revenge trades, oversized positions, a moved stop) lose more
often, which is the pattern path 10 teaches to look for. It illustrates the
method; it is not evidence of anything.

Sizes are derived from the risk in money and the stop distance, so R is exact.

No Streamlit, no database.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta, timezone

from .models import Direction, Trade
from .review import TradingPlan

PLAN = TradingPlan(capital=10_000, currency="EUR", risk_pct=1.0, require_stop=True, min_rr=2.0,
                   sessions=("london", "new_york"),
                   setups=("liquidity_sweep", "fvg", "order_block", "bos"),
                   require_setup=True, max_trades_per_day=3, daily_loss_r=2.0, pause_after_losses=2)

RISK = 100.0
COMMISSION = -3.0
WEEKS = 9

# symbol: (price, typical stop distance, decimals)
MARKETS = {"EURUSD": (1.0850, 0.0012, 5), "GBPUSD": (1.2700, 0.0015, 5),
           "XAUUSD": (2650.0, 4.5, 2), "NAS100": (21_400.0, 35.0, 1)}
PLAN_SETUPS = ("liquidity_sweep", "fvg", "order_block", "bos")
EMOTIONS_OK = ("calm", "confident", "calm", "calm")


def _trade(rng: random.Random, n: int, opened: datetime, *, setups, risk=RISK,
           result_r: float, rr: float, mistakes=(), emotion="calm", stop=True) -> Trade:
    symbol = rng.choice(tuple(MARKETS))
    price, distance, decimals = MARKETS[symbol]
    price *= 1 + rng.uniform(-0.02, 0.02)
    direction = rng.choice((Direction.LONG, Direction.SHORT))
    sign = direction.sign
    distance *= rng.uniform(0.8, 1.25)
    entry = round(price, decimals)
    stop_price = round(entry - sign * distance, decimals)
    distance = abs(entry - stop_price)
    size = risk / distance
    target = round(entry + sign * distance * rr, decimals)
    exit_price = entry + sign * distance * result_r
    held = timedelta(minutes=rng.choice((18, 35, 50, 75, 110, 160)))
    return Trade(
        id=f"demo-{n:03d}", symbol=symbol, direction=direction, entry_price=entry, size=size,
        opened_at=opened, exit_price=exit_price, closed_at=opened + held,
        stop_loss=stop_price if stop else None, take_profit=target,
        gross_pnl=(exit_price - entry) * sign * size, commission=COMMISSION,
        account_id="demo", account_currency="EUR", setups=list(setups),
        timeframe=rng.choice(("M5", "M15", "M15", "H1")), mistakes=list(mistakes),
        emotion_before=emotion, discipline=2 if mistakes else rng.choice((4, 4, 5)),
        notes=None, source="demo",
    )


def trades(today: date | None = None) -> list[Trade]:
    """About fifty closed trades over the nine weeks before `today`, always the same for a given day."""
    today = today or date.today()
    rng = random.Random(20261021)
    out: list[Trade] = []
    day = today - timedelta(weeks=WEEKS)
    n = 0
    while day < today:
        if day.weekday() < 5 and rng.random() < 0.82:
            losses_today = 0
            count = rng.choice((1, 1, 2, 2, 2, 3))
            hours = sorted(rng.sample((8, 9, 10, 13, 14, 15), count))
            last_close = None
            for hour in hours:
                n += 1
                at = datetime.combine(day, time(hour, rng.choice((5, 15, 25, 40, 50))), tzinfo=timezone.utc)
                if last_close and at < last_close + timedelta(minutes=10):
                    at = last_close + timedelta(minutes=10)
                roll = rng.random()
                if losses_today >= 2 and rng.random() < 0.7:
                    # The plan says stop for the day; the demo trader does not.
                    out.append(_trade(rng, n, at, setups=(rng.choice(PLAN_SETUPS),),
                                      result_r=-1.0 if rng.random() < 0.75 else 1.5, rr=2.0,
                                      mistakes=("revenge",), emotion="frustrated"))
                    break
                if roll < 0.06:
                    t = _trade(rng, n, at, setups=(rng.choice(PLAN_SETUPS),), risk=RISK * 2.2,
                               result_r=-1.0 if rng.random() < 0.7 else 2.0, rr=2.0,
                               mistakes=("oversized",), emotion="euphoric")
                elif roll < 0.10:
                    t = _trade(rng, n, at, setups=(rng.choice(PLAN_SETUPS),),
                               result_r=-1.7, rr=2.5, mistakes=("moved_stop",), emotion="anxious")
                elif roll < 0.14:
                    t = _trade(rng, n, at.replace(hour=rng.choice((2, 3, 4))), setups=("breakout",),
                               result_r=-1.0 if rng.random() < 0.65 else 2.0, rr=2.0, emotion="bored")
                elif roll < 0.17:
                    t = _trade(rng, n, at, setups=(rng.choice(PLAN_SETUPS),),
                               result_r=-1.0 if rng.random() < 0.6 else 1.2, rr=1.2,
                               mistakes=("fomo",), emotion="impatient")
                else:
                    rr = rng.choice((2.0, 2.0, 2.5, 3.0))
                    win = rng.random() < 0.46
                    result = rr if win else (-1.0 if rng.random() < 0.88 else 0.0)
                    t = _trade(rng, n, at, setups=(rng.choice(PLAN_SETUPS),),
                               result_r=result, rr=rr, emotion=rng.choice(EMOTIONS_OK))
                out.append(t)
                last_close = max(last_close or t.closed_at, t.closed_at)
                if t.r_multiple is not None and t.r_multiple < 0:
                    losses_today += 1
        day += timedelta(days=1)
    return out
