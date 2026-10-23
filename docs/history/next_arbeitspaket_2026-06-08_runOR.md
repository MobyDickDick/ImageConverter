# Nächstes Arbeitspaket – Plan-B AC0502_1_M Run OR (2026-06-08)

## Ziel

Run OR arbeitet den in Run OQ dokumentierten Kandidaten `AC0502_1_M.jpg`
vollständig ab. Das bisherige SVG lag mit `normalized_mse=0.15533278` deutlich
über der Review-Grenze und stellte die im Raster sichtbare gedrehte Diagonale
nicht korrekt dar.

## Reale Re-Konvertierung

```bash
rm -rf /tmp/ic-ac0502-input /tmp/ic-ac0502-run
mkdir -p /tmp/ic-ac0502-input
cp artifacts/images_to_convert/AC0502_1_M.jpg /tmp/ic-ac0502-input/
timeout 240 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir /tmp/ic-ac0502-input \
  --output-dir /tmp/ic-ac0502-run \
  --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`, dimensionstreues `60x30`-SVG und Auswahl des allgemeinen
`non_composite_elementwise_symbol_fit`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `30301.542969` | `3126.661621` |
| `normalized_mse` | `0.15533278` | `0.01602799` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung beträgt `27174.881348` beziehungsweise rund `89.68 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Der allgemeine Element-Fit erkennt deklarierte Vierteldrehungen beziehungsweise
90-Grad-Drehungen und tauscht bei genau einer beschriebenen Diagonale die beiden
Diagonalachsen. Damit wird die Familienbeschreibung zuerst semantisch gelesen
und anschließend auf die geometrische Variante transformiert. Farbe, Breite,
Verlauf, Mittelpunkt und Diagonalausdehnung werden weiterhin aus dem Raster
geschätzt; es wurden weder ein Kandidaten-SVG noch feste AC0502-Koordinaten in
den Algorithmus aufgenommen.

Die PF8-Frage ist **generalisiert**: Rechteck-, Linien- und Kreis-/Ringkandidaten
waren bereits allgemein detektierbar; die Runtime verbindet diese Evidenz nun
mit der rotationsbereinigten Beschreibungstopologie. Regressionstests sichern
die Achsentransformation, die Primitive, den roten Rasterfarberhalt und die
Qualitätsgrenze.

## Rotation

`AC0502_1_M` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0551_2_M` auf. Die aktiven Kandidaten sind nun
`AC0551_1_M`, `AC0403_1_M`, `AC0150_2`, `AC0253_1` und `AC0551_2_M`.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0502-1-M-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `89.68 %` auf `3126.661621` gesenkt; `normalized_mse=0.01602799` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; JPEG-Antialiasing und die sehr flache Rastergradientenvariation bleiben als Restabweichung.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0551_1_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
