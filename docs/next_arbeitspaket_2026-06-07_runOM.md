# Nächstes Arbeitspaket – Qualitätsrefresh und Plan-B-Triage Run OM (2026-06-07)

## Ziel

Nach dem vollständigen Abschluss der Run-OG-Rotation aktualisiert Run OM die
Qualitätsreports reproduzierbar und kuratiert daraus die nächste begrenzte
Plan-B-/Perception-Rotation.

## Reproduzierbarer Qualitätsrefresh

Der bestehende Review wurde ohne manuelle Kandidatenvorgabe ausgeführt:

```bash
PYENV_VERSION=3.10.20 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python tools/review_conversion_quality.py
```

Er prüft die Erfolgsliste zuerst und ergänzt anschließend kompakte Fälle aus
dem vorhandenen Diff-Inventar. Die Auswahl bleibt auf fünf Kandidaten und eine
Bildfläche von höchstens 3200 Pixeln begrenzt; `_sia`-Spezialvarianten werden
nicht aufgenommen.

## Qualitätsbefund

- `48/48` Varianten der Erfolgsliste besitzen ein renderbares Bild-/SVG-Paar.
- `AC0820_L` ist mit `normalized_mse=0.05117826` der einzige erfolgreiche
  Altbestand oberhalb der Review-Grenze `0.04594568`.
- `120/129` Diff-Inventarvarianten besitzen ein renderbares Paar.
- Die neue Rotation lautet `AC0820_L`, `AC0531_1_S`, `AC0502_1_M`,
  `AC0551_1_M`, `AC0403_1_M`.

## PF8-Linkage

Plan-B-Liste, Triage-CSV, statische PF8-Ziele und Linkage-Report enthalten die
fünf Varianten in derselben Reihenfolge. Vier Perception-Fragen sind bereits
`generalisiert`: Kreis-/Ring-Signale für `AC0820_L` und `AC0403_1_M` sowie
Primitive plus Kreis-Seed für `AC0531_1_S` und `AC0502_1_M`. Bei
`AC0551_1_M` werden Rechteck und Linien erkannt; ohne allgemeinen
`RectangleBackground`- oder `HorizontalRule`-Seed bleibt der Lerneffekt
`nur Sonderfall`.

## Abschluss

Run OM ist abgeschlossen: Review und PF8-Evidenz wurden neu erzeugt, alle
Kandidatenlisten sind synchron, und `AC0820_L.jpg` ist als nächster regulärer
Plan-B-Punkt festgelegt.

## 5-Zeilen-Log

- **Getestet:** Reproduzierbarer Quality-Review, deterministische Kandidatenauswahl und PF8-Linkage-Synchronität.
- **Ergebnis:** 48 Erfolgsvarianten und 129 Diff-Fälle geprüft; fünf aktive Kandidaten kuratiert.
- **Blocker:** Kein Triage-Blocker; `AC0551_1_M` besitzt noch keinen allgemeinen Rechteck-/HorizontalRule-Seed.
- **Nächster Schritt:** `AC0820_L.jpg` real re-konvertieren und Kreis-/CO²-Perception-Lerneffekt abschließen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
