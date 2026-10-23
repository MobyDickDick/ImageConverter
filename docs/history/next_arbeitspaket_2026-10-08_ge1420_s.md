# Arbeitspaket – Alarmglocke und Schallbögen (2026-10-08)

Branch: `codex/ge1420-quality-2026-10-08`, Basis `7ddd60b21`.
Das nach dem Luftbefeuchter dokumentierte reguläre Paket `GE1420_S` ist
umgesetzt. Die unabhängige Abnahme umfasst zusätzlich M, L und die neutrale
Konturvariante. Qualitätsgrenzen, CLI-Budget und SVG-Zugriffsschutz bleiben
unverändert. `PB-POOL-2026-10-07` bleibt offen.

## Beschreibung und Rasterregistrierung

Die bisherige gemeinsame XML nannte drei Schallwellen je Seite. Die Raster
zeigen zwei voneinander getrennte Bögen je Seite. Beide XML-Dateien beschreiben
nun eigenständig den gewölbten Glockenkörper, geschwungene Seiten, ovalen unteren
Rand und hellen Klöppel links im unteren Innenbereich. Die neutrale Variante
bekommt eine eigene ungefüllte Beschreibung. Farben und Maße werden nicht aus
einer Katalogvorlage übernommen.

Die allgemeine Registrierung schätzt den Körper aus Zeilenprofilen, den unteren
Rand aus seiner größten horizontalen Ausdehnung und den Klöppel aus dem hellen
Kontrast im unteren Innenbereich. Zwei radiale Signalgruppen trennen die
Schallbögen; pro Seite und Bogen wird eine quadratische Kurve regressiert.
Begrenzte Render-/Fehlersuche verfeinert Lage, Rundung, Linienbreiten und Farben.
Der neutrale Pfad berücksichtigt zusätzlich die Vordergrunddeckung. Höchstens
1.746 Renderprüfungen sind möglich; die farbigen Fälle benötigen höchstens 470.

Die Runtime erhält ausschließlich Beschreibung und Raster. Der neue Pfad liegt
vor den bisherigen Ersatzpfaden. Die Beschreibungsprüfung erkennt die Glocke
als Geometriebegriff und leitet die vollständige Beschreibung automatisch
weiter. Die SVG-Ausgabe enthält sieben native Vektorelemente mit 15 Pfadbefehlen:
Glockenkörper, ovalen Rand, Klöppel und vier Schallbögen. Sie enthält keine
Rastereinbettung. Ablationsprüfungen verlangen eigene Bildevidenz für jeden
Bogen und den Klöppel; zusätzliche isolierte Objekte werden verworfen.

## Allgemeiner Bézier-Verlaufsadapter

PyMuPDF stellt den nativen Farbverlauf im geschlossenen Glockenpfad schwarz dar.
Der private Adapter für geschlossene absolute `M/L/C/Q/Z`-Konturen schätzt die
Verlaufsgrenzen durch adaptive Kurvenunterteilung. Die tatsächliche Füllmaske
wird dagegen aus dem nativen Pfad in der angeforderten Ausgabeauflösung
gerendert. Eine temporäre Farb-/Alpha-Ebene trägt den berechneten Verlauf in
das private Renderdokument ein; die native Kontur bleibt erhalten. Dadurch
werden antialiasierte Außenkanten nicht mehrfach durch überlappende Farbstreifen
abgedunkelt. **Das gespeicherte SVG behält Bézierkurven und nativen Verlauf.**

Unabhängige Prüfungen vergleichen einen konstanten Verlauf mit der passenden
flächigen Bézierfüllung in einfacher und doppelter Auflösung und prüfen einen
analytischen vertikalen Verlauf. Offene oder zusammengesetzte Pfade, andere
Pfadbefehle, Transformationen, Transparenz, nicht achsparallele Verläufe und
abweichende Viewport-Abbildungen werden durch diesen Adapter nicht erweitert.
Die vorhandenen Rechteck-, Polygon- und Radialadapter bleiben unverändert.

## Frische echte CLI-Abnahme

Der Vorlauf wurde vor den Runtime-Änderungen mit der ursprünglichen XML unter
neutralen Dateinamen eingefroren. Der Runner reproduziert ihn mit deaktivierter
Glockenregistrierung. Beide Seiten verwenden Seed 0 und `semantic-only`, eigene
Eingabekopien sowie den gleichen abschließenden Renderer.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| GE1420_S | 10032.782227 | 559.539978 |
| GE1420_M | 11103.889648 | 743.713623 |
| GE1420_L | 11656.105469 | 1274.206665 |
| GE1420_M_neutral | 5600.411133 | 1709.550415 |

**4/4 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression.** Zwei unabhängige CLI-Läufe reproduzieren alle acht
SVG-Bytes, Qualitätsmetriken und Gateentscheidungen. Die ursprünglichen vier
Baseline-SVGs bleiben bytegleich. Beide Abnahmen haben null verbotene
SVG-Zugriffe. Bestehende CLI-Restfehlerwarnungen bleiben sichtbar; der historische
Batch-Erfolgsstatus ersetzt die unabhängige Abnahme nicht.

Die farbigen S-/M-/L-Ausgaben bestehen zusätzlich die strengeren Plan-B-
Pixel-/Konturgrenzen. Die neutrale Ausgabe verfehlt dort die separate
Vordergrund-IoU-Grenze (`0.683673 < 0.85`), obwohl sie beide regulären Gates
besteht. Dieser engere Nachweis bleibt offen. Für dieses Paket wurde keine
SVG-Vorlage bereitgestellt; es wird kein 16-Varianten-SVG-Roundtrip behauptet.
Synthetische Holdouts verwenden unabhängig formulierte Kurven und verändern
Farbe, Lage und Auflösung. Fehlende Bögen, fehlender Klöppel, Zusatzobjekte,
widersprüchliche Beschreibungen und ungültige Fehlerfunktionen werden geprüft.

## Nachweise und Reproduktion

Versioniert sind Eingabemanifest und kompakter JSON-Nachweis unter
`artifacts/evaluation/alarm_bell_recheck_v1/`. Die vollständigen SVGs, Raster,
Logs und Reviewtabellen bleiben lokal unter `.tmp/ge1420/`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_alarm_bell_recheck artifacts/evaluation/alarm_bell_recheck_v1/manifest.json --output-dir .tmp/bell-reproduction
.venv/Scripts/python.exe -m tools.evaluate_alarm_bell_recheck .tmp/bell-reproduction/manifest.json --output .tmp/bell-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_alarm_bell_runtime.py tests/detailtests/test_rendering_gradient_compatibility.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
$env:TEMP = "$PWD/.tmp/bell-test-temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pytest -q -ra --basetemp=.tmp/bell-pytest
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Direktes Rendering ist ausdrücklich gewählt; ein vollständiger zusätzlicher
Lauf mit automatischer Prozessisolation wird durch diesen Abschluss nicht
belegt. Die Abnahmeläufe liegen unter `.tmp/ge1420/acceptance03` und
`acceptance04`, der originale Vorlauf unter `.tmp/ge1420/baseline`.

## Testabschluss und Rotation

Alle 25 Glocken- und 25 Rendererprüfungen bestehen. Syntaxprüfung, CLI-Hilfe,
Runtime-ID-Nullprüfung (`0 occurrences`) und Diff-Whitespace-Prüfung bestehen.
Die vollständige Suite einschließlich aller drei Heavy-Module und der
Satisfactory-Bestandsschutzbatterie besteht: **2.237 bestanden, 0 fehlgeschlagen,
29 übersprungen**, insgesamt 2.266 Tests in 748,42 Sekunden mit Exit 0.
Die Skips betreffen ausschließlich POSIX-Shelltests unter Windows. Testzahlen,
Laufzeit sowie Protokoll-/JUnit-Hashes stehen im kompakten JSON-Nachweis.
Die vollständigen lokalen Protokolle liegen unter `.tmp/ge1420/completion.log`
und `completion.xml`.

Der erneuerte Review enthält 956 Einträge, davon 950 renderbare Paare. Alle 48
gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze. Die vier neuen
Rasterpässe sowie früher separat belegte Pässe sind aus der Auswahl ausgeschlossen.
Historische Sammel-SVGs werden durch die frischen CLI-Läufe nicht überschrieben.
Der genaue Review-Aufruf steht unter `review.reproduction_arguments` im JSON.

Die nächste reguläre Rotation beginnt mit **`AC0704_1_L`**, gefolgt von
`AC0402_1_S`, `AC0403_1_L`, `GE0032` und `AC0413_1_M`.
Vor Änderungen ist wieder eine frische CLI-Baseline erforderlich.
