# Arbeitspaket – Checkbox mit gefülltem Verlaufshaken (2026-10-08)

Branch: `codex/dlg0031-quality-2026-10-08`, Basis `9c21f00bf`.
Das nach dem Dachlinienpaket dokumentierte reguläre Paket `DLG0031` ist
umgesetzt. Qualitätsgrenzen, CLI-Iterationsbudget und SVG-Zugriffsschutz
bleiben unverändert. Der Gesamtpool-Nachweis `PB-POOL-2026-10-07` bleibt offen.

## Ursache und allgemeine Korrektur

Die XML verwies auf einen anderen Katalogeintrag. Die sichtbare Struktur ist
eine weiße Checkbox mit grauem Rahmen vor weißem Hintergrund, überlagert von
einem breiten Haken mit dunkler Umrandung und vertikalem grünem Farbverlauf.
Die bisherige Beschreibungsausgabe verwendete dafür offene Linienzüge und
rekonstruierte weder die gefüllte Hakenform noch deren Lage ausreichend.

Die Beschreibungen für `DLG0031` und das pixelgleiche `DLG0021` nennen diese
Topologie jetzt eigenständig, ohne Kataloggeometrie, feste Farben oder Maße.
Die neue katalogfreie Registrierung bestimmt beide Hakenachsen aus grüner
Rasterevidenz. Die beiden Kappen und der innere/äußere Knick ergeben zusammen
ein Polygon mit sechs Ecken. Die sichtbaren Seiten und die Unterkante des
Checkboxrahmens bestimmen dessen Grenzen; die verdeckte Oberkante wird
zunächst aus der quadratischen Form abgeleitet. Helle Innenflächen und
Unterstützung auf beiden Seiten und der Unterkante sind erforderlich.

Eine auf höchstens 417 Renderprüfungen begrenzte Suche passt Lage, Breiten,
Rahmen und drei Verlaufsfarben an. Sie minimiert quadratischen RGB-Fehler;
die Übernahme verlangt zusätzlich eine Verbesserung des unveränderten
absoluten CLI-Fehlermaßes. Fehlende oder zusätzliche Objekte, widersprüchliche
Beschreibungen, nichtendliche und konstante Zielfunktionen werden verworfen.
Dateinamen und vorhandene SVGs liefern keine Geometrie. Das gespeicherte SVG
enthält genau ein weiß gefülltes Rechteck mit Rahmen und ein gefülltes
Hakenpolygon mit nativem Verlauf und dunkler Umrandung.

PyMuPDF stellte native Polygonverläufe schwarz dar. Der private Renderadapter
zerlegt einfache achsenparallele Polygonverläufe in geometrisch beschnittene
Vektorbänder und zeichnet die Umrandung darüber. Auch konkave Grenzen,
umgekehrte Verlaufsrichtungen und `userSpaceOnUse`-Koordinaten werden geprüft.
Komplexe Paint-Server, Transparenz und nicht unterstützte Attribute bleiben
unverändert. Die gespeicherten Konvertierungen behalten native Verläufe.
Die Abnahme verwendet den Produktionsrenderer; sie belegt keine pixelgenaue
Übereinstimmung seiner Kantenglättung mit allen externen SVG-Renderern.

## Frische echte CLI-Abnahme

Vor Änderungen wurde die aktuelle Runtime auf neutral benannten Eingaben mit
der ursprünglichen Zielbeschreibung ausgeführt. Dieser Vorlauf ist eingefroren.
Der Nachlauf verwendet die eigenständige Beschreibung und Rasterregistrierung.
Der abschließende Repro-Vorlauf mit deaktivierter Registrierung produziert
dieselben ursprünglichen SVG-Bytes; der neue Polygonadapter verändert die
bisherigen offenen Linienzüge nicht. Beide Seiten erhalten eigene Rasterkopien,
damit ein fehlgeschlagener Vorlauf keinen Nachlauf-Eingang archivieren kann.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| DLG0031 | 16540.876953 | 1557.055542 |
| DLG0021 | 16540.876953 | 1557.055542 |

**2/2 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression.** Der quadratische Pixelfehler sinkt um rund 90,6 %.
Konturübereinstimmung: `0.609398 → 0.871728`; Vordergrund-IoU:
`0.635688 → 0.930556`. Die unabhängigen CLI-Läufe reproduzieren sämtliche vier
Vorher-/Nachher-SVGs und alle Gateentscheidungen exakt. Alle Konvertierungen
laufen mit Seed 0 in `semantic-only`, ohne verbotene SVG-Zugriffe und ohne
eingebettete Rasterbilder. Bestehende Restfehlerwarnungen bleiben sichtbar.

Die beiden Katalograster sind bytegleich. `DLG0021` ist deshalb ausdrücklich
kein unabhängiger Bild-Holdout. Synthetische Tests mit anderen Farben,
verschobener Lage und doppelter Auflösung prüfen die Verallgemeinerung.
Ein Runtime-Test verwendet das echte absolute CLI-Fehlermaß und verlangt
identische SVGs und Pixel unter zwei neutralen Dateinamen.

## Nachweise und Reproduktion

Versioniert sind nur Eingabemanifest und kompakter JSON-Nachweis unter
`artifacts/evaluation/checkbox_checkmark_recheck_v1/`. Die vollständigen SVGs,
Raster, Logs, versiegelten Baselines und Reviewtabellen liegen lokal unter
`.tmp/dlg0031/`. Der Runner prüft Quellhashes, verwendet getrennte Eingabekopien
und verweigert vorhandene Ausgabeverzeichnisse.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_checkbox_checkmark_recheck artifacts/evaluation/checkbox_checkmark_recheck_v1/manifest.json --output-dir .tmp/checkbox-reproduction
.venv/Scripts/python.exe -m tools.evaluate_checkbox_checkmark_recheck .tmp/checkbox-reproduction/manifest.json --output .tmp/checkbox-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_checkbox_checkmark_runtime.py tests/test_checkmark_disk_runtime.py tests/test_chevron_panel_runtime.py tests/test_three_way_valve_runtime.py tests/detailtests/test_rendering_gradient_compatibility.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
$env:TEMP = "$PWD/.tmp/checkbox-test-temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pytest -q -ra --basetemp=.tmp/checkbox-pytest
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Das Profil verwendet direktes Rendering. Die automatische Prozessisolation
wird durch diesen Abschluss nicht zusätzlich vollständig geprüft.

## Testabschluss und Rotation

82 fokussierte Tests sind grün. Der Runtime-Test wurde anschließend nochmals
mit dem tatsächlichen CLI-Fehlermaß geprüft; alle 18 Checkboxtests bestehen.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung (`0 occurrences`) und
Diff-Whitespace-Prüfung bestehen.

Der erste Gesamtlauf verwendete das automatisch gewählte Windows-Sandbox-
Tempverzeichnis. Dort scheiterten bestehende Dateiarchivierungs-, Umbenennungs-
und atomare Schreibtests an `WinError 5`; auch `py_compile` konnte seine
temporäre Datei nicht umbenennen. Der abschließende Lauf verwendet deshalb ein
frisches `--basetemp` sowie `TEMP`/`TMP` innerhalb des freigegebenen Arbeitsbereichs.
Die vollständige Suite einschließlich aller drei Heavy-Module besteht:
**2.178 bestanden, 0 fehlgeschlagen, 29 übersprungen**, insgesamt 2.207 Tests
in 677,93 Sekunden. Die Skips betreffen ausschließlich POSIX-Shelltests unter
Windows. Der Bestandsschutz aller gespeicherten zufriedenstellenden Varianten
besteht ebenfalls. Das vollständige Protokoll steht lokal in
`.tmp/dlg0031/completion.log`, Einzelresultate in `completion.xml`; die kompakte
Zusammenfassung bewahrt Testzahlen, Laufzeit und den XML-Hash.

Eine native Windows-Diagnose `0xc0000008` wurde beim bestehenden
Template-Transfer-Test ausgegeben. Pytest setzte den Lauf fort; der betreffende
Test und der gesamte Abschluss bestehen mit Exit 0. Derselbe Test reproduziert
die Diagnose auch isoliert und besteht dabei ebenfalls. Die Ursache dieser
Diagnose wurde in diesem Paket nicht verändert oder geklärt. Zwei weitere im
anfänglichen Lauf auffällige Tests bestehen isoliert mit dem freigegebenen
Testverzeichnis; die finale Gesamtsuite bestätigt sie ebenfalls.

Der erneuerte Review enthält 956 Einträge, davon 950 renderbare Paare. Alle 48
gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze. Bereits separat
belegte Pässe und die beiden Checkboxeinträge werden aus der Kandidatenauswahl
ausgeschlossen. Die zentralen Sammel-SVGs bleiben historische Artefakte; die
frischen CLI-SVGs sind in den lokalen Abnahmeläufen nachgewiesen.

Die nächste reguläre Rotation beginnt mit **`AC0130_S`**, gefolgt von
`GE1420_S`, `AC0704_1_L`, `AC0402_1_S` und `AC0403_1_L`. Vor Änderungen ist
wieder eine frische CLI-Baseline erforderlich. Der genaue Reviewaufruf steht
unter `review.reproduction_arguments` im kompakten JSON-Nachweis.

Die abschließende Git-Prüfung korrigierte CRLF-Zeilenenden in zwei neuen Dateien
und die UTF-8-Kodierung der Wörter `Kästchen` und `zusätzlich` in den
Beschreibungsprüfungen. Ein zusätzlicher Test sichert beide Umlautwörter ab.
Nach dieser kleinen Korrektur bestehen 32 fokussierte Tests; die beiden
gespeicherten CLI-SVGs behalten ihre exakten Bytes einschließlich der
Windows-Zeilenenden. Die vollständige Heavy-Suite wurde davor ausgeführt.
