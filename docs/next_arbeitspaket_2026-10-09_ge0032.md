# Arbeitspaket – Abwärtspfeil und Kreisscheiben mit Querbalken (2026-10-09)

Branch: `codex/ge0032-quality-2026-10-09`, Basis `532d4d581`.
Das nächste dokumentierte Ziel `GE0032` und die drei Größenvarianten bestehen
beide unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.
Alle vier bestehen zusätzlich die strengeren Plan-B-Pixelgrenzen.
Die tatsächlich geprüften SVGs, Manifest, Vergleichsbild und kompakter Nachweis
liegen unter `artifacts/evaluation/disk_bar_recheck_v1/`.

## Unterschiedliche Motive im bisherigen Katalogeintrag

Das Grundbild zeigt einen gefüllten Abwärtspfeil mit zusammenhängendem Schaft
und dreieckiger Spitze. Die drei Größenvarianten zeigen dagegen eine
Kreisscheibe mit vertikalem Verlauf, hellem Rand und mittigem dunklem Querbalken
mit runden Enden und heller Kontur. Sie sind keine Größen-Holdouts des Pfeils.
Beide XML-Kataloge trennen diese Motive jetzt in eigenständige Beschreibungen.
Der bisherige Verweis auf andere Katalogeinträge und relative Drehungen entfällt.
Bildnamen und Dateien bleiben erhalten; die Beschreibungen enthalten keine
numerischen Formparameter. Die explizite Grundform des neuen Größen-Eintrags
verhindert, dass dessen Beschreibung den Grundbild-Eintrag überschreibt.

## Allgemeine Registrierung und Rendering

Die neue Registrierung in `imageCompositeConverterFilledSymbols.py` verwendet
ausschließlich Beschreibung und Raster. Für die Kreisscheibe bestimmt eine
Kreisregression Lage und Radius. Exponierte obere und untere Bereiche liefern
den vertikalen Farbverlauf. Kontrast gegenüber diesem Farbfeld lokalisiert
den Querbalken; Profil und Konturresiduum verlangen runde Enden. Rand- und
Balkenfarben stammen ebenfalls aus den Pixeln. Eine kleine morphologische
Schließung verbindet die durch Antialiasing und Glanzkante geteilte Endkappe.
Zusätzliche Objekte, fehlender Balken, gerade Enden, falsche Orientierung und
verschobene Innenbefunde werden verworfen.

Beim Pfeil liefern Zeilenprofile den geraden Schaft und die breitere Schulter.
Zwei Geradenregressionen bestimmen die zusammenlaufenden Dreieckskanten.
Die Ausgabe ist ein Polygon mit sieben geometrisch begründeten Eckpunkten;
Rasterkonturen werden nicht als SVG-Pfade exportiert.

Eine begrenzte Grob-zu-fein-Suche verfeinert die Parameter mit gerenderter
Pixelevidenz. Sie umfasst höchstens `1 + 16 × Parameterzahl` Renderproben,
also 385 für die Scheibe und 209 für den Pfeil, mit frühem Stagnationsende.
Der Suchverlust ist der quadratische Farbfehler; der Fehlervertrag der
aufrufenden Runtime bleibt die abschließende Annahmeprüfung. Fehlendes Rendering
und nicht endliche Fehler führen zu keiner Annahme. Die Registrierung läuft
vor Sample- und Ersatzpfaden; Dateiumbenennung verändert das SVG nicht.

PyMuPDF stellte zuvor lineare Verläufe in Kreisen schwarz dar. Der vorhandene
private Bézier-Verlaufsadapter unterstützt jetzt auch native Kreise und Ellipsen.
Seine Deckkraftmaske wird direkt aus dem jeweiligen Originalprimitive gerendert;
die analytischen Grenzen dienen ausschließlich zur Verlaufsauswertung.
Die gespeicherten SVGs enthalten weiterhin native Kreise, Rundrechtecke und
Verläufe. Die temporäre Rasterfarbe gehört nur zum privaten Renderer-Dokument.
Horizontale und vertikale Kreis-/Ellipsenverläufe sind auf identische native
Alphamasken und korrekte Farbinterpolation geprüft.

## Frische CLI-Abnahme

Vor jeder Runtime-Änderung wurden vier echte CLI-SVGs mit der Originalbeschreibung
unter neutralen Dateinamen eingefroren. Vorher und nachher laufen mit Seed 0,
`semantic-only`, eigenen Eingabekopien und demselben End-SVG-Messvertrag.
Der Reproduktionsrunner schaltet nur im Vorher-Lauf die neuen Registrierungen
ab. Alle reproduzierten Vorher-SVGs stimmen bytegleich mit dem tatsächlich
vor der Änderung erzeugten Vorlauf überein; der Vorlauf wird nicht ersetzt.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| GE0032 | 13607.773438 | 367.705048 |
| GE0032_L | 6327.752930 | 79.891838 |
| GE0032_M | 6103.882324 | 74.008614 |
| GE0032_S | 6305.712891 | 137.159607 |

**4/4 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression; 4/4 bestehen zusätzlich die strengeren Plan-B-Pixelgrenzen.**
Die unabhängige Semantikprüfung verlangt entweder den zusammenhängenden
Abwärtspfeil oder den vollständig innen liegenden Rundbalken im Verlaufskreis.
Dieselbe Prüfung bewertet beide Seiten. Die allgemeinen Qualitätsgrenzen
und Bewertungsfunktionen bleiben unverändert. Zwei unabhängige Abnahmen
reproduzieren alle acht Vorher-/Nachher-SVGs und Gateentscheidungen und melden
null verbotene Referenz-SVG-Zugriffe. Die vier gelieferten SVG-Hashes stimmen
mit den tatsächlich geprüften CLI-Ausgaben überein.

## Perception-Lerneffekt und Grenzen

Die beiden beschriebenen Topologien sind für die geprüften Fälle
`generalisiert`. Unabhängige synthetische Geometrien variieren Position,
Farbe und Auflösung; sie sind eigenständige Holdouts für den einzelnen Pfeil.
Fehlende/zusätzliche Primitive, falsche Beschreibungen, Richtung und
Anschlussunterbrechung sind geprüft. Perfekte synthetische SVGs kalibrieren
beide Gates auf ideale Pixel-, Kanten-, Masken- und Semantikwerte.

Weitere Pfeilrichtungen, mehr Innenzeichen und andere Füllmodelle sind nicht
Teil dieses Pakets. Im Sample-Pool gibt es keine SVG-Vorlage für diese Familie;
ein Vorlagen-Roundtrip wird deshalb nicht behauptet. `PB-POOL-2026-10-07`
bleibt offen. CLI-Restfehlerwarnungen bleiben sichtbar; die Ergebnisse sind
qualitativ akzeptiert, nicht pixelidentisch zum JPG.

## Reproduktion und Prüfung

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_disk_bar_recheck artifacts/evaluation/disk_bar_recheck_v1/manifest.json --output-dir .tmp/disk-bar-reproduction
.venv/Scripts/python.exe -m tools.evaluate_disk_bar_recheck .tmp/disk-bar-reproduction/manifest.json --output .tmp/disk-bar-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_filled_symbols_runtime.py tests/test_radial_disk_runtime.py tests/test_gradient_arrow_runtime.py tests/test_alarm_bell_runtime.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q -ra
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7;
direktes Rendering ist explizit gewählt. Vollständige lokale Logs, Eingabekopien
und Wiederholungen liegen unter `.tmp/ge0032/`.
**134 fokussierte Tests bestehen**, davon 38 neue Prüfungen. Syntaxprüfung,
CLI-Hilfe und Runtime-ID-Nullprüfung (`0 occurrences`) bestehen.
Die vollständige Suite einschließlich aller drei Heavy-Module besteht mit
**2.380 bestandenen Tests, 0 Fehlern und 29 bestehenden Windows-Skips**,
insgesamt 2.409 Tests in 1.032,49 Sekunden, Exit 0. Die Skips betreffen
POSIX-Shellintegration unter Windows. Nach dem Start dieser Suite wurde die
Initialisierung der hellen Balkenkontur auf Rasterfarben umgestellt; die finale
Version ist durch die anschließenden 134 fokussierten Tests und beide finalen
CLI-Abnahmen abgesichert. Sechs neue Negativ-/Kalibrierprüfungen gehören zu
diesem fokussierten Nachlauf. Die Bestandsschutzbatterie konvertiert 31 Varianten
im dokumentierten `standard`-Kompatibilitätsmodus und meldet null Regressionen;
die separate Paketabnahme läuft in `semantic-only`. JUnit-/Loghashes und die
Testabgrenzung stehen im versionierten JSON-Nachweis.

Der bestehende Template-Transfer-Test protokolliert weiterhin die bereits im
vorherigen Quadratpaket dokumentierte Windows-Diagnose `0xc0000008`. Er besteht
im Gesamtprofil und im separaten Kontrolllauf mit Exit 0. Die Diagnose wird
nicht als behoben bezeichnet; Testname und Kontrollnachweis sind im JSON erfasst.

Der erneuerte Review enthält 1.000 Einträge, davon 993 renderbare Paare.
Alle 48 gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze.
Die vier frisch akzeptierten Fälle sind aus der Rotation ausgeschlossen.
Die nächste reguläre Aufgabe ist **`GE9023_6M`**, gefolgt von `AC0413_1_M`,
`AC0713_1_L`, `AC0721_1_S` und `AC0711_1_M`. Der genaue Review-Aufruf steht
im JSON-Nachweis; die historischen Sammelausgaben bleiben erhalten.
