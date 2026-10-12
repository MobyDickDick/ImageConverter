# Arbeitspaket – Linkspfeil auf einer Verlaufsscheibe (2026-10-12)

Branch: `codex/ge0039-quality-2026-10-11`.
Das nach `SE0081` dokumentierte Ziel `GE0039_M` und die großen und kleinen
Größenvarianten bestehen beide unveränderten regulären Qualitätsgates und
die strengeren Pixelgrenzen ohne Pflichtmetrikregression.

## Ursache und Korrektur

Alle drei Rasterbilder zeigen einen gefüllten Linkspfeil innerhalb einer
Kreisscheibe mit horizontalem Farbverlauf und heller Randkontur. Die bisherige
Beschreibung verweist auf andere Katalogbilder, eine Spiegelung und Drehung.
Der frische CLI-Vorlauf erzeugt stattdessen einen Kreis mit einem Buchstaben.
Beide XML-Kataloge beschreiben die sichtbaren Primitive jetzt eigenständig;
Lage, Maße und Farben bleiben ausschließlich Rasterbefunde.

Die allgemeine Registrierung `fit_disk_arrow` misst Kreiskontur, Farbverlauf,
Pfeilspitze, Schultern und rechteckigen Schaft. Sie prüft die Bildevidenz auf
verbundene Geometrie, konsistente Richtung, gleichmäßige Pfeilfarbe und fehlende
Zusatzobjekte. Eine begrenzte Pixelsuche bestimmt Geometrie, Konturen und Farben.
Eine helle Kontur kann im großen JPG einen einpixelbreiten Schaftstreifen
abtrennen: ein lokaler Lückenschluss unterstützt die Geometrieschätzung;
die Füllfarbe wird weiterhin aus den ursprünglichen Kontrastpixeln bestimmt.
Größere Lücken und zusätzliche Markierungen bestehen die Negativtests nicht.

Die Ausgabe besteht aus nativem Kreis, linearem Verlauf und einem verbundenen
Siebenpunkt-Pfeilpolygon. Es gibt keine Katalogkennung, gespeicherte Motivvorlage,
Konturkopie oder Rastereinbettung im Runtime-Ergebnis. Suchbudgets und
Qualitätsgrenzen bleiben unverändert.

## Rendererbefund aus der unabhängigen Zufallsprüfung

Der Produktionsrenderer ließ lineare Kreisverläufe innerhalb verschobener oder
skalierter Gruppen unangepasst an MuPDF durch; die Zufallsbilder hatten dadurch
schwarze Kreisscheiben. Der private Gradientadapter berücksichtigt jetzt
Verschiebung und positive gleichmäßige Skalierung der übergeordneten Gruppen
bei Alphamaske, Farbkoordinaten und Platzierung. Native Formen und Verläufe im
gespeicherten SVG bleiben erhalten. Drehung, Scherung, Spiegelung, ungleichmäßige
Skalierung und ungültige Transformationen bleiben außerhalb dieses Vertrags.
Tests vergleichen den Rand gegen die native Vollfarbenmaske und den Verlauf
gegen analytische Farbwerte, einschließlich verschachtelter Gruppen.

## Frische Abnahme und Wiederholbarkeit

Vor der Runtime-Änderung wurden vier neutrale CLI-Vorläufe mit der ursprünglichen
Beschreibung eingefroren. Zwei Abschlussläufe reproduzieren alle acht
Vorher-/Nachher-Vektoren und sämtliche Messwerte und Gates. Alle vier Vorlauf-SVGs
sind bytegleich mit dem tatsächlich vor der Änderung gespeicherten Lauf.
Referenz-SVG-Zugriffe bleiben im Konvertierungsprozess gesperrt; null Zugriffe.

Ein gesonderter Lauf mit echten Katalognamen und der vollständigen ursprünglichen
Beschreibungstabelle aus Commit `8f6a19982` bildet den alten Beschreibungskontext
nach. Die neue Registrierung ist auf dieser Vorlaufseite deaktiviert; die
untransformierten Renderpfade bleiben unverändert. Alle drei Nachher-Vektoren
sind bytegleich mit ihren neutralen Ergebnissen. Der große Vorlauf unterscheidet
sich im Katalogkontext; die Werte werden getrennt ausgewiesen.

| Fall | Mean-Delta² vorher, neutral | Mean-Delta² nachher |
|---|---:|---:|
| GE0039_M | 10712.346680 | 148.783890 |
| GE0039_L | 11055.168945 | 132.414291 |
| GE0039_S | 10434.291016 | 155.768005 |
| Unabhängige grüne Vorlage | 6116.553711 | 9.709574 |

Der echte große Katalogvorlauf erreicht `11105.766602`; die übrigen beiden
Katalogvorläufe stimmen in der Metrik mit dem neutralen Kontext überein.
Alle vier Fälle bestehen beide regulären Gates und die strengeren Pixelgrenzen
ohne Pflichtmetrikregression. Die unabhängige Semantikprüfung verlangt die
Kreisscheibe, den horizontalen Verlauf und den vollständig innenliegenden,
verbundenen Linkspfeil. Bewertet wird das erneut gerenderte gespeicherte SVG.
CLI-Restfehlerwarnungen bleiben sichtbar; Prozessabschluss allein zählt nicht
als Qualitätsabnahme. Der historische Kandidatenwert `11544.757812` ist keine
frische Baseline.

## Perception-Lerneffekt und Grenzen

Die grüne Vorlage wurde unabhängig mit anderer Geometrie, Lage, Farbpalette und
Auflösung konstruiert. Original plus 16 Zufallsvarianten bestehen über die echte
CLI mit Seed `20261011` zweimal **17/17**. Ausgabehashes, Rasterhashes,
Pixelmessungen und Qualitätsentscheidungen stimmen zwischen den beiden Läufen
überein. Größere Auflösung, weitere Verschiebungen und eine braune Pfeilfarbe
bestehen zusätzlich die gezielten Tests. Fehlender Pfeil, umgekehrte Richtung,
Zusatzobjekte, innere Markierungen und ein unterbrochener Schaft werden von der Registrierung verworfen.

Der Nachweis gilt für die beschriebene Linkspfeil-/Scheibentopologie mit
horizontalem Verlauf. Andere Richtungen, mehrere Pfeile, OCR und beliebige
Hintergründe gehören nicht zu dieser Abnahme.

## Erfolgsübersicht und nächste Rotation

Die drei angenommenen Originalbild-/SVG-Paare liegen separat in der
Erfolgsübersicht. Sie enthält **216 Paare**; alle 213 bisherigen Indexeinträge
bleiben identisch. Der erste Archivlauf mit höchstens 48 Fällen pro Prozess
scheitert am bekannten `ARCHIVE-WINDOWS-IO` beim Schreiben von
`batch_failure_summary.csv`. Dieser Ausführungsfehler ist keine Qualitätsabnahme.
Die Wiederholung prüft die semantischen Motivfamilien einzeln und erhält den
gemeinsamen Kontext aller 48 Kompatibilitätsfälle.

Die getrennte Archivprüfung besteht mit **216/216** erneuten Review-Pässen;
alle 22 bekannten älteren Kompatibilitätsdrifts bleiben unverändert. Der
Windows-I/O-Fehler des größeren Laufes bleibt separat offen.

Der erneuerte Review erfasst 1.000 Einträge und 993 renderbare Paare. Alle 48
bisherigen Bestenlisteneinträge bleiben unter der unveränderten Reviewgrenze.
Nach Ausschluss der drei erledigten Varianten folgt **`GE9022_2M`**, danach
`AC0920_L`, `AC1000_S`, `GE0022` und `GE9024_1M`.

Die fokussierte Suite besteht mit **104 Tests**. Syntaxprüfung für `src`,
`tests` und `tools`, CLI-Hilfe und Runtime-ID-Nullprüfung bestehen.
Der vollständige Standardtestlauf besteht mit **2406 Tests und 30
bestehenden Skips**, null Fehlern. Die zwei zusätzlichen AC08-/AC0100-Smoke-Tests
bestehen ebenfalls. Die finalen Logs und die maschinenlesbare Zusammenfassung
sind im Nachweisordner versioniert.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_disk_arrow_recheck artifacts/evaluation/disk_arrow_recheck_v1/manifest.json --output-dir .tmp/disk-arrow-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/disk_arrow_recheck_v1/independent.svg --description-file artifacts/evaluation/disk_arrow_recheck_v1/independent.txt --seed 20261011 --output-dir .tmp/disk-arrow-plan-b-reproduce --keep-debug-artifacts
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/disk-arrow-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
.venv/Scripts/python.exe artifacts/evaluation/disk_arrow_recheck_v1/recheck_archive_families.py --output-dir .tmp/disk-arrow-archive-reproduce
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Rechecks benötigen frische Ausgabeverzeichnisse. Manifest, eingefrorene
Vektoren, beide Gates, Katalognamenvergleich, unabhängige Vorlage,
Plan-B-Vektoren und Messwerte sowie Archivbestandsschutz stehen unter
`artifacts/evaluation/disk_arrow_recheck_v1/`. Die vollständigen Arbeitslogs
liegen unter `.tmp/disk-arrow-*.log`.
