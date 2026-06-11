# Nächstes Arbeitspaket – Plan-B AC0551_2_M Run OW (2026-06-11)

## Ziel

Run OW arbeitet den dokumentierten Kandidaten `AC0551_2_M.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.09445446` oberhalb der
Review-Grenze und stellte statt der beschriebenen rechten Winkelkontur ein
Diagonalkreuz mit einem nicht beschriebenen Pluszeichen dar.

## Reale Re-Konvertierung

Der isolierte Ein-Datei-Lauf nutzt die XML-Beschreibung und den regulären
Non-Composite-Pfad. Ergebnis: Exit `0`, dimensionstreues `30x60`-SVG und
Auswahl von `non_composite_elementwise_symbol_fit`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `18425.703125` | `3294.235596` |
| `normalized_mse` | `0.09445446` | `0.01688702` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `82.12 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Der bereits für `AC0551_1_M` eingeführte allgemeine Element-Fit erkennt die
beschriebene Punktfolge Oben-Mitte → Rechts-Mitte → Unten-Mitte und rendert sie
als parametrisierte Polylinie. Linienbreite, vertikaler Einzug, Mittelachse,
rechter Scheitelpunkt, Farbe und Verlauf werden aus Beschreibung und Raster
angepasst. Für `AC0551_2_M` waren weder neue Sonderfalllogik noch feste
Koordinaten erforderlich.

Die Konturtopologie ist damit variantenübergreifend **generalisiert**. Die
vorgelagerte PF8-Erkennung bleibt unabhängig davon für die übrigen Kandidaten
an fehlenden Rechteck-/Text-Seeds beziehungsweise Kreis-Fehlpriorisierungen
begrenzt.

## Rotation

`AC0551_2_M` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0732_1_M` auf. Die aktiven Kandidaten sind nun
`AC0733_1_L`, `AC0733_1_M`, `AC0722_1_L`, `AC0723_1_S` und `AC0732_1_M`.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0551-2-M-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `82.12 %` auf `3294.235596` gesenkt; `normalized_mse=0.01688702` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; `AC0732_1_M` benötigt vor der Umsetzung eine robustere ROI-/Detector-Regel gegen die priorisierte Kreisdetektion.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0733_1_L.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
