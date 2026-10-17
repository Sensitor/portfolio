"""
The lesson body format.

A lesson is Markdown with a handful of block directives, one per line:

    ::: callout note "À retenir"
    Markdown inside the callout.
    :::

    ::: figure structure-tendance.svg
    Caption, in Markdown.
    :::

    ::: formula
    \\text{Risque} = \\text{Capital} \\times \\frac{\\text{Risque \\%}}{100}
    :::

    ::: exercise cas-eurusd
    :::

    ::: tool risk-calculator
    :::

Directives do not nest. Anything outside a directive is plain Markdown. The
parser only splits the text into blocks; whether a figure file or an exercise id
actually exists is checked by `content.load_catalog`, which knows where to look.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

CALLOUT_KINDS = {
    "note": "À retenir",
    "definition": "Définition",
    "example": "Exemple",
    "warning": "Attention",
    "mistake": "Erreur fréquente",
    "recap": "Récapitulatif",
    "method": "Hypothèse de méthode",
    # Separating views from facts is a rule of the Bitcoin and crypto tracks:
    # a founder's conviction and a debated theory each get their own frame.
    "opinion": "Opinion du fondateur",
    "debate": "Débat",
}

DIRECTIVES = {"callout", "figure", "formula", "exercise", "tool", "chart"}
TOOLS = {"risk-calculator", "ruin-simulator"}

_OPEN = re.compile(r"^:::\s*([a-z-]+)\s*(.*)$")
_CLOSE = re.compile(r"^:::\s*$")


class MarkupError(ValueError):
    """The body could not be split into blocks. Carries the line number."""


@dataclass(frozen=True)
class Block:
    kind: str                      # markdown | callout | figure | formula | exercise | tool
    text: str = ""
    args: tuple[str, ...] = field(default_factory=tuple)

    @property
    def callout_kind(self) -> str:
        return self.args[0] if self.args else "note"

    @property
    def title(self) -> str:
        if self.kind == "callout":
            return self.args[1] if len(self.args) > 1 else CALLOUT_KINDS.get(self.callout_kind, "")
        return ""

    @property
    def target(self) -> str:
        """The file, exercise id or tool name a directive points at."""
        return self.args[0] if self.args else ""


def parse(body: str) -> list[Block]:
    blocks: list[Block] = []
    buffer: list[str] = []
    open_kind: str | None = None
    open_args: tuple[str, ...] = ()
    open_line = 0

    def flush_markdown():
        text = "\n".join(buffer).strip("\n")
        if text.strip():
            blocks.append(Block("markdown", text))
        buffer.clear()

    for number, line in enumerate(body.splitlines(), start=1):
        if open_kind is None:
            match = _OPEN.match(line)
            if match and match.group(1):
                kind = match.group(1)
                if kind not in DIRECTIVES:
                    raise MarkupError(f"ligne {number} : directive inconnue « {kind} »")
                flush_markdown()
                try:
                    open_args = tuple(shlex.split(match.group(2)))
                except ValueError as exc:
                    raise MarkupError(f"ligne {number} : arguments illisibles ({exc})") from exc
                _check_args(kind, open_args, number)
                open_kind, open_line = kind, number
                continue
            if _CLOSE.match(line):
                raise MarkupError(f"ligne {number} : « ::: » fermant sans bloc ouvert")
            buffer.append(line)
            continue

        if _CLOSE.match(line):
            blocks.append(Block(open_kind, "\n".join(buffer).strip("\n"), open_args))
            buffer.clear()
            open_kind = None
            continue
        if _OPEN.match(line) and _OPEN.match(line).group(1):
            raise MarkupError(f"ligne {number} : les directives ne s'imbriquent pas "
                              f"(bloc ouvert ligne {open_line})")
        buffer.append(line)

    if open_kind is not None:
        raise MarkupError(f"bloc « {open_kind} » ouvert ligne {open_line} jamais fermé")
    flush_markdown()
    return blocks


def _check_args(kind: str, args: tuple[str, ...], number: int) -> None:
    if kind == "callout":
        if not args or args[0] not in CALLOUT_KINDS:
            raise MarkupError(f"ligne {number} : type d'encadré attendu parmi "
                              f"{', '.join(sorted(CALLOUT_KINDS))}")
    elif kind in ("figure", "exercise", "tool", "chart"):
        if len(args) != 1:
            raise MarkupError(f"ligne {number} : « {kind} » attend exactement un argument")
        if kind == "tool" and args[0] not in TOOLS:
            raise MarkupError(f"ligne {number} : outil inconnu « {args[0]} »")
    elif kind == "formula" and args:
        raise MarkupError(f"ligne {number} : « formula » ne prend pas d'argument")
