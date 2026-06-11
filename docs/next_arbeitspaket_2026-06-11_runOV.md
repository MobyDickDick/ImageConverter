# Nächstes Arbeitspaket – Plan-B AC0253_1 Run OV (2026-06-11)

## Ziel

Run OV arbeitet den dokumentierten Kandidaten `AC0253_1.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.10473690` oberhalb der
Review-Grenze und enthielt nur einen unpassend positionierten Kreis, obwohl die
Familienbeschreibung ein Pumpensymbol aus Kreis und um 180 Grad gedrehtem
Dreieck vorgibt.

## Reale Re-Konvertierung

Der isolierte Ein-Datei-Lauf nutzt die XML-Beschreibung und den regulären
Non-Composite-Pfad. Ergebnis: Exit `0`, dimensionstreues `31x31`-SVG und
Auswahl von `non_composite_description_geometry_ir`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `20431.550781` | `3327.906250` |
| `normalized_mse` | `0.10473690` | `0.01705962` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `83.71 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Das bereits für referenzierende AC0251-/AC0401-Beschreibungen eingeführte
Pumpen-Geometry-IR wird unverändert auf die AC0253-Familie übertragen. Es
modelliert den Kreisgrundkörper und das rotationsfähige Innendreieck als
getrennte Primitive; die bestehende Rasterregistrierung bestimmt Geometrie und
Farben für die konkrete Bildgröße. Der Lauf bestätigt damit die
Familiengeneralisierung ohne AC0253-spezifische Koordinaten oder fest
hinterlegtes Kandidaten-SVG.

## Rotation

`AC0253_1` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare Review
füllt mit `AC0723_1_S` auf. Die aktiven Kandidaten sind nun `AC0551_2_M`,
`AC0733_1_L`, `AC0733_1_M`, `AC0722_1_L` und `AC0723_1_S`. Die neue
Anschluss-/Quadrat-Frage bleibt mangels allgemeinem Rechteck-Seed zunächst
`nur Sonderfall`.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0253-1-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `83.71 %` auf `3327.906250` gesenkt; `normalized_mse=0.01705962` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; `AC0723_1_S` benötigt für eine Generalisierung noch einen allgemeinen Rechteck-Seed.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0551_2_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
