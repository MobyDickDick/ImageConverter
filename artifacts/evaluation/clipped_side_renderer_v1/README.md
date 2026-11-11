# Dünne Rechteckseiten: Renderer- und Registrierungsabnahme

SVG-CLIPPED-SIDE-RENDERER-01, synthetischer Teilumfang vom 11.11.2026
abgeschlossen. Die unabhängige reale Gesamtabnahme bleibt offen.

## Ergebnisse

| Unveränderte Eingaben | Vorher | Nachher, beide Renderer / alle lokalen Gates |
| --- | ---: | ---: |
| Vor Änderung eingefrorene Renderer-Kontrollen | 21/26 | 26/26 |
| Echte CLI, Hauptseed 718293 | 12/12 | 12/12 |
| Echte CLI, separater Zusatzseed 391827 | 10/12 | 12/12 |
| Echte CLI, gekoppelte Varianten 718293 | 17/17 | 17/17 |

Alle 41 CLI-Ausgaben bestehen native Objekt-/Relations-, globale,
objektlokale, Restbild-, 164 sichtbare Eck- und 131 sichtbare Seitengates
je Renderer. Maximale überwachte Prozesszeit lokal 4,047 Sekunden;
maximaler nativer Boxfehler 0,6416 Pixel. Die Grenzen bleiben fünf Sekunden,
96 Strukturzustände, MSE 0,01, Vordergrund-MSE 0,04, IoU 0,85,
Kantenübereinstimmung 0,72, Boxfehler 2,5 Pixel, Radiusfehler 1,25 Pixel und
Konturbreitenfehler 0,85 Pixel. Die anfängliche Pixelerrorgrenze gilt weiter.

Die gemeinsame Szenen-/Renderer-/Registrierungs-/Budgetregression besteht
**398/398** Tests in 220,33 Sekunden; das separate Kernprofil **42/42**.
Alle Befehle haben Exit 0, keine Fehler oder Überspringungen.
Der vorherige gezielte Lauf bestand 63/63; die nachfolgend ergänzte
ViewBox-/Transformationsgegenprobe ist im endgültigen 398er-Lauf enthalten.
Python 3.10.11, PyMuPDF 1.26.7, OpenCV 4.14.0, librsvg 2.62.3 / cairo 1.18.4.
Der GitHub-CI-Job ist erweitert, wurde hier aber nicht gestartet.

## Ursachen und getrennte Korrekturen

Der exakte scharfe Referenzfall `clipped_rectangle_10` bestand schon vorher
die native und globale Abnahme. Zwei Seiten verfehlten ausschließlich im
internen Renderer das lokale Kantengate: 0,692406 und 0,476888. Die gespeicherten
Originalprofile zeigen kleine Deckungs- und Farbquantisierungsabweichungen,
die die tatsächliche Canny-Maximumposition um ein Pixel verschieben. Gleiche
Kantenpixelzahlen sind deshalb kein Gleichheitsnachweis.

Der private Adapter integriert scharfe Rechteckflächen und ihre zentrierte
Kontur an den Originalpixeln; vormultiplizierte 8-Bit-Quellen werden getrennt
überlagert. Danach bestehen diese Seiten mit 1,0 und 0,933220. Native
Ausgabegeometrie und Vektorprimitive bleiben erhalten. Es gibt keine
Verwendung von Generatorparametern oder Referenz-SVGs im Konverter.

Der separate gerundete Fall `clipped_rectangle_02` hatte bereits vorher
korrekte exakte Referenzraster mit beiden Renderern. Eine einzelne veränderte
Elternseite verändert auch das Verlaufsfeld: Lokale Kanten konnten bestehen,
während der globale Ausgangsfehler schlechter wurde. Kleine gemeinsame
Verschiebungen und symmetrische Größenänderungen gegenüberliegender Grenzen
beheben diese Registrierungsgrenze unter derselben Fehlergrenze und Deadline.
Bereits vollständig geprüfte Startmodelle werden vor alternativen Startwerten
abgenommen; dadurch bleibt auch der zwischenzeitlich wieder abgelehnte
Zusatzfall 08 im vollständigen Nenner erfolgreich.

Die zusätzliche Kontrolle umfasst zwei historische unveränderte SVG/PNG-Paare
und 24 vor Änderung eingefrorene Seitenkontrollen mit Subpixellagen,
Konturbreiten 1/1,5/3 und beiden Verlaufsachsen. Analytische Deckungsprüfungen,
ViewBox/Transformationen, vollständig sichtbare scharfe/gerundete Eltern,
angeschnittene Kreise, Konturfarben, Tiefenbelege und negative Beobachtbarkeit
sind Teil der Regression. Hysterese und Qualitätsgrenzen wurden nicht geändert.

## Nachweise und Grenzen

`summary.json` enthält alle endgültigen CLI-Fälle mit Eingabe-, Referenz-,
Beschreibungs- und Ausgabehashes, Objekt-/Relationsorakeln und allen lokalen
Messwerten beider Renderer. Die Renderer-Gegenprobe verwendet zusätzlich den
unveränderten Renderingquelltext des Ausgangscommits `e3c40eb1e` auf denselben
eingefrorenen Pixeln. Für die zwei ursprünglichen Problemfälle sind vollständige
BGR-Seitenprofile und tatsächliche Canny-Positionen vor/nach enthalten.
Alle weiteren Kontrollen bleiben mit Metriken und Prüfsummen nachprüfbar.
`checks.json` sichert Befehle, Exitcodes, Testresultate und Bericht-/Runtimehashes.
Rohberichte, Diagnoseprogramme und CLI-Bäume bleiben unter `.tmp/clipped-side/`.

Die historischen 10/12 aus dem Vorgängerpaket werden nicht überschrieben.
Zwei Entwicklungszwischenstände (10/12 und 11/12) bleiben mit Berichtshashes
gesondert ausgewiesen. Jeder endgültige Versuch bleibt im Nenner. Es gibt
keine neue reale Familienabnahme, keine Archiv-Neukonvertierung und keinen
Kataloggewinn. HC0010 und Rail bleiben nach schreibfreier Nachprüfung
`sealed_unrun`, ohne Konvertierung und ohne positive Abnahme.

## Reproduktion

```powershell
.venv/Scripts/python.exe -m tools.evaluate_clipped_side_renderer --controls tests/fixtures/clipped_side_renderer --report .tmp/clipped-side-replay.json --require-all
.venv/Scripts/python.exe -m pytest tests/detailtests/test_clipped_side_renderer.py tests/test_clipped_rectangular_parent.py -q
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --prepare .tmp/clipped-side-extra-new --seed 391827
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-side-extra-new --output .tmp/clipped-side-extra-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-side-extra-new --output .tmp/clipped-side-extra-cli-new --audit .tmp/clipped-side-extra-audit-new.json --require-all
```

Für die Hauptkohorte Seed 718293 und für die gekoppelte Kohorte zusätzlich
`--variations` verwenden. Bestehende Eingaben bleiben unangetastet; die
Vorbereitung lehnt bestehende Zielordner ab.
