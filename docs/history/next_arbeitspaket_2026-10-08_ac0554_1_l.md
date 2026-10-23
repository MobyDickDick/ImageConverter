# Arbeitspaket – Dachlinie im Verlaufsfeld und CI-Ventilfall (2026-10-08)

Branch: `codex/ac0554-quality-2026-10-08`, Basis `6751c2e7e`.
Das nächste reguläre Paket `AC0554_1_L` und der anschließend vom Nutzer
benannte CI-Ausfall `AC0223_L_sia` sind umgesetzt. Die Qualitätsgrenzen,
Iterationsbudgets und der SVG-Zugriffsschutz bleiben unverändert.

## Dachlinie: Ursache und allgemeine Korrektur

Die XML verwies auf andere Katalogeinträge und beschrieb einen Kreis mit Griff.
Die neun Bilder zeigen stattdessen ein gerahmtes Verlaufsrechteck mit zwei
geraden Schenkeln, die oben eine offene Spitze bilden. Die Beschreibung nennt
jetzt diese sichtbare Topologie eigenständig, ohne feste Farben oder Maße.

Die neue Rasterregistrierung bestimmt Feldgrenzen, Rahmen, beide Schenkel,
Schnittpunkt, Strichstärke und Farben aus den Pixeln. Eine begrenzte
Render-/Fehlersuche verfeinert diese Schätzungen. Das gespeicherte SVG enthält
ein Rechteck mit nativem vertikalem Verlauf und eine offene Polyline; keine
Rasterkopie und keine referenzierte Kataloggeometrie. Fehlende Markierung,
umgekehrte Spitze, zusätzliche Objekte und widersprüchliche Beschreibungen
werden verworfen. Tests prüfen andere Farben, Lage, doppelte Auflösung und
identische Ausgaben unter unterschiedlichen neutralen Dateinamen.

Der private PyMuPDF-Verlaufsadapter erzeugte durch antialiasierte Teilflächen
helle Nähte. Ein deckender Untergrund und begrenzt überlappende Streifen
beseitigen diese Nähte im Renderer. Die gespeicherten SVGs behalten ihre
nativen Verläufe. Tests vergleichen konstante Farben mit den exakten RGB-Werten,
prüfen unveränderte Außenkanten und einen analytischen kontinuierlichen Verlauf.
Die vorhandene Punkt-/Klappenregistrierung gewichtet ihre Überlappungsstrafe
nun relativ zur belegten Region, damit schwache, kleine Strukturen erhalten
bleiben. Alle sieben einschlägigen Punktregressionen bestehen.

## Abnahme: neun echte CLI-Fälle

Alle Eingaben tragen neutrale Namen und laufen mit Seed 0 im Modus
`semantic-only`. Der Vorlauf verwendet die ursprüngliche XML-Beschreibung,
der Nachlauf die eigenständige Beschreibung mit Rasterregistrierung. Beide
verwenden dieselbe übrige Runtime und den korrigierten Renderer. Beide Seiten
erhalten getrennte Eingabekopien: Das Archivieren einer fehlgeschlagenen
Vorlaufdatei darf keinen Nachlauffall entfernen. Ein Regressionstest sichert
diesen Fehlerpfad ab.

| Variante | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| AC0554_1_L | 45532.085938 | 110.979378 |
| AC0554_1_M | 44963.089844 | 199.141113 |
| AC0554_1_S | 44104.070312 | 421.473755 |
| AC0554_2_L | 35629.445312 | 89.789375 |
| AC0554_2_M | 35881.671875 | 142.702774 |
| AC0554_2_S | 34691.703125 | 277.623749 |
| AC0554_L | 9950.183594 | 253.077194 |
| AC0554_M | 9699.209961 | 30.541666 |
| AC0554_S | 13273.793945 | 76.118752 |

**9/9 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression.** Zwei unabhängige CLI-Läufe reproduzieren alle 18
Vorher-/Nachher-SVGs und sämtliche Gateentscheidungen exakt. Die bestehenden
CLI-Restfehlerwarnungen bleiben sichtbar; der historische Batch-Erfolgsstatus
ersetzt die unabhängige Qualitätsabnahme nicht.

## Unveränderter CI-Fall: 0/16 → 16/16

Der [CI-Job vom 7. Oktober](https://github.com/MobyDickDick/ImageConverter/actions/runs/37680964416/job/112996576222)
wählte `AC0223_L_sia.svg` mit Seed `5321758631963497707` und bestand 0/16.
Der originale CI-Bericht wurde heruntergeladen. Der lokale Vorlauf reproduziert
alle vier Fehlerklassen: RGB-Fehler, Vordergrundfehler, Konturen und Überlappung.
Die Quell-/Beschreibungshashes sowie sämtliche 16 Raster- und Referenzhashes
stimmen mit dem CI-Bericht überein.

Der bisherige Ersatzpfad zeichnete die beschriebenen drei Ventilflügel,
Verbindung und den quadratischen Antrieb nicht ausreichend nach. Die neue
Registrierung erkennt drei Dreiecke mit gemeinsamer Spitze, eine senkrechte
Verbindung und ein helles Quadrat mit zwei Diagonalen aus dem Raster. Separate
Beobachtungsprüfungen sichern Flügel, lichte Quadratflächen, beide Diagonalen
und die durchgehende Verbindung. Die begrenzte Fehlersuche verändert nur die
Parameter dieser sieben nativen Vektorelemente. Der echte automatische
CLI-Ersatzpfad ruft die Registrierung vor der allgemeinen Ersatzgeometrie auf.

**Derselbe Seed besteht jetzt 16/16.** Ein zweiter unabhängiger Lauf erzeugt
dieselben 16 SVG-Bytes und Metriken. Ein weiterer Seed `20261008` besteht
ebenfalls 16/16. Alle Läufe haben null verbotene SVG-Zugriffe und enthalten
keine eingebetteten Rasterbilder. Kein Motiv wurde gegen ein leichteres
ausgetauscht; keine Grenze wurde gelockert.

Eine Grenze dieses Nachweises bleibt sichtbar: Der bestehende Referenzrenderer
stellt Polygonverläufe dieses SVGs schwarz dar. Die eingefrorenen CI-Raster
wurden ausdrücklich beibehalten. Die Registrierung übernimmt die beobachteten
Flügelfarben als flächige Füllungen; diese Abnahme belegt keine Rückgewinnung
der ursprünglichen Flügelverläufe oder vollständige sprachliche Semantik.
Andere Ventilorientierungen, runde Antriebe und beschriftete Antriebe gehören
nicht zu dieser Abnahme. Der Gesamtpool-Nachweis `PB-POOL-2026-10-07` bleibt offen.

## Nachweise und Reproduktion

Versioniert werden nur das Eingabemanifest und kompakte JSON-Nachweise:

- `artifacts/evaluation/chevron_panel_recheck_v1/manifest.json`
- `artifacts/evaluation/chevron_panel_recheck_v1/summary_2026-10-08.json`
- `artifacts/evaluation/three_way_valve_recheck_v1/summary_2026-10-08.json`

Vollständige SVGs, Raster, Logs, CI-Download und Reviewtabellen bleiben lokal
unter `.tmp/`. Die Nachweise enthalten Quell-/Eingabe-/SVG-Hashes, Metriken,
Gateentscheidungen und die eingefrorene CI-Beschreibung. Reproduzierbare Aufrufe:

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_chevron_panel_recheck artifacts/evaluation/chevron_panel_recheck_v1/manifest.json --output-dir .tmp/roof-reproduction
.venv/Scripts/python.exe -m tools.evaluate_chevron_panel_recheck .tmp/roof-reproduction/manifest.json --output .tmp/roof-gates.json
.venv/Scripts/python.exe -c "import json; from pathlib import Path; r=json.loads(Path('artifacts/evaluation/three_way_valve_recheck_v1/summary_2026-10-08.json').read_text(encoding='utf-8')); Path('.tmp/valve-description.txt').write_text(r['source_description'],encoding='utf-8')"
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/images_to_convert/samples/AC0223_L_sia.svg --description-file .tmp/valve-description.txt --seed 5321758631963497707 --output-dir .tmp/valve-reproduction
.venv/Scripts/python.exe -m pytest -q tests/test_chevron_panel_runtime.py tests/test_three_way_valve_runtime.py tests/detailtests/test_rendering_gradient_compatibility.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q -ra
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Der Abschluss verwendet ausdrücklich direktes SVG-Rendering.

## Testabschluss und Rotation

Die vollständige Suite einschließlich aller drei normalerweise ausgeblendeten
Heavy-Module besteht: **2.156 bestanden, 0 fehlgeschlagen, 29 übersprungen**
bei insgesamt 2.185 Tests in 638,48 Sekunden. Die 29 Skips betreffen ausschließlich
POSIX-Shelltests unter Windows. Die Qualitätsbatterie für die gespeicherten
zufriedenstellenden Konvertierungen besteht ebenfalls. Syntaxprüfung,
CLI-Hilfe und Runtime-ID-Nullprüfung sind grün (`0 occurrences`).
Das Profil verwendet direktes Rendering; die automatische Prozessisolation
wurde nicht zusätzlich in einem vollständigen Lauf geprüft. Einzelresultate
stehen lokal in `.tmp/ac0554-valve-full-final.xml`, das vollständige Protokoll
in `.tmp/ac0554-valve-full-final.log`. Die kompakten JSON-Nachweise bewahren
Testzahlen und Laufzeit; die umfangreichen Logs werden nicht eingecheckt.

Der frische Review enthält 956 Einträge, davon 950 renderbare Paare. Alle 48
gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze. Bereits separat
belegte Pässe und die neun neuen Dachvarianten werden aus der Kandidatenauswahl
ausgeschlossen. Die zentral gespeicherten Sammel-SVGs bleiben historische
Artefakte; die frischen CLI-Ausgaben liegen in den obigen Abnahmeläufen.
Die nächste reguläre Rotation beginnt mit `DLG0031`, gefolgt von `DLG0021`,
`AC0130_S`, `GE1420_S` und `AC0704_1_L`. Vor Änderungen ist wieder eine frische
CLI-Baseline erforderlich. Der genaue Reviewaufruf steht im kompakten Nachweis.
