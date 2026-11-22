# Unterteilte Raute, Parallelstriche und Hintergrund-X

Die gemeldete Beschreibung bleibt in beiden XML-Tabellen unverändert. Der
Fehlversuch `303b495654134d07ac3a89bfb8d2afe1` brach nach zwei Sekunden mit
`description_geometry_ir_no_valid_candidate` ab; kein SVG wurde ausgegeben.

## Ursachen und Korrektur

Das alte Inventar zählte fünf Rauten: den Elternumriss und zusätzlich seine
vier Teilflächen. Das Geometry-IR enthielt lediglich ein Diagonalband und
zwei Zeichen. Die beiden Teilungsachsen, die parallelen Striche einer Achse
und das Hintergrund-X waren damit nicht vollständig konstruierbar.

Die beschriebene Unterteilung erhält jetzt einen gemeinsamen Elternumriss,
zwei Teilungsachsen mit optionalem Parallelstrich, optionale Plus-/Minuszeichen
in einem benannten Feld und zwei optionale Hintergrundbänder. Eine geschlossene
Sprachauswertung erklärt die gesamte Topologie vor jedem Bildzugriff. Die
Klauseln für Zeichen, Parallelstriche und Hintergrund sind kombinierbar; die
Unterteilung unterstützt auch die umgekehrte Satzstellung und „aufgeteilt“.
Unbekannte oder widersprüchliche Zusätze werden nicht von diesem Modell
ignoriert. Die vollständige Beschreibung bleibt die verbindliche Elementliste.

Die Bildmessung initialisiert Umriss, Zeichen und freiliegende Bandabschnitte.
Die Suche passt native Geometrie und Grautöne am jeweiligen Raster an. Die
beiden möglichen Richtungen einer Doppellinie werden anhand der sichtbaren
Achsen priorisiert. Es gibt keine Bildnamen-Abfrage, Referenzvektoren oder
zusätzliche Restlinienrekonstruktion. Vorlagen und auch unvollständige Entwürfe
müssen den Umriss, die an seinen Seiten endenden Teilungsachsen, getrennte
Parallelstriche, Plus/Minus im benannten Feld und die Hintergrundreihenfolge
beibehalten.

Ein echter GUI-Versuch deckte zusätzlich eine allgemeine Randmessungsursache
auf. Konservative PDF-Konturgrenzen vergrössern das Messfenster bei breiten
Linien. Der bisherige gebrochene Rasterzoom liess Pixel an exakt begrenzten
Canvasrändern über die Grenze ragen. Dadurch wurde die ganze Szene minimal
verkleinert und ihr weisses Hintergrundrechteck als zusätzliche Raute gezählt.
Die Messung verwendet bei mindestens einfacher Auflösung jetzt einen ganzzahligen
Zoom. Tatsächlich überstehende Formen werden weiterhin eingepasst; exakt
begrenzte Hintergründe und gerade Bandenden bleiben unverändert. Drei unabhängige
Canvasgrössen sichern diesen Fehler ab. Die GUI-Prüfversion ist 15.

## Ergebnis und Bedienweg

Der finale HTTP-/GUI-Versuch `1e0b8cc77bb04c90ad6ce6e3f4a7fcfb` verwendet die
unveränderte Beschreibung, Seed 2026, Profil `normal` und keine SVG-Vorlage.
Er besteht nach 20,8 Sekunden und speichert regulär
`artifacts/converted_images/converted_svgs/AC0160_M.svg`.
377 Renderkandidaten, eine vollständige Szenenvalidierung und kein Renderfehler
sind protokolliert. Der lokale Server ist mit beiden Korrekturen neu gestartet;
laufende andere Aufträge wurden vorher abgewartet. Die automatische Nachprüfung
des Katalogeintrags meldet ebenfalls `pixel_pass`.
Die vollständige Katalogübersicht wurde anschliessend mit denselben Prüfregeln
und vier unabhängigen Messprozessen neu aufgebaut: 1.786 Einträge, 3.889 neue
Paarprüfungen und sechs wiederverwendete Messungen. Beschreibung und ausgewähltes
Projekt-SVG des gemeldeten Bildes stimmen im fertigen Manifest überein.

| Gespeichertes SVG | MuPDF | unabhängiges librsvg |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0,00007681 | 0,00007894 |
| Vordergrundfehler | 0,00048577 | 0,00050892 |
| Vordergrund-IoU | 0,94682568 | 0,94787699 |
| Kantenübereinstimmung | 0,95846307 | 0,95659596 |
| Bildprüfung | bestanden | bestanden |

Alle Qualitätsgrenzen bleiben unverändert. Das SVG enthält zehn native
Zeichenelemente ohne Rastereinbettung. `comparison.png` zeigt Original und
unabhängiges Rendering nebeneinander; Rohdaten und vollständige Logs bleiben lokal.

## Tests und Grenzen

30 neue Beschreibung-/Geometrietests bestehen, einschliesslich eines echten
GUI-Workers mit neutralem Dateinamen und Projektablage. Unabhängig gezeichnete
Testbilder variieren Seitenverhältnis, Grösse, Grautöne, Parallelstrichrichtung,
Zusatzzeichen und Hintergrund. Fehlende oder falsch angeordnete Elemente werden
auch bei Entwürfen abgewiesen. Drei weitere neue Canvasprüfungen bestehen.

Der gemeinsame finale Lauf ergibt 47 bestandene Tests und einen bereits
vorhandenen Fehler in `test_model_validation_binds_the_bounded_svg_not_the_overflowing_candidate`.
Dieser Fehler und ein Scheduler-Cachetest scheitern auch mit abgeschaltetem
neuen Beschreibungspfad und zurückgenommenem Zoom-Fix im Arbeitsspeicher.

Der breitere Beschreibungs-/Vorlagen-/Formenlauf ergibt 154 bestandene Tests
und 16 Fehler; dieselben 16 Fehler treten mit deaktiviertem neuen
Beschreibungspfad auf. Ein zusätzlicher GUI-/Suchlauf vor der abschliessenden
Randkorrektur ergibt 77
bestandene und 36 fehlgeschlagene Tests, darunter lokale Socketrestriktionen,
veraltete SVG-Strukturerwartungen und weitere hier nicht behobene Modellfehler.
Eine vollständig grüne Gesamtsuite wird ausdrücklich nicht behauptet.
Syntaxprüfung, CLI-Help, Prüfung auf Bild-ID-Sonderfälle und `git diff --check`
für die betroffenen Dateien bestehen. Parallele, fremde Änderungen bleiben
unverändert; die globale Prüfung meldet dort zusätzlich Zeilenendewarnungen.

Die neue Sprache ist weiterhin begrenzt: eine flach gefüllte graue Raute mit
vier gleichen Teilfeldern, optionalen Parallelstrichen, Plus/Minus und einem
hellgrauen Hintergrund-X. Beliebige Freitextbeschreibungen, andere Farben,
unregelmässige Teilungen oder asymmetrische Hintergrundbänder sind damit nicht
allgemein gelöst. Die freie Grundformensuche erhält dadurch keinen neuen
Sprachumfang; die normalen Konvertierungsprofile verwenden diese Anpassung.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_partitioned_rhombus.py tests/test_canvas_containment.py -q
.venv/Scripts/python.exe -m compileall -q src tests
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```
