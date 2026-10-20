"""
Sensitor Academy — the educational domain.

Covers the content loader and its validation, quiz scoring, numeric exercises,
the risk calculations, course progress, and the store's progress and attempt
tables — including that one member's progress is invisible to another.

Every figure quoted in a lesson is checked against the module that computes it,
so a lesson cannot drift away from the calculator it sends people to.

Run with:  python tests/test_academy.py
"""

from __future__ import annotations

import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensitor.academy import content as C  # noqa: E402
from sensitor.academy import exercise as E  # noqa: E402
from sensitor.academy import markup as M  # noqa: E402
from sensitor.academy import progress as P  # noqa: E402
from sensitor.academy import quiz as Q  # noqa: E402
from sensitor.academy import risk as R  # noqa: E402
from sensitor.academy import access  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def raises(fn, exc=Exception) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def close(a, b, tol=1e-9) -> bool:
    return a is not None and abs(a - b) <= tol


# =============================================================================
# CONTENT
# =============================================================================

def test_real_catalog():
    print("\nThe shipped content")
    catalog = C.load_catalog()
    check("loads without a single problem", True)
    check("validate() reports nothing, drafts and completeness included",
          C.validate() == [], str(C.validate()))

    available = [p for p in catalog.paths if p.is_available]
    check("the open paths are exactly those with published courses",
          all(p.courses for p in available) and available[0].id == "bases-marches"
          and all(not p.courses for p in catalog.paths if p not in available),
          str([p.id for p in available]))
    check("four tracks, trading first, completed by money, Bitcoin and crypto", [t.id for t in catalog.tracks]
          == ["trading", "monnaie-bitcoin", "crypto", "investissement"])
    trading = catalog.paths_in("trading")
    check("the ten trading paths keep their numbers", [p.number for p in trading] == list(range(1, 11)))
    check("paths are ordered by track, then number",
          [p.track for p in catalog.paths] == sorted((p.track for p in catalog.paths),
                                                     key=[t.id for t in catalog.tracks].index))
    check("every path belongs to a known track", all(catalog.track(p.track) for p in catalog.paths))
    check("two universes: trading, then money with Bitcoin, crypto and investing",
          [t.universe for t in catalog.tracks] == ["trading", "monnaie", "monnaie", "monnaie"]
          and catalog.track("crypto").universe_label == "Monnaie et crypto")
    check("a course takes the universe of its track",
          catalog.universe_of(catalog.course("premiers-pas")) == "trading"
          and catalog.universe_of(catalog.course("la-monnaie")) == "monnaie"
          and catalog.universe_of(None) == "trading")
    check("a path is named by its track", catalog.path("structure-price-action").label == "Trading · Parcours 02"
          and catalog.path("bitcoin").label == "Monnaie et Bitcoin · Parcours 02")
    planned = {p.id for p in catalog.paths if p.status == C.PLANNED}
    check("only the founder's two methods are still announced",
          planned == {"methode-sensitor", "methode-fondateur"} and len(catalog.paths) == 16,
          str(sorted(planned)))
    check("only the new tracks require sources",
          {t.id for t in catalog.tracks if t.require_sources} == {"monnaie-bitcoin", "crypto", "investissement"})
    check("planned paths carry no readable course",
          all(not p.courses for p in catalog.paths if p.status == C.PLANNED))

    course = catalog.course("premiers-pas")
    check("the first course exists", course is not None)
    ids = [l.id for l in course.lessons]
    check("six lessons, in the order of the plan",
          ids == ["fonctionnement-marche", "ordres-et-couts", "structure-de-marche",
                  "budget-de-risque", "cas-pratique", "recapitulatif"], str(ids))
    check("lesson numbers follow the order", [l.number for l in course.lessons] == [1, 2, 3, 4, 5, 6])
    check("the first two lessons are free to read",
          [l.access for l in course.lessons[:2]] == ["public", "public"])
    check("the rest are member lessons",
          all(l.access == "member" for l in course.lessons[2:]))
    check("course duration is the sum of lesson durations",
          course.duration_minutes == sum(l.duration_minutes for l in course.lessons))
    check("the final quiz is attached", course.final_quiz_id == "premiers-pas-validation")

    first, second = course.lessons[0], course.lessons[1]
    check("neighbours of the first lesson", course.neighbours(first.id) == (None, second))

    for lesson in course.lessons:
        check(f"{lesson.id}: meets the editorial standard",
              C.completeness(lesson, catalog) == [], str(C.completeness(lesson, catalog)))
        for block in lesson.blocks:
            if block.kind == "figure":
                svg = catalog.figures[block.target]
                check(f"{lesson.id}: figure {block.target} is labelled for screen readers",
                      'role="img"' in svg and "<title" in svg and "<desc" in svg)

    for quiz in catalog.quizzes.values():
        for question in quiz.questions:
            check(f"{quiz.id}/{question.id}: every option is explained",
                  all(o.explanation for o in question.options))

    final = catalog.quiz("premiers-pas-validation")
    check("the final quiz has ten questions", len(final.questions) == 10)
    check("its pass mark is 7 / 10", Q.required_correct(10, final.pass_threshold) == 7)
    check("it corrects at the end", final.feedback == "deferred")
    check("every final question points back to a lesson",
          all(q.lesson_id for q in final.questions))

    for resource in catalog.resources.values():
        check(f"resource {resource.id}: the file is really there", resource.file.is_file())

    dashed = [str(p.relative_to(C.CONTENT_ROOT)) for p in C.CONTENT_ROOT.rglob("*")
              if p.is_file() and p.suffix in (".md", ".toml", ".svg")
              and any(d in p.read_text(encoding="utf-8") for d in ("\u2014", "\u2013"))]
    check("no em or en dash anywhere in the content (house style)", not dashed, str(dashed))


def test_lesson_figures_match_the_calculator():
    """The numbers printed in lessons are recomputed here, from the modules."""
    print("\nFigures quoted in lessons")
    rows = {0.5: (9511, 4.9, 5.1), 1: (9044, 9.6, 10.6), 2: (8171, 18.3, 22.4),
            5: (5987, 40.1, 67.0)}
    for pct, (equity, drawdown, recovery) in rows.items():
        last = R.losing_streak(10_000, pct, 10)[-1]
        check(f"{pct} % over ten losses: {equity} $", round(last.equity) == equity,
              f"{last.equity:.2f}")
        check(f"{pct} %: drawdown {drawdown} %", round(last.drawdown_pct, 1) == drawdown,
              f"{last.drawdown_pct:.3f}")
        check(f"{pct} %: recovery {recovery} %", round(last.recovery_pct, 1) == recovery,
              f"{last.recovery_pct:.3f}")
    check("a 5-loss streak in 100 trades at 50 %: about 81 %",
          round(R.streak_probability(100, 5, 0.5) * 100) == 81)
    check("a 6-loss streak in 100 trades at 50 %: about 55 %",
          round(R.streak_probability(100, 6, 0.5) * 100) == 55)
    check("recovering from −50 % takes +100 %", close(R.recovery_needed(0.5), 1.0))

    example = R.plan(equity=10_000, risk_pct=1, entry=1.0850, stop=1.0820,
                     direction=R.LONG, target=1.0910,
                     spec=R.InstrumentSpec(contract_size=100_000, lot_step=0.01,
                                           pip_size=0.0001))
    check("lesson example: 100 $ at risk", close(example.risk_amount, 100))
    check("lesson example: 30 pips", close(example.stop_distance_pips, 30, 1e-6))
    check("lesson example: 0.333 lot before rounding", close(example.position.raw_lots, 1 / 3, 1e-6))
    check("lesson example: 0.33 lot after rounding down", close(example.position.lots, 0.33))
    check("lesson example: 99 $ effective risk", close(example.position.effective_risk, 99, 1e-6))
    check("lesson example: 2R to the target", close(example.reward_to_risk, 2, 1e-9))

    catalog = C.load_catalog()
    case = catalog.exercise("cas-eurusd")
    plan = R.plan(equity=8_000, risk_pct=0.75, entry=1.0745, stop=1.0705,
                  direction=R.LONG, target=1.0825,
                  spec=R.InstrumentSpec(contract_size=100_000, lot_step=0.01, pip_size=0.0001))
    answers = {s.id: s.answer for s in case.steps}
    check("case study: risk amount", close(plan.risk_amount, answers["montant"]))
    check("case study: distance in pips", close(plan.stop_distance_pips, answers["distance"], 1e-6))
    check("case study: loss per lot",
          close(plan.stop_distance * plan.position.value_per_point, answers["perte-par-lot"], 1e-6))
    check("case study: size", close(plan.position.lots, answers["taille"]))
    check("case study: ratio", close(plan.reward_to_risk, answers["ratio"], 1e-9))
    costs = 0.9 * 10 * plan.position.lots + 7 * plan.position.lots
    check("case study: costs", close(costs, answers["couts"], 1e-6), str(costs))


def test_structure_figures():
    """Path 2: the exercise answers are recomputed with the rules the lessons teach."""
    print("\nPath 2 figures")
    from sensitor.academy import structure as T
    catalog = C.load_catalog()
    ex = {s.id: s.answer for s in catalog.exercise("reperer-swings").steps}
    highs = [1.0810, 1.0824, 1.0841, 1.0835, 1.0827, 1.0819, 1.0806, 1.0814, 1.0828]
    lows = [1.0791, 1.0802, 1.0818, 1.0812, 1.0801, 1.0789, 1.0776, 1.0783, 1.0797]
    found = T.swings(highs, lows)
    tops = [s for s in found if s.kind == T.HIGH]
    bottoms = [s for s in found if s.kind == T.LOW]
    check("exactly one swing high and one swing low", len(tops) == 1 and len(bottoms) == 1, str(found))
    check("swing high: bar and price", tops[0].index + 1 == ex["sommet-bougie"]
          and close(tops[0].price, ex["sommet-prix"]))
    check("swing low: bar", bottoms[0].index + 1 == ex["creux-bougie"])
    check("swing low: confirmed at the close of bar 9", bottoms[0].confirmed_at + 1 == ex["confirmation"])
    check("amplitude in pips", close((tops[0].price - bottoms[0].price) / 0.0001, ex["amplitude"], 1e-6))

    quiz = catalog.quiz("check-swings")
    q = quiz.question("regle")
    five = [1.1010, 1.1024, 1.1037, 1.1031, 1.1019]
    hit = [s for s in T.swings(five, [0.0] * 5) if s.kind == T.HIGH]
    check("check-swings: the third bar is the swing high", [s.index for s in hit] == [2]
          and q.correct_ids == {"troisieme"})
    final = catalog.quiz("structure-validation")
    lows5 = [1.2540, 1.2531, 1.2518, 1.2526, 1.2533]
    low_hit = [s for s in T.swings([9.0] * 5, lows5) if s.kind == T.LOW]
    check("validation quiz: the third bar is the swing low", [s.index for s in low_hit] == [2]
          and final.question("creux-swing").correct_ids == {"troisieme"})

    check("BOS on a close beyond, not at the level", T.is_break(1.0897, 1.0890, direction="up")
          and not T.is_break(1.0884, 1.0890, direction="up"))
    check("MSS lesson: 1,0855 breaks 1,0861 down", T.is_break(1.0855, 1.0861, direction="down"))
    check("BOS quiz option: close 1,3057 breaks 1,3050", T.is_break(1.3057, 1.3050, direction="up")
          and not T.is_break(1.3044, 1.3050, direction="up"))

    case = {s.id: s.answer for s in catalog.exercise("cas-gbpusd").steps}
    check("case: the key low is C3", close(case["creux-cle"], 1.2683))
    check("case: 12 pips below it", close((1.2683 - 1.2671) / 0.0001, case["ecart-mss"], 1e-6))
    check("case: lower high 23 pips under S3", close((1.2764 - 1.2741) / 0.0001, case["sommet-plus-bas"], 1e-6))
    check("case: invalidation 5 pips above it", close(1.2741 + 0.0005, case["invalidation"], 1e-9))
    plan = R.plan(equity=10_000, risk_pct=0.5, entry=1.2718, stop=case["invalidation"],
                  direction=R.SHORT, spec=R.InstrumentSpec(contract_size=100_000, lot_step=0.01,
                                                           pip_size=0.0001))
    check("case: 28 pips to the invalidation", close(plan.stop_distance_pips, case["distance"], 1e-6))
    check("case: 50 $ budget gives 0.17 lot", close(plan.risk_amount, 50)
          and close(plan.position.lots, case["taille"]))
    check("case: 47,60 $ effective risk", close(plan.position.effective_risk, 47.6, 1e-6))
    size = R.position_size(60, 0.0024, R.InstrumentSpec(contract_size=100_000, lot_step=0.01))
    check("validation quiz: 60 $ over 24 pips is 0.25 lot", close(size.lots, 0.25))

    for bad in (lambda: T.swings([1, 2], [1]), lambda: T.swings([1], [1], n=0),
                lambda: T.is_break(1, 1, direction="sideways")):
        check("structure helpers refuse bad input", raises(bad, ValueError))
    check("bars at the edges are never swings", T.swings([1, 9, 1], [5, 0, 5]) == [])
    check("equal highs are not a swing (strict rule)",
          not [s for s in T.swings([1, 2, 5, 5, 2, 1], [0] * 6) if s.kind == T.HIGH])


def test_liquidity_figures():
    """Path 3: equal levels, sweeps and the XAUUSD case, recomputed with the lesson rules."""
    print("\nPath 3 figures")
    from sensitor.academy import structure as T
    catalog = C.load_catalog()
    ex = {s.id: s.answer for s in catalog.exercise("egalites-tolerance").steps}
    tops = [1.0942, 1.0915, 1.0944, 1.0928, 1.0941]
    groups = T.equal_levels(tops, 0.0003)
    check("three equal highs: S1, S3, S5", groups == [[0, 2, 4]], str(groups))
    group = [tops[i] for i in groups[0]]
    check("exercise: group size", len(group) == ex["nombre"])
    check("exercise: reference is the highest", close(max(group), ex["reference"]))
    check("exercise: 3 pips spread", close((max(group) - min(group)) / 0.0001, ex["ecart"], 1e-6))
    check("exercise: 7 pips beyond", close((1.0951 - max(group)) / 0.0001, ex["depassement"], 1e-6))
    check("exercise: close 6 pips back", close((max(group) - 1.0938) / 0.0001, ex["retour"], 1e-6))
    check("lesson example: 1,0928 sits outside a 3 pip band",
          T.equal_levels([1.0942, 1.0944, 1.0928], 0.0003) == [[0, 1]])

    check("1,0951 / 1,0938 sweeps 1,0944", T.is_sweep(1.0951, 1.0930, 1.0938, 1.0944, side="above"))
    check("a close at 1,0947 is a break, not a sweep",
          not T.is_sweep(1.0951, 1.0930, 1.0947, 1.0944, side="above")
          and T.is_break(1.0947, 1.0944, direction="up"))
    check("sweep below a level of lows", T.is_sweep(1.2, 1.0990, 1.1003, 1.1000, side="below")
          and not T.is_sweep(1.2, 1.1001, 1.1003, 1.1000, side="below"))
    check("false break lesson: 1,0943 closes back under 1,0944",
          not T.is_break(1.0943, 1.0944, direction="up"))
    check("confirmed break: 1,0949 and 1,0956 hold",
          all(T.is_break(c, 1.0944, direction="up") for c in (1.0947, 1.0949, 1.0956)))

    case = {s.id: s.answer for s in catalog.exercise("cas-xauusd").steps}
    gold = [2412.40, 2398.10, 2412.90, 2405.00]
    check("XAUUSD: the two tops are equal within 1 $", T.equal_levels(gold, 1.0) == [[0, 2]])
    check("XAUUSD: 0,50 $ between them", close(2412.90 - 2412.40, case["ecart"], 1e-9))
    check("XAUUSD: 2,40 $ beyond", close(2415.30 - 2412.90, case["depassement"], 1e-9))
    check("XAUUSD: close 2,10 $ back", close(2412.90 - 2410.80, case["retour"], 1e-9))
    check("XAUUSD: the sweep bar is a sweep", T.is_sweep(2415.30, 2408.0, 2410.80, 2412.90, side="above"))
    check("XAUUSD: invalidation 0,50 $ above the sweep high", close(2415.30 + 0.50, case["invalidation"], 1e-9))
    gold_spec = R.InstrumentSpec(contract_size=100, lot_step=0.01)
    plan = R.plan(equity=10_000, risk_pct=1, entry=2409.30, stop=case["invalidation"],
                  direction=R.SHORT, spec=gold_spec)
    check("XAUUSD: 6,50 $ to the invalidation", close(abs(2409.30 - case["invalidation"]), case["distance"], 1e-9))
    check("XAUUSD: 100 $ budget gives 0.15 lot", close(plan.risk_amount, 100)
          and close(plan.position.lots, case["taille"]))
    check("XAUUSD: 97,50 $ effective risk", close(plan.position.effective_risk, 97.5, 1e-6))
    ten = R.position_size(100, 6.50, R.InstrumentSpec(contract_size=10, lot_step=0.01))
    check("quiz: a 10 oz contract gives 1.53 lot", close(ten.lots, 1.53))
    final = catalog.quiz("liquidite-validation")
    taught = {lesson.id for lesson in catalog.course("liquidite-et-scenarios").lessons} - {"recap-liquidite"}
    check("validation quiz: covers every path 3 lesson", {q.lesson_id for q in final.questions} == taught)

    for bad in (lambda: T.equal_levels([1, 2], -1), lambda: T.is_sweep(1, 0, 1, 1, side="up")):
        check("liquidity helpers refuse bad input", raises(bad, ValueError))


def test_zone_figures():
    """Path 4: FVGs, order blocks, OTE and the GBPUSD case, recomputed with the lesson rules."""
    print("\nPath 4 figures")
    from sensitor.academy import zones as Z
    catalog = C.load_catalog()
    pip = 0.0001

    ex = {s.id: s.answer for s in catalog.exercise("fvg-reperage").steps}
    highs = [1.0832, 1.0861, 1.0874, 1.0870, 1.0858]
    lows = [1.0818, 1.0829, 1.0846, 1.0851, 1.0838]
    gaps = Z.fair_value_gaps(highs, lows)
    check("exactly one FVG in the series", len(gaps) == 1 and gaps[0].kind == Z.BULLISH, str(gaps))
    gap = gaps[0]
    check("FVG exercise: middle bar", gap.index + 1 == ex["bougie"])
    check("FVG exercise: bounds", close(gap.low, ex["bas"]) and close(gap.high, ex["haut"]))
    check("FVG exercise: 14 pips", close(gap.size / pip, ex["taille"], 1e-6))
    check("FVG exercise: midpoint", close(gap.midpoint, ex["milieu"], 1e-9))
    check("FVG exercise: 57 % filled", abs(Z.filled_fraction(gap, 1.0838) * 100 - ex["remplissage"]) < 0.6)
    check("FVG quiz: 1,0839 fills half", close(Z.filled_fraction(gap, 1.0839), 0.5, 1e-9))
    check("lesson 1: touching wicks leave no gap", Z.fair_value_gaps([1.0832, 1.0861, 1.0874],
                                                                    [1.0818, 1.0829, 1.0832]) == [])
    bear = Z.fair_value_gaps([1.2720, 1.2715, 1.2698], [1.2710, 1.2690, 1.2680])
    check("validation quiz: bearish FVG 1,2698 to 1,2710", len(bear) == 1 and bear[0].kind == Z.BEARISH
          and close(bear[0].low, 1.2698) and close(bear[0].high, 1.2710))
    check("validation quiz: 1,2707 fills 75 %", close(Z.filled_fraction(bear[0], 1.2707), 0.75, 1e-9))

    case = {s.id: s.answer for s in catalog.exercise("cas-zone-entree").steps}
    opens = [1.2652, 1.2646, 1.2634, 1.2668, 1.2697]
    highs = [1.2658, 1.2650, 1.2671, 1.2702, 1.2730]
    lows = [1.2641, 1.2630, 1.2632, 1.2664, 1.2690]
    closes = [1.2645, 1.2634, 1.2668, 1.2697, 1.2722]
    from sensitor.academy import structure as T
    check("case: C2 sweeps the equal lows", T.equal_levels([1.2633, 1.2632], 0.0002) == [[0, 1]]
          and T.is_sweep(highs[1], lows[1], closes[1], 1.2632, side="below"))
    check("case: C4 breaks the swing high on the close", T.is_break(closes[3], 1.2685, direction="up")
          and not T.is_break(closes[2], 1.2685, direction="up"))
    ob = Z.order_block(opens, closes, 2, direction=Z.BULLISH)
    check("case: the order block is C2, 1,2630 to 1,2650", ob == 1 and close(lows[ob], 1.2630)
          and close(highs[ob], 1.2650))
    check("lesson 3: body-only variant 1,2634 to 1,2646",
          close(min(opens[ob], closes[ob]), 1.2634) and close(max(opens[ob], closes[ob]), 1.2646))
    fvgs = Z.fair_value_gaps(highs, lows)
    check("case: two FVGs, 1,2650-1,2664 and 1,2671-1,2690",
          [(round(g.low, 4), round(g.high, 4)) for g in fvgs] == [(1.2650, 1.2664), (1.2671, 1.2690)])
    ote = Z.ote_zone(1.2630, 1.2730)
    check("case: OTE high", close(ote[1], case["ote-haut"], 1e-9))
    check("case: OTE low", close(ote[0], case["ote-bas"], 1e-9))
    common = Z.overlap(ote, (fvgs[0].low, fvgs[0].high))
    check("case: 13 pips of overlap", close((common[1] - common[0]) / pip, case["chevauchement"], 1e-6))
    check("case: the upper FVG and the order block miss the OTE zone",
          Z.overlap(ote, (fvgs[1].low, fvgs[1].high)) is None and Z.overlap(ote, (1.2630, 1.2650)) is None)
    check("case: entry at the FVG midpoint, inside the zone", close(fvgs[0].midpoint, case["entree"], 1e-9)
          and common[0] <= case["entree"] <= common[1])
    plan = R.plan(equity=10_000, risk_pct=0.5, entry=case["entree"], stop=1.2630 - 0.0005,
                  direction=R.LONG, target=1.2730,
                  spec=R.InstrumentSpec(contract_size=100_000, lot_step=0.01, pip_size=pip))
    check("case: 32 pips to the invalidation", close(plan.stop_distance_pips, case["distance"], 1e-6))
    check("case: 0.15 lot", close(plan.risk_amount, 50) and close(plan.position.lots, case["taille"]))
    check("case: 48 $ effective risk", close(plan.position.effective_risk, 48, 1e-6))
    check("case: 2.28R", abs(plan.reward_to_risk - case["ratio"]) < 0.006)
    check("case lesson: 45 pips at 0.15 lot risk 67,50 $", close(45 * 10 * 0.15, 67.5))
    check("case quiz: 0.16 lot would risk 51,20 $", close(32 * 10 * 0.16, 51.2))

    ote_ex = {s.id: s.answer for s in catalog.exercise("ote-calcul").steps}
    gold = Z.ote_zone(2380, 2420)
    check("OTE exercise: 50 %", close(Z.retracement(2380, 2420, 0.5), ote_ex["cinquante"]))
    check("OTE exercise: bounds 2 388,40 to 2 395,20", close(gold[0], ote_ex["ote-bas"], 1e-9)
          and close(gold[1], ote_ex["ote-haut"], 1e-9))
    check("OTE exercise: 6,80 $ wide", close(gold[1] - gold[0], ote_ex["largeur"], 1e-9))
    down = Z.ote_zone(2450, 2410)
    check("OTE exercise: bearish leg 2 434,80 to 2 441,60", close(down[0], 2434.8, 1e-9)
          and close(down[1], ote_ex["vente-haut"], 1e-9))
    check("OTE middle 70,5 % at 2 391,80", close(Z.retracement(2380, 2420, Z.OTE_MIDDLE), 2391.8, 1e-9))
    eur = Z.ote_zone(1.0800, 1.0900)
    check("lesson 4: EURUSD OTE 1,0821 to 1,0838", close(eur[0], 1.0821, 1e-9) and close(eur[1], 1.0838, 1e-9))
    check("lesson 4: 70,5 % at 1,08295", close(Z.retracement(1.0800, 1.0900, 0.705), 1.08295, 1e-9))
    common = Z.overlap(eur, (1.0826, 1.0845))
    check("lesson 5: overlap 1,0826 to 1,0838, 12 pips", close(common[0], 1.0826) and close(common[1], 1.0838)
          and close((common[1] - common[0]) / pip, 12, 1e-6))

    final = catalog.quiz("zones-validation")
    taught = {lesson.id for lesson in catalog.course("zones-et-entrees").lessons} - {"recap-zones"}
    check("validation quiz: covers every path 4 lesson", {q.lesson_id for q in final.questions} == taught)
    for bad in (lambda: Z.fair_value_gaps([1, 2], [1]), lambda: Z.ote_zone(1, 2, 0.8, 0.6),
                lambda: Z.order_block([1], [1], 0, direction="up"),
                lambda: Z.filled_fraction(Z.Gap(Z.BULLISH, 1, 2.0, 2.0), 2.0)):
        check("zone helpers refuse bad input", raises(bad, ValueError))
    check("order block: none when no opposite bar", Z.order_block([1, 2], [2, 3], 1, direction=Z.BULLISH) is None)


def test_psychology_figures():
    """Path 6: streaks, small samples, the chased entry, the revenge trade and overtrading, recomputed."""
    print("\nPath 6 figures")
    from sensitor.academy import expectancy as X
    catalog = C.load_catalog()
    check("lesson 1: 50 % at 1.5R is +0.25R", close(X.expectancy_r(0.5, 1.5), 0.25))
    check("lesson 1: five losses in five trades, 3.1 %", round(R.streak_probability(5, 5, 0.5) * 100, 1) == 3.1)
    streaks = [round(R.streak_probability(n, 5, 0.5) * 100, 1) for n in (10, 20, 50, 100, 200)]
    check("lesson 1 figure: 10.9, 25.0, 55.2, 81.0, 96.6 %", streaks == [10.9, 25.0, 55.2, 81.0, 96.6], str(streaks))

    for (w, n), (lo, hi) in {(4, 5): (38, 96), (2, 5): (12, 77), (52, 100): (42, 62)}.items():
        i = X.win_rate_interval(w, n)
        check(f"lesson 2: {w}/{n} interval {lo} to {hi} %", round(i.low * 100) == lo and round(i.high * 100) == hi,
              f"{i.low:.4f} {i.high:.4f}")
    check("validation quiz: 70 % sits inside the 2/5 interval", X.win_rate_interval(2, 5).high > 0.70)
    check("lesson 2: 40 % sits inside the 4/5 interval", X.win_rate_interval(4, 5).low < 0.40)

    spec = R.InstrumentSpec(contract_size=100_000, lot_step=0.01, pip_size=0.0001)
    planned = R.plan(equity=10_000, risk_pct=0.5, entry=1.2657, stop=1.2625, direction=R.LONG,
                     target=1.2730, spec=spec)
    chased = R.plan(equity=10_000, risk_pct=0.5, entry=1.2700, stop=1.2625, direction=R.LONG,
                    target=1.2730, spec=spec)
    check("FOMO: 75 pips of risk, 0.40R", close(chased.stop_distance_pips, 75, 1e-6)
          and close(chased.reward_to_risk, 0.4, 1e-9))
    check("FOMO: break-even 30 % against 71 %", round(X.breakeven_win_rate(planned.reward_to_risk) * 100) == 30
          and round(X.breakeven_win_rate(chased.reward_to_risk) * 100) == 71)
    check("FOMO: 0.06 lot, 45 $ for the chased entry", close(chased.position.lots, 0.06)
          and close(chased.position.effective_risk, 45, 1e-6))

    rev = {s.id: s.answer for s in catalog.exercise("revanche-serie").steps}
    three = X.equity_path(10_000, [-1, -1, -1], 1)
    check("revenge: 9 702,99 after three losses", close(round(three[-1], 2), rev["apres-trois"]))
    check("revenge: 2,97 % drawdown", abs(X.max_drawdown(three).pct - rev["drawdown-trois"]) < 0.006)
    disc = three[-1] * 0.99
    revenge = three[-1] * 0.97
    check("revenge: 9 605,96 at 1 %", close(round(disc, 2), rev["discipline"]))
    check("revenge: 9 411,90 at 3 %", close(round(revenge, 2), rev["revanche"]))
    check("revenge: 5,88 % drawdown", abs((1 - revenge / 10_000) * 100 - rev["drawdown-revanche"]) < 0.006)
    check("revenge: 6,25 % to recover", abs(R.recovery_needed(1 - revenge / 10_000) * 100 - rev["recuperation"]) < 0.006)
    check("revenge conclusion: 97,03 $ and 291,09 $", close(round(three[-1] * 0.01, 2), 97.03)
          and close(round(three[-1] * 0.03, 2), 291.09))

    cost = {s.id: s.answer for s in catalog.exercise("cout-suractivite").steps}
    check("overtrading: +0,22R net", close(0.30 - 0.08, cost["net-a"], 1e-9))
    check("overtrading: +1,10R", close(5 * (0.30 - 0.08), cost["total-a"], 1e-9))
    check("overtrading: -0,06R net", close(0.02 - 0.08, cost["net-marginal"], 1e-9))
    check("overtrading: -0,90R", close(15 * (0.02 - 0.08), cost["total-marginal"], 1e-9))
    check("overtrading: +0,20R for the week", close(cost["total-a"] + cost["total-marginal"], cost["semaine"], 1e-9))
    check("overtrading: 45 $", close((cost["total-a"] - cost["semaine"]) * 50, cost["difference"], 1e-9))

    final = catalog.quiz("psychologie-validation")
    taught = {lesson.id for lesson in catalog.course("decider-sous-incertitude").lessons} - {"recap-psychologie"}
    check("validation quiz: covers every path 6 lesson", {q.lesson_id for q in final.questions} == taught)


def test_backtest_figures():
    """Path 7: the 20-trade series, intervals, multiple testing and the 120-trade case, recomputed."""
    print("\nPath 7 figures")
    from sensitor.academy import backtest as B
    from sensitor.academy import expectancy as X
    catalog = C.load_catalog()

    ex = {s.id: s.answer for s in catalog.exercise("backtest-serie").steps}
    series = [2.0, -1, -1, 1.5, -1, 2.5, -1, -1, -1, 2.0, -1, 1.8, -1, -1, 2.2, -1, -1, 1.5, -1, -1]
    s20 = B.summarize(series, cost_r=0.05)
    check("20 trades: 7 wins, 35 %", s20.wins == ex["gains"] and close(s20.win_rate * 100, ex["taux"], 1e-9))
    check("20 trades: +0,5R total", close(sum(series), ex["total"], 1e-9))
    check("20 trades: +0,025R gross, -0,025R net", close(s20.gross_expectancy, ex["brute"], 1e-9)
          and close(s20.net_expectancy, ex["nette"], 1e-9))
    check("20 trades: profit factor 1,04", abs(s20.profit_factor - ex["profit-factor"]) < 0.005)

    iv = {s.id: s.answer for s in catalog.exercise("intervalle-esperance").steps}
    check("interval: SE 0,19 on 40 trades", abs(B.standard_error(1.2, 40) - iv["se-40"]) < 0.005)
    i40, i400 = B.mean_interval(0.20, 1.2, 40), B.mean_interval(0.20, 1.2, 400)
    check("interval: -0,17 to 0,57 on 40", abs(i40.low - iv["bas-40"]) < 0.006 and abs(i40.high - iv["haut-40"]) < 0.006)
    check("interval: SE 0,06 and +0,08 on 400", close(B.standard_error(1.2, 400), iv["se-400"], 1e-9)
          and abs(i400.low - iv["bas-400"]) < 0.006)
    check("interval: 554 trades for 0,10R", B.trades_needed(1.2, 0.10) == iv["trades-requis"])
    figure = [(round(B.mean_interval(0.20, 1.2, n).low, 2), round(B.mean_interval(0.20, 1.2, n).high, 2))
              for n in (40, 100, 400, 1000)]
    check("lesson 4 figure: zero inside on 40 and 100, outside on 400 and 1 000",
          [lo <= 0 for lo, _ in figure] == [True, True, False, False], str(figure))

    chances = [round(B.false_discovery_chance(k) * 100, 1) for k in (1, 5, 10, 20, 50, 100)]
    check("lesson 5: 5,0 / 22,6 / 40,1 / 64,2 / 92,3 / 99,4 %", chances == [5.0, 22.6, 40.1, 64.2, 92.3, 99.4], str(chances))
    check("lesson 5: 4 x 5 x 5 = 100 combinations", 4 * 5 * 5 == 100)

    is_iv, oos_iv = B.mean_interval(0.35, 1.3, 300), B.mean_interval(0.08, 1.3, 100)
    check("lesson 6: in sample +0,20 to +0,50", round(is_iv.low, 2) == 0.20 and round(is_iv.high, 2) == 0.50)
    check("lesson 6: out of sample -0,17 to +0,33", round(oos_iv.low, 2) == -0.17 and round(oos_iv.high, 2) == 0.33)
    check("lesson 6: 77 % degradation", round(B.degradation(0.35, 0.08) * 100) == 77)

    case = {s.id: s.answer for s in catalog.exercise("cas-backtest-120").steps}
    built = B.summarize([1.9] * 52 + [-1] * 68, cost_r=0.07)
    check("case: 43,3 %", abs(built.win_rate * 100 - case["taux"]) < 0.06)
    check("case: +0,26R gross, +0,19R net", abs(built.gross_expectancy - case["brute"]) < 0.005
          and abs(built.net_expectancy - case["nette"]) < 0.005)
    check("case: profit factor 1,45", abs(built.profit_factor - case["profit-factor"]) < 0.006)
    check("case: the deviation quoted is 1,44R", round(built.sd, 2) == 1.44)
    net = B.mean_interval(built.net_expectancy, 1.44, 120)
    check("case: interval -0,07 to +0,44, zero inside", abs(net.low - case["bas"]) < 0.006
          and round(net.high, 2) == 0.44 and net.low < 0)
    wr = X.win_rate_interval(52, 120)
    check("case: win rate 35 % to 52 %", round(wr.low * 100) == 35 and round(wr.high * 100) == 52)
    check("case: break-even 34,5 %", abs(X.breakeven_win_rate(1.9) * 100 - case["seuil"]) < 0.06)
    oos = B.summarize([1.8] * 20 + [-1] * 30, cost_r=0.07)
    check("case: +0,05R out of sample", close(oos.net_expectancy, case["oos"], 1e-9))
    check("case: 73 % degradation", abs(B.degradation(built.net_expectancy, oos.net_expectancy) * 100
                                        - case["degradation"]) < 0.6)

    final = catalog.quiz("backtest-validation")
    taught = {lesson.id for lesson in catalog.course("tester-une-strategie").lessons} - {"recap-backtest"}
    check("validation quiz: covers every path 7 lesson", {q.lesson_id for q in final.questions} == taught)
    for bad in (lambda: B.summarize([1.0]), lambda: B.summarize([1, -1], cost_r=-0.1),
                lambda: B.trades_needed(0, 0.1), lambda: B.false_discovery_chance(0),
                lambda: B.degradation(0, 0.1), lambda: B.standard_error(1, 1)):
        check("backtest helpers refuse bad input", raises(bad, ValueError))
    check("no loss, no profit factor", B.summarize([1, 2]).profit_factor is None)


def test_macro_figures():
    """Path 8: every figure of the lessons and exercises, recomputed from the data and macro.py."""
    print("\nPath 8 figures")
    from datetime import date, time
    from sensitor.academy import macro as MA
    catalog = C.load_catalog()
    course = catalog.course("trader-l-actualite")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}

    rows = catalog.dataset("emploi-etats-unis").rows
    by_year = {}
    for r in rows:
        by_year.setdefault(r["mois"][:4], []).append(r["creations"])
    means = {y: round(sum(v) / len(v)) for y, v in by_year.items()}
    check("jobs: +210 000, +122 000, +10 000 and +68 000 a month", means == {"2023": 210, "2024": 122, "2025": 10, "2026": 68}
          and len(by_year["2026"]) == 9, str(means))
    negative = [r["mois"] for r in rows if r["mois"] >= "2025-01" and r["creations"] < 0]
    check("jobs: seven negative months since January 2025", len(negative) == 7, str(negative))
    unemployment = {r["mois"][:7]: r["chomage"] for r in catalog.dataset("chomage-etats-unis").rows}
    known = {m: v for m, v in unemployment.items() if v is not None}
    check("unemployment: 14,8 % in April 2020, the series high since 1948",
          max(known.values()) == 14.8 and known["2020-04"] == 14.8 and min(unemployment) == "1948-01")
    check("unemployment: the previous record, 10,8 % in December 1982",
          max(v for m, v in known.items() if m < "2020") == 10.8 and known["1982-12"] == 10.8)
    since = [v for m, v in known.items() if m >= "2022-01"]
    check("unemployment: between 3,4 % and 4,5 % since 2022", min(since) == 3.4 and max(since) == 4.5)
    check("unemployment: October 2025 missing, not interpolated", unemployment["2025-10"] is None)
    check("lesson 2 quotes them", all(t in text["indicateurs-majeurs"] for t in
          ("+210 000", "+122 000", "+10 000", "+68 000", "14,8 %", "10,8 %", "3,4 % et 4,5 %")))

    two = {r["mois"][:7]: (r["deux_ans"], r["fed_funds"]) for r in catalog.dataset("taux-2-ans-fed").rows}
    check("2 years: 0,20 % in June 2021, 1,44 % in February 2022, funds at 0,08 %",
          two["2021-06"] == (0.20, 0.08) and two["2022-02"] == (1.44, 0.08))
    check("2 years: the first hike shows in March 2022", two["2022-02"][1] == 0.08 and two["2022-03"][1] > 0.08)
    peak = max((v[0], m) for m, v in two.items() if "2023" <= m < "2025")
    check("2 years: peak of 5,07 % in October 2023", peak == (5.07, "2023-10"))
    check("2 years: 3,97 % in August 2024 with funds at 5,33 %, the cut shows in September",
          two["2024-08"] == (3.97, 5.33) and two["2024-09"][1] < 5.33)
    check("2 years: 4,65 % against 3,75 % in September 2026, 0,90 point",
          two["2026-09"] == (4.65, 3.75) and round(two["2026-09"][0] - two["2026-09"][1], 2) == 0.90)

    curve = catalog.dataset("courbe-taux-us").rows
    runs = MA.inverted_runs([r["mois"][:7] for r in curve], [r["ecart"] for r in curve])
    check("curve: twelve inversions since 1977", len(runs) == 12 and curve[0]["mois"].startswith("1977"), str(len(runs)))
    longest = max(runs, key=lambda r: r.months)
    check("curve: the longest, 26 months, July 2022 to August 2024",
          (longest.start, longest.end, longest.months) == ("2022-07", "2024-08", 26))
    check("curve: low of -2,13 points in March 1980", min((r["ecart"], r["mois"]) for r in curve) == (-2.13, "1980-03-01"))
    check("curve: a single month in June 1998", any(r.start == r.end == "1998-06" for r in runs))
    check("curve: every spread is 10 years minus 2 years",
          all(abs(r["ecart"] - MA.curve_spread(r["dix_ans"], r["deux_ans"])) < 0.006 for r in curve))
    check("curve: the -0,93 of July 2023 is the low since 2000",
          min((r["ecart"], r["mois"]) for r in curve if r["mois"] >= "2000") == (-0.93, "2023-07-01"))

    cv = ex("courbe-taux-reel")
    by_month = {r["mois"][:7]: r for r in curve}
    us = {r["mois"][:7]: r["inflation"] for r in catalog.dataset("inflation-taux-etats-unis").rows}
    check("exercise curve: -0,93 and +0,34", close(MA.curve_spread(3.90, 4.83), cv["ecart-2023"])
          and close(MA.curve_spread(4.99, 4.65), cv["ecart-2026"])
          and (by_month["2023-07"]["dix_ans"], by_month["2023-07"]["deux_ans"]) == (3.90, 4.83)
          and (by_month["2026-09"]["dix_ans"], by_month["2026-09"]["deux_ans"]) == (4.99, 4.65))
    check("exercise curve: real rate 0,95 with the 3,7 % of the inflation series",
          us["2026-09"] == 3.7 and close(MA.real_rate(4.65, us["2026-09"]), cv["reel"]))
    check("exercise curve: 26 months", cv["duree"] == longest.months)

    se = ex("surprise-emploi")
    check("exercise jobs: -110, -1,47, -40, -150, +0,1", MA.surprise(40, 150) == se["surprise"]
          and abs(-110 / 75 - se["normalisee"]) < 0.005 and 80 - 120 == se["revision"]
          and se["surprise"] + se["revision"] == se["total"] and close(MA.surprise(4.4, 4.3), se["chomage"], 1e-9))
    check("standardized surprise: divided by the sample deviation",
          close(MA.standardized_surprise(40, 150, [75, -75]), -110 / math.sqrt(11250)))
    check("monthly changes: a gap stays a gap", MA.monthly_changes([1, 3, None, 4]) == [2, None, None])

    ta = ex("taux-anticipes")
    check("exercise rates: 4,20 %, -0,175, 0,70 cut, 70 %", close(MA.implied_rate(95.80), ta["implicite"], 1e-9)
          and close(MA.implied_rate(95.80) - 4.375, ta["ecart"], 1e-9)
          and close(abs(MA.priced_moves(MA.implied_rate(95.80), 4.375)), ta["quarts"], 1e-9)
          and close(MA.move_probability(MA.implied_rate(95.80), 4.375) * 100, ta["probabilite"], 1e-9))
    check("probability: capped at 100 %", MA.move_probability(3.9, 4.375) == 1.0)

    ma = ex("mouvement-attendu")
    move = MA.expected_move(1.0850, 12, 1) * 10_000
    check("exercise move: 68 pips, 136 for two deviations", round(move) == ma["mouvement"] and 2 * ma["mouvement"] == ma["fourchette"])
    check("exercise move: 1,00 lot, 0,40 lot, 500 dollars", close(200 / (20 * 10), ma["taille-normale"])
          and close(MA.event_size(200, 40, 10, 10), ma["taille-publication"])
          and close(MA.loss_at_stop(1.0, 40, 10, 10), ma["perte"]))
    check("lesson 6 quotes the 68 pips", "**68 pips**" in text["volatilite-evenementielle"])

    case = ex("cas-inflation-us")
    spec = R.InstrumentSpec(contract_size=1, lot_step=0.1)
    sized = R.position_size(125, 30 + 5, spec)
    usual = R.position_size(125, 12, spec)
    check("case: +0,2 surprise, +2,0 deviations, 75 points", close(MA.surprise(0.5, 0.3), case["surprise"], 1e-9)
          and close(0.2 / 0.1, case["normalisee"], 1e-9) and round(MA.expected_move(6000, 24, 1)) == case["mouvement"])
    check("case: 3,5 contracts for 122,50 dollars", close(sized.lots, case["taille"]) and close(sized.effective_risk, case["risque"]))
    check("case: the usual 10,4 contracts would lose 2,9 times the budget", close(usual.lots, 10.4)
          and round(MA.loss_at_stop(usual.lots, 30, 5, 1) / 125, 1) == case["multiple"])
    check("case: 90 points, beyond one deviation, inside two", 75 < 90 < 2 * MA.expected_move(6000, 24, 1))

    paris = lambda d, h=8, m=30: MA.release_time_paris(d, h, m)
    check("calendar: 8 h 30 in Washington is 14 h 30 in Paris most weeks",
          paris(date(2026, 1, 9)) == time(14, 30) and paris(date(2026, 11, 6)) == time(14, 30))
    check("calendar: 13 h 30 on Friday 13 March and Friday 30 October 2026",
          paris(date(2026, 3, 13)) == time(13, 30) and paris(date(2026, 10, 30)) == time(13, 30)
          and date(2026, 3, 13).weekday() == 4 and date(2026, 10, 30).weekday() == 4)
    check("calendar: the Fed at 20 h 00, 19 h 00 in the shifted weeks",
          paris(date(2026, 6, 17), 14, 0) == time(20, 0) and paris(date(2026, 3, 18), 14, 0) == time(19, 0))
    check("expected move: refuses a zero horizon", raises(lambda: MA.expected_move(100, 10, 0), ValueError))
    check("the course is in the trading universe", catalog.universe_of(course) == "trading")


def test_bitcoin_course_figures():
    """« Bitcoin : origines et fonctionnement » : the white paper's table, the exercises, the figures."""
    print("\nBitcoin course figures")
    import datetime as dt
    from sensitor.academy import bitcoin as B
    from sensitor.academy import hashing as H
    catalog = C.load_catalog()
    course = catalog.course("bitcoin-fonctionnement")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}

    paper = {0.1: [1.0, 0.2045873, 0.0509779, 0.0131722, 0.0034552, 0.0009137, 0.0002428, 0.0000647,
                   0.0000173, 0.0000046, 0.0000012],
             0.3: {0: 1.0, 5: 0.1773523, 10: 0.0416605, 15: 0.0101008, 20: 0.0024804, 25: 0.0006132,
                   30: 0.0001522, 35: 0.0000379, 40: 0.0000095, 45: 0.0000024, 50: 0.0000006}}
    check("white paper, q = 0,1: z = 0 to 10, to seven decimals",
          [round(B.attacker_success(0.1, z), 7) for z in range(11)] == paper[0.1])
    check("white paper, q = 0,3: z = 0 to 50 by 5, to seven decimals",
          all(round(B.attacker_success(0.3, z), 7) == v for z, v in paper[0.3].items()))
    check("white paper: confirmations for P < 0,1 %",
          {q: B.confirmations_needed(q) for q in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45)}
          == {0.10: 5, 0.15: 8, 0.20: 11, 0.25: 15, 0.30: 24, 0.35: 41, 0.40: 89, 0.45: 340})
    check("a majority always catches up", B.attacker_success(0.5, 6) == 1.0
          and raises(lambda: B.confirmations_needed(0.5), ValueError))
    check("lesson 6 quotes 20,5 %, 0,09 %, 0,024 % and 13,2 %",
          all(t in text["consensus-securite"] for t in ("20,5 %", "0,09 %", "0,024 %", "13,2 %"))
          and round(B.attacker_success(0.3, 6) * 100, 1) == 13.2)
    rows = catalog.dataset("rattrapage-attaquant").rows
    check("the chart's rows come from the same formula", len(rows) == 25
          and close(rows[6]["q10"], B.attacker_success(0.1, 6)) and close(rows[24]["q30"], B.attacker_success(0.3, 24)))

    ca = ex("confirmations-attaquant")
    check("exercise confirmations: 0,024 %, 5, 50 minutes, 4 hours",
          abs(B.attacker_success(0.1, 6) * 100 - ca["six"]) < 0.0006 and B.confirmations_needed(0.1) == ca["seuil-10"]
          and ca["seuil-10"] * 10 == ca["duree"] and B.confirmations_needed(0.3) * 10 / 60 == ca["seuil-30"])

    ad = ex("ajustement-difficulte")
    check("retarget: 14 days, x 1,111, +11,1 %, 156 200 billion",
          B.RETARGET_SECONDS / 86400 == ad["duree"] and abs(B.retarget(1, 12.6 * 86400) - ad["facteur"]) < 0.0006
          and abs((B.retarget(1, 12.6 * 86400) - 1) * 100 - ad["hausse"]) < 0.06
          and abs(B.retarget(140_580, 12.6 * 86400) - ad["nouvelle"]) < 60)
    check("retarget: capped at a factor of four", B.retarget(100, 1) == 400 and B.retarget(100, 10 ** 9) == 25)
    check("a 2 % miner: 500 minutes, 2,88 blocks a day", B.minutes_between_blocks(0.02) == ad["minutes"]
          and close(24 * 60 / B.TARGET_SPACING_MINUTES * 0.02, ad["par-jour"]))
    check("lesson 5: 86 390 to 140 580 billion is +63 %, about 6 x 10^23 tries a block",
          round((140_580 / 86_390 - 1) * 100) == 63 and round(140_577_680_051_919.62 * 2 ** 32 / 1e23) == 6
          and "63 %" in text["preuve-de-travail"])

    tx = ex("transaction-utxo")
    fee = B.fee_sats(209, 12)
    check("exercise transaction: 0,8 in, 2 508 sats, change 0,19997492, 0,2 lost without change",
          close(0.5 + 0.3, tx["entrees"]) and fee == tx["frais-sats"] and close(fee / B.COIN, tx["frais-btc"])
          and (80_000_000 - 60_000_000 - fee) / B.COIN == tx["monnaie"] and close(0.8 - 0.6, tx["oubli"]))

    em = ex("emission-halving")
    check("exercise issuance: 3,125, 450 a day, 164 250 a year, 0,82 %",
          B.block_subsidy(840_000) / B.COIN == em["recompense"] and em["recompense"] * 144 == em["par-jour"]
          and em["par-jour"] * 365 == em["par-an"]
          and abs(em["par-an"] / (B.supply_after(971_911) / B.COIN) * 100 - em["taux"]) < 0.006)
    check("exercise issuance: 1,5625 next, 542 days, around 11 April 2028",
          B.block_subsidy(1_050_000) / B.COIN == em["suivante"] and round((1_050_000 - 971_911) / 144) == em["jours"]
          and B.estimated_date(971_911, dt.date(2026, 10, 17), 1_050_000) == dt.date(2028, 4, 11))
    last = max(h for h in range(0, 64 * B.HALVING_INTERVAL, B.HALVING_INTERVAL) if B.block_subsidy(h) > 0) + B.HALVING_INTERVAL - 1
    check("the last fraction around 2140, block 6 929 999", last == 6_929_999
          and B.estimated_date(971_911, dt.date(2026, 10, 17), last).year == 2140 and "6 929 999" in text["emission-halvings"])
    check("lesson 7 quotes 20 099 725 BTC and 95,7 %", B.supply_after(971_911) == 20_099_725 * B.COIN
          and round(B.supply_after(971_911) / B.total_supply() * 100, 1) == 95.7 and "95,7 %" in text["emission-halvings"])

    check("SHA-256 of « abc », the FIPS 180-4 example",
          H.digest("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    mined = H.mine("Sensitor", 3)
    check("toy proof of work: three leading zeros, checked in one hash", mined.digest.startswith("000")
          and H.digest(f"Sensitor{mined.nonce}") == mined.digest and mined.tries == mined.nonce + 1)
    check("toy proof of work: refuses more than five zeros", raises(lambda: H.mine("x", 6), ValueError))
    honest = H.chain(["Alice paie Bob", "Bob paie Carol", "Carol paie Dan"])
    svg = catalog.figures["chaine-blocs.svg"]
    forged = H.digest(honest[0].digest + "Bob paie Eve" + "0")
    check("the chain figure prints the real digests", all(h.digest[:10] in svg for h in honest) and forged[:10] in svg
          and forged != honest[1].digest)
    check("bits: genesis 0x1d00ffff is difficulty 1", B.difficulty_from_bits(0x1D00FFFF) == 1.0
          and B.target_from_bits(0x1D00FFFF) == B.MAX_TARGET)
    net = catalog.dataset("reseau-bitcoin").rows
    headers = [{"height": r["hauteur"], "timestamp": r["horodatage"], "bits": r["bits"]} for r in net]
    headers.append({"height": net[-1]["hauteur_suivante"], "timestamp": net[-1]["horodatage_suivant"], "bits": 0})
    rebuilt = B.epoch_rows(headers)
    check("network: 482 complete periods, every one recomputed from its header",
          len(net) == len(rebuilt) == 482 and all(
              abs(a["difficulte"] / b["difficulte"] - 1) < 1e-5 and abs(a["jours"] - b["jours"]) < 0.006
              and abs(a["puissance"] / b["puissance"] - 1) < 1e-5 and a["date"] == b["date"]
              for a, b in zip(net, rebuilt)))
    check("network: periods follow each other, 2 016 blocks apart",
          all(n["hauteur_suivante"] - n["hauteur"] == 2016 and n["horodatage_suivant"] > n["horodatage"] for n in net)
          and all(a["hauteur_suivante"] == b["hauteur"] for a, b in zip(net, net[1:])))
    first = lambda level: next(r["date"][:7] for r in net if r["puissance"] >= level)
    peak = max(net, key=lambda r: r["puissance"])
    check("network: 1 EH/s in January 2016, 100 in January 2020, a high of about 1 116 on 16 October 2025",
          first(1) == "2016-01" and first(100) == "2020-01" and peak["date"] == "2025-10-16" and round(peak["puissance"]) == 1116)
    check("network: about 1 000 EH/s in early October 2026", net[-1]["date"] == "2026-10-03" and 950 < net[-1]["puissance"] < 1050)
    import statistics
    since2016 = [r["jours"] for r in net if r["date"] >= "2016"]
    longest = max((r for r in net if r["date"] >= "2013"), key=lambda r: r["jours"])
    by_date = {r["date"]: r for r in net}
    check("network: median of 13,7 days since 2016; 19,4 days from 13 June 2021, the longest since 2013",
          round(statistics.median(since2016), 1) == 13.7 and longest["date"] == "2021-06-13" and round(longest["jours"], 1) == 19.4)
    check("network: about 179 EH/s from 1 May 2021, about 98 from 3 July",
          round(by_date["2021-05-01"]["puissance"]) == 179 and round(by_date["2021-07-03"]["puissance"]) == 98)
    check("lesson 5 quotes the network figures", all(t in text["preuve-de-travail"] for t in
          ("1 116 EH/s", "13,7 jours", "19,4 jours", "179 EH/s", "98 EH/s", "482 périodes")))
    check("the course is in the money universe", catalog.universe_of(course) == "monnaie")


def test_crypto_course_figures():
    """« Utiliser la crypto en sécurité » : pools, gas, backups and depegs, recomputed."""
    print("\nCrypto course figures")
    import re
    from sensitor.academy import crypto as K
    catalog = C.load_catalog()
    course = catalog.course("crypto-en-securite")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}

    pool = ex("pool-automatique")
    check("pool: 3 000 USDC an ether, k = 30 million", K.pool_price(300_000, 100) == pool["prix"]
          and 300_000 * 100 / 1e6 == pool["constante"])
    received = K.amm_out(300_000, 100, 30_000, fee=0)
    check("pool: 9,09 ETH at 3 300 on average, 10 % impact", abs(received - pool["recu"]) < 0.006
          and abs(30_000 / received - pool["moyen"]) < 1e-6
          and abs(K.price_impact(300_000, 100, 30_000) * 100 - pool["impact"]) < 1e-9)
    check("pool: 9,07 ETH with the 0,30 % fee", abs(K.amm_out(300_000, 100, 30_000) - pool["commission"]) < 0.006)
    check("pool: the impact equals the deposit's share of the reserve",
          all(abs(K.price_impact(300_000, 100, 300_000 * f) - f) < 1e-12 for f in (0.01, 0.1, 0.5)))
    check("pool: the product stays constant", abs((300_000 + 30_000) * (100 - received) - 30_000_000) < 1e-6)
    svg = catalog.figures["produit-constant.svg"]
    check("pool figure: 90,91 ETH after, 9,09 received at 3 300", "90,91 ETH" in svg and "9,09 ETH" in svg
          and "3 300 USDC" in svg and abs(100 - received - 90.91) < 0.005)

    gas = ex("frais-ethereum")
    check("gas: 420 000 gwei, 0,00042 ETH, 1,26 dollar, 3,90 for a token",
          21_000 * 20 == gas["gwei"] and close(K.gas_fee_eth(21_000, 20), gas["eth"])
          and close(K.gas_fee_eth(21_000, 20) * 3000, gas["dollars"]) and close(K.gas_fee_eth(65_000, 20) * 3000, gas["jeton"]))

    seed = ex("securite-phrase")
    years = K.years_to_try(K.entropy_bits(12), 1e12)
    check("seed: 132 bits with the checksum, 128 of secret, 256 for 24 words",
          12 * 11 == seed["bits"] and K.entropy_bits(12) == 128 and K.entropy_bits(24) == 256)
    check("seed: 3,4 x 10^38, 3,4 x 10^26 seconds, 1,1 x 10^19 years",
          f"{2 ** 128:.1e}" == "3.4e+38" and int(f"{2 ** 128:.1e}".split("e")[1]) == seed["exposant"]
          and int(f"{2 ** 128 / 1e12:.1e}".split("e")[1]) == seed["secondes"]
          and f"{years:.1e}" == "1.1e+19" and int(f"{years:.1e}".split("e")[1]) == seed["annees"])
    check("seed: hundreds of millions of times the age of the universe", 1e8 < years / 13.8e9 < 1e9)
    check("seed: a BIP 39 phrase has 12 to 24 words", raises(lambda: K.entropy_bits(13), ValueError))

    dp = ex("decrochage-stablecoin")
    check("depeg: 22 000 dollars, 3 000 lost, 12 %, 13,6 % to recover", K.depeg_value(25_000, 0.88) == dp["valeur"]
          and 25_000 - K.depeg_value(25_000, 0.88) == dp["perte"] and close(3000 / 25_000 * 100, dp["pourcentage"])
          and abs((1 / 0.88 - 1) * 100 - dp["remontee"]) < 0.06)
    check("lesson 2: 10 000 USDC worth 8 800 at 0,88", K.depeg_value(10_000, 0.88) == 8800 and "8 800" in text["stablecoins"])

    check("the course is in the money universe", catalog.universe_of(course) == "monnaie")
    for path in sorted((catalog.root / "courses" / "crypto-en-securite" / "lessons").glob("*.md")) + \
            sorted((catalog.root / "courses" / "bitcoin-fonctionnement" / "lessons").glob("*.md")):
        body = path.read_text(encoding="utf-8").lower()
        if re.search(r"(entrez|saisissez|tapez|indiquez|communiquez)[^.]{0,40}(phrase de récupération|clé privée|seed)", body):
            check(f"{path.stem}: never asks for a seed or a key", False)
    check("no lesson asks the reader to enter a seed phrase or a private key", True)


def test_process_figures():
    """Path 10: limits, journals, sample sizes and the case month, recomputed."""
    print("\nPath 10 figures")
    from sensitor.academy import backtest as B
    from sensitor.academy import discipline as D
    from sensitor.academy import expectancy as X
    catalog = C.load_catalog()
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}

    lim = ex("limites-perte")
    check("limits: 200 €, 2 losses a session, 5 a week", R.risk_amount(20_000, 1) == lim["risque"]
          and X.losses_to_limit(2, 1) == lim["seance"] and X.losses_to_limit(5, 1) == lim["semaine"])
    check("limits: 90 € after a 10 % drawdown, 11,1 % to recover",
          close(R.risk_amount(18_000, D.risk_after_drawdown(1, 0.10)), lim["risque-reduit"])
          and abs(R.recovery_needed(0.10) * 100 - lim["rattrapage"]) < 0.06
          and D.risk_after_drawdown(1, 0.09) == 1 and close(R.recovery_needed(0.20), 0.25))

    week = [D.JournalTrade(2, True), D.JournalTrade(-1, True), D.JournalTrade(-1, True), D.JournalTrade(-1.5, False),
            D.JournalTrade(1.8, True), D.JournalTrade(-1, False), D.JournalTrade(-1, True), D.JournalTrade(2.2, True),
            D.JournalTrade(-1, True), D.JournalTrade(-1, False)]
    js = ex("journal-semaine")
    followed = D.results(week, followed=True)
    check("week: -1,5R, 70 %, +2,0R conform, +0,29R, -3,5R of departures",
          close(sum(t.result_r for t in week), js["total"]) and close(D.compliance_rate(week) * 100, js["respect"])
          and close(sum(followed), js["conformes"]) and abs(D.mean(followed) - js["esperance"]) < 0.006
          and close(D.cost_of_departures(week), js["cout"]))
    table = catalog.exercise("journal-semaine").context
    check("week: the table of the exercise is the same journal",
          all(f"{abs(t.result_r):.1f}".replace(".", ",") + "R" in table for t in week) and table.count("| non") == 3)

    rv = ex("revue-echantillon")
    iv = B.mean_interval(0.15, 1.3, 30)
    check("review: SE 0,24, -0,32 to +0,62 on 30 trades, 650 for 0,10R",
          abs(B.standard_error(1.3, 30) - rv["erreur"]) < 0.006 and abs(iv.low - rv["bas"]) < 0.006
          and abs(iv.high - rv["haut"]) < 0.006 and B.trades_needed(1.3, 0.10) == rv["trades"])

    month = D.CASE_MONTH
    cm = ex("cas-mois")
    check("case: 24 trades, 75 % compliance, -6,4R of departures, -0,6R for the month",
          len(month) == 24 and close(D.compliance_rate(month) * 100, cm["respect"])
          and close(D.cost_of_departures(month), cm["cout"]) and close(sum(t.result_r for t in month), cm["mois"]))
    check("case: +0,32R conform, -1,07R departures", abs(D.mean(D.results(month, followed=True)) - cm["esperance-plan"]) < 0.006
          and abs(D.mean(D.results(month, followed=False)) - cm["esperance-ecarts"]) < 0.006
          and close(sum(D.results(month, followed=True)), 5.8))
    by_tag = {}
    for t in month:
        if not t.followed:
            by_tag.setdefault(t.tag, []).append(t.result_r)
    check("case: the lesson's table by broken rule", {k: round(sum(v), 1) for k, v in by_tag.items()}
          == {"revanche": -2.0, "stop déplacé": -1.8, "hors zone": -1.0, "taille doublée": -2.2, "sortie anticipée": 0.6}
          and len(by_tag["revanche"]) == 2)
    after_loss = sum(1 for i, t in enumerate(month) if not t.followed and i and month[i - 1].result_r < 0)
    check("case: four departures out of six follow a loss", after_loss == 4)
    rows = catalog.dataset("mois-de-trading").rows
    check("case chart: ends at -0,6R traded and +5,8R for the plan alone, flagged as synthetic",
          close(rows[-1]["realise"], -0.6) and close(rows[-1]["plan"], 5.8) and catalog.dataset("mois-de-trading").synthetic)
    check("the risk halves from 10 % of drawdown, not before", D.risk_after_drawdown(1, 0.10) == 0.5 and D.risk_after_drawdown(1, 0.099) == 1)
    check("the course is in the trading universe", catalog.universe_of(catalog.course("processus-de-trading")) == "trading")


def test_reserve_figures():
    """« Bitcoin, une réserve de valeur ? » : supply growth from the chain, M2 and M3, stock-to-flow."""
    print("\nReserve of value figures")
    import datetime as dt
    from sensitor.academy import bitcoin as B
    catalog = C.load_catalog()
    course = catalog.course("bitcoin-reserve-de-valeur")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}
    net = catalog.dataset("reseau-bitcoin").rows
    points = [(r["hauteur"], r["horodatage"]) for r in net] + [(net[-1]["hauteur_suivante"], net[-1]["horodatage_suivant"])]
    rows = catalog.dataset("offre-monnaie-comparee").rows
    ts = lambda y, m: dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp()
    rebuilt = []
    for r in rows:
        y, m = int(r["mois"][:4]), int(r["mois"][5:7])
        g = B.supply_growth(B.height_at(ts(y, m), points), B.height_at(ts(y - 1, m), points)) * 100
        rebuilt.append(abs(g - r["bitcoin"]) < 0.006 and abs(r["stock_flux_bitcoin"] - 100 / r["bitcoin"]) < 0.06)
    check("supply growth: every month rebuilt from the chain's headers and the protocol", all(rebuilt) and len(rows) == 153)
    by = {r["mois"][:7]: r for r in rows}
    m3 = {r["mois"][:7]: r["m3"] for r in catalog.dataset("m3-inflation-zone-euro").rows}
    check("the euro column is the ECB M3 series", all(by[k]["zone_euro_m3"] == m3.get(k) for k in by if by[k]["zone_euro_m3"] is not None))
    us = [(r["etats_unis_m2"], r["mois"][:7]) for r in rows if r["etats_unis_m2"] is not None]
    eu = [(r["zone_euro_m3"], r["mois"][:7]) for r in rows if r["zone_euro_m3"] is not None]
    check("M2: +26,8 % in February 2021, -4,6 % in April 2023", max(us) == (26.78, "2021-02") and min(us) == (-4.64, "2023-04"))
    check("M3: +12,5 % in January 2021, -1,3 % in August 2023", max(eu) == (12.5, "2021-01") and min(eu) == (-1.3, "2023-08"))
    check("Bitcoin: 0,82 % in September 2026, a stock-to-flow of 122", by["2026-09"]["bitcoin"] == 0.82
          and round(by["2026-09"]["stock_flux_bitcoin"]) == 122)
    check("lesson 3 quotes them", all(t in text["creation-monetaire-comparee"] for t in ("0,82 %", "26,8 %", "4,6 %", "12,5 %", "1,3 %")))

    dl = ex("dilution-offre")
    s0, s10 = B.supply_after(971_911) / B.COIN, B.supply_after(971_911 + int(10 * 365.25 * 144)) / B.COIN
    check("dilution: 0,61 %, 0,92 %, +3,72 % of bitcoins, 0,96 %", abs(1 / 1.05 ** 10 - dl["cinq"]) < 0.006
          and abs(1 / 1.0082 ** 10 - dl["rythme"]) < 0.006 and s10 == 20_846_825 and abs((s10 / s0 - 1) * 100 - dl["bitcoin"]) < 0.006
          and abs(s0 / s10 - dl["part-bitcoin"]) < 0.006)
    sf = ex("stock-flux")
    check("stock-to-flow: gold 58, 164 250 BTC a year, Bitcoin 122, 248 after 2028",
          round(212_582 / 3_644) == sf["or"] and 3.125 * 144 * 365 == sf["flux"] and round(20_099_725 / sf["flux"]) == sf["bitcoin"]
          and B.supply_after(1_049_999) == 20_343_750 * B.COIN and round(20_343_750 / (1.5625 * 144 * 365)) == sf["apres"])
    check("objections: -62 % from about 43 400 to 16 500 dollars", round((16_500 / 43_400 - 1) * 100) == -62
          and "62 %" in text["objections-reserve"])
    check("height interpolation: refuses a date outside the chain", raises(lambda: B.height_at(0, points), ValueError))
    check("the course is in the money universe", catalog.universe_of(course) == "monnaie")


def test_analysis_figures():
    """« Analyser un projet crypto » : capitalisation, dilution, revenues, loans, impermanent loss."""
    print("\nCrypto analysis figures")
    from sensitor.academy import crypto as K
    catalog = C.load_catalog()
    course = catalog.course("analyser-un-projet-crypto")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}
    cf = ex("capitalisation-fdv")
    check("cap: 1 bn, FDV 5 bn, 20 % circulating, 0,10 dollar diluted",
          K.market_cap(0.5, 2e9) / 1e9 == cf["cap"] and K.fully_diluted(0.5, 1e10) / 1e9 == cf["fdv"]
          and 2 / 10 * 100 == cf["part"] and close(K.price_after_dilution(0.5, 2e9, 1e10), cf["prix"]))
    dj = ex("deblocage-jetons")
    check("unlock: +25 %, -20 %, 92,6 % for a non-staker", 100 / 400 * 100 == dj["hausse"]
          and close((K.price_after_dilution(1, 400e6, 500e6) - 1) * 100, dj["baisse"]) and abs(100 / 1.08 - dj["part"]) < 0.06)
    check("dilution: refuses a shrinking supply", raises(lambda: K.price_after_dilution(1, 10, 5), ValueError))
    rp = ex("revenus-protocole")
    check("revenues: 12 M$, 50 times, -8 M$ net", close(30 * 0.4, rp["detenteurs"]) and close(600 / 12, rp["ratio"])
          and close(12 - 20, rp["net"]))
    pl = ex("pret-liquidation")
    check("loan: 50 %, health 1,6, liquidation at 1 875 (-37,5 %), 937,50 with half the debt",
          3000 / 6000 * 100 == pl["ratio"] and close(K.health_factor(6000, 0.8, 3000), pl["sante"])
          and close(K.liquidation_price(2, 3000, 0.8), pl["liquidation"])
          and close((K.liquidation_price(2, 3000, 0.8) / 3000 - 1) * 100, pl["baisse"])
          and close(K.liquidation_price(2, 1500, 0.8), pl["moitie"]))
    check("loan: the health factor is 1 at the liquidation price", close(K.health_factor(2 * 1875, 0.8, 3000), 1.0))
    ip = ex("perte-impermanente")
    lp = 10_000 * 2 ** 0.5
    check("impermanent loss: 15 000 held, 14 142 pooled, -5,7 %, 858 dollars, -20 % at x4",
          5000 * 2 + 5000 == ip["detention"] and round(lp) == ip["position"] and abs(K.impermanent_loss(2) * 100 - ip["perte"]) < 0.06
          and round(15_000 - lp) == ip["frais"] and close(K.impermanent_loss(4) * 100, ip["quatre"])
          and close(lp, 15_000 * (1 + K.impermanent_loss(2))))
    table = {1.25: "−0,6 %", 1.5: "−2,0 %", 2: "−5,7 %", 4: "−20,0 %", 0.5: "−5,7 %"}
    check("impermanent loss: the lesson's table", all(f"{K.impermanent_loss(r) * 100:.1f}".replace(".", ",").replace("-", "−") + " %" == v
                                                   and v in text["perte-impermanente"] for r, v in table.items()))
    check("impermanent loss: same loss up or down, none without a move",
          close(K.impermanent_loss(2), K.impermanent_loss(0.5)) and K.impermanent_loss(1) == 0)
    check("the course is in the money universe", catalog.universe_of(course) == "monnaie")


def test_invest_figures():
    """« Investir dans la crypto avec méthode » : allocation, DCA, value averaging, rebalancing, tax."""
    print("\nInvesting figures")
    from sensitor.academy import invest as I
    from sensitor.academy import savings as S
    catalog = C.load_catalog()
    course = catalog.course("investir-avec-methode")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}
    al = ex("allocation-volatilite")
    check("allocation: 10,5 % with 5 %, 15,7 % with 20 %, 3 750 and 15 000 € lost",
          abs(S.portfolio_volatility(0.05, 0.6, 0.1, 0.2) * 100 - al["vol-5"]) < 0.06
          and abs(S.portfolio_volatility(0.20, 0.6, 0.1, 0.2) * 100 - al["vol-20"]) < 0.06
          and close(-I.portfolio_move([0.05, 0.95], [-0.75, 0]) * 100_000, al["baisse-5"])
          and close(-I.portfolio_move([0.20, 0.80], [-0.75, 0]) * 100_000, al["baisse-20"]))
    check("allocation: the lesson's table", all(t in text["allocation-et-taille"] for t in ("10,0 %", "10,5 %", "15,7 %"))
          and round(S.portfolio_volatility(0, 0.6, 0.1, 0.2) * 100, 1) == 10.0)
    dca = ex("dca-achats")
    acc = I.fixed_amount(100, [40, 50, 25, 50])
    check("DCA: 10,5 units, 38,10 € against a 41,25 € average, 525 € against 500 €",
          close(acc.units, dca["unites"]) and abs(acc.average_cost - dca["revient"]) < 0.006
          and close(sum([40, 50, 25, 50]) / 4, dca["moyenne"]) and close(acc.units * 50, dca["final-dca"])
          and close(I.lump_sum(400, 40).units * 50, dca["final-une-fois"]))
    check("DCA: the cost never exceeds the average price", all(
        I.fixed_amount(10, p).average_cost <= sum(p) / len(p) + 1e-12 for p in ([1, 2, 3], [5, 5, 5], [9, 1, 4, 7])))
    va = ex("va-versements")
    check("value averaging: 100, 75, 200, -200", I.value_averaging(100, [40, 50, 25, 50]) == [va["m1"], va["m2"], va["m3"], va["m4"]])
    rb = ex("reequilibrage")
    w = I.weight_after_move(0.10, 1.0)
    check("rebalancing: 110 000 €, 18,2 %, 9 000 € to sell", close(10_000 * 2 + 90_000, rb["total"])
          and abs(w * 100 - rb["part"]) < 0.06 and close(I.rebalance_amount(110_000, w, 0.10), rb["vente"]))
    st = ex("stress-patrimoine")
    move = I.portfolio_move([0.05, 0.55, 0.40], [-0.8, -0.3, 0])
    check("stress: -20,5 %, -41 000 €, -8 000 € from crypto, +25,8 % to recover",
          close(move * 100, st["variation"]) and close(move * 200_000, st["euros"]) and close(200_000 * 0.05 * -0.8, st["crypto"])
          and abs(R.recovery_needed(-move) * 100 - st["rattrapage"]) < 0.06)
    check("weights must add up to 1", raises(lambda: I.portfolio_move([0.5, 0.4], [0, 0]), ValueError))
    tx = ex("plus-value-150vh")
    gain = I.gain_on_disposal(5000, 10_000, 25_000)
    check("tax: 20 %, 2 000 € of cost, 3 000 € of gain, 942 € at 31,4 %, 8 000 € remaining",
          5000 / 25_000 * 100 == tx["fraction"] and close(5000 - gain, tx["acquisition"]) and close(gain, tx["plus-value"])
          and close(gain * 0.314, tx["impot"]) and close(I.remaining_acquisition_cost(10_000, 5000, 25_000), tx["reste"]))
    check("tax: a sale above the portfolio's value is refused", raises(lambda: I.gain_on_disposal(30_000, 1, 25_000), ValueError))
    check("tax: the lesson tells to check the year's rate on impots.gouv.fr",
          "impots.gouv.fr" in text["fiscalite-crypto"] and "impots.gouv.fr" in catalog.exercise("plus-value-150vh").context)
    check("the course is in the money universe", catalog.universe_of(course) == "monnaie")


def test_visual_figures():
    """The computed charts of the Crypto and Investment courses: what each caption says, recomputed."""
    print("\nComputed charts")
    from sensitor.academy import crypto as K
    from sensitor.academy import invest as I
    catalog = C.load_catalog()
    rows = lambda d: catalog.dataset(d).rows
    il = {r["rapport"]: r["perte"] for r in rows("perte-impermanente-courbe")}
    check("impermanent loss curve: zero at 1, -5,72 % at x2 and at /2", il[1] == 0 and il[2] == -5.72 and il[0.5] == -5.72)
    liq = {r["ratio"]: r["baisse"] for r in rows("liquidation-par-ratio")}
    check("liquidation: -68,8 % at 25 %, -6,2 % at 75 %", liq[25] == -68.8 and liq[75] == -6.2)
    un = rows("deblocages-exemple")
    total = lambda r: sum(v for k, v in r.items() if k != "mois")
    check("unlocks: 20 % at launch, 100 % after four years", total(un[0]) == 20 and round(total(un[48]), 6) == 100)
    steps = [total(b) - total(a) for a, b in zip(un, un[1:])]
    check("unlocks: the pace rises from month 13, when the team's cliff ends", round(steps[12], 2) > round(steps[11], 2)
          and un[12]["equipe"] == 0 and un[13]["equipe"] > 0)
    st = rows("dilution-staking")
    check("staking: 46 % kept after ten years at 8 %", round(st[-1]["sans_staking"]) == 46 and st[-1]["staking"] == 100)
    vol = {r["part"]: r["volatilite"] for r in rows("volatilite-part-crypto")}
    check("volatility curve: 10 %, 10,5 % and 15,7 % as in the table, accelerating",
          vol[0] == 10 and round(vol[5], 1) == 10.5 and round(vol[20], 1) == 15.7
          and all(b - a < c - b for a, b, c in zip(list(vol.values())[2:], list(vol.values())[3:], list(vol.values())[4:])))
    dca = rows("dca-exemple")
    check("DCA chart: a 60 % fall, a cost of 61,60 € against 100 €", min(r["prix"] for r in dca) == 40 and dca[0]["prix"] == 100
          and dca[-1]["prix_de_revient"] == 61.6 and dca[-1]["en_une_fois"] == 100 and len(dca) == 24)
    dr = rows("derive-allocation")
    check("drift: about 4,1 % at the low without rebalancing, near 10 % when rebalanced",
          round(min(r["sans_reequilibrage"] for r in dr), 1) == 4.1 and all(abs(r["reequilibre"] - 10) < 3.5 for r in dr))
    sp = {r["poche"]: r["contribution"] for r in rows("stress-poches")}
    check("stress: 8 000 and 33 000 € out of 41 000 €", sp["Crypto"] == -8000 and sp["Actions"] == -33000
          and sum(sp.values()) == -41000)
    hn = {r["baisse"]: r["hausse_necessaire"] for r in rows("hausse-necessaire")}
    check("recovery: 25 % after -20 %, 100 % after -50 %, 400 % after -80 %", hn[20] == 25 and hn[50] == 100 and hn[80] == 400)
    fp = {r["mots"]: r["annees"] for r in rows("force-phrase")}
    check("seed strength: about 10^19 years for 12 words, more than 10^57 for 24",
          f"{fp['12 mots']:.0e}" == "1e+19" and fp["24 mots"] > 1e57)
    gz = {r["gwei"]: r for r in rows("frais-gaz")}
    check("gas: 1,26 and 3,90 dollars at 20 gwei", gz[20]["ether"] == 1.26 and gz[20]["jeton"] == 3.9)
    check("pool impact: equal to the deposit's share", all(close(r["impact"], r["part"], 1e-9) for r in rows("impact-pool")))
    synthetic = {d for d in ("deblocages-exemple", "dilution-staking", "dca-exemple", "derive-allocation", "stress-poches",
                             "frais-gaz", "indicateurs-exemple")}
    check("constructed examples are flagged as such", all(catalog.dataset(d).synthetic for d in synthetic))
    used = {b.target for c in catalog.available_courses() for l in c.lessons for b in l.blocks if b.kind == "chart"}
    check("every chart is used by a lesson", set(catalog.charts) <= used, str(set(catalog.charts) - used))


def test_onchain_figures():
    """« Lire les métriques on-chain » : every dataset rebuilt from the raw sample, every quoted figure checked."""
    print("\nOn-chain figures")
    from sensitor.academy import bitcoin as B
    from sensitor.academy import onchain as O
    catalog = C.load_catalog()
    course = catalog.course("metriques-on-chain")
    text = {l.id: "\n".join(b.text for b in l.blocks) for l in course.lessons}
    ex = lambda i: {s.id: s.answer for s in catalog.exercise(i).steps}
    # Read as text: the dataset loader would turn an all-digit coinbase script into a number.
    import csv
    with open(C.CONTENT_ROOT / "data" / "blocs-echantillon.csv", encoding="utf-8") as handle:
        raw = list(csv.DictReader(handle))
    samples = [O.Sample(day=r["jour"], height=int(r["hauteur"]), tx_count=int(r["transactions"]), size=int(r["taille"]),
                        weight=int(r["poids"]), reward=int(r["coinbase_sats"]), coinbase=r["coinbase_script"]) for r in raw]
    check("sample: one block a day, 6 474 days from 9 January 2009 to 30 September 2026",
          len(samples) == 6474 and samples[0].day == "2009-01-09" and samples[-1].day == "2026-09-30"
          and len({s.day for s in samples}) == 6474)
    check("sample: heights grow with the days, and no coinbase pays less than the subsidy",
          all(a.height <= b.height for a, b in zip(samples, samples[1:]))
          and all(s.reward >= B.block_subsidy(s.height) for s in samples))
    check("sample: no block exceeds the weight limit", all(s.weight <= O.MAX_WEIGHT for s in samples))
    periods = [{"date": r["date"], "jours": r["jours"], "puissance": r["puissance"]} for r in catalog.dataset("reseau-bitcoin").rows]
    rebuilt = O.monthly_rows(samples, periods)
    monthly = catalog.dataset("activite-on-chain").rows
    same = lambda a, b: (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= 1e-6 + abs(b) * 1e-6)
    check("monthly activity: every month rebuilt from the sample", len(rebuilt) == len(monthly) == 213 and all(
        r["mois"] == m["mois"] and all(same(r[k], m[k]) for k in r if k != "mois") for r, m in zip(rebuilt, monthly)))
    pools = catalog.dataset("pools-par-annee").rows
    ok = True
    for row in pools:
        sh = O.pool_shares(samples, str(row["annee"]))
        ok &= abs(sh.get("Non identifié", 0) - row["non_identifie"]) < 0.06
        ok &= (row["coefficient_nakamoto"] is None) == (O.nakamoto_coefficient(sh) is None)
        ok &= row["coefficient_nakamoto"] is None or row["coefficient_nakamoto"] == O.nakamoto_coefficient(sh)
        ok &= abs(sum(v for k, v in row.items() if k not in ("annee", "echantillon", "coefficient_nakamoto")) - 100) < 0.6
    check("pools: every year rebuilt, shares adding up to 100 %", ok)
    check("pools: no coefficient when the tagged pools do not reach half, as in 2014",
          next(r for r in pools if r["annee"] == 2014)["coefficient_nakamoto"] is None)
    check("pool tags: Foundry, AntPool and F2Pool's Chinese tag are recognised",
          O.pool_of("Foundry USA Pool".encode().hex()) == "Foundry USA" and O.pool_of("Mined by AntPool".encode().hex()) == "AntPool"
          and O.pool_of("七彩神仙鱼".encode().hex()) == "F2Pool" and O.pool_of("zz") == "Non identifié")
    by = {r["mois"][:7]: r for r in monthly}
    last = by["2026-09"]
    fmt = lambda x, nd=0: f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")
    peak = max(monthly, key=lambda r: r["transactions_par_jour"])
    check("activity: the figures quoted in lesson 2", all(t in text["activite-reseau"] for t in (
        fmt(round(by["2012-06"]["transactions_par_jour"], -2)), fmt(round(peak["transactions_par_jour"], -3)),
        fmt(round(last["transactions_par_jour"], -3)), fmt(last["remplissage"], 1))) and peak["mois"].startswith("2026-06"))
    check("activity: blocks first above 90 % full in April 2016",
          next(r for r in monthly if r["remplissage"] >= 90)["mois"].startswith("2016-04") and "avril 2016" in text["activite-reseau"])
    fee_peak = max(monthly, key=lambda r: r["frais_par_bloc"])
    outside = max((r for r in monthly if not r["mois"].startswith(("2017", "2018"))), key=lambda r: r["frais_par_bloc"])
    share = max(monthly, key=lambda r: r["part_frais"])
    check("fees: 3,89 BTC in December 2017, 1,99 in December 2023, a 22,2 % share in December 2023",
          fee_peak["mois"].startswith("2017-12") and round(fee_peak["frais_par_bloc"], 2) == 3.89
          and outside["mois"].startswith("2023-12") and round(outside["frais_par_bloc"], 2) == 1.99
          and share["mois"].startswith("2023-12") and round(share["part_frais"], 1) == 22.2
          and all(t in text["frais-budget-securite"] for t in ("3,89 BTC", "1,99 BTC", "22,2 %")))
    size = max(monthly, key=lambda r: r["taille_mo"])
    check("block space: above 1 MB from November 2017, 1,95 MB in February 2023",
          next(r for r in monthly if r["taille_mo"] > 1)["mois"].startswith("2017-11") and size["mois"].startswith("2023-02")
          and round(size["taille_mo"], 2) == 1.95 and "1,95 Mo" in text["espace-de-bloc"])
    check("mining: about 1 153 BTC per EH/s a day in September 2016, 0,50 in September 2026",
          round(by["2016-09"]["revenu_par_eh"]) == 1153 and round(last["revenu_par_eh"], 2) == 0.50
          and "1 153 BTC" in text["minage-et-pools"])
    p26 = next(r for r in pools if r["annee"] == 2026)
    check("mining: Foundry USA about 30 % in 2026, three pools for half of the blocks",
          round(p26["foundry_usa"]) == 30 and p26["coefficient_nakamoto"] == 3 and "3 pools" in text["minage-et-pools"])
    ac = ex("activite-calcul")
    check("exercise activity: transactions per day, weight used, free space",
          abs(ac["par-jour"] - last["transactions_par_jour"]) <= 100 and abs(ac["poids"] - last["remplissage"] / 100 * 4e6) <= 600
          and abs(ac["reste"] - (100 - last["remplissage"])) < 0.06)
    pn = ex("pools-nakamoto")
    ranked = sorted((v for k, v in p26.items() if k not in ("annee", "echantillon", "coefficient_nakamoto", "autres", "non_identifie")), reverse=True)
    check("exercise pools: the two largest and the coefficient", abs(pn["deux"] - (ranked[0] + ranked[1])) < 0.06
          and pn["coefficient"] == p26["coefficient_nakamoto"])
    fc = ex("frais-coinbase")
    check("exercise coinbase: blocks 839 999 and 840 000",
          B.block_subsidy(839_999) == 625_000_000 and B.block_subsidy(840_000) == 312_500_000
          and abs((729_455_386 - 625_000_000) / B.COIN - fc["frais-avant"]) < 0.006
          and abs((4_075_061_499 - 312_500_000) / B.COIN - fc["frais-apres"]) < 0.006
          and abs(37.62561499 / 40.75061499 * 100 - fc["part-apres"]) < 0.06 and abs(3_993_281 / 4e6 * 100 - fc["remplissage"]) < 0.06)
    coins = list(O.EXAMPLE_COINS)
    mv = ex("mvrv-calcul")
    check("exercise MVRV: realized price 32,50, MVRV 1,38, NUPL 0,28",
          close(O.realized_price(coins), mv["prix-realise"]) and abs(O.mvrv(45, coins) - mv["mvrv"]) < 0.006
          and abs(O.nupl(45, coins) - mv["nupl"]) < 0.006)
    ind = {r["mois"]: r for r in catalog.dataset("indicateurs-exemple").rows}
    check("indicators example: MVRV 2,57 at month 6, 0,56 at month 11", ind[6]["mvrv"] == 2.57 and ind[11]["mvrv"] == 0.56
          and "2,57" in text["indicateurs-de-prix"] and catalog.dataset("indicateurs-exemple").synthetic)
    check("the course is in the money universe", catalog.universe_of(course) == "monnaie")


def test_bitcoin_issuance():
    """The issuance schedule, from the protocol rules, in satoshis."""
    print("\nBitcoin issuance")
    from sensitor.academy import bitcoin as B
    check("the total supply is 20 999 999,9769 BTC", B.total_supply() == 2_099_999_997_690_000)
    check("50 BTC per block at first", B.block_subsidy(0) == 50 * B.COIN and B.block_subsidy(209_999) == 50 * B.COIN)
    check("25 BTC from block 210 000", B.block_subsidy(210_000) == 25 * B.COIN)
    check("3,125 BTC since block 840 000", B.block_subsidy(840_000) == 312_500_000)
    check("the shift reaches zero after 33 epochs", B.block_subsidy(33 * 210_000) == 0
          and B.block_subsidy(32 * 210_000) == 1)
    check("zero after the 64th halving", B.block_subsidy(64 * 210_000) == 0)
    check("half of all bitcoins in the first epoch", B.supply_after(209_999) == 1_050_000_000_000_000)
    check("19 687 500 BTC before the 2024 halving", B.supply_after(839_999) == 1_968_750_000_000_000)
    check("supply equals the sum of subsidies on a small range",
          B.supply_after(5) == 6 * 50 * B.COIN)
    ep = B.epochs(64)
    check("33 epochs carry a subsidy", sum(1 for e in ep if e.subsidy) == 33)
    check("past halving dates are recorded, not estimated",
          [(e.start_date.isoformat(), e.estimated) for e in ep[1:5]]
          == [("2012-11-28", False), ("2016-07-09", False), ("2020-05-11", False), ("2024-04-20", False)])
    check("later dates are flagged as estimates", all(e.estimated for e in ep[5:]))
    check("an estimated epoch lasts 210 000 blocks of 10 minutes",
          (ep[6].start_date - ep[5].start_date).days in (1458, 1459))
    rows = B.issuance_rows()
    check("the chart rows end at 99,99 % issued", round(rows[-1]["part"], 2) == 99.99 and rows[0]["part"] == 50.0)
    check("negative heights are refused", raises(lambda: B.block_subsidy(-1), ValueError)
          and raises(lambda: B.supply_after(-1), ValueError))


def test_datasets_and_charts():
    """Every chart has a dataset, every dataset a source, a licence and a date."""
    print("\nDatasets and charts")
    from sensitor.academy import datasets as D
    from sensitor.academy import markup as M2
    catalog = C.load_catalog()
    emission = catalog.dataset("btc-emission")
    check("the issuance dataset is computed from the protocol", emission and emission.kind == D.COMPUTED
          and len(emission.rows) == 13)
    check("its credit line names the source, licence and date",
          emission.credit.startswith("Calcul : règles du protocole") and "licence" in emission.credit
          and "17 octobre 2026" in emission.credit)
    check("the issuance charts exist", {"emission-bitcoin", "recompense-bitcoin"} <= set(catalog.charts))
    check("a chart directive parses", M2.parse("::: chart emission-bitcoin\nLégende.\n:::")[0].target == "emission-bitcoin")
    from sensitor.academy.ui import chart_view
    fig = chart_view.figure(catalog.chart("emission-bitcoin"), emission)
    check("the step chart draws one series with French separators",
          len(fig.data) == 1 and fig.data[0].line.shape == "hv" and fig.layout.separators == ", ")
    bars = chart_view.figure(catalog.chart("recompense-bitcoin"), emission)
    check("estimated bars are drawn lighter", list(bars.data[0].marker.opacity[:5]) == [0.9] * 5
          and bars.data[0].marker.opacity[5] == 0.45)

    def broken(edit_data=None, edit_charts=None, files=None):
        root = _copy_tree()
        if edit_data:
            f = root / "data" / "datasets.toml"
            f.write_text(edit_data(f.read_text()))
        if edit_charts:
            f = root / "charts.toml"
            f.write_text(edit_charts(f.read_text()))
        for name, text in (files or {}).items():
            (root / "data" / name).write_text(text)
        return C.validate(root)

    check("a dataset without a licence is refused", any("license" in p for p in broken(
        edit_data=lambda t: t.replace('license = "calcul Sensitor, aucune donnée tierce"\n', ""))))
    check("an unknown generator is refused", any("générateur inconnu" in p for p in broken(
        edit_data=lambda t: t.replace('generator = "bitcoin-issuance"', 'generator = "devinette"'))))
    check("a chart on an unknown column is refused", any("absente du jeu" in p for p in broken(
        edit_charts=lambda t: t.replace('column = "offre"', 'column = "prix"'))))
    check("a chart on an unknown dataset is refused", any("jeu de données introuvable" in p for p in broken(
        edit_charts=lambda t: t.replace('dataset = "btc-emission"', 'dataset = "inconnu"', 1))))
    csv_entry = ('\n[[dataset]]\nid = "ipc-test"\ntitle = "Test"\nkind = "file"\nfile = "ipc.csv"\n'
                 'source = "Institut de test"\nurl = "https://example.org"\nlicense = "Licence ouverte"\n'
                 'retrieved = 2026-10-17\ncolumns = ["mois", "indice"]\n')
    check("a file dataset whose CSV is missing is refused", any("fichier de données introuvable" in p for p in broken(
        edit_data=lambda t: t + csv_entry)))
    check("a file dataset with its CSV loads", not broken(edit_data=lambda t: t + csv_entry,
                                                         files={"ipc.csv": "mois,indice\n2026-01,100\n2026-02,100.4\n"}))
    check("a declared column absent from the CSV is refused", any("colonne(s) absente(s)" in p for p in broken(
        edit_data=lambda t: t + csv_entry, files={"ipc.csv": "mois,valeur\n2026-01,100\n"})))
    synthetic = '\n[[dataset]]\nid = "exemple"\ntitle = "Exemple"\nkind = "file"\nfile = "ex.csv"\nsynthetic = true\n'
    check("a synthetic example needs no source, and says so", not broken(
        edit_data=lambda t: t + synthetic, files={"ex.csv": "x,y\n1,2\n"}))
    root = _copy_tree()
    f = root / "data" / "datasets.toml"
    f.write_text(f.read_text() + synthetic)
    (root / "data" / "ex.csv").write_text("x,y\n1,2\n")
    check("…and its credit line says it is synthetic",
          C.load_catalog(root).dataset("exemple").credit.startswith("Exemple synthétique"))
    root = _copy_tree()
    lesson = root / "courses" / "premiers-pas" / "lessons" / "budget-de-risque.md"
    lesson.write_text(lesson.read_text() + "\n::: chart absent\nLégende.\n:::\n")
    check("a lesson pointing at an unknown chart is refused", any("graphique introuvable" in p for p in C.validate(root)))


def test_access_levels():
    """Public, member and premium, decided in one place."""
    print("\nAccess levels")
    from sensitor.academy import access as A
    catalog = C.load_catalog()
    lesson = next(l for c in catalog.courses.values() for l in c.lessons if l.access == C.MEMBER)
    from dataclasses import replace
    premium = replace(lesson, access=C.PREMIUM)
    public = replace(lesson, access=C.PUBLIC)
    check("public: anyone", A.can_read_lesson(public, None))
    check("member: any account", not A.can_read_lesson(lesson, None) and A.can_read_lesson(lesson, "a@x.fr"))
    check("premium: not a visitor", not A.can_read_lesson(premium, None, "pro"))
    check("premium: not a free account", not A.can_read_lesson(premium, "a@x.fr", "free")
          and not A.can_read_lesson(premium, "a@x.fr"))
    check("premium: an account with the pro or premium tier", A.can_read_lesson(premium, "a@x.fr", "pro")
          and A.can_read_lesson(premium, "a@x.fr", " Premium "))
    check("the lock says what would unlock it",
          A.lock_reason(C.PREMIUM, None) == A.SIGN_IN and A.lock_reason(C.PREMIUM, "a@x.fr", "free") == A.UPGRADE
          and A.lock_reason(C.MEMBER, None) == A.SIGN_IN and A.lock_reason(C.PREMIUM, "a@x.fr", "pro") is None)
    check("an unknown level opens nothing", not A.can_read_lesson(replace(lesson, access="vip"), "a@x.fr", "pro"))
    check("no published content is premium yet", all(l.access != C.PREMIUM for c in catalog.courses.values()
                                                     for l in c.lessons))
    root = _copy_tree()
    f = root / "courses" / "premiers-pas" / "lessons" / "budget-de-risque.md"
    f.write_text(f.read_text().replace('access = "member"', 'access = "premium"'))
    check("a lesson may declare premium", not C.validate(root))


def test_money_figures():
    """Course « La monnaie »: balance sheets, loans, bonds and the policy-rate data, recomputed."""
    print("\nCourse « La monnaie » figures")
    from sensitor.academy import money as M
    catalog = C.load_catalog()

    ex = {s.id: s.answer for s in catalog.exercise("bilan-credit").steps}
    start = M.BalanceSheet({"Réserves": 10, "Crédits": 90}, {"Dépôts": 92, "Capital": 8})
    check("balance sheet: 100 at the start", start.total_assets == ex["total-avant"] and start.balanced)
    lent = M.grant_loan(start, 10)
    check("a loan of 10 creates 10 of deposits", lent.liabilities["Dépôts"] == ex["depots-credit"]
          and lent.total_assets == ex["total-credit"] and lent.balanced)
    paid = M.transfer_out(lent, 4)
    check("a payment to another bank settles in reserves", paid.assets["Réserves"] == ex["reserves-paiement"]
          and paid.liabilities["Dépôts"] == ex["depots-paiement"] and paid.balanced)
    repaid = M.repay_loan(paid, 5)
    check("a repayment destroys money", repaid.liabilities["Dépôts"] == ex["depots-remboursement"]
          and repaid.assets["Crédits"] == 95 and repaid.balanced)
    check("quiz: 92 + 10 = 102", M.grant_loan(start, 10).liabilities["Dépôts"] == 102)
    for bad in (lambda: M.grant_loan(start, 0), lambda: M.transfer_out(start, 11),
                lambda: M.repay_loan(start, 91)):
        check("balance sheet helpers refuse impossible operations", raises(bad, ValueError))

    loan = {s.id: s.answer for s in catalog.exercise("cout-credit").steps}
    check("loan: 1 211,96 a month at 4 %", abs(M.payment(200_000, 0.04, 20) - loan["mensualite-4"]) < 0.005)
    check("loan: 290 870,56 repaid", abs(M.payment(200_000, 0.04, 20) * 240 - loan["total-4"]) < 0.01)
    check("loan: 90 870,56 of interest", abs(M.total_interest(200_000, 0.04, 20) - loan["interets-4"]) < 0.01)
    check("loan: 1 011,77 a month at 2 %", abs(M.payment(200_000, 0.02, 20) - loan["mensualite-2"]) < 0.005)
    check("loan: 42 824 of interest at 2 %", abs(M.total_interest(200_000, 0.02, 20) - loan["interets-2"]) < 1)
    check("loan: 48 046,56 apart", abs(loan["interets-4"] - loan["interets-2"] - loan["ecart"]) < 0.01)
    check("lesson: two points more than double the interest",
          M.total_interest(200_000, 0.04, 20) > 2 * M.total_interest(200_000, 0.02, 20))
    rows = M.example_amortisation_rows()
    check("lesson: year 1 is 7 878,69 of interest out of 14 543,53",
          rows[0]["interets"] == 7878.69 and round(rows[0]["interets"] + rows[0]["capital"], 2) == 14543.53)
    check("lesson: the last year is 310,27 of interest", rows[-1]["interets"] == 310.27 and rows[-1]["restant"] == 0)
    check("the schedule repays the whole principal", abs(sum(r["capital"] for r in rows) - 200_000) < 0.5)
    check("a zero rate divides the principal evenly", M.payment(1200, 0, 1) == 100)

    bond = {s.id: s.answer for s in catalog.exercise("obligation-taux").steps}
    check("bond: 3 a year", 100 * 0.03 == bond["coupon"])
    check("bond: 100 at 3 %", abs(M.bond_price(100, 0.03, 10, 0.03) - bond["prix-3"]) < 1e-9)
    check("bond: 91,89 at 4 %", round(M.bond_price(100, 0.03, 10, 0.04), 2) == bond["prix-4"])
    check("bond: 8,11 % lower", round(100 - M.bond_price(100, 0.03, 10, 0.04), 2) == bond["perte"])
    check("bond: 108,98 at 2 %", round(M.bond_price(100, 0.03, 10, 0.02), 2) == bond["prix-2"])
    check("bond: 98,11 at two years", round(M.bond_price(100, 0.03, 2, 0.04), 2) == bond["prix-court"])
    check("the yield of a 91,89 bond is 4 %", abs(M.bond_yield(M.bond_price(100, 0.03, 10, 0.04), 100, 0.03, 10) - 0.04) < 1e-9)

    rates = catalog.dataset("taux-directeurs")
    by_month = {r["mois"][:7]: r for r in rates.rows}
    negative = sorted(m for m, r in by_month.items() if r["bce_depot"] < 0)
    check("data: the ECB deposit rate is negative from June 2014 to June 2022 (month ends)",
          negative[0] == "2014-06" and negative[-1] == "2022-06", f"{negative[0]} {negative[-1]}")
    check("data: back to zero at the end of July 2022", by_month["2022-07"]["bce_depot"] == 0)
    check("data: 4 % in September 2023", by_month["2023-09"]["bce_depot"] == 4.0)
    check("data: the first cut lands in June 2024", by_month["2024-05"]["bce_depot"] == 4.0
          and by_month["2024-06"]["bce_depot"] == 3.75)
    check("data: the floor is -0,5 %", min(r["bce_depot"] for r in rates.rows) == -0.5)
    check("data: monthly rows from January 1999", rates.rows[0]["mois"] == "1999-01-01"
          and len({r["mois"] for r in rates.rows}) == len(rates.rows))
    check("data: the dataset names its sources and licence",
          "FM.D.U2.EUR.4F.KR.DFR.LEV" in rates.source and "FEDFUNDS" in rates.source and rates.license)

    course = catalog.course("la-monnaie")
    check("the course opens path 1 of the Monnaie et Bitcoin track",
          catalog.path("monnaie-inflation").is_available and catalog.path("monnaie-inflation").track == "monnaie-bitcoin")
    check("every lesson is sourced and dated", all(l.sources and l.updated for l in course.lessons))
    final = catalog.quiz("monnaie-validation")
    taught = {l.id for l in course.lessons} - {"recap-monnaie"}
    check("validation quiz: covers every lesson", {q.lesson_id for q in final.questions} == taught)
    opinion = [b for l in course.lessons for b in l.blocks if b.kind == "callout" and b.callout_kind == "opinion"]
    check("the founder's view appears once, framed as an opinion", len(opinion) == 1)


def test_inflation_figures():
    """Course « L'inflation »: exercises recomputed, every figure quoted from the data checked against the files."""
    print("\nCourse « L'inflation » figures")
    from sensitor.academy import inflation as I
    catalog = C.load_catalog()

    ex = {s.id: s.answer for s in catalog.exercise("indices-inflation").steps}
    r1, r2 = I.rate_from_index(100, 105.1), I.rate_from_index(105.1, 114.0)
    check("index: 5,1 % then 8,47 %", round(r1 * 100, 2) == ex["taux-2022"] and round(r2 * 100, 2) == ex["taux-2023"])
    total = I.cumulative([r1, r2])
    check("index: 14 % over two years", round(total * 100, 2) == ex["cumul"])
    check("index: 6,77 % a year", round(I.annualised(total, 2) * 100, 2) == ex["annualise"])
    check("index: 100 € worth 87,72 €", round(I.real_value(100, total), 2) == ex["valeur-reelle"])

    co = {s.id: s.answer for s in catalog.exercise("contributions-inflation").steps}
    parts = I.contributions({"e": .10, "a": .20, "b": .25, "s": .45}, {"e": .30, "a": .12, "b": .05, "s": .04})
    check("contributions: 3 / 2,4 / 1,8 points", round(parts["e"] * 100, 3) == co["energie"]
          and round(parts["a"] * 100, 3) == co["alimentation"] and round(parts["s"] * 100, 3) == co["services"])
    check("contributions: 8,45 % in total, 35,5 % from energy", round(sum(parts.values()) * 100, 2) == co["total"]
          and round(parts["e"] / sum(parts.values()) * 100, 1) == co["part-energie"])
    check("quiz: the unweighted mean would be 12,75 %", (30 + 12 + 5 + 4) / 4 == 12.75)

    pa = {s.id: s.answer for s in catalog.exercise("pouvoir-achat-long").steps}
    thirty = I.cumulative([0.02] * 30)
    check("30 years at 2 %: 81,14 %, 552,07 €", round(thirty * 100, 2) == pa["cumul-2"]
          and round(I.real_value(1000, thirty), 2) == pa["valeur-2"])
    check("halving: 35 years at 2 %, 14,2 at 5 %", round(I.years_to_halve(0.02), 1) == pa["moitie-2"]
          and round(I.years_to_halve(0.05), 1) == pa["moitie-5"])
    check("lesson table: 23,4 years at 3 %, 7,3 at 10 %", round(I.years_to_halve(0.03), 1) == 23.4
          and round(I.years_to_halve(0.10), 1) == 7.3)
    check("lesson: five years at 4 % make 21,7 %", round(I.cumulative([0.04] * 5) * 100, 1) == 21.7)
    check("lesson: 5 % of inflation leaves 95,24 € of 100", round(I.real_value(100, 0.05), 2) == 95.24)
    check("lesson: M up 8 %, Y up 2 %: prices up 5,9 %; with V down 5 %: 0,6 %",
          round(I.quantity_growth(.08, 0, .02) * 100, 1) == 5.9 and round(I.quantity_growth(.08, -.05, .02) * 100, 1) == 0.6)

    fr = catalog.dataset("pouvoir-achat-france")
    rows = {r["mois"][:7]: r for r in fr.rows}
    rise = rows["2026-01"]["indice"] / rows["1996-01"]["indice"] - 1
    check("data: French prices up 67,2 % from 1996 to 2026", round(rise * 100, 1) == 67.2)
    check("data: 100 € of 1996 worth 59,82 € in 2026", rows["2026-01"]["valeur_reelle_100"] == 59.82)
    check("data: 1,73 % a year on average", round(I.annualised(rise, 30) * 100, 2) == pa["france-annuel"])
    check("exercise: 1 000 € worth about 598 €", abs(1000 / (1 + rise) - pa["france-valeur"]) < 0.6)

    head = {r["mois"][:7]: r for r in catalog.dataset("inflation-zone-euro-france-us").rows}
    ea = {m: r["zone_euro"] for m, r in head.items()}
    window = [v for m, v in ea.items() if "1999-01" <= m <= "2019-12"]
    check("data: 1,7 % a year in the euro area, 1999 to 2019", round(sum(window) / len(window), 1) == 1.7)
    peak = max(ea.items(), key=lambda kv: kv[1])
    check("data: euro area peak 10,6 % in October 2022", peak == ("2022-10", 10.6), str(peak))
    check("data: September 2026, 3,8 % in the euro area and 3,4 % in France",
          head["2026-09"]["zone_euro"] == 3.8 and head["2026-09"]["france"] == 3.4)
    check("data: negative months in 2009, 2014 to 2016 and 2020",
          {m[:4] for m, v in ea.items() if v < 0} == {"2009", "2014", "2015", "2016", "2020"})
    check("data: 0,9 % in January 2021, 2,5 % in June 2024", ea["2021-01"] == 0.9 and ea["2024-06"] == 2.5)
    us = {m: r["etats_unis"] for m, r in head.items() if r["etats_unis"] is not None}
    check("data: US 9,0 % in June 2022", us["2022-06"] == 9.0 and max(v for m, v in us.items() if m >= "2020") == 9.0)
    check("data: the unpublished US October 2025 index is a gap, not a zero", head["2025-10"]["etats_unis"] is None)

    comp = {r["mois"][:7]: r for r in catalog.dataset("inflation-composantes-zone-euro").rows}
    def peak_of(col):
        return max(((m, r[col]) for m, r in comp.items()), key=lambda kv: kv[1])
    check("data: energy 44,3 % in March 2022", peak_of("energie") == ("2022-03", 44.3))
    check("data: food 15,5 % in March 2023", peak_of("alimentation") == ("2023-03", 15.5))
    check("data: services 5,6 % in July 2023", peak_of("services") == ("2023-07", 5.6))

    m3 = {r["mois"][:7]: r for r in catalog.dataset("m3-inflation-zone-euro").rows}
    check("data: M3 12,6 % in November 2007, its peak", max(m3.items(), key=lambda kv: kv[1]["m3"])[0] == "2007-11"
          and m3["2007-11"]["m3"] == 12.6)
    check("data: M3 12,5 % in January 2021, -1,3 % in August 2023", m3["2021-01"]["m3"] == 12.5
          and m3["2023-08"]["m3"] == -1.3)

    usr = {r["mois"][:7]: r for r in catalog.dataset("inflation-taux-etats-unis").rows}
    def us_peak(lo, hi):
        return max(((m, r["inflation"]) for m, r in usr.items() if lo <= m <= hi and r["inflation"] is not None),
                   key=lambda kv: kv[1])
    check("data: US 12,2 % in November 1974", us_peak("1973-01", "1976-12") == ("1974-11", 12.2))
    check("data: US 14,6 % in March 1980", us_peak("1977-01", "1985-12") == ("1980-03", 14.6))
    check("data: federal funds 19,1 % in June 1981, the peak",
          max(usr.items(), key=lambda kv: kv[1]["fed_funds"])[0] == "1981-06" and usr["1981-06"]["fed_funds"] == 19.1)
    check("data: US 3,8 % at the end of 1983", usr["1983-12"]["inflation"] == 3.8)

    course = catalog.course("l-inflation")
    check("the inflation course is the second of path 1", [c.id for c in catalog.path("monnaie-inflation").courses][:2]
          == ["la-monnaie", "l-inflation"])
    check("every lesson is sourced and dated", all(l.sources and l.updated for l in course.lessons))
    final = catalog.quiz("inflation-validation")
    taught = {l.id for l in course.lessons} - {"recap-inflation"}
    check("validation quiz: covers every lesson", {q.lesson_id for q in final.questions} == taught)
    for bad in (lambda: I.rate_from_index(0, 1), lambda: I.years_to_halve(0), lambda: I.annualised(0.1, 0),
                lambda: I.contributions({"a": .5}, {"a": .1}), lambda: I.cumulative([-1])):
        check("inflation helpers refuse bad input", raises(bad, ValueError))


def test_savings_figures():
    """Course « Inflation et patrimoine »: the simulator's arithmetic and every quoted figure, recomputed."""
    print("\nCourse « Inflation et patrimoine » figures")
    from sensitor.academy import bitcoin as B
    from sensitor.academy import savings as S
    catalog = C.load_catalog()

    check("Fisher: 5 % with 2 % inflation is 2,94 % real", round(S.real_rate(.05, .02) * 100, 2) == 2.94)
    check("Fisher: 3 % with 5 % inflation is -1,90 % real", round(S.real_rate(.03, .05) * 100, 2) == -1.90)
    check("Fisher: 2 % with 2,5 % inflation loses about 0,5 %", round(S.real_rate(.02, .025) * 100, 1) == -0.5)

    ex = {s.id: s.answer for s in catalog.exercise("composes-volatilite").steps}
    check("compound: 19 671,51 and 76 122,55", round(S.compound(10_000, .07, 10), 2) == ex["dix-ans"]
          and round(S.compound(10_000, .07, 30), 2) == ex["trente-ans"])
    check("doubling at 7 %: 10,24 years, rule of 72 gives 10,29", round(S.doubling_time(.07), 2) == ex["doublement"]
          and round(S.rule_of_72(.07), 2) == 10.29)
    check("doubling at 6 %: 11,9 years, rule 12", round(S.doubling_time(.06), 1) == 11.9 and S.rule_of_72(.06) == 12)
    seq = [.30, -.20, .25, -.30]
    check("drag: +1,25 % arithmetic, 91 € left, -2,33 % compounded", round(sum(seq) / 4 * 100, 2) == ex["moyenne"]
          and round(100 * 1.3 * .8 * 1.25 * .7, 2) == ex["resultat"] and round(S.geometric_mean(seq) * 100, 2) == ex["geometrique"])
    check("figure: +50 % then -50 % loses 25 %, -13,4 % a year", round(S.geometric_mean([.5, -.5]) * 100, 1) == -13.4)

    def last(*args, **kw):
        return S.project(*args, **kw)[-1]
    cash, prudent, risky = last(10_000, 30, 0, .02), last(10_000, 30, .02, .02), last(10_000, 30, .05, .02)
    check("scenario cash: 10 000 shown, 5 521 real", cash.nominal == 10_000 and round(cash.real) == 5521)
    check("scenario prudent: 18 114 shown, 10 000 real", round(prudent.nominal) == 18114 and round(prudent.real) == 10000)
    check("scenario 5 %: 43 219 shown, 23 860 real", round(risky.nominal) == 43219 and round(risky.real) == 23860)
    plan = last(10_000, 30, .05, .02, monthly_contribution=200)
    check("with 200 € a month: 82 000 paid, 206 295 shown, 113 889 real", plan.contributed == 82_000
          and round(plan.nominal) == 206295 and round(plan.real) == 113889)
    check("the projection starts at year 0 with the capital", S.project(500, 1, .1, .02)[0].nominal == 500)

    fe = {s.id: s.answer for s in catalog.exercise("frais-epargne").steps}
    free, fee, taxed = last(10_000, 30, .06, .02), last(10_000, 30, .06, .02, annual_fee=.015), \
        last(10_000, 30, .06, .02, annual_fee=.015, tax_on_gains=.30)
    check("fees: 57 434,91 without", abs(free.nominal - fe["sans-frais"]) < 0.01)
    check("fees: 36 497,48 with 1,5 %", abs(fee.nominal - fe["avec-frais"]) < 0.01)
    check("fees: 36,5 % less", round((1 - fee.nominal / free.nominal) * 100, 1) == fe["ecart"])
    check("fees: 9 302,38 paid", abs(fee.fees - fe["frais-payes"]) < 0.01)
    check("tax: 28 548,24 after 30 % on the gains, 15 760,65 real", abs(taxed.nominal - fe["apres-impot"]) < 0.01
          and abs(taxed.real - fe["reel"]) < 0.01)
    check("lesson: about 1,5 % real a year, net of everything", round(((taxed.real / 10_000) ** (1 / 30) - 1) * 100, 1) == 1.5)
    check("lesson: 1 % of fees cuts 26 % at 5 % over 30 years",
          round((1 - last(10_000, 30, .05, .02, annual_fee=.01).nominal / risky.nominal) * 100) == 26)

    dv = {s.id: s.answer for s in catalog.exercise("diversification-deux-actifs").steps}
    vol = lambda w, r: round(S.portfolio_volatility(w, .15, .60, r) * 100, 2)
    check("diversification: 32,35 / 15,83 / 15,14 %", vol(.5, .2) == dv["moitie"] and vol(.9, .2) == dv["dix"]
          and vol(.95, .2) == dv["cinq"])
    check("diversification: 37,5 % if perfectly correlated, 30,92 % if independent",
          vol(.5, 1) == dv["correle"] and vol(.5, 0) == dv["independant"])
    check("quiz: the weighted mean at 95/5 would be 17,25 %", round(.95 * 15 + .05 * 60, 2) == 17.25)

    real = {r["mois"][:7]: r for r in catalog.dataset("taux-reel-bce").rows}
    negative = sum(1 for r in real.values() if r["taux_reel"] < 0) / len(real)
    check("data: the real ECB rate is negative in 72 % of months", round(negative * 100) == 72)
    low = min(real.items(), key=lambda kv: kv[1]["taux_reel"])
    high = max(real.items(), key=lambda kv: kv[1]["taux_reel"])
    check("data: its low is -9,85 % in October 2022, deposit rate 0,75 %", low[0] == "2022-10"
          and low[1]["taux_reel"] == -9.85 and low[1]["taux_nominal"] == 0.75)
    check("data: its high is 1,8 % in September 2024", high[0] == "2024-09" and high[1]["taux_reel"] == 1.8)
    check("data: real = nominal minus inflation, every month",
          all(abs(r["taux_reel"] - (r["taux_nominal"] - r["inflation"])) < 0.006 for r in real.values()))

    check("Bitcoin: 93,75 % issued at the April 2024 halving", round(B.supply_after(839_999) / B.total_supply() * 100, 2) == 93.75)
    check("Bitcoin: 20 099 725 BTC at block 971 911, 95,7 %", B.supply_after(971_911) == 2_009_972_500_000_000
          and round(B.supply_after(971_911) / B.total_supply() * 100, 1) == 95.7)
    check("Bitcoin: the last subsidy falls in the 22nd century",
          B.epochs(33)[-1].start_date.year >= 2100 and B.epochs(34)[-1].subsidy == 0)

    from sensitor.academy.ui import savings_view
    fig = savings_view.figure(S.project(10_000, 30, .05, .02, monthly_contribution=200))
    check("the simulator draws three curves over 31 points", len(fig.data) == 3 and len(fig.data[0].x) == 31)
    course = catalog.course("inflation-et-patrimoine")
    check("the course closes path 1", [c.id for c in catalog.path("monnaie-inflation").courses][-1] == course.id)
    check("every lesson is sourced and dated", all(l.sources and l.updated for l in course.lessons))
    final = catalog.quiz("patrimoine-validation")
    taught = {l.id for l in course.lessons} - {"recap-patrimoine"}
    check("validation quiz: covers every lesson", {q.lesson_id for q in final.questions} == taught)
    for bad in (lambda: S.project(-1, 10, .05, .02), lambda: S.project(100, 0, .05, .02),
                lambda: S.project(100, 10, .05, .02, annual_fee=1), lambda: S.portfolio_volatility(1.2, .1, .2, 0),
                lambda: S.doubling_time(0), lambda: S.real_rate(.05, -1)):
        check("savings helpers refuse bad input", raises(bad, ValueError))


def test_risk_path_figures():
    """Path 5: every figure quoted in a lesson, exercise or quiz, recomputed."""
    print("\nPath 5 figures")
    from sensitor.academy import expectancy as X
    check("40 % at 2R: +0.20R", close(X.expectancy_r(.4, 2), .2))
    check("60 % at 0.5R loses 0.1R per trade (-1R over ten)", close(X.expectancy_r(.6, .5) * 10, -1))
    check("35 % at 2.5R: +0.225R", close(X.expectancy_r(.35, 2.5), .225))
    check("60 % at 0.8R: +0.08R", close(X.expectancy_r(.6, .8), .08))
    check("50 % at 1.5R: +0.25R", close(X.expectancy_r(.5, 1.5), .25))
    check("break-even 1R / 1.5R / 2R / 3R", [round(X.breakeven_win_rate(r) * 100) for r in (1, 1.5, 2, 3)]
          == [50, 40, 33, 25])
    check("profit factor 1.33", round(X.profit_factor(.4, 2), 2) == 1.33)
    rows = {(10, 6): (31.3, 83.2), (20, 12): (38.7, 78.1), (50, 30): (46.2, 72.4),
            (100, 60): (50.2, 69.1), (400, 240): (55.1, 64.7)}
    for (n, w), (lo, hi) in rows.items():
        i = X.win_rate_interval(w, n)
        check(f"Wilson interval {w}/{n}", round(i.low * 100, 1) == lo and round(i.high * 100, 1) == hi,
              f"{i.low:.4f} {i.high:.4f}")
    table = {.45: [None, 1.9, 16.0, 31.2, 53.0], .40: [0.9, 20.7, 55.9, 72.0, 86.1],
             .36: [11.0, 60.7, 88.1, 94.3, 98.0]}
    for p, values in table.items():
        for risk, want in zip((0.5, 1, 2, 3, 5), values):
            got = X.ruin_probability(p, 1.5, risk, 200, 20) * 100
            ok = got < 0.1 if want is None else round(got, 1) == want
            check(f"ruin table {p:.0%} at {risk} %", ok, f"{got:.3f}")
    check("ruin agrees with brute force on a small case",
          close(X.ruin_probability(.5, 1, 10, 8, 25), _brute_ruin(.5, 1, 10, 8, 25), 1e-12))

    path = X.equity_path(10000, [1, -1, 2, -1, -1, -1, 1.5, -1, -1, 2, 2, -1, 1], 1)
    dd = X.max_drawdown(path)
    ex = {s.id: s.answer for s in C.load_catalog().exercise("drawdown-serie").steps}
    check("drawdown exercise: mean result", abs(2.5 / 13 - ex["esperance"]) <= 0.006)
    check("drawdown exercise: peak", close(round(path[dd.peak], 2), ex["sommet"]) and dd.peak == 3)
    check("drawdown exercise: trough", close(round(path[dd.trough], 2), ex["creux"]) and dd.trough == 9)
    check("drawdown exercise: max drawdown", abs(dd.pct - ex["drawdown"]) <= 0.01)
    check("drawdown exercise: recovery",
          abs((path[dd.peak] / path[dd.trough] - 1) * 100 - ex["recuperation"]) <= 0.01)
    check("drawdown exercise: final equity 10 241,31", close(round(path[-1], 2), 10241.31))
    double = X.max_drawdown(X.equity_path(10000, [1, -1, 2, -1, -1, -1, 1.5, -1, -1, 2, 2, -1, 1], 2))
    check("at 2 % the drawdown is about twice as deep", 1.8 < double.pct / dd.pct < 2.2, str(double.pct))
    check("12 000 then 10 500: 12.5 %", close(X.max_drawdown([10000, 12000, 10500]).pct, 12.5))

    lim = {s.id: s.answer for s in C.load_catalog().exercise("limites-prop").steps}
    check("prop exercise: 5 losses at 1 %", X.losses_to_limit(5, 1) == lim["pertes-1pct"])
    check("prop exercise: 10 losses at 0.5 %", X.losses_to_limit(5, .5) == lim["pertes-demi"])
    check("prop exercise: 3 losses at 2 %", X.losses_to_limit(5, 2) == lim["pertes-2pct"])
    check("prop exercise: 5 left before the maximum", (95000 - 90000) / 1000 == lim["reste-max"])
    check("validation quiz: 3 losses at 1.5 % for a 4 % limit", X.losses_to_limit(4, 1.5) == 3)

    q = X.final_equity_quantiles(.45, 1.5, 1, 200)
    check("final equity quantiles are ordered", q[0.05] < q[0.5] < q[0.95])
    for bad in (lambda: X.expectancy_r(1.5, 1), lambda: X.breakeven_win_rate(0),
                lambda: X.win_rate_interval(5, 3), lambda: X.ruin_probability(.5, 1, 0, 10, 20),
                lambda: X.max_drawdown([]), lambda: X.losses_to_limit(0, 1)):
        check("path 5 helpers refuse bad input", raises(bad, ValueError))


def _brute_ruin(p, reward, risk, n, threshold):
    from itertools import product
    total = 0.0
    for outcome in product((True, False), repeat=n):
        equity, prob = 1.0, 1.0
        for won in outcome:
            prob *= p if won else 1 - p
        for won in outcome:
            equity *= (1 + risk / 100 * reward) if won else (1 - risk / 100)
            if equity <= 1 - threshold / 100 + 1e-12:
                total += prob
                break
    return total


def test_printable():
    print("\nPrintable resources")
    from sensitor.academy import printable
    catalog = C.load_catalog()
    with_pdf = [r for r in catalog.resources.values() if r.pdf]
    check("every library resource has a PDF", len(with_pdf) == len(catalog.resources))
    for resource in with_pdf:
        check(f"{resource.pdf_name} is a real PDF", resource.read_pdf()[:5] == b"%PDF-")
    built = printable.read_manifest(catalog.root / "resources")
    check("every PDF was built from the current source",
          all(built.get(r.pdf_name) == printable.source_hash(r.file) for r in with_pdf))

    root = _copy_tree()
    sheet = root / "resources" / "fiche-lire-la-structure.md"
    sheet.write_text(sheet.read_text() + "\nUne ligne ajoutée.\n")
    check("editing a sheet without rebuilding its PDF is reported",
          any("PDF à reconstruire" in p for p in C.validate(root)))
    root = _copy_tree()
    (root / "resources" / "checklist-avant-trade.pdf").unlink()
    check("a declared PDF that is missing is refused",
          any("PDF introuvable" in p for p in C.validate(root)))

    out = printable.markdown_to_html("# Titre\n\n*Sous-titre*\n\n## Partie\n\n- **Gras** : texte\n"
                                     "- [ ] Case\n\n1. Un\n2. Deux\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n---\n\nFin & <b>")
    check("headings", "<h1>Titre</h1>" in out and "<h2>Partie</h2>" in out)
    check("emphasis", "<em>Sous-titre</em>" in out and "<strong>Gras</strong>" in out)
    check("task lists", 'class="task"' in out and "Case" in out)
    check("numbered lists", "<ol><li>Un</li><li>Deux</li></ol>" in out)
    check("tables, separator row dropped", "<th>A</th>" in out and "<td>2</td>" in out and "---" not in out)
    check("rules", "<hr>" in out)
    check("text is escaped", "&lt;b&gt;" in out and "&amp;" in out)


def _copy_tree() -> Path:
    target = Path(tempfile.mkdtemp(prefix="academy-content-")) / "academy"
    shutil.copytree(C.CONTENT_ROOT, target)
    return target


def test_validation_catches_mistakes():
    print("\nValidation refuses broken content")

    root = _copy_tree()
    quiz = root / "quizzes" / "check-budget-de-risque.toml"
    quiz.write_text(quiz.read_text().replace("correct = true", "correct = false"))
    problems = C.validate(root)
    check("a question with no right answer", any("aucune bonne réponse" in p for p in problems))
    check("…makes load_catalog raise", raises(lambda: C.load_catalog(root), C.ContentError))

    root = _copy_tree()
    lesson = root / "courses" / "premiers-pas" / "lessons" / "structure-de-marche.md"
    lesson.write_text(lesson.read_text().replace("structure-range.svg", "absente.svg"))
    check("a missing figure", any("figure introuvable" in p for p in C.validate(root)))

    root = _copy_tree()
    lesson = root / "courses" / "premiers-pas" / "lessons" / "budget-de-risque.md"
    lesson.write_text(lesson.read_text().replace('quiz = "check-budget-de-risque"',
                                                 'quiz = "inexistant"'))
    check("a lesson pointing at an unknown quiz",
          any("quiz « inexistant »" in p for p in C.validate(root)))

    root = _copy_tree()
    cur = root / "curriculum.toml"
    cur.write_text(cur.read_text().replace('track = "trading"\nid = "bases-marches"',
                                           'track = "inconnue"\nid = "bases-marches"'))
    check("a path in an unknown track is refused", any("filière inconnue" in p for p in C.validate(root)))

    root = _copy_tree()
    cur = root / "curriculum.toml"
    cur.write_text(cur.read_text().replace('code = "C"\nuniverse = "monnaie"', 'code = "C"\nuniverse = "defi"'))
    check("a track in an unknown universe is refused",
          any("univers « defi » inconnu" in p for p in C.validate(root)))

    root = _copy_tree()
    cur = root / "curriculum.toml"
    cur.write_text(cur.read_text().replace('id = "structure-price-action"\nnumber = 2',
                                           'id = "structure-price-action"\nnumber = 1'))
    check("two paths with one number in a track are refused",
          any("en double dans une filière" in p for p in C.validate(root)))

    root = _copy_tree()
    cur = root / "curriculum.toml"
    cur.write_text(cur.read_text().replace('track = "trading"\nid = "bases-marches"\nnumber = 1',
                                           'track = "crypto"\nid = "bases-marches"\nnumber = 3'))
    problems = C.validate(root)
    check("a track that requires sources refuses lessons without them",
          any("sources manquantes" in p for p in problems) and any("date de mise à jour manquante" in p for p in problems))
    lessons = root / "courses" / "premiers-pas" / "lessons"
    for f in lessons.glob("*.md"):
        f.write_text(f.read_text().replace("+++\n", '+++\nupdated = 2026-10-17\nsources = ["Source de test"]\n', 1))
    check("…and accepts them once sourced and dated",
          not any("manquante" in p for p in C.validate(root)), str([p for p in C.validate(root) if "manquante" in p][:2]))

    root = _copy_tree()
    lesson = root / "courses" / "premiers-pas" / "lessons" / "budget-de-risque.md"
    lesson.write_text(lesson.read_text().replace("+++\n", '+++\nupdated = "17/10/2026"\n', 1))
    check("an update date in the wrong format is refused", any("date de mise à jour invalide" in p for p in C.validate(root)))

    root = _copy_tree()
    (root / "resources" / "checklist-avant-trade.md").unlink()
    problems = C.validate(root)
    check("a resource whose file is missing is refused",
          any("fichier introuvable" in p for p in problems), str(problems))

    root = _copy_tree()
    meta = root / "resources" / "resources.toml"
    meta.write_text(meta.read_text().replace('file = "checklist-avant-trade.md"',
                                             'file = "../curriculum.toml"'))
    check("a resource outside the resources folder is refused",
          any("dans resources/" in p for p in C.validate(root)))

    root = _copy_tree()
    quiz = root / "quizzes" / "check-structure-de-marche.toml"
    text = quiz.read_text()
    quiz.write_text(text.replace('id = "baisse"\ntext = "Une tendance baissière."',
                                 'id = "baisse"\ntext = "Une tendance baissière."\ncorrect = true'))
    check("a single-choice question with two right answers",
          any("plusieurs bonnes réponses" in p for p in C.validate(root)))

    root = _copy_tree()
    orphan = root / "courses" / "premiers-pas" / "lessons" / "orpheline.md"
    orphan.write_text('+++\nid = "orpheline"\ntitle = "x"\n+++\ntexte\n')
    check("a lesson file left out of the course plan",
          any("absente du plan" in p for p in C.validate(root)))

    root = _copy_tree()
    figure = root / "figures" / "carnet-ordres.svg"
    figure.write_text(figure.read_text().replace("</svg>", "<script>alert(1)</script></svg>"))
    check("a figure carrying a script is refused",
          any("script" in p for p in C.validate(root)))


def test_drafts():
    print("\nDrafts stay out of the catalogue")
    root = _copy_tree()
    lesson = root / "courses" / "premiers-pas" / "lessons" / "cas-pratique.md"
    lesson.write_text(lesson.read_text().replace('status = "published"', 'status = "draft"'))
    published = C.load_catalog(root)
    check("a draft lesson is not in the published course",
          published.course("premiers-pas").lesson("cas-pratique") is None)
    check("the following lesson moves up",
          published.course("premiers-pas").lesson("recapitulatif").number == 5)
    preview = C.load_catalog(root, include_drafts=True)
    check("…and is there in preview",
          preview.course("premiers-pas").lesson("cas-pratique") is not None)

    os.environ.pop("SENSITOR_ACADEMY_PREVIEW", None)
    check("preview is off by default", not C.preview_enabled())
    os.environ["SENSITOR_ACADEMY_PREVIEW"] = "1"
    check("SENSITOR_ACADEMY_PREVIEW=1 turns it on", C.preview_enabled())
    os.environ.pop("SENSITOR_ACADEMY_PREVIEW")

    check("the cache returns the same object while nothing changes",
          C.cached_catalog(root, include_drafts=False) is C.cached_catalog(root, include_drafts=False))


def test_markup():
    print("\nLesson markup")
    blocks = M.parse("Intro\n\n::: callout note \"Titre\"\nCorps\n:::\n\nSuite\n"
                     "::: formula\nx = 1\n:::\n::: tool risk-calculator\n:::\n")
    check("splits into blocks", [b.kind for b in blocks] ==
          ["markdown", "callout", "markdown", "formula", "tool"], str([b.kind for b in blocks]))
    check("keeps a quoted callout title", blocks[1].title == "Titre")
    check("defaults a callout title to its kind",
          M.parse("::: callout recap\nx\n:::")[0].title == "Récapitulatif")
    check("an unclosed block is an error",
          raises(lambda: M.parse("::: callout note\nx"), M.MarkupError))
    check("a stray closing fence is an error", raises(lambda: M.parse(":::"), M.MarkupError))
    check("nesting is an error",
          raises(lambda: M.parse("::: callout note\n::: formula\n:::\n:::"), M.MarkupError))
    check("an unknown directive is an error",
          raises(lambda: M.parse("::: video x\n:::"), M.MarkupError))
    check("an unknown callout kind is an error",
          raises(lambda: M.parse("::: callout shiny\nx\n:::"), M.MarkupError))
    check("an unknown tool is an error",
          raises(lambda: M.parse("::: tool magic\n:::"), M.MarkupError))


# =============================================================================
# QUIZ
# =============================================================================

def test_quiz_scoring():
    print("\nQuiz scoring")
    catalog = C.load_catalog()
    quiz = catalog.quiz("check-fonctionnement-marche")

    perfect = Q.grade(quiz, {"prix-achat": "ask", "spread": ["ecart"],
                             "spread-large": ["annonce", "ferie", "nuit"]})
    check("all right: 3 / 3", perfect.correct_count == 3 and perfect.passed)
    check("score is a fraction", perfect.score == 1.0)
    check("no mistakes to review", perfect.mistakes == ())

    partial = Q.grade(quiz, {"prix-achat": "ask", "spread": ["ecart"],
                             "spread-large": ["annonce", "ferie"]})
    check("a multiple-answer question with a missing answer is not correct",
          partial.results[2].status == Q.INCORRECT)
    check("no partial credit", partial.correct_count == 2)

    extra = Q.grade(quiz, {"spread-large": ["annonce", "ferie", "nuit", "chevauchement"]})
    check("an extra wrong answer makes it incorrect", extra.results[2].status == Q.INCORRECT)
    check("missing questions are unanswered, not wrong",
          [r.status for r in extra.results[:2]] == [Q.UNANSWERED, Q.UNANSWERED])
    check("unanswered are counted", extra.unanswered_count == 2)
    check("…and do not pass", not extra.passed)

    check("an unknown question id is refused",
          raises(lambda: Q.grade(quiz, {"nope": ["a"]}), ValueError))
    check("an unknown option id is refused",
          raises(lambda: Q.grade(quiz, {"spread": ["zzz"]}), ValueError))
    check("two answers to a single-choice question are refused",
          raises(lambda: Q.grade(quiz, {"spread": ["ecart", "commission"]}), ValueError))
    check("duplicate selections collapse",
          Q.normalise_responses(quiz, {"spread": ["ecart", "ecart"]})["spread"] == ("ecart",))

    final = catalog.quiz("premiers-pas-validation")
    key = {q.id: sorted(q.correct_ids) for q in final.questions}
    seven = dict(list(key.items())[:7])
    result = Q.grade(final, seven)
    check("exactly 7 / 10 passes the 0.7 threshold", result.correct_count == 7 and result.passed)
    six = dict(list(key.items())[:6])
    check("6 / 10 does not", not Q.grade(final, six).passed)
    check("required count for awkward thresholds", Q.required_correct(3, 0.66) == 2
          and Q.required_correct(3, 0.67) == 3 and Q.required_correct(10, 0.7) == 7)

    public = Q.public_view(final)
    keys = {k for q in public["questions"] for o in q["options"] for k in o} | \
           {k for q in public["questions"] for k in q}
    check("the public view carries no answer key",
          not keys & {"correct", "explanation"}, str(keys))
    feedback = Q.feedback_view(final, result)
    check("feedback carries every explanation",
          all(o["explanation"] for q in feedback["questions"] for o in q["options"]))
    check("feedback links mistakes back to lessons",
          all(q["lesson_id"] for q in feedback["questions"] if q["status"] != Q.CORRECT))
    check("stored responses round-trip", Q.grade(final, result.responses()).correct_count == 7)


def test_exercises():
    print("\nNumeric exercises")
    check("French decimals", E.parse_number("0,15") == 0.15)
    check("thousands with spaces", E.parse_number("1 234,5") == 1234.5)
    check("non-breaking spaces and currency", E.parse_number("8 000 $") == 8000)
    check("dot decimals", E.parse_number("2.40") == 2.4)
    check("blank is None", E.parse_number("  ") is None)
    check("garbage raises", raises(lambda: E.parse_number("abc"), ValueError))
    check("the typographic minus of the solutions", E.parse_number("\u22120,06") == -0.06)
    check("a hyphen minus too", E.parse_number("-0,90") == -0.9)
    check("a trailing percent sign", E.parse_number("57 %") == 57)
    check("a trailing R", E.parse_number("2,28R") == 2.28 and E.parse_number("1,10 R") == 1.1)
    check("a unit alone is still blank", E.parse_number("%") is None)
    check("letters elsewhere still raise", raises(lambda: E.parse_number("R2"), ValueError))

    step = C.ExerciseStep("x", "?", "$", 60, 0.01, "…")
    check("exact answer is correct", E.check_step(step, "60").status == E.CORRECT)
    check("within tolerance is correct", E.check_step(step, "60,01").status == E.CORRECT)
    check("outside tolerance is incorrect", E.check_step(step, "61").status == E.INCORRECT)
    check("blank is unanswered", E.check_step(step, "").status == E.UNANSWERED)
    check("garbage is invalid, not wrong", E.check_step(step, "soixante").status == E.INVALID)


# =============================================================================
# RISK
# =============================================================================

def test_risk():
    print("\nRisk calculations")
    check("risk amount", close(R.risk_amount(10_000, 1), 100))
    check("risk amount, fractional percent", close(R.risk_amount(20_000, 0.5), 100))

    short = R.plan(equity=5_000, risk_pct=2, entry=2000, stop=2010, direction=R.SHORT,
                   target=1970)
    check("short: stop above is accepted", close(short.stop_distance, 10))
    check("short: 3R target", close(short.reward_to_risk, 3))
    check("short: planned reward", close(short.planned_reward, 300))
    check("no spec, no position size", short.position is None)
    check("the costs caveat travels with the plan", any("spread" in n for n in short.notes))

    errors = lambda **kw: _errors(kw)  # noqa: E731
    base = dict(equity=10_000, risk_pct=1, entry=100, stop=95, direction=R.LONG)
    check("equity must be positive", "equity" in errors(**{**base, "equity": 0}))
    check("risk must be > 0", "risk_pct" in errors(**{**base, "risk_pct": 0}))
    check("risk must be ≤ 100", "risk_pct" in errors(**{**base, "risk_pct": 150}))
    check("NaN is refused", "risk_pct" in errors(**{**base, "risk_pct": float("nan")}))
    check("a long stop above entry is refused", "stop" in errors(**{**base, "stop": 105}))
    check("a short stop below entry is refused",
          "stop" in errors(**{**base, "direction": R.SHORT}))
    check("a stop equal to entry is refused", "stop" in errors(**{**base, "stop": 100}))
    check("a long target below entry is refused", "target" in errors(**{**base, "target": 90}))
    check("an unknown direction is refused", "direction" in errors(**{**base, "direction": "up"}))
    check("messages are in French", "achat" in errors(**{**base, "stop": 105})["stop"])
    check("a zero contract size is refused",
          "contract_size" in errors(**base, spec=R.InstrumentSpec(contract_size=0)))

    spec = R.InstrumentSpec(contract_size=100, quote_to_account=0.9, lot_step=0.01, min_lot=0.01)
    gold = R.plan(equity=10_000, risk_pct=1, entry=2000, stop=1990, direction=R.LONG, spec=spec)
    check("conversion rate enters the value per point", close(gold.position.value_per_point, 90))
    check("size with conversion: 100 / (10 × 90) → 0.11", close(gold.position.lots, 0.11))
    check("rounding never raises the risk", gold.position.effective_risk <= gold.risk_amount + 1e-9)
    check("units follow lots", close(gold.position.units, 11))

    tiny = R.plan(equity=100, risk_pct=0.5, entry=1.1, stop=1.0, direction=R.LONG,
                  spec=R.InstrumentSpec(contract_size=100_000, lot_step=0.01, min_lot=0.01))
    check("a size below the broker minimum is flagged", tiny.position.below_minimum)
    check("…and explained", any("minimum" in n for n in tiny.notes))

    no_step = R.position_size(100, 0.003, R.InstrumentSpec(contract_size=100_000))
    check("without a lot step the raw size is kept", close(no_step.lots, 1 / 3, 1e-9))
    exact = R.position_size(60, 0.004, R.InstrumentSpec(contract_size=100_000, lot_step=0.01))
    check("an exact multiple is not rounded down by float noise", close(exact.lots, 0.15))

    flat = R.losing_streak(10_000, 10, 12, compounding=False)
    check("fixed-amount losses cannot go below zero", flat[-1].equity == 0)
    check("recovery from a total loss is infinite", math.isinf(flat[-1].recovery_pct))
    check("streak path starts at the initial equity",
          R.losing_streak(10_000, 1, 3)[0].equity == 10_000)
    check("losses must be a non-negative integer",
          raises(lambda: R.losing_streak(10_000, 1, -1), R.RiskInputError))

    check("a streak longer than the series is impossible", R.streak_probability(3, 5, 0.5) == 0)
    check("a 1-loss streak with no wins is certain", close(R.streak_probability(10, 1, 0.0), 1))
    check("with every trade won, no streak", R.streak_probability(10, 1, 1.0) == 0)
    check("one trade, one loss streak = loss rate", close(R.streak_probability(1, 1, 0.3), 0.7))
    check("brute force agrees on a small case", close(R.streak_probability(6, 3, 0.5),
                                                       _brute_force(6, 3, 0.5)))
    check("win rate outside 0–1 is refused",
          raises(lambda: R.streak_probability(10, 2, 1.5), R.RiskInputError))


def _errors(kwargs) -> dict:
    try:
        R.plan(**kwargs)
    except R.RiskInputError as exc:
        return exc.errors
    return {}


def _brute_force(n: int, k: int, win: float) -> float:
    from itertools import product
    total = 0.0
    for outcome in product((True, False), repeat=n):
        run = best = 0
        for won in outcome:
            run = 0 if won else run + 1
            best = max(best, run)
        if best >= k:
            p = 1.0
            for won in outcome:
                p *= win if won else 1 - win
            total += p
    return total


# =============================================================================
# PROGRESS & ACCESS
# =============================================================================

def test_progress_logic():
    print("\nProgress")
    catalog = C.load_catalog()
    course = catalog.course("premiers-pas")

    empty = P.course_progress(course, set())
    check("nothing done: 0 / 6", empty.done == 0 and empty.total == 6)
    check("next is the first lesson", empty.next_lesson.id == "fonctionnement-marche")
    check("final quiz not passed", empty.final_quiz_passed is False)

    some = P.course_progress(course, {"fonctionnement-marche", "structure-de-marche"})
    check("2 / 6", some.done == 2 and math.isclose(some.fraction, 2 / 6))
    check("next is the first unfinished, not the last finished + 1",
          some.next_lesson.id == "ordres-et-couts")

    stale = P.course_progress(course, {"fonctionnement-marche", "lecon-retiree"})
    check("a withdrawn lesson does not count", stale.done == 1)

    everything = P.course_progress(course, {l.id for l in course.lessons},
                                   passed_quizzes={"premiers-pas-validation"})
    check("all lessons done", everything.lessons_finished and everything.next_lesson is None)
    check("final quiz passed", everything.final_quiz_passed is True)

    step = P.next_step(catalog, {}, set())
    check("a new member starts with the first trading course", step.kind == "lesson"
          and step.lesson.id == "fonctionnement-marche")
    step = P.next_step(catalog, {"premiers-pas": {"fonctionnement-marche"}}, set())
    check("a started member is sent to the next lesson", step.lesson.id == "ordres-et-couts")
    step = P.next_step(catalog, {"premiers-pas": {l.id for l in course.lessons}}, set())
    check("lessons done, quiz not passed: the final quiz", step.kind == "final_quiz")
    step = P.next_step(catalog, {"premiers-pas": {l.id for l in course.lessons}},
                       {"premiers-pas-validation"})
    check("trading course 1 finished: the next trading course starts, not the top of the programme",
          step.kind == "lesson" and step.course.id == "lire-la-structure" and step.lesson.id == "swings-definition")
    step = P.next_step(catalog, {"la-monnaie": {"fonctions-monnaie"}}, set())
    check("a started money course is resumed", step.lesson.id == "histoire-monnaie")
    courses = catalog.available_courses()
    everything = {c.id: {l.id for l in c.lessons} for c in courses}
    step = P.next_step(catalog, everything, {c.final_quiz_id for c in courses})
    check("everything done: explore", step.kind == "explore")


def test_access():
    print("\nAccess policy")
    catalog = C.load_catalog()
    course = catalog.course("premiers-pas")
    public, member = course.lesson("fonctionnement-marche"), course.lesson("budget-de-risque")
    check("anyone reads a public lesson", access.can_read_lesson(public, None))
    check("a visitor cannot read a member lesson", not access.can_read_lesson(member, None))
    check("a member can", access.can_read_lesson(member, "a@example.com"))
    check("a public lesson's quiz is open to visitors",
          access.can_take_quiz(catalog, catalog.quiz("check-fonctionnement-marche"), None))
    check("a member lesson's quiz is not",
          not access.can_take_quiz(catalog, catalog.quiz("check-budget-de-risque"), None))
    check("the public sheet downloads without an account",
          access.can_download(catalog.resource("fiche-vocabulaire-execution"), None))
    check("the member checklist does not",
          not access.can_download(catalog.resource("checklist-avant-trade"), None))


# =============================================================================
# STORE
# =============================================================================

def test_store():
    print("\nStored progress and attempts")
    from sensitor.database import Store
    path = os.path.join(tempfile.mkdtemp(prefix="academy-store-"), "t.db")
    store = Store(path)
    alice, bob = "alice@example.com", "Bob@Example.com"

    store.mark_lesson_complete(alice, "premiers-pas", "fonctionnement-marche", version=1)
    store.mark_lesson_complete(alice, "premiers-pas", "ordres-et-couts", version=1)
    store.mark_lesson_complete(alice, "premiers-pas", "ordres-et-couts", version=2)
    rows = store.completed_lessons(alice)
    check("completions are stored once per lesson", len(rows) == 2, str(rows))
    check("re-completing records the newer version",
          [r["lesson_version"] for r in rows if r["lesson_id"] == "ordres-et-couts"] == [2])
    check("filtering by course", len(store.completed_lessons(alice, "premiers-pas")) == 2
          and store.completed_lessons(alice, "autre") == [])

    first = store.record_quiz_attempt(alice, "q1", version=1, correct=2, total=3,
                                      passed=True, responses={"a": ["x"]})
    second = store.record_quiz_attempt(alice, "q1", version=1, correct=1, total=3,
                                       passed=False, responses={"a": ["y"]})
    attempts = store.quiz_attempts(alice, "q1")
    check("attempt ids are returned", second > first > 0)
    check("attempts come back newest first", [a["id"] for a in attempts] == [second, first])
    check("responses are decoded", attempts[0]["responses"] == {"a": ["y"]})
    check("passed is a bool", attempts[1]["passed"] is True)

    check("bob sees none of alice's progress", store.completed_lessons(bob) == [])
    check("bob sees none of alice's attempts", store.quiz_attempts(bob) == [])
    store.mark_lesson_complete(bob, "premiers-pas", "structure-de-marche")
    check("bob's address is normalised",
          len(store.completed_lessons("bob@example.com")) == 1)
    check("alice still has exactly her two", len(store.completed_lessons(alice)) == 2)

    store.unmark_lesson(alice, "premiers-pas", "fonctionnement-marche")
    check("a lesson can be marked unread again", len(store.completed_lessons(alice)) == 1)

    check("a quiz attempt with correct > total is refused by the database",
          raises(lambda: store.record_quiz_attempt(alice, "q1", version=1, correct=4,
                                                   total=3, passed=True, responses={})))
    check("an empty address is refused",
          raises(lambda: store.mark_lesson_complete("", "c", "l"), ValueError))

    exported = store.export_user(alice)
    check("the export includes progress", len(exported["lesson_progress"]) == 1)
    check("the export includes attempts", len(exported["quiz_attempts"]) == 2)
    counts = store.delete_user(alice)
    check("deletion reports what it removed",
          counts["lesson_progress"] == 1 and counts["quiz_attempts"] == 2, str(counts))
    check("alice's rows are gone",
          store.completed_lessons(alice) == [] and store.quiz_attempts(alice) == [])
    check("bob's survive", len(store.completed_lessons(bob)) == 1)

    from sensitor.database.models import SCHEMA_VERSION
    version = store._read("PRAGMA user_version")[0][0]
    check("a fresh database is stamped with the current version", version == SCHEMA_VERSION)


def test_upgrade_from_v5():
    print("\nUpgrading a version-5 database")
    import sqlite3
    from sensitor.database import Store
    path = os.path.join(tempfile.mkdtemp(prefix="academy-upgrade-"), "old.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (email TEXT PRIMARY KEY, tier TEXT NOT NULL DEFAULT 'free',
            display_name TEXT, password_hash TEXT, last_login_at TEXT,
            failed_logins INTEGER NOT NULL DEFAULT 0, locked_until TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        INSERT INTO users (email, created_at, updated_at) VALUES ('old@example.com', 'x', 'x');
        PRAGMA user_version = 5;
    """)
    conn.commit()
    conn.close()
    store = Store(path)
    check("the existing user survives", store.get_user("old@example.com") is not None)
    store.mark_lesson_complete("old@example.com", "premiers-pas", "fonctionnement-marche")
    check("and can record progress at once",
          len(store.completed_lessons("old@example.com")) == 1)
    from sensitor.database.models import SCHEMA_VERSION
    check("the database is now at the current version",
          store._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION)


def main() -> int:
    test_real_catalog()
    test_lesson_figures_match_the_calculator()
    test_structure_figures()
    test_liquidity_figures()
    test_zone_figures()
    test_psychology_figures()
    test_backtest_figures()
    test_macro_figures()
    test_bitcoin_course_figures()
    test_crypto_course_figures()
    test_process_figures()
    test_reserve_figures()
    test_analysis_figures()
    test_invest_figures()
    test_visual_figures()
    test_onchain_figures()
    test_bitcoin_issuance()
    test_datasets_and_charts()
    test_access_levels()
    test_money_figures()
    test_inflation_figures()
    test_savings_figures()
    test_risk_path_figures()
    test_printable()
    test_validation_catches_mistakes()
    test_drafts()
    test_markup()
    test_quiz_scoring()
    test_exercises()
    test_risk()
    test_progress_logic()
    test_access()
    test_store()
    test_upgrade_from_v5()
    print(f"\n{CHECKS} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
