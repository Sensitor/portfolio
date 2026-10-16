"""
Sensitor Academy over HTTP.

Checks the access policy (public lessons open, member lessons 401 without a
token), that the answer key is never served before a submission, that attempts
and progress are stored per caller and invisible to anyone else, and that the
risk endpoint returns the same figures as the module behind it.

`streamlit` is poisoned before the imports, as in `test_api.py`: the API process
has no UI runtime.

Run with:  python tests/test_academy_api.py
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["streamlit"] = None

WORK = tempfile.mkdtemp(prefix="sensitor-academy-api-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "api.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_ACADEMY_PREVIEW", None)

from fastapi.testclient import TestClient  # noqa: E402

from sensitor.api import deps  # noqa: E402
from sensitor.api.app import create_app  # noqa: E402
from sensitor.core.auth import Auth  # noqa: E402
from sensitor.database import Store  # noqa: E402

ALICE, BOB = "alice@example.com", "bob@example.com"
PASSWORD = "correct-horse-battery"
FAILURES: list[str] = []
COUNT = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global COUNT
    COUNT += 1
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def world():
    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")
    alice = auth.sign_up(ALICE, PASSWORD).token
    bob = auth.sign_up(BOB, PASSWORD).token
    deps.get_store.cache_clear()
    return TestClient(create_app()), alice, bob


def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    client, alice, bob = world()

    print("\nCatalogue")
    r = client.get("/academy/catalog")
    check("the catalogue is public", r.status_code == 200)
    paths = r.json()["paths"]
    check("ten paths", len(paths) == 10)
    from sensitor.academy.content import load_catalog
    catalog = load_catalog()
    check("the available paths are the published ones",
          [p["id"] for p in paths if p["available"]] == [p.id for p in catalog.paths if p.is_available])
    check("planned paths list no course",
          all(not p["courses"] for p in paths if p["status"] == "planned"))

    r = client.get("/academy/courses/premiers-pas")
    check("a course is public", r.status_code == 200)
    check("anonymous: no progress", r.json()["progress"] is None)
    check("six lessons across modules",
          sum(len(m["lessons"]) for m in r.json()["modules"]) == 6)
    check("an unknown course is 404", client.get("/academy/courses/nope").status_code == 404)

    print("\nLessons")
    r = client.get("/academy/courses/premiers-pas/lessons/fonctionnement-marche")
    check("a public lesson reads without a token", r.status_code == 200)
    lesson = r.json()
    check("blocks are served", lesson["blocks"] and lesson["blocks"][0]["kind"] == "markdown")
    figure = next(b for b in lesson["blocks"] if b["kind"] == "figure")
    check("figures carry their SVG", figure["svg"].lstrip().startswith("<svg"))
    check("navigation ids", lesson["previous_id"] is None and lesson["next_id"] == "ordres-et-couts")

    r = client.get("/academy/courses/premiers-pas/lessons/budget-de-risque")
    check("a member lesson is 401 without a token", r.status_code == 401)
    r = client.get("/academy/courses/premiers-pas/lessons/budget-de-risque", headers=h(alice))
    check("and 200 with one", r.status_code == 200)
    check("the risk tool block is served",
          any(b["kind"] == "tool" and b["tool"] == "risk-calculator" for b in r.json()["blocks"]))
    r = client.get("/academy/courses/premiers-pas/lessons/cas-pratique", headers=h(alice))
    exercise = next(b for b in r.json()["blocks"] if b["kind"] == "exercise")
    check("exercise steps are served without their answers",
          exercise["steps"] and all(set(s) == {"id", "prompt", "unit"} for s in exercise["steps"]))
    check("an unknown lesson is 404",
          client.get("/academy/courses/premiers-pas/lessons/nope").status_code == 404)
    r = client.get("/academy/courses/premiers-pas/lessons/budget-de-risque",
                   headers=h("forged-token"))
    check("a forged token is treated as anonymous", r.status_code == 401)

    print("\nQuizzes")
    r = client.get("/academy/quizzes/check-fonctionnement-marche")
    check("a public lesson's quiz is open", r.status_code == 200)
    keys = {k for q in r.json()["questions"] for o in q["options"] for k in o}
    check("no answer key before submission", keys == {"id", "text"}, str(keys))
    check("a member lesson's quiz is 401 anonymously",
          client.get("/academy/quizzes/check-budget-de-risque").status_code == 401)
    check("an unknown quiz is 404", client.get("/academy/quizzes/nope").status_code == 404)

    answers = {"prix-achat": ["ask"], "spread": ["ecart"],
               "spread-large": ["annonce", "ferie", "nuit"]}
    r = client.post("/academy/quizzes/check-fonctionnement-marche/attempts",
                    json={"responses": answers})
    check("an anonymous attempt on a public quiz is graded", r.status_code == 200)
    check("…and not stored", r.json()["stored"] is False and r.json()["attempt_id"] is None)
    check("3 / 3 passes", r.json()["correct"] == 3 and r.json()["passed"] is True)

    r = client.post("/academy/quizzes/check-fonctionnement-marche/attempts",
                    json={"responses": {"spread": ["commission"]}}, headers=h(alice))
    body = r.json()
    check("a member attempt is stored", body["stored"] is True and body["attempt_id"])
    check("unanswered questions are reported", body["unanswered"] == 2)
    wrong = next(q for q in body["questions"] if q["id"] == "spread")
    check("the wrong choice is explained",
          wrong["status"] == "incorrect"
          and next(o for o in wrong["options"] if o["id"] == "commission")["explanation"])
    check("and the lesson to reread is named", wrong["lesson_id"] == "fonctionnement-marche")

    r = client.post("/academy/quizzes/check-fonctionnement-marche/attempts",
                    json={"responses": {"spread": ["zzz"]}}, headers=h(alice))
    check("an unknown option is 422, not a wrong answer", r.status_code == 422)
    r = client.post("/academy/quizzes/check-fonctionnement-marche/attempts",
                    json={"responses": {"spread": ["ecart", "commission"]}}, headers=h(alice))
    check("two answers to a single-choice question is 422", r.status_code == 422)

    r = client.get("/academy/quizzes/check-fonctionnement-marche/attempts", headers=h(alice))
    check("alice sees her stored attempt", r.status_code == 200 and len(r.json()) == 1)
    r = client.get("/academy/quizzes/check-fonctionnement-marche/attempts", headers=h(bob))
    check("bob sees none of alice's attempts", r.status_code == 200 and r.json() == [])
    check("attempt history needs a token",
          client.get("/academy/quizzes/check-fonctionnement-marche/attempts").status_code == 401)

    print("\nProgress")
    r = client.post("/academy/courses/premiers-pas/lessons/fonctionnement-marche/complete")
    check("completing needs a token", r.status_code == 401)
    r = client.post("/academy/courses/premiers-pas/lessons/fonctionnement-marche/complete",
                    headers=h(alice))
    check("completing works", r.status_code == 204)
    r = client.post("/academy/courses/premiers-pas/lessons/nope/complete", headers=h(alice))
    check("completing an unknown lesson is 404", r.status_code == 404)

    course = client.get("/academy/courses/premiers-pas", headers=h(alice)).json()
    check("the course shows alice 1 / 6", course["progress"]["done"] == 1
          and course["progress"]["total"] == 6)
    check("and her next lesson", course["progress"]["next_lesson_id"] == "ordres-et-couts")
    course = client.get("/academy/courses/premiers-pas", headers=h(bob)).json()
    check("bob is still at 0 / 6", course["progress"]["done"] == 0)

    progress = client.get("/academy/progress", headers=h(alice)).json()
    check("progress names the next step", progress["next"] == {
        "kind": "lesson", "course_id": "premiers-pas", "lesson_id": "ordres-et-couts"})
    check("progress lists recent attempts", len(progress["recent_attempts"]) == 1)
    check("progress needs a token", client.get("/academy/progress").status_code == 401)

    r = client.delete("/academy/courses/premiers-pas/lessons/fonctionnement-marche/complete",
                      headers=h(alice))
    check("a completion can be undone", r.status_code == 204)
    check("…and progress follows",
          client.get("/academy/courses/premiers-pas", headers=h(alice)).json()
          ["progress"]["done"] == 0)

    print("\nLibrary")
    r = client.get("/academy/resources")
    check("the library lists every real resource",
          r.status_code == 200 and len(r.json()) == len(catalog.resources))
    r = client.get("/academy/resources/fiche-vocabulaire-execution/download")
    check("a public sheet downloads anonymously",
          r.status_code == 200 and r.text.startswith("# Le vocabulaire"))
    check("…as an attachment", "attachment" in r.headers.get("content-disposition", ""))
    check("a member resource is 401 anonymously",
          client.get("/academy/resources/checklist-avant-trade/download").status_code == 401)
    check("and downloads with a token",
          client.get("/academy/resources/checklist-avant-trade/download",
                     headers=h(bob)).status_code == 200)
    r = client.get("/academy/resources/fiche-vocabulaire-execution/download?format=pdf")
    check("the PDF downloads", r.status_code == 200 and r.content[:5] == b"%PDF-"
          and r.headers["content-type"] == "application/pdf")
    check("a member PDF is 401 anonymously",
          client.get("/academy/resources/checklist-avant-trade/download?format=pdf").status_code == 401)
    check("an unknown format is refused",
          client.get("/academy/resources/fiche-vocabulaire-execution/download?format=docx").status_code == 422)
    check("the resource list names its PDF",
          all(item["pdf"] for item in client.get("/academy/resources").json()))
    check("an unknown resource is 404",
          client.get("/academy/resources/nope/download").status_code == 404)

    print("\nRisk lab")
    r = client.post("/academy/risk/plan", json={
        "equity": 10000, "risk_pct": 1, "entry": 1.0850, "stop": 1.0820,
        "direction": "long", "target": 1.0910, "contract_size": 100000,
        "lot_step": 0.01, "pip_size": 0.0001})
    plan = r.json()
    check("a plan is computed", r.status_code == 200)
    check("same figures as the lesson",
          abs(plan["risk_amount"] - 100) < 1e-9 and abs(plan["position"]["lots"] - 0.33) < 1e-9
          and abs(plan["reward_to_risk"] - 2) < 1e-9)
    r = client.post("/academy/risk/plan", json={
        "equity": 10000, "risk_pct": 1, "entry": 100, "stop": 105, "direction": "long"})
    check("an inconsistent stop is 422", r.status_code == 422)
    check("…with the field named", "stop" in r.json()["detail"])
    r = client.post("/academy/risk/plan", json={
        "equity": 10000, "risk_pct": 1, "entry": 100, "stop": 95, "direction": "long"})
    check("without a spec, no position size", r.status_code == 200 and r.json()["position"] is None)

    r = client.post("/academy/risk/expectancy", json={"win_rate": 0.45, "reward_r": 1.5, "risk_pct": 2,
                                                      "trades": 200, "threshold_pct": 20})
    body = r.json()
    check("expectancy endpoint answers", r.status_code == 200)
    check("same figures as the lesson", abs(body["expectancy_r"] - 0.125) < 1e-9
          and round(body["ruin_probability"] * 100, 1) == 16.0 and abs(body["breakeven_win_rate"] - 0.4) < 1e-9)
    check("an impossible win rate is 422",
          client.post("/academy/risk/expectancy", json={"win_rate": 1.5, "reward_r": 1.5, "risk_pct": 2,
                                                         "trades": 200, "threshold_pct": 20}).status_code == 422)

    print("\nThe reflection journal")
    for method, path in (("GET", "/journal"), ("POST", "/journal"), ("DELETE", "/journal/1"),
                         ("GET", "/journal/summary")):
        check(f"{method} {path} without a token is 401", client.request(method, path).status_code == 401)
    check("the entry kinds are public", client.get("/journal/kinds").status_code == 200
          and [k["id"] for k in client.get("/journal/kinds").json()] == ["pre", "post", "free"])
    r = client.post("/journal", json={"kind": "pre", "body": " Plan du jour. ", "mood": 3}, headers=h(alice))
    check("a note is created", r.status_code == 201 and r.json()["id"] > 0, r.text)
    note_id = r.json()["id"]
    mine = client.get("/journal", headers=h(alice)).json()
    check("and listed for its owner, trimmed", [e["body"] for e in mine] == ["Plan du jour."])
    check("bob lists nothing", client.get("/journal", headers=h(bob)).json() == [])
    check("bob cannot delete it: 404, like a missing note",
          client.delete(f"/journal/{note_id}", headers=h(bob)).status_code == 404)
    check("it is still there", len(client.get("/journal", headers=h(alice)).json()) == 1)
    for label, payload in (("an unknown kind", {"kind": "diagnostic", "body": "x"}),
                           ("an empty note", {"kind": "pre", "body": "  "}),
                           ("a mood of 7", {"kind": "pre", "body": "x", "mood": 7}),
                           ("an invented question", {"kind": "pre", "body": "x", "prompt": "Inventée ?"})):
        check(f"{label} is 422", client.post("/journal", json=payload, headers=h(alice)).status_code == 422)
    summary = client.get("/journal/summary", headers=h(alice)).json()
    check("the summary counts with its sample size",
          summary["total"] == 1 and summary["moods"] == [{"kind": "pre", "average": 3.0, "n": 1}], str(summary))
    check("the owner deletes it", client.delete(f"/journal/{note_id}", headers=h(alice)).status_code == 204)
    check("and it is gone", client.get("/journal", headers=h(alice)).json() == [])
    params = {p["name"] for route in client.get("/openapi.json").json()["paths"].values()
              for op in route.values() for p in op.get("parameters", [])}
    check("no journal route takes an address", not params & {"email", "user", "user_email"})

    print(f"\n{COUNT} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
