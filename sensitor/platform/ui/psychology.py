"""
The « Psychologie et discipline » space: a private reflection journal.

Each member writes for themselves. The page reads and deletes notes only
through the store's user-scoped methods, with the signed-in address and nothing
else, and caches nothing between reruns. The figures shown are counts and the
average of the scale the member filled in, with the number of notes behind each
one: no reading of the text, no score, no label. Routine items are counted
the same way: how many notes ticked each one, out of how many offered it.
"""

from __future__ import annotations

import json

import streamlit as st

from .. import journal as J
from .. import spaces
from . import runtime as rt
from .components import (crumbs, date_fr, esc, footer, hexmark, html, icon, note, notice,
                         number, page_header, pill, section, tap)

_ERRORS = {
    "an entry needs some text": "Écrivez quelques mots avant d'enregistrer.",
    f"an entry is limited to {J.MAX_BODY} characters":
        f"Une note est limitée à {J.MAX_BODY} caractères.",
}


def render(catalog, email, route) -> None:
    space = spaces.space("psychology")
    crumbs("Sensitor", space.label)
    page_header(f"Espace {space.numeral} · Psychologie et discipline",
                "Décider avec <em>méthode</em>, aussi dans sa tête.",
                "Un journal de réflexion privé pour préparer chaque séance et y revenir ensuite, "
                "en séparant ce que vous avez décidé de ce que le marché a fait.")
    _why()
    if not email:
        with st.container(key="navy_journal_locked"):
            html('<div class="sx-kicker on-navy">Réservé aux membres</div><h2 class="sx-h3 on-navy">'
                 'Connectez-vous pour tenir votre journal.</h2><p>Vos notes sont personnelles : '
                 'elles ne sont visibles que par vous.</p>')
            rt.link("Se connecter ou créer un compte", "account", key="prompt_signin_journal",
                    kind="primary")
        _further(space, start=2)
        footer()
        return

    store = rt.get_store()
    section(2, "Écrire une note", "Choisissez le moment, une question si elle vous aide, puis écrivez.")
    notice("Privé", "Seul votre compte peut lire ces notes. Elles ne sont ni analysées, ni "
           "partagées, ni utilisées pour vous proposer quoi que ce soit. Vous pouvez les exporter "
           "ou les supprimer à tout moment ; supprimer le compte les efface toutes.", "lock")
    _form(store, email)

    entries = store.journal_entries(email, limit=100_000)
    section(3, "Vos notes", "De la plus récente à la plus ancienne.")
    _entries(store, email, entries)

    section(4, "En chiffres", "Ce que vos notes contiennent, compté, sans interprétation.")
    _summary(entries)

    data = _further(space, start=5)

    section(data, "Vos données", "Vos notes vous appartiennent : exportez-les à tout moment.")
    payload = json.dumps({"journal_entries": entries}, ensure_ascii=False, indent=2)
    st.download_button("Exporter mon journal (JSON)", data=payload.encode("utf-8"),
                       file_name="sensitor-journal.json", mime="application/json",
                       key="export_journal")
    footer()


def _why() -> None:
    section(1, "Pourquoi écrire", "Trois minutes avant, trois minutes après.")
    html('<ul class="sx-plan">'
         '<li><span class="n">01</span><span class="x"><b>Avant la séance</b>, écrire son plan, sa '
         'limite de perte et son état oblige à les fixer avant que le marché ne les discute.</span>'
         '<span></span></li>'
         '<li><span class="n">02</span><span class="x"><b>Après la séance</b>, relire ce qui avait '
         'été écrit permet de juger une décision sur ce que l\'on savait alors, pas sur le résultat '
         'obtenu.</span><span></span></li>'
         '<li><span class="n">03</span><span class="x"><b>Avec le temps</b>, les notes montrent ce '
         'qui revient. Les conclusions vous appartiennent : le journal compte, il ne juge pas.'
         '</span><span></span></li></ul>')


def _form(store, email: str) -> None:
    kinds = [k.id for k in J.KINDS]
    with st.container(key="panel_journal_form"):
        chosen = st.radio("Moment", kinds, format_func=J.kind_label, horizontal=True,
                          key="jr_kind")
        current = J.kind(chosen)
        html(f'<p class="sx-note" style="margin:-.2rem 0 .4rem">{esc(current.hint)}</p>')
        with st.form("journal_form", clear_on_submit=True, border=False):
            prompt = st.selectbox("Question guidée", ("",) + current.prompts,
                                  format_func=lambda p: p or "Sans question, note libre",
                                  key=f"jr_prompt_{chosen}")
            mood = st.radio("Votre état en ce moment (facultatif)", list(J.MOODS),
                            format_func=lambda n: f"{n} · {J.MOODS[n]}", index=None,
                            horizontal=True, key=f"jr_mood_{chosen}")
            ticked = {}
            if current.routine:
                html(f'<div class="sx-routine-label">Routine {esc(current.label.lower())} · '
                     'cochez ce qui est fait</div>')
                for item, label in current.routine:
                    ticked[item] = st.checkbox(label, key=f"jr_chk_{chosen}_{item}")
            body = st.text_area("Votre note", max_chars=J.MAX_BODY, height=170,
                                key=f"jr_body_{chosen}")
            if st.form_submit_button("Enregistrer la note", type="primary"):
                try:
                    kind, text, mood, prompt = J.clean_entry(chosen, body, mood=mood, prompt=prompt)
                    checks = J.clean_checks(kind, [item for item, on in ticked.items() if on])
                except ValueError as exc:
                    st.error(_ERRORS.get(str(exc), "Cette note n'a pas pu être enregistrée."))
                else:
                    store.add_journal_entry(email, kind=kind, body=text, mood=mood, prompt=prompt,
                                            checks=checks)
                    st.success("Note enregistrée.")


def _entries(store, email: str, entries: list[dict]) -> None:
    if not entries:
        note("Aucune note pour l'instant. La première peut tenir en trois lignes.")
        return
    shown = st.selectbox("Afficher", ("",) + tuple(k.id for k in J.KINDS),
                         format_func=lambda k: J.kind_label(k) if k else "Toutes les notes",
                         key="jr_filter")
    visible = [e for e in entries if not shown or e["kind"] == shown]
    if not visible:
        note("Aucune note de ce type pour l'instant.")
    for entry in visible[:50]:
        with st.container(key=f"panel_entry_{entry['id']}"):
            mood = (f' · état {entry["mood"]} sur 5, {esc(J.MOODS[entry["mood"]].lower())}'
                    if entry.get("mood") else "")
            question = (f'<p class="sx-entry-q">{esc(entry["prompt"])}</p>'
                        if entry.get("prompt") else "")
            html(f'<div class="sx-entry-head">{pill(J.kind_label(entry["kind"]), "live")}'
                 f'<span>{esc(date_fr(entry["created_at"], with_day=True))}{mood}</span></div>'
                 f'{question}<div class="sx-entry-body">{_paragraphs(entry["body"])}</div>'
                 f'{_routine(entry)}')
            _delete_control(store, email, entry["id"])
    if len(visible) > 50:
        note(f"Les 50 notes les plus récentes sont affichées sur {len(visible)}. "
             "L'export contient toutes les autres.")


def _routine(entry: dict) -> str:
    """The routine as it was ticked on this note; nothing for a note that offered none."""
    found = J.kind(entry["kind"])
    if entry.get("checks") is None or not found or not found.routine:
        return ""
    done = set(entry["checks"])
    items = "".join(f'<li class="{"on" if item in done else "off"}">{icon("check" if item in done else "dot")}'
                    f'<span>{esc(label)}</span></li>' for item, label in found.routine)
    return (f'<div class="sx-entry-routine"><b>Routine : {len(done)} sur {len(found.routine)}</b>'
            f'<ul>{items}</ul></div>')


def _paragraphs(text: str) -> str:
    """Escaped, with the member's line breaks kept: `html()` flattens raw newlines."""
    return "<br>".join(esc(line) for line in text.splitlines())


def _delete_control(store, email: str, entry_id: int) -> None:
    if st.session_state.get("jr_confirm") == entry_id:
        html('<p class="sx-note">Supprimer définitivement cette note ? Elle ne pourra pas être '
             'récupérée.</p>')
        yes, no, _ = st.columns([1, 1, 3])
        with yes:
            if st.button("Oui, supprimer", key=f"jr_yes_{entry_id}", type="primary"):
                store.delete_journal_entry(email, entry_id)
                st.session_state.pop("jr_confirm", None)
                st.rerun()
        with no:
            if st.button("Annuler", key=f"jr_no_{entry_id}"):
                st.session_state.pop("jr_confirm", None)
                st.rerun()
    elif st.button("Supprimer", key=f"jr_del_{entry_id}", type="tertiary"):
        st.session_state["jr_confirm"] = entry_id
        st.rerun()


def _summary(entries: list[dict]) -> None:
    summary = J.summarize(entries)
    by_kind = " · ".join(f"{summary.by_kind.get(k.id, 0)} {k.label.lower()}" for k in J.KINDS)
    html('<div class="sx-stats" style="margin-top:.4rem">'
         f'<div><div class="l">Notes</div><div class="v">{summary.total}</div>'
         f'<div class="d">{esc(by_kind)}</div></div>'
         f'<div><div class="l">30 derniers jours</div><div class="v">{summary.last_30_days}</div>'
         '<div class="d">notes écrites</div></div>'
         f'<div><div class="l">État renseigné</div><div class="v">{summary.rated}'
         f'<small> / {summary.total}</small></div><div class="d">notes avec l\'échelle</div></div>'
         '</div>')
    if summary.moods:
        rows = "".join(
            f"<tr><td>{esc(J.kind_label(m.kind))}</td><td>{number(m.average, 1)} sur 5</td>"
            f"<td>{m.n} note{'s' if m.n > 1 else ''}</td></tr>" for m in summary.moods)
        html('<table style="margin-top:1.2rem"><thead><tr><th>Moment</th><th>État moyen noté</th>'
             f'<th>Échantillon</th></tr></thead><tbody>{rows}</tbody></table>')
    if summary.routine:
        rows = "".join(
            f"<tr><td>{esc(J.kind_label(r.kind))}</td><td>{esc(r.label)}</td>"
            f"<td>{r.ticked} sur {r.n} note{'s' if r.n > 1 else ''}</td></tr>" for r in summary.routine)
        html('<table style="margin-top:1.2rem"><thead><tr><th>Moment</th><th>Élément de routine</th>'
             f'<th>Coché</th></tr></thead><tbody>{rows}</tbody></table>')
    note("Ces chiffres décrivent uniquement vos notes et l'échelle que vous avez remplie. Sur peu "
         "de notes, une moyenne varie beaucoup d'une semaine à l'autre. Ils ne constituent ni une "
         "évaluation ni un diagnostic.")


def _further(space: spaces.Space, *, start: int) -> int:
    """What is still announced, if anything, then the related content. Returns the next section number."""
    number_ = start
    if space.planned:
        section(number_, "Ce qui est prévu", "Le reste de l'espace, sans date promise.")
        items = "".join(f'<li><span class="n">{i:02d}</span><span class="x">{esc(p)}</span>'
                        f'{pill("Prévu", "soon")}</li>' for i, p in enumerate(space.planned, start=1))
        html(f'<ul class="sx-plan">{items}</ul>')
        number_ += 1
    if space.related:
        section(number_, "Pour aller plus loin", "Ce qui, ailleurs sur Sensitor, prolonge cet espace.")
        number_ += 1
        for index, (label, target) in enumerate(space.related):
            page, fields = spaces.parse_target(target)
            tap(f"related_{space.id}_{index}",
                f'<div class="sx-lesson flush">{hexmark(f"{index + 1:02d}")}<div><div class="title">'
                f'{esc(label)}</div></div><div class="side"></div><span class="arrow">'
                f'{icon("arrow")}</span></div>', label, page, **fields)
    return number_
