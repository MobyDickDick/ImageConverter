# Wiederholtes rotes Rechteck: allgemeine Suchschwäche

Der Einwand wurde am unveränderten Original `AC0701_L.jpg` und seiner aktuellen
Beschreibung reproduziert. Der alte allgemeine Geometry-IR-Fit erzeugt bei Seed
17 und 18 byteidentische SVGs und identische Renderfolgen: einen schmalen roten
Balken am oberen Rand. Das ist ein tatsächlich ignorierter Seed in diesem Pfad.

Die IR-Startvorlage enthält die feste Farbe `#e11e48`. Die bisherige allgemeine
Anpassung verändert diese `body_fill`-Eigenschaft nicht. Sie passt zuerst nur
Position, unabhängige Skalierungen und einen Teil der Strichbreiten an. Mit dem
bisherigen mittleren Pixelabstand lässt sich ein falscher roter Körper durch
Schrumpfen scheinbar verbessern. Die unabhängige Skalierung macht ausserdem aus
dem beschriebenen Quadrat ein Rechteck. Die letzte Quadratprüfung verwirft es.
Wiederholen mit einem anderen Seed erschloss dort keine andere Suchfolge.

## Änderung

Der erste allgemeine Beschreibungsfit verwendet jetzt:

- Gemessene Farben für vorhandene Flächen und Konturen. Schwarz-/Weiss-Proben
  ihrer eigenen Renderabdeckung liefern Farbmasken; daraus werden Farben
  geschätzt und mit Messwerten aus dem Original verglichen. Eine falsche rote
  Fläche wird vor der Randfarbe angepasst, damit keine komplementäre Randfarbe
  die falsche Ausgangsfarbe zu kompensieren versucht.
- Acht räumliche Neustarts mit vom vollständigen Seed abhängigen Positionen,
  Grössen und Strichbreiten. Bis zu vier Zweige werden lokal weiterverfolgt.
  Ein schlechterer Startpunkt darf einen neuen Zweig eröffnen; der beste gültige
  Kandidat bleibt erhalten. Verbesserungen werden anhand von Vordergrund,
  Konturen und Pixelfehler bewertet.
- Gemeinsame Achsenskalierung für beschriebene Quadrate und Kreise. Form- und
  Inventarprüfung erfolgen vor dem Rendern jedes Kandidaten. Die erlaubten
  Objekte stammen ausschliesslich aus der Beschreibung.
- Deduplizierung tatsächlicher SVG-Kandidaten, komprimierte Rasterablage,
  Kandidatenzahlen und Hashes der echten Renderfolge. Das vorhandene
  Kandidatenbudget und das Bildzeitlimit bleiben Grenzen.

Der neue Pfad ist in den normalen allgemeinen Beschreibungsfit von CLI und
GUI integriert. Es gibt keine zweite Rasterrekonstruktion, keine zusätzlichen
erfundenen Formen und keine vom Dateinamen abhängigen Koordinaten. Die
Spezialkorrektur für Quadrat und Griff bleibt ein schneller erster Fit.
Die allgemeine Korrektur wurde zusätzlich bei abgeschaltetem Spezialfit geprüft.

## Nachweis

`summary.json` enthält den reproduzierbaren Vergleich. `comparison.png` zeigt
Original, alten allgemeinen Fit und neue allgemeine Fits mit Seed 17, 18 und 19.
Die generierten SVGs bleiben entsprechend der Repository-Regeln lokale
Prüfartefakte. Die generische Suche hat eine gröbere Qualität als die bereits
gespeicherte spezialisierte Konvertierung; das bessere Projekt-SVG bleibt erhalten.

| Messung | Alter allgemeiner Fit | Neuer allgemeiner Fit |
| --- | --- | --- |
| Seeds | 17, 18 | 17, 18, 19 |
| Eindeutige gerenderte Kandidaten je Lauf | 135 | 384 |
| Renderfolge bei verschiedenen Seeds | identisch | verschieden |
| Ausgabefarbe | unverändert rot | am Original gemessen |
| Quadrat und Griff vollständig | nein | ja |
| Qualitätsprüfung am gemeldeten Bild | fehlgeschlagen | alle drei bestanden |

Ein unabhängiger Negativfall zeigt vier getrennte Kreise bei einer vorgegebenen
Ein-Rechteck-Beschreibung. Die neue Suche prüft jeweils 160 eindeutige Kandidaten
und acht Neustarts, erhält aber keine Qualitätsfreigabe. Derselbe Seed erzeugt
dieselbe Renderfolge; ein anderer Seed prüft andere Geometrie. Ein zusätzlicher
Test verwendet zwei echte isolierte GUI-Worker mit einer ebenfalls unmöglichen
Quadrat-/Griff-Beschreibung am Kreismotiv. Beide bleiben ungenügend und weisen
unterschiedliche tatsächlich gerenderte Suchfolgen nach.

Identische gute Ergebnisse bleiben möglich. Auch schlechte Endergebnisse können
gleich sein, wenn dieselbe beste Annäherung gefunden wird. Entscheidend sind
die tatsächlich geprüften Alternativen und die Qualitätsprüfung; unterschiedliche
Ausgabedateien allein würden den Fehler nicht beheben.

## Prüfstand

- Neue Such-, Wiederholungs-, Inventar- und GUI-Tests plus bestehende Seed-Tests:
  **18 bestanden**.
- Grundformen, Zeichenflächengrenzen, Vorlagenstart, Quadrat-/Griff-Reparatur und
  Zweiwegventil: **67 bestanden**.
- Breiter Block mit IR-Optimierer, Non-Composite-Runtime, Sprache und Seed-Tests:
  **457 bestanden, ein bereits bestehender Fehler** beim Mittelpunkt eines
  skalierten Verlaufspanels (`scale=2`, `shift=-1.2`, `radius=5.5`). Derselbe
  Fehler wurde unabhängig mit der aus `git show HEAD:...` geladenen unveränderten
  `_fit_symbol_element_by_element`-Funktion bestätigt. Dieser historische
  Forschungsfit ruft die hier ergänzte Registrierung nicht auf.
- Bild-ID-Nullprüfung und Whitespace-Prüfung der geänderten Dateien bestanden.

```powershell
$env:PYTHONPATH='.'
.venv/Scripts/python.exe tools/evaluate_description_registration_search.py
.venv/Scripts/python.exe -m pytest tests/test_description_registration_search.py tests/test_seed_search_effect.py -q
.venv/Scripts/python.exe -m pytest tests/test_plain_vertical_square_stem.py tests/test_sample_start_regression.py tests/test_simple_form_representation.py tests/test_canvas_containment.py tests/test_two_way_valve_description.py -q
.venv/Scripts/python.exe -m pytest tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py tests/test_description_language.py -q
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
```
