# AC0151: Röhrenmodell und Renderkorrektur

## Ursachen

Die bisherige Beschreibung nennt eine Röhre, aber kein Rechteck. Sie wird als
unzureichende Geometriebeschreibung eingestuft. Der allgemeine Element-Fallback
liefert ein Panel mit einem seitlichen Verlauf; der senkrechte Farbwechsel und
die beiden grauen Kappen fehlen. Ein frischer unveränderter CLI-Lauf bestätigt
den Fehler (Mean-Delta² 2506,26, Pixelabnahme fehlgeschlagen).

Die Sample-Datei liegt unter `artifacts/samples/AC0151_L.svg`. Der ältere
automatische Sample-Fallback sucht hingegen unter `images_to_convert/samples`
oder in explizit konfigurierten Verzeichnissen. Ein vorhandenes Sample erweitert
den Rekonstruktionsalgorithmus nicht automatisch.

Zusätzlich überspringt der bisherige MuPDF-Adapter Farbverläufe mit
`gradientTransform`. Der nachfolgende ältere Rechteckadapter ignoriert deren
Transparenz. Dadurch wird die Sample-Röhre intern schwarz/grau statt farbig
gerendert. Positive Skalierungen und Verschiebungen des Farbverlaufs werden nun
im passenden Adapter durch inverse Koordinatentransformation berücksichtigt.
Das umfasst auch ungleichmäßige Skalierung und diagonale Verlaufsachsen.
Die gespeicherte Sample-SVG bleibt unverändert.

Auch korrekt gerendert entspricht das Sample nicht exakt dem JPG: Die Kappen
sind dort 13,33 statt 18 Pixel hoch, und die Farben sind unterschiedlich. Es
besteht deshalb weiterhin nicht die unveränderten Kanten-/Maskenprüfungen.

## Korrektur

Die gemeinsame XML-Beschreibung für L/M/S beschreibt nun das lange Rechteck,
die bündigen grauen Kappen, die zwei Verlaufsrichtungen und den rechts der Mitte
liegenden Glanzbereich ausdrücklich. Die alte Kurzbeschreibung wird ebenfalls
unterstützt, einschließlich des bisherigen Modus `insufficient_description`.

Das neue Modell vermisst ausschließlich das Raster: Kappengrenzen, zwei
senkrechte Endfarben, vier seitliche Schattierungsstopps und je vier Stopps für
die Kappen. Es exportiert vier native SVG-Rechtecke mit insgesamt 14 Stopps,
ohne nachgezeichnete Pfade, Rastereinbettung oder Katalog-ID-Verzweigung.
Bei verkleinerten JPEGs werden gemischte Kappenrandpixel berücksichtigt.
Lokale Detailprüfungen sichern beide Kappen und den Röhrenkörper ab.

Eine zusätzliche generische Feinoptimierung änderte bei L die SVG-Bytes und
verlor dadurch die ursprüngliche Modellfreigabe. Der Artefaktschreiber prüft
bei verfeinerten Röhren nun erneut native Struktur, Pixelgrenzen und lokale
Kappen-/Körperdetails. Nur bestandene Verfeinerungen werden übernommen und neu
validiert. Eine unsichtbare Zusatzform oder eine entfernte Kappe genügt nicht.

## Prüfung und Artefakte

`before/AC0151_L.svg` bewahrt die frische Reproduktion mit der ursprünglichen
Beschreibung. `after/` enthält die tatsächlichen CLI-SVGs und die Raster beider
Renderer. `summary.json` enthält die unabhängigen Messwerte.

| Original | MuPDF-MSE, normiert | librsvg-MSE, normiert | Pixel- und lokale Detailabnahme |
| --- | ---: | ---: | --- |
| L | ca. 0,000035 | ca. 0,000035 | beide bestanden |
| M | 0,000039 | 0,000039 | beide bestanden |
| S | 0,000049 | 0,000049 | beide bestanden |

Die Qualitätsgrenzen bleiben unverändert: MSE ≤ 0,01, Vordergrund-MSE ≤ 0,04,
Masken-IoU ≥ 0,85 und Kantenübereinstimmung ≥ 0,72. Die neuen lokalen
Detailprüfungen verlangen zusätzlich ein 95%-Fehlerquantil ≤ 8 je Region.

Reproduktion der gespeicherten Ausgaben:

```powershell
.venv/Scripts/python.exe -m artifacts.evaluation.gradient_tube_2026-11-14.verify
.venv/Scripts/python.exe -m tools.convert_one_image AC0151_L --output-dir .tmp/tube-recheck
.venv/Scripts/python.exe -m pytest -q tests/test_gradient_tube_runtime.py tests/detailtests/test_iteration_initialization_helpers.py tests/detailtests/test_rendering_gradient_compatibility.py tests/test_axial_panel_runtime.py
```

113 fokussierte Tests und 243 angrenzende Regressionstests bestehen. Die Tests
enthalten sechs analytisch erzeugte Raster ohne SVG-Referenzrenderer, drei echte
JPEG-Größen, zusätzliche Objekte/Negationen, beschädigte Kappen und Verläufe,
Budgetablauf, Beschreibungsnormalisierung und transformierte transparente Farben.
Laufprotokolle liegen unter `artifacts/test-evidence/ac0151_tube_*_2026-11-14.log`.

Die Abnahme betrifft diesen beschriebenen Röhrentyp. Anbauten, Beschriftungen,
beliebige Röhrenformen und andere Farben sind damit nicht allgemein abgedeckt.
