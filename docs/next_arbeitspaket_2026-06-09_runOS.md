# Nächstes Arbeitspaket – Plan-B AC0551_1_M Run OS (2026-06-09)

## Ziel

Run OS arbeitet den in Run OR dokumentierten Kandidaten `AC0551_1_M.jpg`
vollständig ab. Das bisherige SVG lag mit `normalized_mse=0.14916385` deutlich
über der Review-Grenze und stellte statt der beschriebenen rechten
Winkelkontur ein nicht passendes Diagonalkreuz mit Pluszeichen dar.

## Reale Re-Konvertierung

```bash
rm -rf /tmp/ic-ac0551-input /tmp/ic-ac0551-run
mkdir -p /tmp/ic-ac0551-input
cp artifacts/images_to_convert/AC0551_1_M.jpg /tmp/ic-ac0551-input/
timeout 240 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir /tmp/ic-ac0551-input \
  --output-dir /tmp/ic-ac0551-run \
  --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`, dimensionstreues `30x60`-SVG und Auswahl des allgemeinen
`non_composite_elementwise_symbol_fit`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `29098.138672` | `4518.557129` |
| `normalized_mse` | `0.14916385` | `0.02316318` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung beträgt `24579.581543` beziehungsweise rund `84.47 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Der allgemeine Element-Fit erkennt die beschriebene Punktfolge
Oben-Mitte → Rechts-Mitte → Unten-Mitte und rendert sie als parametrisierte
Polylinie. Linienbreite, vertikaler Einzug, Mittelachse, rechter Scheitelpunkt
und Linienfarbe werden im bestehenden elementweisen Pixelvergleich angepasst;
der Farbverlauf und Rahmen bleiben rastergemessen. Es wurden weder ein
Kandidaten-SVG noch feste AC0551-Koordinaten in den Algorithmus aufgenommen.

Die Konturtopologie ist damit im Rekonstruktionspfad **generalisiert**. Die
vorgelagerte PF8-Erkennung bleibt `nur Sonderfall`, weil sie zwar Linien und
Rechteck findet, aber noch keinen allgemeinen `RectangleBackground`- oder
`HorizontalRule`-Seed liefert.

## Rotation

`AC0551_1_M` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0733_1_L` auf. Die aktiven Kandidaten sind nun
`AC0403_1_M`, `AC0150_2`, `AC0253_1`, `AC0551_2_M` und `AC0733_1_L`.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0551-1-M-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `84.47 %` auf `4518.557129` gesenkt; `normalized_mse=0.02316318` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; die vorgelagerte Detection besitzt weiterhin keinen allgemeinen Rechteck-/HorizontalRule-Seed.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0403_1_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
