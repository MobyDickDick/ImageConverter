# Nächstes Arbeitspaket – Plan-B AC0150_2 Run OU (2026-06-09)

## Ziel

Run OU arbeitet den dokumentierten Kandidaten `AC0150_2.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.10493784` oberhalb der
Review-Grenze und verlor den gesättigten grünen Verlauf, weil ein heller
Rahmen beziehungsweise die helle Winkelkontur als Verlaufsmaximum dominierte.

## Reale Re-Konvertierung

Der isolierte Ein-Datei-Lauf nutzt die XML-Beschreibung und den regulären
Non-Composite-Pfad. Ergebnis: Exit `0`, dimensionstreues `40x80`-SVG und
Auswahl von `non_composite_elementwise_symbol_fit`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `20470.750000` | `7988.364258` |
| `normalized_mse` | `0.10493784` | `0.04095022` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung beträgt rund `60.98 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Die bereits allgemeine, beschreibungsgetriebene Kontur
Oben-Mitte → Rechts-Mitte → Unten-Mitte bleibt parametrisch. Für gesättigte
Dunkel-Hell-Dunkel-Verläufe wird die mittlere RGB-Farbe nun robust aus dem
zentralen Spaltenband geschätzt. Dadurch können ein weißer Außenrahmen oder
eine helle Kontur nicht mehr fälschlich den Hintergrundmittelpunkt bestimmen.
Es wurden keine AC0150-spezifischen Pixelkoordinaten oder Kandidaten-SVGs im
Algorithmus hinterlegt.

## Rotation

`AC0150_2` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0722_1_L` auf. Die aktiven Kandidaten sind nun
`AC0253_1`, `AC0551_2_M`, `AC0733_1_L`, `AC0733_1_M` und `AC0722_1_L`.
Die neue Anschluss-/Quadrat-/T-Frage ist aufgrund einer fälschlich
priorisierten Kreisdetektion zunächst `noch nicht erkannt`.

## 5-Zeilen-Log

- **Getestet:** Rasterparameter-Tests, isolierter AC0150-2-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `60.98 %` auf `7988.364258` gesenkt; `normalized_mse=0.04095022` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; `AC0722_1_L` benötigt im Folgepaket eine passendere Detector-/ROI-Regel.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0253_1.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
