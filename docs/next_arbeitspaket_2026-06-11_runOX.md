# Nächstes Arbeitspaket – Plan-B AC0733_1_L Run OX (2026-06-11)

## Ziel

Run OX arbeitet den dokumentierten Kandidaten `AC0733_1_L.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.09223704` oberhalb der
Review-Grenze und zeigte lediglich eine rote Ellipse, obwohl die Beschreibung
ein nach rechts gedrehtes Quadrat-Kellen-Symbol mit horizontal bleibendem
`P` verlangt.

## Reale Re-Konvertierung

Der isolierte Lauf nutzt die XML-Beschreibung und den regulären
Non-Composite-Pfad. Ergebnis: Exit `0`, dimensionstreues `25x45`-SVG und
Auswahl von `non_composite_description_geometry_ir`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `17993.140625` | `2707.703125` |
| `normalized_mse` | `0.09223704` | `0.01388032` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `84.95 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Das Geometry-IR erhält ein semantisches Primitive für die in der fehlerhaften
AC0733-Selbstreferenz dennoch explizit beschriebene Rechtsdrehung mit
horizontalem `P`. Anschluss, roter Quadratgrundkörper und Text-Glyph werden als
getrennte SVG-Elemente gerendert; das P wird nicht mit der Grundgeometrie
rotiert. Alle Abmessungen sind größenrelative Familienparameter, und die
bestehende Rasterregistrierung passt Lage und Skalierung an die konkrete
Bildgröße an. Das akzeptierte SVG enthält weder eingebettete Rasterbilder noch
eine SVG-Rotation des Textes.

Die vorgelagerte PF8-Erkennung findet beim abgearbeiteten Raster bislang nur
den vertikalen Anschluss als Linie und keinen allgemeinen Rechteck- oder
Text-Seed. Der Perception-Lerneffekt bleibt deshalb für die aktive
Familienfolge getrennt vom nun generalisierten Beschreibungs-Geometry-IR.

## Rotation

`AC0733_1_L` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0732_1_L` auf. Die aktiven Kandidaten sind nun
`AC0733_1_M`, `AC0722_1_L`, `AC0723_1_S`, `AC0732_1_M` und `AC0732_1_L`.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0733-1-L-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `84.95 %` auf `2707.703125` gesenkt; `normalized_mse=0.01388032` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; PF8 benötigt weiterhin allgemeine Rechteck-/Text-Seeds für diese Symbolfamilie.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0733_1_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
