"""
The lessons' videos, declared in `content/academy/videos.toml`:

    [[video]]
    id = "lire-une-bougie"
    title = "Lire une bougie, en cinq minutes"
    url = "https://www.youtube.com/watch?v=…"     # https, YouTube or Vimeo
    duration_minutes = 5
    transcript = "videos/lire-une-bougie.md"       # required: what is said, in writing

A lesson shows one with `::: video lire-une-bougie` and a caption. The rules
are the lessons' own: the transcript is French, without long dashes, and a
figure said in the video is sourced like one written in a lesson. The player
is loaded only when the reader asks for it, so a page view sends nothing to
the video host; the transcript is always there, for reading, searching and
accessibility.

No Streamlit.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

HOSTS = {"youtube.com": "YouTube", "www.youtube.com": "YouTube", "m.youtube.com": "YouTube", "youtu.be": "YouTube",
         "vimeo.com": "Vimeo", "player.vimeo.com": "Vimeo"}
DASHES = (chr(0x2014), chr(0x2013))


@dataclass(frozen=True)
class Video:
    id: str
    title: str
    url: str
    duration_minutes: int
    transcript: str

    @property
    def host(self) -> str:
        return HOSTS.get((urlparse(self.url).hostname or "").lower(), "")


def load(root: Path, problem) -> dict[str, Video]:
    """The declared videos; every problem goes to `problem(where, message)`."""
    path = root / "videos.toml"
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        problem("videos.toml", f"TOML invalide ({exc})")
        return {}
    out: dict[str, Video] = {}
    for raw in data.get("video", []):
        vid = str(raw.get("id", "")).strip()
        where = f"videos.toml [{vid or '?'}]"
        url = str(raw.get("url", "")).strip()
        parsed = urlparse(url)
        if not vid:
            problem(where, "identifiant manquant")
            continue
        if vid in out:
            problem(where, "identifiant en double")
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in HOSTS:
            problem(where, "l'adresse doit être une adresse https YouTube ou Vimeo")
        transcript_file = root / str(raw.get("transcript", ""))
        transcript = ""
        if not raw.get("transcript") or not transcript_file.is_file():
            problem(where, "transcription introuvable (obligatoire)")
        else:
            transcript = transcript_file.read_text(encoding="utf-8").strip()
            if not transcript:
                problem(where, "transcription vide")
            if any(d in transcript for d in DASHES):
                problem(where, "tiret long dans la transcription")
        try:
            minutes = int(raw.get("duration_minutes", 0))
        except (TypeError, ValueError):
            minutes = 0
        if minutes <= 0:
            problem(where, "durée en minutes manquante")
        title = str(raw.get("title", "")).strip()
        if not title or any(d in title for d in DASHES):
            problem(where, "titre manquant ou avec un tiret long")
        out[vid] = Video(vid, title, url, minutes, transcript)
    return out
