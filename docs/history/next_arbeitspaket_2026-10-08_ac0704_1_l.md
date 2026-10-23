# Arbeitspaket – Quadrat mit rechtem Griff (2026-10-08)

Branch: `codex/ac0704-quality-2026-10-08`, Basis `75fd9dfeb`.
Das nach der Alarmglocke dokumentierte reguläre Paket `AC0704_1_L` ist
umgesetzt. Die Abnahme umfasst alle sechs roten und hellgrauen L-/M-/S-Raster.
Qualitätsgrenzen, CLI-Budget und SVG-Zugriffsschutz bleiben unverändert.
`PB-POOL-2026-10-07` bleibt offen.

## Beschreibung und katalogfreie Registrierung

Beide XML-Dateien beschreiben das Quadrat links und den geraden, mittig an der
rechten Seite anschließenden waagerechten Griff eigenständig. Der bisherige
Verweis auf eine andere Katalogbeschreibung entfällt. Farbe, Lage, Größe und
Linienbreite werden ausschließlich aus dem jeweiligen Raster ermittelt.

Für die unbeschriftete Rechtsorientierung fehlte bisher ein Geometry-IR-Pfad.
Die neue Topologie dreht die vorhandene aufrechte Quadrat-/Griff-Struktur; sie
verarbeitet die absolute Beschreibung und das bisherige relative
Rotationsvokabular. Beschriftete oder widersprüchliche Beschreibungen wählen
diesen unbeschrifteten Pfad nicht. Die Semantic- und Runtime-Kind-Sets kennen
die Topologie, sodass Kreisbadge-Regeln sie nicht überschreiben.

Die Registrierung schätzt die Quadratgrenzen aus Zeilen-/Spaltenprofilen und
prüft den zusammenhängenden, zentrierten Griff außerhalb des Quadrats. Ein
gleichmäßiges Innenfeld liefert die Füllfarbe; Rand und Griff liefern eigene
Farben. Fehlender Griff, zusätzliche isolierte Objekte und kontrastreiche
Innenmarkierungen werden verworfen. Eine begrenzte Render-/Fehlersuche
verfeinert Maße, Konturen und Farben. Gekoppelte Änderungen von Quadratgrenzen
und Randbreite verhindern ein um einen Pixel versetztes lokales Minimum bei
doppelter Auflösung. Höchstens 433 Renderproben plus eine Ausgangsmessung sind
möglich. Die Ausgabe enthält nur ein natives Rechteck und einen Linienpfad
mit zwei Pfadbefehlen; keine Rastereinbettung oder geladene Vorlage.

Der neue Rasterpfad liegt vor dem allgemeinen gerahmten Panel-Ersatzpfad.
Dieser hatte die kleinste hellgraue Variante als panelartige Fläche behandelt
und dabei den beschriebenen Griff vollständig verloren.

## Frische echte CLI-Abnahme

Vor Runtime-Änderungen wurde der Vorlauf mit ursprünglicher Beschreibung und
neutralen Dateinamen eingefroren. Der Runner reproduziert ihn mit deaktiviertem
neuen Topologie-Builder. Beide Seiten verwenden Seed 0, `semantic-only`,
getrennte frische Eingabekopien und denselben abschließenden Renderer.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| AC0704_1_L | 14490.255859 | 79.031998 |
| AC0704_1_M | 15347.247070 | 134.751434 |
| AC0704_1_S | 33807.996094 | 278.970673 |
| AC0704_L | 5316.888184 | 11.824000 |
| AC0704_M | 4271.785645 | 19.534286 |
| AC0704_S | 4486.983887 | 89.031998 |

**6/6 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression.** Alle sechs bestehen zusätzlich die strengeren
Plan-B-Pixel-/Konturgrenzen. Zwei unabhängige CLI-Läufe reproduzieren alle
zwölf Vorher-/Nachher-SVGs, Qualitätsmetriken und Gateentscheidungen. Die sechs
ursprünglichen Baseline-SVGs bleiben bytegleich. Beide Abnahmen haben null
verbotene SVG-Zugriffe. Bestehende CLI-Restfehlerwarnungen bleiben sichtbar;
der historische Batch-Erfolgsstatus ersetzt die unabhängige Abnahme nicht.

Die synthetischen Holdouts verwenden eigenständig formulierte SVG-Geometrie
und verändern Farbe, Lage und Auflösung. Ein Runtime-Test erzwingt den Vorrang
vor Panel- und Sample-Pfaden und prüft identische Ausgabe bei Umbenennung.
Zusätzliche Tests prüfen fehlende/zusätzliche Evidenz, widersprüchliche
Beschreibungen, nicht endliche Fehlerfunktionen und frische Runner-Verzeichnisse.
Der Perception-Lerneffekt ist für diese unbeschriftete Topologie
`generalisiert`; Beschriftungen, andere Griffausrichtungen und Verlaufsfüllungen
sind nicht Teil dieses Nachweises. Für dieses Paket existiert keine SVG-Vorlage;
es wird kein 16-Varianten-SVG-Roundtrip behauptet.

## Nachweise und Reproduktion

Versioniert sind Eingabemanifest und kompakter JSON-Nachweis unter
`artifacts/evaluation/right_stem_square_recheck_v1/`. Vollständige SVGs,
Eingabekopien, Logs und Reviewtabellen bleiben lokal unter `.tmp/ac0704/`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_right_stem_square_recheck artifacts/evaluation/right_stem_square_recheck_v1/manifest.json --output-dir .tmp/square-reproduction
.venv/Scripts/python.exe -m tools.evaluate_right_stem_square_recheck .tmp/square-reproduction/manifest.json --output .tmp/square-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_right_stem_square_runtime.py tests/test_diagonal_square_kelle_runtime.py tests/test_rotated_square_kelle_runtime.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
$env:TEMP = "$PWD/.tmp/square-test-temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pytest -q -ra --basetemp=.tmp/square-pytest
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Direktes Rendering ist ausdrücklich gewählt; ein vollständiger zusätzlicher
Lauf mit automatischer Prozessisolation wird hier nicht belegt. Die Abnahmen
liegen unter `.tmp/ac0704/acceptance03` und `acceptance04`, der originale
Vorlauf unter `.tmp/ac0704/baseline`.

## Testabschluss und Rotation

Alle 24 neuen Prüfungen sowie 20 bestehende Quadrat-/Griff-Prüfungen bestehen.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung (`0 occurrences`) und
Diff-Whitespace-Prüfung bestehen. Die vollständige Suite einschließlich aller
drei Heavy-Module und der Satisfactory-Bestandsschutzbatterie besteht:
**2.261 bestanden, 0 fehlgeschlagen, 29 übersprungen**, insgesamt 2.290 Tests
in 788,86 Sekunden mit Exit 0. Die Skips betreffen POSIX-Shelltests unter
Windows. Die frische Bestandsschutzbatterie prüft 31 Baseline-Varianten ohne
Qualitätsregression; der Review bewertet zusätzlich 48 gespeicherte Erfolge.
Testzahlen sowie Protokoll-/JUnit-Hashes stehen im kompakten JSON-Nachweis.
Vollständige lokale Protokolle: `.tmp/ac0704/completion.log` und `completion.xml`.

Der unveränderte Template-Transfer-Test protokolliert eine native Windows-
Diagnose (`0xc0000008`), besteht aber auch im isolierten Kontrolllauf mit
Exit 0. Testname und Kontrollprotokoll-Hash stehen unter
`native_windows_diagnostic` im Nachweis. Die Diagnose führt zu keinem
Pytest-Fehler; sie wird durch diesen Paketabschluss nicht als behoben bezeichnet.

Der erneuerte Review enthält 956 Einträge, davon 950 renderbare Paare. Alle 48
gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze. Die sechs neuen
Rasterpässe sowie früher separat belegte Pässe sind aus der Auswahl ausgeschlossen.
Historische Sammel-SVGs werden durch die frischen CLI-Läufe nicht überschrieben.
Der genaue Review-Aufruf steht unter `review.reproduction_arguments` im JSON.

Die nächste reguläre Rotation beginnt mit **`AC0402_1_S`**, gefolgt von
`AC0403_1_L`, `GE0032`, `AC0413_1_M` und `AC0713_1_L`.
Vor Änderungen ist wieder eine frische CLI-Baseline erforderlich.
