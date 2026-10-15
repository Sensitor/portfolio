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
    check("exactly one path is open", [p.id for p in available] == ["bases-marches"],
          str([p.id for p in available]))
    check("ten paths in the curriculum", len(catalog.paths) == 10)
    check("paths are in programme order",
          [p.number for p in catalog.paths] == list(range(1, 11)))
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
    check("a fresh database is stamped with the current version", version == SCHEMA_VERSION == 6)


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
    check("the database is now version 6", store._read("PRAGMA user_version")[0][0] == 6)


def main() -> int:
    test_real_catalog()
    test_lesson_figures_match_the_calculator()
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
