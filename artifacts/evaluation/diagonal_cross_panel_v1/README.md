# Gerahmtes Rechteck mit Kreuz und begrenzter Diagonale

AC100_1_M.jpg ist ein stark verpixeltes, eng beschnittenes 30×60-JPEG.
Der Katalog enthielt einen Platzhalter mit einem falschen Kreis-/Griffhinweis.
Die neue eigenständige Beschreibung stammt aus der Benutzerangabe: rotes
stehendes Rechteck, dunkelroter Rand, Kreuz oben links, aufsteigende Diagonale
mit dunkler Mittellinie und zwei hellen Seitenlinien, am Rechteck abgeschnitten.

Die Beschreibung allein genügt nicht: Der generische Fallback besitzt kein
gemeinsames Modell dieser Einzelteile. Seine Ausgabe besteht zwar die globalen
Rastergates, bleibt aber semantisch ein Entwurf. Deshalb ergänzt der reguläre
Konverter einen rastergestützten Fit dieser Formklasse. Begrenzte native
SVG-Primitive rekonstruieren Rahmen, dreistufige Füllfarbe, Plus und die beiden
übereinanderliegenden Diagonalstriche. Ein SVG-Clip begrenzt beide Striche;
der Rahmen wird zuletzt gezeichnet. Dunkle Mitte und helle Seiten bleiben
unterschiedliche Farben und Breiten. Zusätzliche lokale Rasterprüfungen gelten
für Kreuz und Diagonale. Vorhandene Qualitätsgrenzen bleiben unverändert.

Der Fit verwendet keine Bildnamen und keine Referenz-SVGs. Die echten CLI-Läufe
geben ausschließlich Raster und Beschreibung vor; der letzte Lauf erhält eine
isolierte Kopie genau dieser JPEG-Datei, um den ähnlich geschriebenen,
anderen Katalogeintrag AC1001_M nicht mit auszuwählen.

`summary.json` enthält den Vergleich bei identischen JPEG-Bytes:
Platzhalterbeschreibung, neue Beschreibung allein und vollständiger Form-Fit.
MuPDF und unabhängig librsvg bestätigen die finale Ausgabe. Drei eigenständig
gezeichnete Farb-/Größenfälle von 30×60 bis 60×120 bestehen ebenfalls. Fehlendes
Kreuz, fehlende Diagonale und widersprüchliche Beschreibungen werden abgewiesen.
Das Erfolgsarchiv wird nicht erweitert.

## Prüfungen

- 13 neue Formtests bestehen einschließlich einer Prüfung der SVG-Begrenzung.
- Die gemeinsame Prüfung mit den Pfeiltests besteht 34 Tests.
- Die betroffenen Laufzeithelfer, Geometrie- und Formtests bestehen 101 Tests.
- Syntaxprüfung, CLI-Hilfe und Image-ID-Hardcoding-Prüfung bestehen.
- Der vollständige Testbefehl mit `-x` endet nach 744 bestandenen Tests am
  bereits bekannten AC0VR2-ZL-M-Fixturevergleich außerhalb dieser Änderung.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_diagonal_cross_panel_runtime.py tests/detailtests/test_non_composite_runtime_helpers.py tests/test_diagonal_stripe_panel_geometry_ir.py
.venv/Scripts/python.exe -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir .tmp/diagonal-cross-panel-replay --start AC100_1_M --end AC100_1_M --search-seed 42 --deterministic-order
```

Der Bereichsbefehl kann auch den ähnlich geschriebenen anderen Katalogeintrag
auswählen. Für die genaue Einzelprüfung stattdessen einen Ordner verwenden,
der nur eine unveränderte Kopie von AC100_1_M.jpg enthält. Die finale lokale
Ausgabe liegt unter `final/converted_svgs/AC100_1_M.svg`, der Bildvergleich unter
`comparison.png`. Eine gespeicherte Kopie liegt zusätzlich im gemeinsamen
Ausgabeordner und bei den Bestlistensnapshots.
