# Arbeitspaket – Luftbefeuchter und vorhandene SVG-Vorlage (2026-10-08)

Branch: `codex/ac0130-quality-2026-10-08`, Basis `2cec67269`.
Das nach der Checkbox-Abnahme dokumentierte reguläre Paket `AC0130_S` ist
umgesetzt. Die fachliche Bezeichnung **Luftbefeuchter** wurde vom Nutzer
bestätigt. Qualitätsgrenzen, CLI-Budget und SVG-Zugriffsschutz bleiben
unverändert. Der Gesamtpool-Nachweis `PB-POOL-2026-10-07` bleibt offen.

## Drei unterschiedliche Beschreibungen

Die bisherige gemeinsame XML nannte ein Kühlelement mit Andreaskreuz und
verwies auf einen anderen Katalogeintrag. Die Dateien enthalten unterschiedliche
Strukturen; die Beschreibungen werden deshalb eigenständig getrennt:

- `AC0130.jpg`: Verlaufsrechteck mit beschnittenem Andreaskreuz sowie Plus-
  und Minuszeichen. Diese Variante ist kein Holdout der neuen Registrierung.
- `AC0130_S.jpg`, `_M.jpg`, `_L.jpg`: Verlaufsrechteck mit linker Zickzacklinie
  und hohem ungefülltem Innenrechteck rechts. Beide XML-Dateien ordnen alle
  drei Rastervarianten der zutreffenden Beschreibung zu.
- Die vom Nutzer benannte Vorlage `samples/AC0130_L.svg`: linker Balken mit
  Queranschlüssen, wiederholte Gruppen aus zwei schrägen und einer horizontalen
  Linie sowie das rechte Innenrechteck. Die neue Sidecar-Datei `AC0130_L.txt`
  beschreibt diese Struktur und wird auch vom zufälligen Plan-B-Pool bevorzugt.

Die vorhandene SVG-Vorlage wurde gelesen und zum Erzeugen der Testbilder
verwendet. Sie wurde nicht geändert. Ihre Parameter werden weder in die
Beschreibung kopiert noch von der Konverter-Runtime gelesen.

## Allgemeine Rasterregistrierung

Die neue Registrierung erkennt die beiden senkrechten Innenrahmenkanten im
Spaltenprofil und schätzt den horizontalen Verlauf mit höchstens neun nativen
Verlaufstopps. Abweichungen vom Spaltenprofil liefern die wiederholten Linien.
Für die Zickzacklinie bestimmt eine Autokorrelation die Wiederholungsperiode;
für die Vorlagenstruktur liefern beobachtete horizontale Linienzentren ein
regelmäßiges Gitter. Dieses toleriert eine schwache oder verdeckte Beobachtung
und erhält auch Perioden zwischen ganzzahligen Pixelabständen.

Lage, Rahmen, Linienbreiten, Periode, Phase, Balken und Farben werden durch
begrenzte Render-/Fehlersuche verfeinert. Die Vorlagenstruktur gewichtet zusätzlich
die Übereinstimmung des beobachteten Kontrasts gegenüber der aus Randpixeln
geschätzten Hintergrundfarbe. Eine Palette darf den dunklen Balken nicht als
Verlaufsfarbe übernehmen. Höchstens 433 Renderprüfungen für die Zickzackstruktur
und 681 für die Liniengruppen sind möglich. Eine konstante oder nichtendliche
externe Fehlerfunktion liefert keine Übernahme; fehlende Strukturen und
widersprüchliche Topologieangaben werden in den Tests verworfen.

Die Runtime erhält ausschließlich Beschreibung und Raster. Der neue Pfad
liegt vor dem bestehenden Ersatzpfad und arbeitet auch mit neutralen Dateinamen.
Die SVGs enthalten native Rechtecke, Verlauf und Linien, keine Rastereinbettung.
Synthetische Tests verändern Farbe, Lage und Auflösung; die Runtime-Prüfung
verwendet das tatsächliche absolute CLI-Fehlermaß und verbietet Sample-Zugriffe.

## Frische echte CLI-Abnahme

Der vor der Runtime-Änderung ausgeführte CLI-Vorlauf ist lokal eingefroren.
Der abschließende Runner reproduziert dessen Originalbeschreibung mit
deaktivierter neuer Registrierung. Vor- und Nachlauf erhalten jeweils eigene
Rasterkopien, damit ein fehlgeschlagener Vorlauf den Nachlauf nicht beeinflusst.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| AC0130_S | 15686.570312 | 325.073761 |
| AC0130_M | 13784.041992 | 253.841660 |
| AC0130_L | 15599.253906 | 395.726257 |

**3/3 bestehen beide unveränderten Qualitätsgates ohne Pflichtmetrikregression.**
Zwei unabhängige CLI-Läufe reproduzieren sämtliche sechs Vorher-/Nachher-SVGs
und alle Gateentscheidungen. Die ursprünglichen Baseline-SVG-Bytes bleiben
identisch. Alle Konvertierungen verwenden Seed 0 und `semantic-only`;
bestehende CLI-Restfehlerwarnungen bleiben sichtbar.

## Roundtrip der bereitgestellten Vorlage

Die originale SVG-Vorlage wird zunächst parametrisch skaliert und verschoben,
dann gerastert und anschließend mit der eigenständigen Beschreibung konvertiert.
Seed `20261008` besteht **16/16** der unveränderten Plan-B-Grenzen. Ein zweiter
Lauf mit demselben Seed reproduziert alle 16 Eingabe-, Referenz- und Ausgabehashes
sowie die Qualitätsmetriken. Seed `20261009` besteht weitere **16/16**.
Sämtliche Abnahmen haben null verbotene SVG-Zugriffe.

Dieser Nachweis gilt für die geprüfte Liniengruppen-/Balkenstruktur und ihre
Varianten. Er schließt den gesamten zufälligen Aufgabenpool nicht. Die Abnahme
nutzt den Produktionsrenderer und belegt keine pixelgenaue Rückgewinnung aller
Strichelungen unter anderen SVG-Renderern. Die Andreaskreuz-Variante wird durch
diese Abnahme nicht als neue zufriedenstellende Rekonstruktion bestätigt.

## Nachweise und Reproduktion

Versioniert sind Eingabemanifest und kompakter JSON-Nachweis unter
`artifacts/evaluation/zigzag_panel_recheck_v1/`. Die vollständigen SVGs, Raster,
Logs und Reviewtabellen bleiben lokal unter `.tmp/ac0130/`. Die Vorlage selbst
bleibt unverändert; ihre eigenständige Beschreibung liegt unmittelbar daneben.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_zigzag_panel_recheck artifacts/evaluation/zigzag_panel_recheck_v1/manifest.json --output-dir .tmp/air-humidifier-reproduction
.venv/Scripts/python.exe -m tools.evaluate_zigzag_panel_recheck .tmp/air-humidifier-reproduction/manifest.json --output .tmp/air-humidifier-gates.json
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/images_to_convert/samples/AC0130_L.svg --description-file artifacts/images_to_convert/samples/AC0130_L.txt --seed 20261008 --output-dir .tmp/air-humidifier-template
.venv/Scripts/python.exe -m pytest -q tests/test_zigzag_panel_runtime.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
$env:TEMP = "$PWD/.tmp/air-humidifier-test-temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pytest -q -ra --basetemp=.tmp/air-humidifier-pytest
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Direktes Rendering ist ausdrücklich gewählt; die automatische Prozessisolation
wird durch diesen Abschluss nicht zusätzlich in einem vollständigen Lauf geprüft.

## Testabschluss und Rotation

21 fokussierte Tests bestehen. Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung
(`0 occurrences`) und Diff-Whitespace-Prüfung bestehen ebenfalls.
Die vollständige Suite einschließlich aller drei Heavy-Module besteht:
**2.200 bestanden, 0 fehlgeschlagen, 29 übersprungen**, insgesamt 2.229 Tests
in 723,70 Sekunden mit Exit 0. Die Skips betreffen ausschließlich POSIX-
Shelltests unter Windows. Der Bestandsschutz der gespeicherten zufriedenstellenden
Konvertierungen besteht ebenfalls. Testzahlen und Protokoll-/JUnit-Hashes stehen
im kompakten JSON-Nachweis; die vollständigen lokalen Protokolle liegen unter
`.tmp/ac0130/completion.log` und `completion.xml`.

Der bestehende Template-Transfer-Test gibt dieselbe bereits beim Checkbox-
Abschluss dokumentierte Windows-Diagnose `0xc0000008` aus. Pytest setzt den Lauf
fort; der betreffende Test und der vollständige Abschluss bestehen. Die Ursache
dieser Diagnose wurde in diesem Paket nicht verändert oder geklärt.

Der erneuerte Review enthält 956 Einträge, davon 950 renderbare Paare. Alle 48
gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze. Die neuen drei
Rasterpässe sowie die früher separat belegten Pässe sind aus der Auswahl
ausgeschlossen. Historische Sammel-SVGs werden durch die frischen CLI-Läufe
nicht überschrieben. Der genaue Review-Aufruf steht unter
`review.reproduction_arguments` im JSON-Nachweis.

Die nächste reguläre Rotation beginnt mit **`GE1420_S`**, gefolgt von
`AC0704_1_L`, `AC0402_1_S`, `AC0403_1_L` und `GE0032`.
Vor Änderungen ist wieder eine frische CLI-Baseline erforderlich.
