"""
Sourced data for the Academy's charts.

    data/datasets.toml   every dataset: where it comes from, under which licence,
                         when it was retrieved, and either a CSV file next to it
                         or the name of a generator that computes it
    data/*.csv           the files themselves, committed as retrieved
    charts.toml          what a lesson can draw: a dataset, columns, a kind

A chart cannot exist without a dataset, and a dataset cannot exist without a
source, a licence and a date: the loader refuses the content otherwise. That is
the guarantee behind every curve a member sees, and the reason the source line
under a chart is generated rather than typed.

Synthetic examples are allowed and say so: `synthetic = true` is mandatory for
anything that is not observed data, and the chart labels it.

No Streamlit here; `ui/chart_view.py` draws what this module describes.
"""

from __future__ import annotations

import csv
import datetime as _dt
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import bitcoin

FILE = "file"
COMPUTED = "computed"
CHART_KINDS = {"line", "area", "bar", "step"}

# Generators turn protocol rules or formulas into rows. Each is a pure function,
# tested in its own module.
GENERATORS: dict[str, Callable[[], list[dict]]] = {
    "bitcoin-issuance": bitcoin.issuance_rows,
}


@dataclass(frozen=True)
class Dataset:
    id: str
    title: str
    kind: str
    source: str
    url: str
    license: str
    retrieved: _dt.date
    columns: tuple[str, ...]
    rows: tuple[dict, ...]
    unit: str = ""
    synthetic: bool = False
    notes: str = ""

    @property
    def credit(self) -> str:
        """The line printed under every chart that uses this dataset."""
        if self.synthetic:
            return f"Exemple synthétique, construit pour la leçon. {self.notes}".strip()
        head = "Calcul" if self.kind == COMPUTED else "Source"
        parts = [f"{head} : {self.source}", f"licence : {self.license}",
                 f"données du {self.retrieved.day} {_MONTHS[self.retrieved.month - 1]} {self.retrieved.year}"]
        return " · ".join(parts)


@dataclass(frozen=True)
class Chart:
    id: str
    dataset: str
    kind: str
    x: str
    series: tuple[tuple[str, str], ...]     # (column, label)
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    y_log: bool = False
    highlight: str = ""                     # boolean column: points drawn as estimates
    extra: dict = field(default_factory=dict)


_MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre")


def _number(value: str):
    text = value.strip()
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def load(root: Path, problem: Callable[[str, str], None]) -> tuple[dict[str, Dataset], dict[str, Chart]]:
    """Read and check datasets and charts. Problems are reported, not raised."""
    datasets: dict[str, Dataset] = {}
    meta = root / "data" / "datasets.toml"
    if meta.exists():
        with meta.open("rb") as handle:
            data = tomllib.load(handle)
        for raw in data.get("dataset", []):
            where = f"data/datasets.toml · {raw.get('id', '?')}"
            dataset = _dataset(root, raw, where, problem)
            if dataset:
                if dataset.id in datasets:
                    problem(where, "identifiant de jeu de données en double")
                datasets[dataset.id] = dataset

    charts: dict[str, Chart] = {}
    chart_file = root / "charts.toml"
    if chart_file.exists():
        with chart_file.open("rb") as handle:
            data = tomllib.load(handle)
        for raw in data.get("chart", []):
            where = f"charts.toml · {raw.get('id', '?')}"
            chart = _chart(raw, where, datasets, problem)
            if chart:
                if chart.id in charts:
                    problem(where, "identifiant de graphique en double")
                charts[chart.id] = chart
    return datasets, charts


def _dataset(root: Path, raw: dict, where: str, problem) -> Dataset | None:
    synthetic = bool(raw.get("synthetic", False))
    required = ("id", "title", "kind") if synthetic else ("id", "title", "kind", "source", "url", "license", "retrieved")
    missing = [k for k in required if not str(raw.get(k, "")).strip()]
    if missing:
        problem(where, f"champ(s) obligatoire(s) manquant(s) : {', '.join(missing)}")
        return None
    retrieved = raw.get("retrieved") or _dt.date.today()
    if isinstance(retrieved, str):
        try:
            retrieved = _dt.date.fromisoformat(retrieved)
        except ValueError:
            problem(where, f"date de récupération invalide « {retrieved} » (attendu AAAA-MM-JJ)")
            return None
    kind = str(raw["kind"])
    if kind == COMPUTED:
        generator = GENERATORS.get(str(raw.get("generator", "")))
        if generator is None:
            problem(where, f"générateur inconnu « {raw.get('generator', '')} »")
            return None
        rows = generator()
    elif kind == FILE:
        path = (root / "data" / str(raw.get("file", ""))).resolve()
        if not str(raw.get("file", "")).endswith(".csv") or not path.is_file():
            problem(where, f"fichier de données introuvable : data/{raw.get('file', '')}")
            return None
        if (root / "data").resolve() not in path.parents:
            problem(where, "le fichier doit se trouver dans data/")
            return None
        with path.open(encoding="utf-8", newline="") as handle:
            rows = [{k: _number(v) for k, v in row.items()} for row in csv.DictReader(handle)]
    else:
        problem(where, f"type de jeu de données inconnu « {kind} »")
        return None
    if not rows:
        problem(where, "jeu de données vide")
        return None
    columns = tuple(rows[0].keys())
    declared = tuple(raw.get("columns", columns))
    absent = [c for c in declared if c not in columns]
    if absent:
        problem(where, f"colonne(s) absente(s) des données : {', '.join(absent)}")
    return Dataset(id=str(raw["id"]), title=str(raw["title"]), kind=kind,
                   source=str(raw.get("source", "")), url=str(raw.get("url", "")),
                   license=str(raw.get("license", "")), retrieved=retrieved, columns=columns,
                   rows=tuple(rows), unit=str(raw.get("unit", "")), synthetic=synthetic,
                   notes=str(raw.get("notes", "")).strip())


def _chart(raw: dict, where: str, datasets: dict[str, Dataset], problem) -> Chart | None:
    dataset = datasets.get(str(raw.get("dataset", "")))
    if dataset is None:
        problem(where, f"jeu de données introuvable « {raw.get('dataset', '')} »")
        return None
    kind = str(raw.get("kind", "line"))
    if kind not in CHART_KINDS:
        problem(where, f"type de graphique inconnu « {kind} »")
    x = str(raw.get("x", ""))
    series = tuple((str(s.get("column", "")), str(s.get("label", s.get("column", ""))))
                   for s in raw.get("series", []))
    if not series:
        problem(where, "aucune série à tracer")
    for column in (x, *(c for c, _ in series), str(raw.get("highlight", "")) or x):
        if column not in dataset.columns:
            problem(where, f"colonne « {column} » absente du jeu « {dataset.id} »")
    return Chart(id=str(raw.get("id", "")), dataset=dataset.id, kind=kind, x=x, series=series,
                 title=str(raw.get("title", "")), x_label=str(raw.get("x_label", "")),
                 y_label=str(raw.get("y_label", "")), y_log=bool(raw.get("y_log", False)),
                 highlight=str(raw.get("highlight", "")))
