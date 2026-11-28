"""Small AP 1/2 gallery. Execute conversions only in GitHub Actions.

The synthetic reference scenes below are teaching fixtures, not holdouts.
Only the baseline case uses the engine's automatic raster proposals.
"""
import argparse
from dataclasses import asdict, dataclass
from html import escape
import json
import os
from pathlib import Path

import cv2
import numpy as np

from src.exploratory import Candidate, Paint, Primitive, Scene, convert
from src.exploratory import adapters
from src.exploratory.scene import KINDS


@dataclass(frozen=True)
class Example:
    key: str
    title: str
    explanation: str
    target: Scene
    # None uses the automatic AP 1 providers; tuples are scripted proposals.
    proposals: tuple[Candidate, ...] | None


def examples():
    """Edit these small scenes to explore representation and paint order."""
    primitives = Scene(360, 120, tuple(
        Primitive(f"p{i}", kind, center=(.085 + i * .166, .5),
                  size=(.12, .5), angle=.035,
                  paint=Paint((200, 50, 65), (25, 75, 110), .025))
        for i, kind in enumerate(KINDS)))

    panel = Primitive("panel", "ellipse", size=(.55, .65),
                      paint=Paint((205, 45, 55)))
    noise = Primitive("extra", "triangle", center=(.85, .2), size=(.2, .3))
    disk = Primitive("disk", "circle", center=(.65, .5), size=(.55, .7),
                     paint=Paint((35, 100, 215)))
    initial = Scene(200, 140, (panel, noise))
    removed = initial.remove("extra")
    added = removed.add(disk)
    changed = added.update("panel", kind="rect")
    target = changed.reorder(("disk", "panel"))
    steps = (("Ausgangsentwurf", initial), ("Entfernen: extra", removed),
             ("Hinzufügen: disk", added), ("Typwechsel: panel → rect", changed),
             ("Zeichenreihenfolge: disk vor panel", target))
    return (
        Example("primitives", "Alle sechs Grundformen",
                "Vorgegebene Szene: Kreis, Ellipse, Rechteck, Quadrat, Dreieck und Linie. "
                "Das Original wird aus derselben Szene gerastert; dies prüft Darstellung, "
                "nicht Erkennung oder Generalisierung.", primitives,
                (Candidate.from_scene(primitives, "Vorgegebene sechs Grundformen"),)),
        Example("edits", "Vorgegebene Szenenänderungen",
                "Diese fünf Entwürfe und ihre Reihenfolge sind im Beispiel programmiert. "
                "Der Kern bewertet sie und behält den besten; er erfindet die Änderungen "
                "noch nicht selbst. Die Objekt-ID panel bleibt beim Typwechsel erhalten.",
                target, tuple(Candidate.from_scene(scene, label) for label, scene in steps)),
        Example("automatic", "Automatische AP-1-Baseline ohne Beschreibung",
                "Dasselbe Original, diesmal ohne vorgegebene Kandidaten. Nur Raster und "
                "leere Beschreibung gehen an convert. Rechteck und Ellipse aus der "
                "Rasterbegrenzung können diese Komposition noch nicht rekonstruieren. "
                "Der beste unzureichende Vektorentwurf bleibt sichtbar.", target, None),
    )


def _json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False),
                    encoding="utf-8")


def _png(path, pixels):
    if not cv2.imwrite(str(path), pixels):
        raise OSError(f"Cannot write {path}")


def generate(output):
    """Save every actually evaluated draft, then the engine's best selection."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = {"commit": os.environ.get("GITHUB_SHA", "unknown"),
              "run_url": (f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/"
                          f"{os.environ['GITHUB_RUN_ID']}"
                          if os.environ.get("GITHUB_RUN_ID") else None),
              "examples": []}
    sections = []
    for example in examples():
        folder = output / example.key
        folder.mkdir(exist_ok=True)
        reference = adapters.render(example.target.to_svg(), example.target.width,
                                    example.target.height)
        _png(folder / "original.png", reference)
        proposals = {p.svg: p for p in example.proposals or ()}
        records = []

        def evaluate(image, raster, svg):
            # The same production metrics drive selection and the visible report.
            quality, score = adapters.evaluate(image, raster, svg)
            stem = f"draft-{len(records) + 1}"
            candidate = proposals.get(svg)
            (folder / f"{stem}.svg").write_text(svg, encoding="utf-8")
            _png(folder / f"{stem}.png", raster)
            difference = np.clip(np.abs(image.astype(np.int16) - raster.astype(np.int16))
                                 * 4, 0, 255).astype(np.uint8)
            _png(folder / f"{stem}-difference.png", difference)
            if candidate is not None and candidate.scene is not None:
                _json(folder / f"{stem}-scene.json", candidate.scene.to_dict())
            records.append({"stem": stem, "source": candidate.source if candidate else
                            "Automatischer Rastervorschlag", "quality": quality,
                            "score": score, "svg": svg,
                            "scene_file": f"{stem}-scene.json" if candidate else None})
            return quality, score

        # This synchronous call is also the entry for debugger breakpoints.
        result = convert(reference, description="", seconds=10, max_candidates=16,
                         sources=None if example.proposals is None else
                         [lambda image, description: iter(example.proposals)],
                         evaluate=evaluate)
        if result.best is None or result.errors:
            raise RuntimeError(f"Demo {example.key}: {result.errors or result.stop_reason}")
        for record in records:
            record["best"] = record.pop("svg") == result.best.svg
        summary = asdict(result)
        summary.pop("best")
        summary.update(key=example.key, scripted=example.proposals is not None,
                       drafts=records, best_source=result.best.source)
        report["examples"].append(summary)
        (folder / "best.svg").write_text(result.best.svg, encoding="utf-8")
        cards = []
        for record in records:
            stem = record["stem"]
            status = ("Pixelziel bestanden" if record["quality"]["passed"] else
                      "Pixelziel NICHT bestanden – unzureichender Entwurf")
            best = " · Bester Entwurf" if record["best"] else ""
            images = "".join(
                f'<figure><img src="{example.key}/{name}" alt="{label}">'
                f'<figcaption>{label}</figcaption></figure>'
                for name, label in (("original.png", "Original (synthetisch)"),
                                    (f"{stem}.svg", "SVG-Vorschau"),
                                    (f"{stem}-difference.png", "Absolute Differenz ×4")))
            scene_link = (f' · <a href="{example.key}/{record["scene_file"]}">Szene JSON</a>'
                          if record["scene_file"] else "")
            cards.append(
                f'<article><h3>{escape(record["source"])}{best}</h3>'
                f'<p class="status">{status}. Nicht freigegeben.</p><div class="images">'
                f'{images}</div><p><a href="{example.key}/{stem}.svg">SVG öffnen / speichern</a>'
                f' · <a href="{example.key}/{stem}.png">Gerendertes PNG</a>{scene_link}</p>'
                f'<details><summary>Qualitätswerte · Score {record["score"]:.6f}</summary>'
                f'<pre>{escape(json.dumps(record["quality"], indent=2))}</pre></details></article>')
        sections.append(
            f'<section><h2>{example.title}</h2><p>{example.explanation}</p>'
            f'<p>{result.generated} Kandidaten · {result.renderings} Renderings · '
            f'{result.evaluated} Bewertungen · Abbruch: {escape(result.stop_reason)} · '
            f'<a href="{example.key}/best.svg">Bester SVG-Entwurf</a></p>'
            + "".join(cards) + '</section>')
    _json(output / "report.json", report)
    (output / "index.html").write_text(
        '<!doctype html><html lang="de"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Explorativer Konverter – AP 1/2 Demo</title><style>'
        'body{font:16px/1.5 system-ui,sans-serif;margin:2rem auto;padding:0 1rem;max-width:1100px;'
        'color:#172635;background:#f1f5f9}article{background:white;padding:1rem;margin:1rem 0;'
        'border:1px solid #b4c3d1;border-radius:8px}.images{display:flex;flex-wrap:wrap;gap:1rem}'
        'figure{margin:0;flex:1;min-width:200px}img{width:100%;height:160px;object-fit:contain;'
        'background:white;border:1px solid #ddd}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
        '.status{font-weight:bold}a{color:#12539b}</style><body>'
        '<h1>Explorativer Konverter: sichtbarer Stand nach AP 2</h1>'
        '<p>Lehrbeispiele mit synthetischen Originalen. Vorgegebene Szenen demonstrieren '
        'die Repräsentation; die automatische Baseline zeigt die derzeitige Suchgrenze. '
        'Auch ein bestandenes Pixelziel ist keine semantische Freigabe. '
        'AP 3/4 und unabhängige Generalisierungsprüfungen stehen aus.</p>'
        f'<p>Commit: <code>{escape(report["commit"])}</code> · '
        '<a href="report.json">Vollständiger Messbericht (JSON)</a></p>'
        + "".join(sections) + '</body></html>', encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = generate(args.output)
    print(f"Gallery: {args.output / 'index.html'} ({len(report['examples'])} examples)")


if __name__ == "__main__":
    main()
