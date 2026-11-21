# Quadratischer Motor am Zweiwegventil

Die unveränderte Beschreibung von `AC0201_S_sia.jpg` fiel durch den bisherigen
geschlossenen Ventilvertrag: Dieser akzeptierte ausschliesslich den runden
Motor als Kelle. Die allgemeine Geometry-IR-Auswertung interpretierte einzelne
Wörter anschliessend als Verlaufspanel mit Rechteckrand und einer Diagonale.
Griff und Ventilflächen fehlten. Die Inventarprüfung verlangte ein Quadrat und
verwarf deshalb alle neun Startkonstruktionen vor dem Rendern. Der gemeldete
Abbruchgrund `parameter_stagnation` war dabei irreführend.

Die bestehende Ventilauswertung erklärt jetzt abhängig vom beschriebenen Motor
entweder Kreis und Griff oder Quadrat, zwei Diagonalen und Griff; beide Varianten
besitzen zwei an einer gemeinsamen Spitze verbundene Ventildreiecke mit einem
gemeinsamen Verlauf. Dieselbe numerische Suche passt Position, Grösse und Farben
am Original an. Ein gemeinsamer Seitenparameter erhält das exakte Quadrat.
Die dauerhafte Prüfung sichert Diagonalen, gemeinsame Rand-/Diagonalfarbe,
Motoranschluss und gemeinsamen Verlauf auch bei späteren Vorlagenänderungen.

Ein neuer Abbruchgrund `no_valid_candidate` unterscheidet in der allgemeinen
Beschreibungssuche das vollständige Verwerfen der Kandidaten von wirklicher
Parameterstagnation. Die Inventarprüfung bleibt verbindlich.

## Nachweis

Der GUI-Worker verwirft die alte Kompressorvorlage und erstellt aus der
unveränderten Beschreibung ein bestandenes SVG. Beide XML-Beschreibungstabellen
bleiben byteidentisch. Das Ergebnis wird regulär unter
`artifacts/converted_images/converted_svgs/AC0201_S_sia.svg` gespeichert;
vorherige Versionen werden durch die Projektablage gesichert.

Der erste vollständige Lauf benötigt 9,9 Sekunden und 399 Renderauswertungen.
Sein normalisierter Pixelfehler beträgt 0,00066711, die Vordergrund-IoU 0,98024
und die Kantenübereinstimmung 0,88974. Die unabhängige erneute Prüfung des
gespeicherten SVGs besteht ebenfalls, einschliesslich der ursprünglichen
20 × 25 Pixel grossen Zeichengrenzen.

Der untätige lokale Webserver auf Port 8766 wurde neu gestartet. Ein erneuter
Start des zuvor fehlgeschlagenen Auftrags über die HTTP-Schnittstelle besteht
mit unveränderter Beschreibung in 7,5 Sekunden bei 399 Renderauswertungen.
Die unabhängig gespeicherte Projektversion wird als gleich gut beibehalten.
`summary.json` enthält die kompakten Worker-, HTTP- und Qualitätsnachweise.

149 Tests bestehen: beide Motortypen, neutrale Dateinamen im echten GUI-Worker,
unabhängige synthetische Geometrien in zwei Grössen mit anderen Farben,
fehlende oder falsche Diagonalen, gestrecktes Quadrat, fehlerhafter Griff,
getrennter Verlauf, zusätzliche widersprüchliche Aussagen sowie die bestehenden
Sprach-, Vorlagen-, Grundformen-, Canvas- und Beschreibungssuchtests.
Die ergänzte Prüfung des Abbruchgrundes besteht auch separat.
Die Prüfung gegen neue Bild-ID-Sonderfälle und `git diff --check` bestehen.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_two_way_valve_description.py tests/test_description_language.py tests/test_sample_start_regression.py tests/test_simple_form_representation.py tests/test_canvas_containment.py tests/test_description_registration_search.py -q
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```

## Grenzen

Die Erweiterung verwendet denselben begrenzten Beschreibungsvertrag wie der
bisherige Ventilpfad und ist keine allgemeine Lösung für freie Sprache. Die
Quadratvariante verlangt die unterstützte Aussage über beide dunkelgrauen
Diagonalen und den gleichfarbigen Rand. Zusätzliche unerkannte Aussagen werden
nicht stillschweigend akzeptiert. Andere Motorpositionen und Ventilorientierungen
sind durch diese Änderung nicht allgemein abgedeckt. Produktionscode enthält
keine Bild-ID, Referenz-SVGs oder zusätzliche Rasterrekonstruktion.
