# Verbindliche Formränder, Verläufe und geschlossene Polygonkonturen

Die gemeldeten Wiederholungen hatten zwei Ursachen. Normale Profile übernahmen
das bereits global pixelähnliche Projekt-SVG. Die ergänzten Angaben zu gleich
breiten Dreiecksrändern und je einem Grauverlauf wurden dabei nicht geprüft.
Die freie Suche konnte diese Ergänzungen bisher nicht vollständig übersetzen.
Zusätzlich liess MuPDF beim Rendern nativer Polygone die letzte Konturkante weg:
Die Optimierung bewertete andere Konturen als der Browser.

Die gemeinsame Beschreibungsauswertung bindet solche Angaben jetzt an die
genannte Formgruppe. Die Suche teilt den geforderten Breitenparameter und
erzwingt echte, unterschiedliche Verlaufsstopps. Dieselben Prüfungen gelten
für normale Profile, freie Suche, Vorlagen, Entwürfe und Projektvergleiche.
Die ursprüngliche AC0204_L-Beschreibung blieb unverändert; das alte Projekt-SVG
wird mit `scoped_paint:unequal_borders` abgewiesen.

Der Renderer wandelt Polygone nur in seinem privaten Eingabedokument in
explizit geschlossene Pfade um, einschliesslich der Konturen aus dem
Verlaufsadapter. Gespeicherte SVGs behalten native Polygone. Offene Polylinien
bleiben offen. Der Fix gilt für beliebige Polygonformen und Zeichenrichtungen.

Bei diesen vollständigen Rand-/Verlaufsverträgen kann die normale Suche eine
native Kreis-/Linien-/Dreieckvorlage als Startgeometrie übernehmen. Die freie
Suche beginnt weiterhin mit einer unabhängigen Population. Verbundene Formen
behalten ihre beschriebenen Endpunkte auch während Parameteränderungen.
Koordinatenverfeinerung, Grössenwechsel und Drehungen ergänzen die vorhandenen
Operatoren. Bereits bestandene Konstruktionen werden während weiterer
Verbesserungen separat behalten. Der Checkpoint speichert auch die lokale
Suchposition; Programm-, Renderer- und Farbkanalversion gehören zur Bindung.

## Gespeichertes Ergebnis und echte Worker

Massgeblicher normaler GUI-Lauf: `0ffaea841a874c668269267e48d42580`, Profil
`quick`, Seed 2027, 1.156 Renderings, 46,1 Sekunden insgesamt. Er bestätigt die
vollständige Beschreibung und speichert die bessere Projektversion über die
reguläre Projektablage. Das SVG liegt unter
`artifacts/converted_images/converted_svgs/AC0204_L.svg`.

| Prüfung am gespeicherten SVG | MuPDF | unabhängiges librsvg |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0,00083742 | 0,00086139 |
| Vordergrundfehler | 0,00229182 | 0,00236277 |
| Vordergrund-IoU | 0,95132743 | 0,95137047 |
| Kantenübereinstimmung | 0,88171160 | 0,88242912 |
| Bildprüfung | bestanden | bestanden |

Die beiden ausgegebenen Dreiecksränder sind exakt 2,45146 Pixel breit. Beide
Dreiecke haben eigene native lineare Grauverläufe. Beide Spitzen und das freie
Griffende besitzen dieselben Koordinaten. Das SVG bleibt innerhalb 65 × 50 Pixeln.
Keine Qualitätsgrenze wurde gelockert.

Der unabhängige freie GUI-Lauf `233211e38b0e442792c66924898a6671`, Profil
`explore5`, Seed 45, besteht ebenfalls nach 301,4 Sekunden einschliesslich
Abschluss. Sein normalisierter Fehler ist 0,00142517, Vordergrund-IoU 0,93668690
und Kantenübereinstimmung 0,80021453. Die bessere reguläre Projektversion bleibt
erhalten. `summary.json` enthält die kompakten Messdaten. Rohdaten, Bilder und
Journale bleiben lokal; `comparison.png` zeigt Original, vorheriges und neues
SVG mit dem unabhängigen Renderer.

## Prüfungen und Grenzen

Die fokussierte Suite besteht mit **160 Tests**: neue Formgruppenverträge,
Vorlagen-/GUI-Berichtsübergabe, RGB-Referenzbindung, echte Seed-Geometriefolgen,
Checkpoints, geschlossene Polygonkanten, offene Polylinien, vorhandene
Gradientenadapter, Grundformenszenen und beide freien GUI-Profile.

Die grössere Untersuchung meldete zusätzlich zehn Fehler der bestehenden
Rundungs-/Antialiasingtests. Alle zehn treten auch mit abgeschalteter neuer
Polygonkorrektur auf. Ein früherer breiter Sprach-/GUI-Vergleich liefert bei
beiden Implementierungen dieselben 22 Fehler in den kontrolliert verglichenen
Fällen; zwei Ventil-GUI-Erwartungen scheitern ebenfalls bereits im Vergleichsstand.
Diese Bestandsprobleme werden hier nicht als behoben angegeben.

Der Parser bleibt begrenzt. Unterstützt sind die dokumentierten vollständigen
Gruppensätze für Kreis, Ellipse, Rechteck, Quadrat und Dreieck. Andere Farben,
Ausnahmen oder beliebige Freitextbeziehungen werden damit nicht automatisch
verstanden. Ein anderer Seed garantiert kein anderes Endergebnis und auch
keinen Erfolg innerhalb jedes Budgets. Frühere erfolglose Versuche bleiben
lokal erhalten. Die neuen Quellen enthalten keine Bildnamen-Sonderbehandlung.

Der laufende Webserver auf Port 8766 wurde nicht unterbrochen: Zum geplanten
Neustart lief bereits wieder eine Katalog-Hintergrundkonvertierung. Der GUI-
Hauptprozess muss nach deren Abschluss neu gestartet werden. Neue Worker laden
die aktuellen Quelldateien bereits; die neue GUI-Fähigkeit heisst
`scoped_primitive_paint`.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_scoped_paint.py tests/test_polygon_renderer_closure.py tests/test_primitive_evolution.py tests/test_gui_preview.py tests/detailtests/test_rendering_gradient_compatibility.py tests/detailtests/test_svg_gradient_references.py tests/test_primitive_scene_runtime.py tests/test_image_converter_gui.py::test_free_search_profiles_reach_cli_with_durable_memory_and_skip_samples tests/test_image_converter_gui.py::test_free_search_rejects_unsupported_claim_before_launch tests/test_image_converter_gui.py::test_free_search_completion_does_not_rescan_every_rendered_attempt -q
.venv/Scripts/python.exe artifacts/evaluation/scoped_paint_2026-11-22/run_gui.py explore5 45
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```
