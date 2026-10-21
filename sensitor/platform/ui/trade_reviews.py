"""
Reviews by a coach: the member's request, the member's answers, the coach's queue.

What crosses from one account to another is exactly what the member sends: a
frozen copy of one closed trade, its automatic review, the plan, and a question.
The coach sees a pseudonym. The queue and the answer go through store methods
that check the coach role inside their own query, and this page checks it again
before drawing anything, so a member who opens the coach page sees nothing but
a notice.

The coach's form is built for pedagogy on a closed trade: marks on four axes,
what was done well, what to work on, and Academy lessons. It carries the
reminder that no recommendation on a future trade belongs in it.
"""

from __future__ import annotations

import streamlit as st

from ...trading import coaching as C
from ...trading import review as R
from ...trading.models import Trade
from ...trading.setups import mistake_label, setup_label
from .. import spaces
from . import runtime as rt
from . import trade_visuals as V
from .components import (crumbs, date_fr, esc, footer, hexmark, html, icon, note, notice,
                         page_header, pill, section, tap)
from .trading_journal import flash, nav, show_flash


def _quota(email: str) -> tuple[int, int]:
    store = rt.get_store()
    quota = C.monthly_quota(rt.tier(email))
    return store.count_review_requests(email, C.month_start()), quota


# ── On the trade page ────────────────────────────────────────────────────────

def request_form(trade: Trade, review: R.TradeReview | None, plan: R.TradingPlan | None, email: str) -> None:
    store = rt.get_store()
    open_id = store.open_review_for_trade(email, trade.id)
    if open_id:
        html(f'<div class="sx-j-banner">{icon("clock")}<div><b>En attente</b>Votre demande est entre les '
             'mains des coachs. La réponse arrivera dans l\'onglet Revues.</div></div>')
        rt.link("Voir mes demandes", "journal_reviews", key="req_see", review=str(open_id))
        return
    answered = [r for r in store.review_requests(email) if r["trade_id"] == trade.id and r["status"] == "answered"]
    if answered:
        rt.link("Lire la revue du coach sur ce trade", "journal_reviews", key="req_read", kind="primary",
                review=str(answered[0]["id"]))
    used, quota = _quota(email)
    reason = C.can_request(trade, used=used, quota=quota, already_open=False)
    html(f'<p class="sx-note">Revues utilisées ce mois-ci : <b>{used} sur {quota}</b>.</p>')
    if reason:
        notice("Demande impossible pour l'instant", reason[0].upper() + reason[1:] + ".", "info")
        return
    with st.container(key="panel_jr_request"):
        with st.form(f"jr_request_{trade.id}", border=False):
            question = st.text_area("Votre question au coach", max_chars=C.MAX_QUESTION, height=110,
                                    placeholder="Par exemple : mon entrée était-elle cohérente avec ma zone ? "
                                    "Ai-je bien géré la sortie ?", key=f"jr_q_{trade.id}")
            consent = st.checkbox("J'envoie ce trade, ses notes, sa revue automatique et mon plan à l'équipe "
                                  "de coaching. Le reste de mon journal reste privé.", key=f"jr_consent_{trade.id}")
            if st.form_submit_button("Envoyer la demande", type="primary"):
                if not consent:
                    st.error("Cochez la case pour confirmer ce qui est envoyé.")
                    return
                try:
                    text = C.clean_question(question)
                except ValueError as exc:
                    st.error(str(exc)[0].upper() + str(exc)[1:] + ".")
                    return
                used, quota = _quota(email)
                if used >= quota or store.open_review_for_trade(email, trade.id):
                    st.error("Le quota du mois est atteint ou une demande existe déjà.")
                    return
                store.create_review_request(
                    email, trade_id=trade.id, trade=C.snapshot(trade),
                    auto_review=review.to_dict() if review else {"trade_id": trade.id, "checks": []},
                    plan=plan.to_dict() if plan else None, question=text)
                flash("Demande envoyée. Vous serez prévenu dans l'onglet Revues.")
                st.rerun()
    note("Le coach commente un trade clôturé : la lecture, l'exécution, la gestion et le respect de votre "
         "plan. Il ne donne pas de recommandation sur un trade à venir.")


# ── The member's reviews ─────────────────────────────────────────────────────

STATUS = {"pending": ("En attente", "soon"), "answered": ("Répondue", "live")}


def reviews_page(catalog, email, route) -> None:
    space = spaces.space("journal")
    crumbs("Sensitor", space.label, "Revues")
    page_header(f"Espace {space.numeral} · Journal de trading", "Le regard d'un <em>coach</em>.",
                "Envoyez un trade et votre question : un coach Sensitor le relit avec sa revue automatique et "
                "vous répond, avec les leçons à travailler.")
    store = rt.get_store()
    requests = store.review_requests(email) if email and store is not None else []
    chosen = next((r for r in requests if str(r["id"]) == str(route.get("review"))), None)
    if chosen and chosen["status"] == "answered":
        # Marked before the tabs are drawn, so their « nouvelle » count is already right.
        store.mark_review_seen(email, chosen["id"])
    nav("journal_reviews", email)
    if not email:
        _how_it_works()
        with st.container(key="navy_jr_reviews"):
            html('<div class="sx-kicker on-navy">Réservé aux membres</div><h2 class="sx-h3 on-navy">'
                 'Connectez-vous pour demander une revue.</h2><p>Chaque membre dispose d\'une revue par mois ; '
                 'le niveau Premium en compte davantage.</p>')
            rt.link("Se connecter ou créer un compte", "account", key="signin_reviews", kind="primary")
        footer()
        return
    if chosen:
        _review_detail(catalog, chosen, email)
        footer()
        return
    used, quota = _quota(email)
    html('<div class="sx-stats">'
         f'<div><div class="l">Ce mois-ci</div><div class="v">{used}<small> / {quota}</small></div>'
         '<div class="d">revues demandées</div></div>'
         f'<div><div class="l">En attente</div><div class="v">{sum(r["status"] == "pending" for r in requests)}</div>'
         '<div class="d">chez les coachs</div></div>'
         f'<div><div class="l">Répondues</div><div class="v">{sum(r["status"] == "answered" for r in requests)}</div>'
         '<div class="d">depuis le début</div></div></div>')
    section(1, "Vos demandes", "De la plus récente à la plus ancienne.")
    if not requests:
        note("Aucune demande pour l'instant. Ouvrez un trade dans l'onglet Trades, puis « Demander la revue "
             "d'un coach ».")
        rt.link("Choisir un trade", "journal_trades", key="reviews_pick", kind="primary")
    for r in requests:
        trade = r["trade"] or {}
        label, kind = STATUS[r["status"]]
        if r["status"] == "answered" and not r.get("seen_at"):
            label, kind = "Nouvelle réponse", "done"
        mark = hexmark(f"{r['id'] % 100:02d}")
        tap(f"review_{r['id']}",
            f'<div class="sx-j-trade">{mark}<div>'
            f'<div class="sym">{esc(trade.get("symbol", ""))}<span>{"ACHAT" if trade.get("direction") == "long" else "VENTE"}</span></div>'
            f'<div class="meta">Demandée le {esc(date_fr(r["created_at"]))} · {esc(_excerpt(r["question"]))}</div></div>'
            f'<div class="tags">{pill(label, kind)}</div>'
            f'<div class="sx-j-r {V.tone(trade.get("r_multiple"))}">{esc(V.r_text(trade.get("r_multiple")))}</div>'
            f'<span class="arrow">{icon("arrow")}</span></div>',
            f"Demande sur {trade.get('symbol', '')}, {label.lower()}", "journal_reviews", review=str(r["id"]))
    section(2, "Comment ça marche", "")
    _how_it_works()
    footer()


def _excerpt(text: str, n: int = 70) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _how_it_works() -> None:
    html('<ul class="sx-plan">'
         '<li><span class="n">01</span><span class="x"><b>Vous choisissez un trade clôturé</b> et posez votre '
         'question. Seul ce trade est envoyé, avec ses notes, sa revue automatique et votre plan.</span><span></span></li>'
         '<li><span class="n">02</span><span class="x"><b>Un coach le relit</b> sans connaître votre identité : '
         'il voit un pseudonyme.</span><span></span></li>'
         '<li><span class="n">03</span><span class="x"><b>Vous recevez une revue</b> : quatre axes notés, ce qui '
         'est solide, ce qui est à travailler, et les leçons de l\'Academy qui y répondent.</span><span></span></li>'
         '</ul>')


def _trade_block(request: dict, *, key: str) -> None:
    trade = request["trade"] or {}
    auto = R.TradeReview.from_dict(request.get("auto_review") or {})
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        with st.container(key=f"panel_ladder_{key}"):
            html(V.price_ladder(trade))
    with right:
        center = f"{auto.passed}/{len(auto.evaluated)}" if auto.evaluated else ""
        r = trade.get("r_multiple")
        with st.container(key=f"navy_result_{key}"):
            html(f'<div class="sx-j-big">{V.score_ring(auto.score, size=96, on_navy=True, center=center)}<div>'
                 f'<div class="k">{esc(trade.get("symbol", ""))} · {"achat" if trade.get("direction") == "long" else "vente"}</div>'
                 f'<div class="r {V.tone(r)}">{esc(V.r_text(r))}</div>'
                 f'<p>{esc(_session_line(trade))}</p></div></div>')
        notes = trade.get("notes")
        setups = ", ".join(setup_label(s, "fr") for s in trade.get("setups") or []) or "sans setup"
        mistakes = ", ".join(mistake_label(m, "fr").lower() for m in trade.get("mistakes") or []) or "aucun"
        risk = trade.get("risk_amount")
        rows = [("Setup", setups),
                ("Risque engagé", f"{V.fr(risk)} {_symbol(trade.get('account_currency', ''))}" if risk else "sans stop"),
                ("Rapport prévu", "n.d." if trade.get("planned_rr") is None else V.fr(trade["planned_rr"])),
                ("Écarts notés", mistakes)]
        html('<dl class="sx-j-facts">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows) + "</dl>")
        if notes:
            html(f'<div class="sx-j-text"><h5>Notes du membre</h5><p>{_paragraphs(notes)}</p></div>')
    if auto.checks:
        with st.expander(f"Revue automatique : {auto.passed} règle{'s' if auto.passed > 1 else ''} respectée"
                         f"{'s' if auto.passed > 1 else ''} sur {len(auto.evaluated)} vérifiables"):
            html(V.checks_list(auto.checks))


def _symbol(code: str) -> str:
    return {"EUR": "€", "USD": "$", "GBP": "£"}.get(code or "", code or "")


def _session_line(trade: dict) -> str:
    opened = trade.get("opened_at") or ""
    session = V.SESSION_SHORT.get(trade.get("session") or "", "")
    return " · ".join(x for x in (date_fr(opened[:19]) if opened else "", session) if x)


def _paragraphs(text: str) -> str:
    return "<br>".join(esc(line) for line in (text or "").splitlines())


def _review_detail(catalog, request: dict, email: str) -> None:
    store = rt.get_store()
    rt.link("Toutes mes demandes", "journal_reviews", key="review_back")
    label, kind = STATUS[request["status"]]
    html(f'<div style="margin-top:.6rem">{pill(label, kind)}</div>')
    html(f'<div class="sx-j-quote"><span class="k">Votre question · {esc(date_fr(request["created_at"]))}</span>'
         f'{_paragraphs(request["question"])}</div>')
    _trade_block(request, key=f"m{request['id']}")
    if request["status"] == "pending":
        notice("En attente d'un coach", "Vous pouvez retirer votre demande tant qu'elle n'a pas reçu de réponse ; "
               "elle ne sera alors plus comptée dans votre quota.", "clock")
        if st.button("Retirer ma demande", key="review_withdraw", type="tertiary"):
            store.withdraw_review_request(email, request["id"])
            rt.go("journal_reviews")
            st.rerun()
        return
    feedback = request.get("feedback") or {}
    section(1, "La revue du coach", "Sur ce trade clôturé, au regard de votre plan.")
    _feedback(catalog, feedback, key=f"m{request['id']}", answered_at=request.get("answered_at") or "")


def _feedback(catalog, feedback: dict, *, key: str, answered_at: str = "") -> None:
    with st.container(key=f"panel_feedback_{key}"):
        html(f'<div class="sx-j-fbhead">{icon("people")}<div><b>Coach Sensitor</b>'
             f'<span>Revue pédagogique{" · " + esc(date_fr(answered_at)) if answered_at else ""}</span></div></div>')
        if feedback.get("scores"):
            html(V.score_bars(feedback["scores"], C.AXES, C.SCORE_LABELS))
        cols = []
        for field, title, tone in (("strengths", "Ce qui est solide", "good"), ("improve", "À travailler", "work")):
            if feedback.get(field):
                cols.append(f'<div class="{tone}"><h5>{title}</h5><p>{_paragraphs(feedback[field])}</p></div>')
        if cols:
            html(f'<div class="sx-j-fbcols n{len(cols)}">{"".join(cols)}</div>')
        if feedback.get("comment"):
            html(f'<div class="sx-j-text"><h5>Commentaire</h5><p>{_paragraphs(feedback["comment"])}</p></div>')
    lessons = feedback.get("lessons") or []
    if lessons:
        html('<div class="sx-kicker" style="margin-top:1.4rem">Les leçons recommandées</div>')
        for i, target in enumerate(lessons):
            page, fields = spaces.parse_target(target)
            lesson = catalog.find_lesson(fields.get("lesson", "")) if fields else None
            title = lesson.title if lesson else target
            tap(f"fb_lesson_{key}_{i}",
                f'<div class="sx-lesson flush">{hexmark(f"{i + 1:02d}")}<div><div class="title">{esc(title)}</div>'
                f'</div><div class="side"></div><span class="arrow">{icon("arrow")}</span></div>',
                f"Leçon : {title}", page, **fields)


# ── The coach's queue ────────────────────────────────────────────────────────

def coach_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Coaching", "File de revue")
    page_header("Coaching · réservé à l'équipe", "La file de <em>revue</em>.",
                "Les trades que les membres ont choisi d'envoyer, du plus ancien au plus récent.")
    store = rt.get_store()
    if not email or store is None or not store.is_coach(email):
        notice("Accès réservé", "Cette page est réservée aux coachs de Sensitor.", "lock")
        footer()
        return
    show_flash()
    pending = store.coach_queue(email, "pending")
    chosen = next((r for r in pending if str(r["id"]) == str(route.get("review"))), None)
    if chosen:
        _answer(catalog, chosen, email)
        footer()
        return
    answered = store.coach_queue(email, "answered", limit=30)
    html('<div class="sx-stats">'
         f'<div><div class="l">À traiter</div><div class="v">{len(pending)}</div><div class="d">demandes en attente</div></div>'
         f'<div><div class="l">Plus ancienne</div><div class="v" style="font-size:1.4rem">'
         f'{esc(date_fr(pending[0]["created_at"])) if pending else "aucune"}</div><div class="d">date de la demande</div></div>'
         f'<div><div class="l">Répondues</div><div class="v">{len(answered)}</div><div class="d">les trente dernières</div></div></div>')
    section(1, "À traiter", "Ouvrez une demande pour y répondre.")
    if not pending:
        note("Aucune demande en attente.")
    for r in pending:
        _queue_row(r, key="p")
    if answered:
        section(2, "Dernières réponses", "Pour garder une cohérence d'un membre à l'autre.")
        for r in answered[:10]:
            trade = r["trade"] or {}
            html(f'<p class="sx-note"><b>{esc(C.pseudonym(r["user_email"]))}</b> · {esc(trade.get("symbol", ""))} · '
                 f'répondue le {esc(date_fr(r["answered_at"] or ""))}</p>')
    footer()


def _queue_row(r: dict, *, key: str) -> None:
    trade = r["trade"] or {}
    mark = hexmark(f"{r['id'] % 100:02d}")
    tap(f"coach_{key}_{r['id']}",
        f'<div class="sx-j-trade">{mark}<div>'
        f'<div class="sym">{esc(trade.get("symbol", ""))}<span>{esc(C.pseudonym(r["user_email"]).upper())}</span></div>'
        f'<div class="meta">Demandée le {esc(date_fr(r["created_at"]))} · {esc(_excerpt(r["question"]))}</div></div>'
        f'<div class="tags">{pill("En attente", "soon")}</div>'
        f'<div class="sx-j-r {V.tone(trade.get("r_multiple"))}">{esc(V.r_text(trade.get("r_multiple")))}</div>'
        f'<span class="arrow">{icon("arrow")}</span></div>',
        f"Demande de {C.pseudonym(r['user_email'])} sur {trade.get('symbol', '')}", "coach", review=str(r["id"]))


def _lesson_choices(catalog) -> dict[str, str]:
    choices = {}
    for path in catalog.paths_in("trading"):
        for course in path.courses:
            course = catalog.course(course) if isinstance(course, str) else course
            if course is None:
                continue
            for lesson in course.lessons:
                choices[f"lesson:{course.id}/{lesson.id}"] = f"{course.title} · {lesson.title}"
    return choices


def _answer(catalog, request: dict, email: str) -> None:
    store = rt.get_store()
    rt.link("Retour à la file", "coach", key="coach_back")
    html(f'<div class="sx-kicker" style="margin-top:.8rem">{esc(C.pseudonym(request["user_email"]))} · '
         f'demandée le {esc(date_fr(request["created_at"]))}</div>')
    html(f'<div class="sx-j-quote"><span class="k">La question du membre</span>{_paragraphs(request["question"])}</div>')
    _trade_block(request, key=f"c{request['id']}")
    if request.get("plan"):
        plan = R.TradingPlan.from_dict(request["plan"])
        with st.container(key=f"navy_coach_plan_{request['id']}"):
            items = "".join(f"<li>{esc(s)}</li>" for s in R.plan_sentences(plan))
            html(f'<div class="sx-kicker on-navy">Le plan du membre</div><ol class="sx-j-plan">{items}</ol>')
    else:
        note("Le membre n'a pas encore écrit de plan : la revue automatique a utilisé le plan de départ.")
    section(1, "Votre réponse", "Sur ce trade clôturé uniquement.")
    notice("Retour pédagogique", "Commentez la lecture, l'exécution, la gestion et le respect du plan. Aucune "
           "recommandation d'achat ou de vente, aucun avis sur un trade à venir.", "info")
    choices = _lesson_choices(catalog)
    with st.container(key="panel_coach_answer"):
        with st.form(f"coach_answer_{request['id']}", border=False):
            scores = {}
            cols = st.columns(len(C.AXES))
            for col, (axis, name) in zip(cols, C.AXES):
                with col:
                    scores[axis] = st.selectbox(name, [0, 1, 2, 3, 4, 5], key=f"coach_s_{axis}",
                                                format_func=lambda v: "non noté" if not v else f"{v} · {C.SCORE_LABELS[v]}")
            strengths = st.text_area("Ce qui est solide", max_chars=C.MAX_TEXT, height=90, key="coach_strengths")
            improve = st.text_area("À travailler", max_chars=C.MAX_TEXT, height=110, key="coach_improve")
            comment = st.text_area("Commentaire", max_chars=C.MAX_TEXT, height=110, key="coach_comment")
            lessons = st.multiselect(f"Leçons recommandées (au plus {C.MAX_LESSONS})", list(choices),
                                     format_func=lambda k: choices[k], max_selections=C.MAX_LESSONS,
                                     key="coach_lessons", placeholder="Choisir")
            if st.form_submit_button("Envoyer la revue", type="primary"):
                try:
                    feedback = C.clean_feedback({"strengths": strengths, "improve": improve, "comment": comment,
                                                 "scores": {k: v for k, v in scores.items() if v},
                                                 "lessons": lessons})
                except ValueError as exc:
                    st.error(str(exc)[0].upper() + str(exc)[1:] + ".")
                    return
                if store.answer_review(email, request["id"], feedback):
                    flash("Revue envoyée au membre.")
                    rt.go("coach")
                    st.rerun()
                else:
                    st.error("Cette demande a déjà reçu une réponse ou a été retirée.")
