# Arbeitspaket – unten offener Bogen unter Verlaufsschaft (2026-10-11)

Branch: `codex/ge9021-quality-2026-10-11`.
Das nächste dokumentierte Ziel `GE9021_1M` und alle 13 Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Gates ohne Pflichtmetrikregression.
Alle 14 JPGs bestehen außerdem die strengeren Plan-B-Pixelgrenzen.

## Ursache und allgemeine Korrektur

Die ursprüngliche Beschreibung nennt eine gelbe, unten geschlossene U-Form.
Das Raster zeigt einen senkrechten Verlaufsschaft über einem getrennten,
unten offenen Bogen. Beide XML-Kataloge beschreiben diese Topologie jetzt
eigenständig; Lage, Abmessungen, Strichbreite und Farben bleiben Rasterbefunde.

Die bestehende Registrierung für einen oben offenen Bogen über einem Schaft
wird für die ausdrücklich beschriebene Gegenrichtung vertikal normalisiert.
Der Renderer prüft Kandidaten in den ursprünglichen Bildachsen. Die Ausgabe
enthält native Koordinaten, einen elliptischen Bogenpfad und einen Rechteckschaft
mit horizontalem SVG-Farbverlauf, ohne Rastereinbettung oder SVG-Transformation.
Es gibt keine neue Runtime-Bildkennung oder gespeicherte Motivvorlage.

Bei der grauen Variante konnte die reine Pixelfehleroptimierung zuletzt den
separaten Optimierungswert verschlechtern und dadurch die gesamte Registrierung
verwerfen. Die neue Suche behält den besten zulässigen Zwischenstand unter dem
ursprünglichen Optimierungswert. Der bestehende Suchvertrag anderer Familien
bleibt unverändert.

Unabhängige Subpixelvarianten deckten weiße Randbeimischungen im gemessenen
Verlaufsprofil und fehlerhafte innere Kanten auf. Die neue Richtung vergleicht
zusätzlich ein aus inneren Rasterspalten geschätztes stückweise lineares
Verlaufsmodell. Ein nichtlinearer Verlauf behält seinen gemessenen Kandidaten.
Die Suchkosten kombinieren den quadratischen RGB-Fehler mit dem symmetrischen
Kantenabstand; die Abnahmegrenzen ändern sich nicht. Beide Kandidatensuchen
zusammen sind auf höchstens **578 Renderbewertungen** begrenzt. Widersprüchliche
Richtungen, fehlende Teile, ein geschlossener Kreis, eckiges U, zusätzliche
Objekte, nicht endliche Daten und fehlendes Rendering werden verworfen.

## Frische CLI-Abnahme und Wiederholbarkeit

Alle 14 Originalbeschreibung-SVGs wurden vor den Runtime- und XML-Änderungen
mit neutralen Dateinamen eingefroren. Der Recheck verwendet Wegwerfkopien,
kontrolliert Quellhashes und sperrt Referenz-SVG-Zugriffe. Die ursprüngliche
Beschreibung aktiviert den neuen Pfad nicht; sämtliche Vorlauf-SVGs bleiben
bytegleich. Es wird kein historischer Sammelwert als frische Baseline ausgegeben.

Gespeicherte End-SVGs werden mit dem Produktionsrenderer erneut gemessen.
Der unabhängige Semantikcheck verlangt einen unten offenen oberen Halbkreis,
einen schmaleren mittigen Schaft darüber, einen weißen Abstand und den
horizontalen Verlauf mit hellerer Mitte. Er akzeptiert unabhängig von der
Reihenfolge gezeichnete, nicht überlappende Elemente.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9021_1M | 12463.036133 | 194.409164 |
| GE9021_1S | 7132.523438 | 139.283340 |
| GE9021_2M | 9452.843750 | 197.198334 |
| GE9021_2S | 6311.709961 | 133.973328 |
| GE9021_3M | 4484.923340 | 110.464165 |
| GE9021_3S | 3831.976562 | 93.353333 |
| GE9021_4M | 2664.002441 | 53.509167 |
| GE9021_4S | 2044.089966 | 41.060001 |
| GE9021_5M | 4381.134766 | 107.166664 |
| GE9021_5S | 3261.043213 | 96.660004 |
| GE9021_6M | 9368.926758 | 217.192505 |
| GE9021_6S | 7190.436523 | 149.763336 |
| GE9021_7M | 4136.462402 | 134.294998 |
| GE9021_7S | 4182.443359 | 92.660004 |

**14/14 bestehen beide regulären Gates und sämtliche strengeren Pixelgrenzen;
null Pflichtmetrikregressionen.** Zwei unabhängige CLI-Abnahmen reproduzieren
alle 28 Vorher-/Nachher-SVGs und sämtliche Gateentscheidungen exakt.
Verbotene Referenz-SVG-Zugriffe: null. Die CLI-Restfehlerwarnungen bleiben sichtbar.

## Perception-Lerneffekt: generalisiert

Eine unabhängig konstruierte Vorlage mit anderer Geometrie und Farbe besteht
mit Seed `20261011` Original plus 16 Zufallsvarianten über die echte CLI
(**17/17**). Ein zweiter Lauf reproduziert alle Ausgabehashes und Qualitätswerte.
Zusätzliche Rastertests prüfen andere Farben, Lage, halbe und doppelte Auflösung
sowie dieselben 16 unterschiedlichen Pixelphasen. Der Konverter erhält nur
Rasterbild und Beschreibung.

Der Nachweis betrifft diese Bogen-/Schaftstruktur. Andere Richtungen, komplexere
Verläufe und beliebige zusätzliche Topologien sind damit nicht allgemein belegt.
Die offene Stressaufgabe für den bisherigen oben offenen U-Bogen bleibt separat.

## Erfolgsübersicht und nächste Rotation

Die 14 angenommenen Paare sind mit Beschreibung, Messwerten und Hashes in
`artifacts/satisfactory_conversions/` abgelegt. Die Übersicht enthält jetzt
**212** Paare; alle 198 bisherigen Indexeinträge bleiben unverändert.
Alle 212 erneuten Konvertierungen bestehen die Reviewgrenze in fünf getrennten
Prozessen (48, 46, 42, 28 und 48 Fälle). Die 22 bekannten älteren
Kompatibilitätsdrifts bleiben unverändert. Bericht:
`artifacts/satisfactory_conversions/recheck_ge9021_2026-10-11.json`.
Der erneuerte Review erfasst 1.000 Einträge und 993 renderbare Paare;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Nach Ausschluss der erledigten Varianten folgt **`SE0081`**, danach `GE0039_M`,
`GE9022_2M`, `AC0920_L` und `AC1000_S`.


Drei große Windows-Archivreprüfungen brechen beim Schreiben von CSV-Berichten
mit `OSError: [Errno 22]` ab; der Fehler tritt auch im normalen Windows-Prozess
auf. Die Ursache ist nicht belegt und bleibt als `ARCHIVE-WINDOWS-IO` offen.
Der neue optionale Parameter `--max-cases-per-worker 48` begrenzt die Zahl der
Bilder pro Prozess, hält komplette semantische Familien und sämtliche 48 Kompatibilitätsfälle zusammen
und übernimmt sämtliche Einzelprüfungen, Quellhashes und Fehlerentscheidungen.
Ein fehlendes oder doppeltes Ergebnis verwirft den Gesamtnachweis. Acht
Archiv-/Runner-Prüfungen bestehen, eine bestehende erweiterte Profilprüfung
bleibt im Standardprofil ausgelassen.

Die fokussierte Abnahme besteht mit **246 Tests**; die zehn schweren
Bestandsschutz-/Smoke-/Weak-Family-Tests bestehen ebenfalls, einschließlich
der 31 geschützten Varianten. Syntaxprüfung für `src`, `tests` und `tools`,
CLI-Hilfe, Runtime-ID-Nullprüfung und Diff-Prüfung bestehen.

Der vollständige Erstlauf erfasst **2.382 Fälle**: 2.350 bestanden,
30 bestehende Skips und zwei Fehler in der Zurückweisung zusätzlicher Objekte.
Während dieses bereits laufenden Prozesses wurde ein beim Bearbeiten
entstandener UTF-8-Kodierungsfehler in den Beschreibungsliteralen behoben.
Beide Fälle bestehen in der finalen fokussierten Suite und im separaten
Nachlauf der zehn Beschreibungsnegativfälle. Der Erstlauf dauert 1.728,54 Sekunden.
Vier anschließend hinzugefügte Archiv-Runner-Tests bestehen ebenfalls.

Der Gesamtnachweis für das aktuelle Standardprofil umfasst damit **2.356
bestandene Fälle, 30 bestehende Skips und keine ungelösten Testfehler**.
Es wird kein zweiter vollständig grüner monolithischer Lauf behauptet.
Erstlauf, Nachprüfungen und die Archivabnahme sind getrennt in
`artifacts/evaluation/inverted_arc_shaft_recheck_v1/validation_2026-10-11.json`
dokumentiert. Ausführliche lokale Logs liegen unter `.tmp/ge9021-*.log`.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_inverted_arc_shaft_recheck artifacts/evaluation/inverted_arc_shaft_recheck_v1/manifest.json --output-dir .tmp/inverted-arc-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/inverted_arc_shaft_recheck_v1/independent.svg --description-file artifacts/evaluation/inverted_arc_shaft_recheck_v1/independent.txt --seed 20261011 --output-dir .tmp/inverted-arc-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --max-cases-per-worker 48 --output-dir .tmp/inverted-arc-archive
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/inverted-arc-full
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Jeder CLI- und Archivrecheck benötigt ein frisches Ausgabeverzeichnis.
Manifest, eingefrorene SVGs, Gatebericht, strenger Pixelbericht, unabhängige
Vorlage, Plan-B-Ausgaben, Reproduzierbarkeit und Review-Aufruf stehen unter
`artifacts/evaluation/inverted_arc_shaft_recheck_v1/`.
