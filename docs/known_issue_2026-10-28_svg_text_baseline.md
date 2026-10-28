# AC0721: Textprüfung und sichtbare SVG-Darstellung widersprechen sich

Am 28.10.2026 anhand der vom Nutzer gezeigten Original-/Ausgabebilder und
des bestehenden Archiv-SVGs `AC0721_1_L.svg` reproduziert. Reiner Diagnosebefund;
der Branch `codex/search-structure-composition-2026-10-28` ändert diesen
Textpfad und vorhandene Archiv-SVGs noch nicht.

## Ursache

Der [Geometry-IR-Emitter](../src/iCCModules/imageCompositeConverterGeometryIr/runtime.py)
schreibt einen Textanker `y="23.5"`, `font-size="18.793"` und
`dominant-baseline="middle"`. Die
[Beschriftungsregistrierung](../src/iCCModules/imageCompositeConverterLabeledSquare.py)
verschiebt `label_center` anhand tatsächlich gerenderter Buchstabengrenzen.
Dafür verwendet sie den produktiven MuPDF-Renderer. Dieser berücksichtigt
die Baselineangabe bei diesem SVG nicht: `middle` und `alphabetic` erzeugen
im Produktionsrenderer bytegleiche Raster.

librsvg berücksichtigt die Angabe dagegen. Bei achtfacher Darstellung des
unveränderten Archiv-SVGs ergeben sich folgende tatsächlichen Textgrenzen,
jeweils in ursprünglichen SVG-Koordinaten. Die Textmaske ist die Differenz
zum gleichen SVG ohne Textelement; Quadrat und Griff zählen dadurch nicht mit.

| Renderer und Baseline | Linke/obere Grenze | Rechte/untere Grenze |
| --- | --- | --- |
| MuPDF, `middle` | 7,0 / 9,75 | 18,0 / 23,5 |
| librsvg, `middle` | 7,125 / 15,5 | 17,875 / 27,625 |
| librsvg, `alphabetic` | 7,125 / 10,0 | 17,875 / 23,5 |

Das Quadrat reicht vertikal von 4,5 bis 28,5. Die relevante Abweichung der
oberen Textkante beträgt somit **5,75 Pixel bei nur 24 Pixel Quadratgröße**.
Die Baselineänderung allein führt auch im unabhängigen Renderer wieder
annähernd zur internen Position. Unterschiede der verwendeten Schriftmetriken
bleiben separat sichtbar.

## Warum die bisherige Abnahme das übersieht

Optimierung und Pixel-/Kantenbewertung verwenden denselben Renderer. Auch
das erneut gerenderte gespeicherte SVG aus der damaligen Abnahme läuft über
diesen Pfad. Der
[semantische Prüfer](../tools/evaluate_labeled_square_recheck.py)
prüft den exakten Buchstaben, Quadrat und Griff sowie `x < tx < x+w` und
`y < ty < y+h`. Das ist nur die Lage des Textankers. Tatsächliche Glyphenbox,
Abstand zum Quadratrand und Übereinstimmung verschiedener Renderer werden
dort nicht geprüft. Deshalb widerlegt der Befund die browserübergreifende
visuelle Abnahme trotz der bisherigen internen grünen Tests.

## Erforderliche Korrektur

`SVG-TEXT-BASELINE-01`: Für ausgegebene Texte eine explizite, rendererübergreifend
konsistente Baselinekonvention verwenden. Bestehende Textmodelle und gespeicherte
SVGs auf die gleiche Ursache prüfen. Tatsächliche Buchstabengrenzen und ihre
Position relativ zur Trägerform prüfen; eine vertikal verschobene T-Ausgabe
muss auch bei gültigem Textanker durchfallen. Mindestens ein unabhängiger
SVG-Renderer muss die endgültigen Ausgaben gegen Originalpixel abnehmen.
Vorhandene Qualitätsgrenzen bleiben erhalten.

Reproduktion des unabhängigen Renderings im vorhandenen lokalen Werkzeug:

```powershell
C:/msys64/ucrt64/bin/rsvg-convert.exe --width 200 --height 360 --output .tmp/ac0721-librsvg.png artifacts/satisfactory_conversions/svgs/AC0721_1_L.svg
```

Die drei lokalen Renderings und Hilfsdateien liegen unter `.tmp/ac0721-*`.
Der Befund betrifft mindestens den gezeigten Textpfad; die Häufigkeit in anderen
Textmodellen ist noch nicht inventarisiert.
