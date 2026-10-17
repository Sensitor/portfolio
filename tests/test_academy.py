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
    check("four tracks, Bitcoin first", [t.id for t in catalog.tracks]
          == ["monnaie-bitcoin", "crypto", "investissement", "trading"])
    trading = catalog.paths_in("trading")
    check("the ten trading paths keep their numbers", [p.number for p in trading] == list(range(1, 11)))
    check("paths are ordered by track, then number",
          [p.track for p in catalog.paths] == sorted((p.track for p in catalog.paths),
                                                     key=[t.id for t in catalog.tracks].index))
    check("every path belongs to a known track", all(catalog.track(p.track) for p in catalog.paths))
    check("a path is named by its track", catalog.path("structure-price-action").label == "Trading · Parcours 02"
          and catalog.path("bitcoin").label == "Monnaie et Bitcoin · Parcours 02")
    check("the new tracks are announced, not open yet",
          all(p.status == C.PLANNED for t in ("monnaie-bitcoin", "crypto", "investissement")
              for p in catalog.paths_in(t)) and len(catalog.paths) == 16)
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
    check("a new member is sent to lesson 1", step.kind == "lesson"
          and step.lesson.id == "fonctionnement-marche")
    step = P.next_step(catalog, {"premiers-pas": {"fonctionnement-marche"}}, set())
    check("a started member is sent to the next lesson", step.lesson.id == "ordres-et-couts")
    step = P.next_step(catalog, {"premiers-pas": {l.id for l in course.lessons}}, set())
    check("lessons done, quiz not passed: the final quiz", step.kind == "final_quiz")
    step = P.next_step(catalog, {"premiers-pas": {l.id for l in course.lessons}},
                       {"premiers-pas-validation"})
    check("course 1 finished: the next course starts", step.kind == "lesson"
          and step.course.id == "lire-la-structure" and step.lesson.id == "swings-definition")
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
    test_bitcoin_issuance()
    test_datasets_and_charts()
    test_access_levels()
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
