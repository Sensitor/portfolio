"""
The journal's drawings, as SVG and HTML strings.

Pure functions, no Streamlit: the pages place them, the tests read them. Every
drawing is built from the design tokens, labels its numbers in French and is
`aria-hidden`, with the same figures stated in text next to it, so nothing is
known only from a picture.

* `score_ring`     the share of the plan's rules respected, as a ring;
* `price_ladder`   one trade on a vertical price scale: stop, entry, target,
                   exit, with the risk and reward zones and the levels in R;
* `calendar`       R per day over the last weeks, one square per day;
* `rule_bars`      how often each rule was broken and what it cost;
* `checks_list`    the automatic review of one trade, rule by rule.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

from .components import MONTHS, esc, icon
from .theme import TOKENS

T = TOKENS
SESSION_SHORT = {"asia": "Asie", "london": "Londres", "new_york": "New York",
                 "overlap": "Londres et New York", "off_hours": "Hors séance"}
_SHORT_MONTHS = ("janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.",
                 "nov.", "déc.")


def fr(value: float, decimals: int = 2) -> str:
    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return text


def signed(value: float, decimals: int = 2) -> str:
    sign = "+" if value > 0.00001 else "−" if value < -0.00001 else ""
    return sign + fr(abs(value), decimals)


def r_text(value: float | None, decimals: int = 2) -> str:
    return "n.d." if value is None else f"{signed(value, decimals)} R"


def tone(value: float | None) -> str:
    if value is None or abs(value) < 1e-9:
        return "flat"
    return "up" if value > 0 else "down"


def score_color(score: float | None) -> str:
    if score is None:
        return T["line-strong"]
    if score >= 0.999:
        return T["green"]
    if score >= 0.75:
        return T["gold"]
    return T["red"]


# ── Ring ─────────────────────────────────────────────────────────────────────

def score_ring(score: float | None, *, size: int = 120, center: str = "", caption: str = "",
               on_navy: bool = False) -> str:
    """A ring filled to `score` (0 to 1). `center` is the text in the middle, « 7/9 » for instance."""
    stroke = 9 if size >= 100 else 6
    r = (size - stroke) / 2 - 1
    c = size / 2
    length = 2 * math.pi * r
    filled = 0 if score is None else max(0.0, min(1.0, score)) * length
    track = "#2b3f52" if on_navy else T["paper-2"]
    color = score_color(score)
    if on_navy and score is not None:
        color = {T["green"]: "#9fd3b4", T["gold"]: "#e3c58a", T["red"]: "#e7b2a8"}[color]
    ink = "#f6f3ec" if on_navy else T["ink"]
    muted = T["on-navy-muted"] if on_navy else T["muted"]
    big = size * 0.27 if len(center) <= 4 else size * 0.2
    text = esc(center or ("n.d." if score is None else f"{round(score * 100)} %"))
    cap = (f'<text x="{c}" y="{c + big * 0.95}" text-anchor="middle" font-family="DM Mono, monospace" '
           f'font-size="{max(8.5, size * 0.085):.1f}" letter-spacing=".08em" fill="{muted}">{esc(caption)}</text>'
           if caption else "")
    return (f'<svg class="sx-ring" viewBox="0 0 {size} {size}" width="{size}" height="{size}" aria-hidden="true">'
            f'<circle cx="{c}" cy="{c}" r="{r:.2f}" fill="none" stroke="{track}" stroke-width="{stroke}"/>'
            + (f'<circle cx="{c}" cy="{c}" r="{r:.2f}" fill="none" stroke="{color}" stroke-width="{stroke}" '
               f'stroke-linecap="round" stroke-dasharray="{filled:.2f} {length:.2f}" '
               f'transform="rotate(-90 {c} {c})"/>' if filled > 0 else "") +
            f'<text x="{c}" y="{c + big * 0.36 - (big * 0.25 if caption else 0):.1f}" text-anchor="middle" '
            f'font-family="Playfair Display, Georgia, serif" font-weight="600" font-size="{big:.1f}" '
            f'fill="{ink}">{text}</text>{cap}</svg>')


# ── Price ladder ─────────────────────────────────────────────────────────────

def _price(value: float) -> str:
    if value >= 1000:
        return fr(value, 1)
    if value >= 10:
        return fr(value, 2)
    return fr(value, 5)


def price_ladder(trade: dict, *, width: int = 440, height: int = 380) -> str:
    """
    One trade drawn on its price scale. `trade` is a `Trade.to_dict()`: the same
    drawing serves the member's journal and the coach's frozen copy.
    """
    entry = trade.get("entry_price")
    exit_ = trade.get("exit_price")
    stop = trade.get("stop_loss")
    target = trade.get("take_profit")
    long = trade.get("direction") == "long"
    if not entry:
        return ""
    levels = [v for v in (entry, exit_, stop, target) if v]
    lo, hi = min(levels), max(levels)
    span = (hi - lo) or abs(entry) * 0.002 or 1
    lo, hi = lo - span * 0.14, hi + span * 0.14
    top, bottom = 26, height - 26
    left, right = 84, width - 118

    def y(v: float) -> float:
        return bottom - (v - lo) / (hi - lo) * (bottom - top)

    risk = abs(entry - stop) if stop else None

    def in_r(v: float) -> str:
        if not risk:
            return ""
        return r_text((v - entry) / risk * (1 if long else -1), 1).replace(" ", " ")

    parts = [f'<rect x="{left}" y="{top - 8}" width="{right - left}" height="{bottom - top + 16}" '
             f'fill="{T["white"]}" stroke="{T["line"]}" rx="3"/>']
    if stop:
        y1, y2 = sorted((y(entry), y(stop)))
        parts.append(f'<rect x="{left + 1}" y="{y1:.1f}" width="{right - left - 2}" height="{y2 - y1:.1f}" '
                     f'fill="{T["red-soft"]}"/>')
    if target:
        y1, y2 = sorted((y(entry), y(target)))
        parts.append(f'<rect x="{left + 1}" y="{y1:.1f}" width="{right - left - 2}" height="{y2 - y1:.1f}" '
                     f'fill="{T["green-soft"]}"/>')

    def level(v: float, name: str, color: str, *, dash: str = "", weight: float = 1.4) -> None:
        yy = y(v)
        dashes = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{left}" x2="{right}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{color}" '
                     f'stroke-width="{weight}"{dashes}/>')
        parts.append(f'<text x="{right + 10}" y="{yy - 2:.1f}" font-family="DM Mono, monospace" font-size="10" '
                     f'letter-spacing=".1em" fill="{color}">{esc(name.upper())}</text>')
        parts.append(f'<text x="{right + 10}" y="{yy + 11:.1f}" font-family="DM Mono, monospace" font-size="11" '
                     f'fill="{T["ink"]}">{esc(_price(v))}</text>')
        r_label = in_r(v)
        if r_label:
            parts.append(f'<text x="{left - 10}" y="{yy + 4:.1f}" text-anchor="end" font-family="DM Mono, monospace" '
                         f'font-size="11" fill="{T["muted"]}">{esc(r_label)}</text>')

    if target:
        level(target, "Objectif", T["green"], dash="5 4")
    if stop:
        level(stop, "Stop", T["red"], dash="5 4")
    level(entry, "Entrée", T["ink"], weight=1.8)
    if exit_:
        won = (exit_ - entry) * (1 if long else -1) >= 0
        color = T["green"] if won else T["red"]
        yy = y(exit_)
        x_in, x_out = left + 30, right - 34
        parts.append(f'<path d="M{x_in} {y(entry):.1f} L{x_out} {yy:.1f}" stroke="{color}" stroke-width="2" '
                     f'fill="none" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{x_in}" cy="{y(entry):.1f}" r="4.5" fill="{T["ink"]}"/>')
        parts.append(f'<circle cx="{x_out}" cy="{yy:.1f}" r="6" fill="{T["white"]}" stroke="{color}" stroke-width="2.4"/>')
        near = any(v and abs(y(v) - yy) < 14 for v in (target, stop, entry))
        if not near:
            level(exit_, "Sortie", color, weight=0.01)
        else:
            parts.append(f'<text x="{x_out}" y="{yy - 12:.1f}" text-anchor="middle" font-family="DM Mono, monospace" '
                         f'font-size="10" letter-spacing=".1em" fill="{color}">SORTIE</text>')
    arrow = "▲ ACHAT" if long else "▼ VENTE"
    parts.append(f'<text x="{left}" y="{top - 13}" font-family="DM Mono, monospace" font-size="10.5" '
                 f'letter-spacing=".12em" fill="{T["blue"]}">{arrow}</text>')
    return (f'<svg class="sx-ladder" viewBox="0 0 {width} {height}" width="100%" role="img" aria-hidden="true">'
            + "".join(parts) + "</svg>")


# ── Calendar ─────────────────────────────────────────────────────────────────

def _cell_color(value: float | None) -> str:
    if value is None:
        return T["paper-2"]
    if abs(value) < 1e-9:
        return T["line-strong"]
    strength = min(1.0, abs(value) / 3)
    if value > 0:
        shades = ("#c9dccf", "#93b9a0", "#5d8f71", T["green"])
    else:
        shades = ("#ecc9c1", "#d79a8d", "#b4685a", T["red"])
    return shades[min(3, int(strength * 3.999))]


def calendar(daily: dict[date, tuple[float, int]], *, end: date, weeks: int = 13) -> str:
    """R per closing day, Monday to Sunday down, weeks across, the last column holding `end`."""
    cell, gap = 15, 3
    start = end - timedelta(days=end.weekday()) - timedelta(weeks=weeks - 1)
    left, top = 26, 18
    parts = []
    for i, name in enumerate(("L", "", "M", "", "V", "", "D")):
        if name:
            parts.append(f'<text x="{left - 8}" y="{top + i * (cell + gap) + 11}" text-anchor="end" '
                         f'font-family="DM Mono, monospace" font-size="9.5" fill="{T["faint"]}">{name}</text>')
    last_month, last_label = None, -9
    for w in range(weeks):
        monday = start + timedelta(weeks=w)
        if monday.month != last_month and w - last_label >= 3:
            last_month, last_label = monday.month, w
            parts.append(f'<text x="{left + w * (cell + gap)}" y="{top - 6}" font-family="DM Mono, monospace" '
                         f'font-size="9.5" fill="{T["muted"]}">{_SHORT_MONTHS[monday.month - 1]}</text>')
        for d in range(7):
            day = monday + timedelta(days=d)
            if day > end:
                continue
            value, n = daily.get(day, (None, 0))
            label = (f"{day.day} {MONTHS[day.month - 1]} : {r_text(value)}, {n} trade{'s' if n > 1 else ''}"
                     if n else f"{day.day} {MONTHS[day.month - 1]} : aucun trade")
            parts.append(f'<rect x="{left + w * (cell + gap)}" y="{top + d * (cell + gap)}" width="{cell}" '
                         f'height="{cell}" rx="2.5" fill="{_cell_color(value)}"><title>{esc(label)}</title></rect>')
    width = left + weeks * (cell + gap)
    height = top + 7 * (cell + gap)
    return (f'<svg class="sx-calendar" viewBox="0 0 {width} {height}" width="100%" aria-hidden="true">'
            + "".join(parts) + "</svg>")


def calendar_legend() -> str:
    swatches = "".join(f'<i style="background:{_cell_color(v)}"></i>' for v in (-3, -1.6, -0.5, None, 0.5, 1.6, 3))
    return (f'<div class="sx-j-legend"><span>Perte</span>{swatches}<span>Gain</span>'
            f'<em>une case par jour, intensité selon le résultat en R</em></div>')


# ── Rules ────────────────────────────────────────────────────────────────────

def rule_bars(tallies) -> str:
    """One row per rule of the plan: breaches over trades checked, and the R those trades made."""
    rows = []
    worst = max((t.breaches / t.checked for t in tallies if t.checked), default=0) or 1
    for t in tallies:
        share = t.breaches / t.checked if t.checked else 0
        width = 0 if not t.breaches else max(3.0, share / worst * 100)
        cost = (f'<span class="cost {tone(t.cost_r)}">{r_text(t.cost_r)}</span>' if t.breaches
                else '<span class="cost ok">respectée</span>')
        rows.append(
            f'<li class="{"clean" if not t.breaches else ""}"><div class="name">{esc(t.label)}</div>'
            f'<div class="bar"><i style="width:{width:.1f}%"></i></div>'
            f'<div class="n">{t.breaches} sur {t.checked}</div>{cost}</li>')
    return f'<ul class="sx-j-rules">{"".join(rows)}</ul>'


def checks_list(checks) -> str:
    items = []
    for c in checks:
        mark = {"ok": ("ok", icon("check")), "fail": ("ko", icon("cross")), "na": ("na", icon("dot"))}[c.status]
        items.append(f'<li class="{mark[0]}"><span class="mark">{mark[1]}</span><b>{esc(c.label)}</b>'
                     f'<span class="why">{esc(c.detail)}</span></li>')
    return f'<ul class="sx-j-checks">{"".join(items)}</ul>'


def score_bars(scores: dict, axes, labels: dict) -> str:
    """A coach's marks, one bar of five steps per axis."""
    rows = []
    for axis, name in axes:
        value = scores.get(axis)
        steps = "".join(f'<i class="{"on" if value and k <= value else ""}"></i>' for k in range(1, 6))
        text = f"{value} sur 5 · {labels[value]}" if value else "non noté"
        rows.append(f'<li><span class="name">{esc(name)}</span><span class="steps">{steps}</span>'
                    f'<span class="v">{esc(text)}</span></li>')
    return f'<ul class="sx-j-marks">{"".join(rows)}</ul>'


# =============================================================================
# CARNET DE BORD (prototype of the direction in docs/DIRECTION_ARTISTIQUE.md)
# =============================================================================
#
# The same figures, drawn the way the direction proposes: trades shown one by
# one rather than as a percentage, the plan's rules in a fixed order, levels
# marked with the hook of the S, risk and target zones hatched at the
# monogram's 30°, and annotations in italic in the margin.

from ...trading.review import RULES  # noqa: E402
from .. import brand  # noqa: E402
from .theme import CARNET_TOKENS as K  # noqa: E402

CIRCLED = "①②③④⑤⑥⑦⑧⑨"
RULE_ORDER = tuple(RULES)


def circled(i: int) -> str:
    return CIRCLED[i] if 0 <= i < len(CIRCLED) else f"({i + 1})"


def record(marks: list[tuple[str, str]], *, max_width: int = 640) -> str:
    """
    One mark per trade, in closing order: `marks` is a list of (state, label),
    state in « in » (plan followed), « out » (a rule broken), « na » (nothing
    checkable). A departure is taller and in brick, so it reads without colour.
    """
    n = len(marks)
    if not n:
        return ""
    step = min(12.0, max_width / n)
    bar = max(1.6, min(4.0, step * 0.45))
    parts = []
    for i, (state, label) in enumerate(marks):
        x = i * step + (step - bar) / 2
        y, h, color = {"in": (16, 22, K["ink"]), "out": (4, 34, K["down"]), "na": (26, 12, K["na"])}[state]
        parts.append(f'<rect x="{x:.2f}" y="{y}" width="{bar:.2f}" height="{h}" fill="{color}"><title>{esc(label)}</title></rect>')
    width = n * step
    parts.append(f'<line x1="0" x2="{width:.1f}" y1="38.5" y2="38.5" stroke="{K["rule-strong"]}"/>')
    parts.append(f'<text x="0" y="50" font-family="Schibsted Grotesk, sans-serif" font-size="10" fill="{K["graphite"]}">1</text>')
    if n > 1:
        parts.append(f'<text x="{width:.1f}" y="50" text-anchor="end" font-family="Schibsted Grotesk, sans-serif" font-size="10" '
                     f'fill="{K["graphite"]}">{n}</text>')
    return (f'<svg class="sx-c-releve" viewBox="0 0 {width:.1f} 52" width="{width:.1f}" height="52" '
            f'style="max-width:100%" aria-hidden="true">' + "".join(parts) + "</svg>")


def rule_print(checks, *, big: bool = False) -> str:
    """The plan's rules for one trade, always in the same order: ink kept, brick broken, outline not checkable."""
    by_rule = {c.rule if hasattr(c, "rule") else c["rule"]: (c.status if hasattr(c, "status") else c["status"])
               for c in checks}
    cells, words = [], []
    for rule in RULE_ORDER:
        status = by_rule.get(rule, "na")
        css = {"ok": "ok", "fail": "fail"}.get(status, "na")
        state = {"ok": "respectée", "fail": "enfreinte"}.get(status, "non vérifiable")
        cells.append(f'<i class="{css}" title="{esc(RULES[rule].label)} : {state}"></i>')
        if status == "fail":
            words.append(RULES[rule].label.lower())
    summary = ("aucune règle enfreinte" if not words else "enfreinte : " + ", ".join(words))
    return (f'<span class="sx-c-print{" big" if big else ""}" role="img" aria-label="Règles du plan, {esc(summary)}">'
            + "".join(cells) + "</span>")


def _hatch(id_: str, color: str) -> str:
    return (f'<pattern id="{id_}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-30)">'
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="{color}" stroke-width="1.3" stroke-opacity=".55"/></pattern>')


def levels(trade: dict, *, uid: str = "lv", width: int = 400, height: int = 330) -> str:
    """
    One trade on its price scale, in the direction's grammar: each level marked
    with the hook of the S and named on its line, risk and target zones hatched
    at 30°, the exit circled and annotated in italic.
    """
    entry, exit_ = trade.get("entry_price"), trade.get("exit_price")
    stop, target = trade.get("stop_loss"), trade.get("take_profit")
    long = trade.get("direction") == "long"
    if not entry:
        return ""
    values = [v for v in (entry, exit_, stop, target) if v]
    lo, hi = min(values), max(values)
    span = (hi - lo) or abs(entry) * 0.002 or 1
    lo, hi = lo - span * 0.12, hi + span * 0.12
    top, bottom, left, right = 30, height - 18, 70, width - 104

    def y(v: float) -> float:
        return bottom - (v - lo) / (hi - lo) * (bottom - top)

    risk = abs(entry - stop) if stop else None

    def r_of(v: float) -> str:
        if not risk:
            return ""
        return r_text((v - entry) / risk * (1 if long else -1), 1)

    text = "font-family=\"Schibsted Grotesk, sans-serif\""
    parts = [f'<defs>{_hatch(uid + "d", K["down"])}{_hatch(uid + "u", K["up"])}</defs>']
    for value, fill, pat in ((stop, K["down-soft"], uid + "d"), (target, K["up-soft"], uid + "u")):
        if value:
            y1, y2 = sorted((y(entry), y(value)))
            parts.append(f'<rect x="{left}" y="{y1:.1f}" width="{right - left}" height="{y2 - y1:.1f}" fill="{fill}"/>'
                         f'<rect x="{left}" y="{y1:.1f}" width="{right - left}" height="{y2 - y1:.1f}" fill="url(#{pat})"/>')

    hook = brand.hook_path()

    def level(v: float, name: str, color: str, weight: float) -> None:
        yy = y(v)
        parts.append(f'<line x1="{left}" x2="{right}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{color}" stroke-width="{weight}"/>')
        parts.append(f'<g transform="translate({left - 20} {yy - 6.5:.1f}) scale(.19)"><path d="{hook}" '
                     f'transform="translate(-28 -22)" fill="{color}"/></g>')
        label = r_of(v)
        if label:
            parts.append(f'<text x="{left - 26}" y="{yy + 4:.1f}" text-anchor="end" {text} font-size="12" '
                         f'font-weight="500" fill="{K["graphite"]}">{esc(label)}</text>')
        parts.append(f'<text x="{right + 12}" y="{yy - 1:.1f}" {text} font-size="12.5" font-weight="600" fill="{color}">{esc(name)}</text>')
        parts.append(f'<text x="{right + 12}" y="{yy + 14:.1f}" {text} font-size="12" fill="{K["graphite"]}">{esc(_price(v))}</text>')

    if target:
        level(target, "Objectif", K["up"], 1.2)
    if stop:
        level(stop, "Stop", K["down"], 1.2)
    level(entry, "Entrée", K["ink"], 2)
    if exit_:
        yy = y(exit_)
        x_in, x_out = left + 24, right - 30
        parts.append(f'<path d="M{x_in} {y(entry):.1f} L{x_out} {yy:.1f}" stroke="{K["ink"]}" stroke-width="1.4" fill="none"/>')
        parts.append(f'<circle cx="{x_in}" cy="{y(entry):.1f}" r="3.5" fill="{K["ink"]}"/>')
        parts.append(f'<circle cx="{x_out}" cy="{yy:.1f}" r="6.5" fill="{K["sheet"]}" stroke="{K["note"]}" stroke-width="2"/>')
        result = r_of(exit_)
        where = ("à l'objectif" if target and abs(exit_ - target) <= span * 0.01 else
                 "au stop" if stop and abs(exit_ - stop) <= span * 0.01 else
                 (f"à {result}" if result else "hors niveaux"))
        # The annotation leaves the exit at 30°, as the margin notes do.
        dx, dy = 34, 34 * math.tan(math.radians(30)) * (1 if yy < (top + bottom) / 2 else -1)
        ax, ay = x_out - dx, yy + dy
        parts.append(f'<path d="M{x_out - 5} {yy + (4 if dy > 0 else -4):.1f} L{ax:.1f} {ay:.1f} L{ax - 30:.1f} {ay:.1f}" '
                     f'stroke="{K["note"]}" stroke-width="1" fill="none"/>')
        parts.append(f'<text x="{ax - 34:.1f}" y="{ay + 4:.1f}" text-anchor="end" font-family="Newsreader, Georgia, serif" '
                     f'font-style="italic" font-size="14" fill="{K["note"]}">sortie {esc(where)}</text>')
    arrow = "Achat ▲" if long else "Vente ▼"
    parts.append(f'<text x="{left}" y="{top - 14}" {text} font-size="12.5" font-weight="600" fill="{K["plan"]}">{arrow}</text>')
    return (f'<svg class="sx-c-levels" viewBox="0 0 {width} {height}" width="100%" aria-hidden="true">'
            + "".join(parts) + "</svg>")


def graduation(value: int | None, *, steps: int = 5) -> str:
    """A mark out of five on a graduated rule, the hook above the mark given."""
    width, gap, x0 = 132, 132 / (steps - 1), 8
    parts = [f'<line x1="{x0}" x2="{width + x0}" y1="20" y2="20" stroke="{K["rule-strong"]}" stroke-width="1.5"/>']
    if value:
        parts.append(f'<line x1="{x0}" x2="{x0 + (value - 1) * gap:.1f}" y1="20" y2="20" stroke="{K["ink"]}" stroke-width="3"/>')
    for k in range(1, steps + 1):
        x = x0 + (k - 1) * gap
        on = value and k <= value
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{14 if on else 16}" y2="26" stroke="{K["ink"] if on else K["rule-strong"]}" stroke-width="1.5"/>')
    if value:
        x = x0 + (value - 1) * gap
        parts.append(f'<g transform="translate({x - 6:.1f} 1) scale(.17)"><path d="{brand.hook_path()}" transform="translate(-28 -22)" '
                     f'fill="{K["note"]}"/></g>')
    return f'<svg viewBox="0 0 {width + 2 * x0} 30" width="{width + 2 * x0}" height="30" aria-hidden="true">' + "".join(parts) + "</svg>"


def notes(items: list[str]) -> str:
    """Numbered margin notes, in italic: what the figures mean."""
    return '<ol class="sx-c-notes">' + "".join(f"<li><b>{circled(i)}</b><span>{esc(t)}</span></li>"
                                               for i, t in enumerate(items)) + "</ol>"


def facts(items: list[str]) -> str:
    """A plain list of facts (a plan, what was sent): upright, because nothing here is interpreted."""
    return '<ul class="sx-c-facts">' + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>"


def visa(when: str) -> str:
    """The coach's signature at the foot of a review, like a corrected copy."""
    return (f'<div class="sx-c-visa">{brand.monogram_svg(22, color=K["ink"])}<div><b>Revu par un coach Sensitor</b>'
            f'<span>{esc(when)}</span></div></div>')
