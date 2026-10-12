# Arbeitspaket – links offener Bogen neben Verlaufsschaft (2026-10-12)

Branch: `codex/ge9022-quality-2026-10-12`.
Das nach `GE0039_M` dokumentierte Ziel `GE9022_2M` und alle 13 Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Gates und die strengeren Plan-B-Pixelgrenzen
ohne Pflichtmetrikregression.

## Ursache und allgemeine Korrektur

Die ursprüngliche Beschreibung verweist auf ein hellgraues Quadrat. Das Raster
zeigt einen nach links offenen rechten Halbkreis links neben einem getrennten
waagerechten Schaft. Dessen vertikaler Farbverlauf ist in der Mitte heller.
Beide XML-Kataloge beschreiben diese Primitive und ihre Lagebeziehungen jetzt
eigenständig. Zahlen, Strichbreite und Farben bleiben ausschließlich Rasterbefunde.

Die bestehende allgemeine Bogen-/Schaftregistrierung normalisiert die ausdrücklich
beschriebene neue Richtung durch eine Vierteldrehung der Rasterachsen. Jeder
Suchkandidat wird in den ursprünglichen Bildachsen gerendert und bewertet.
Die finale Ausgabe enthält native Koordinaten, einen elliptischen Bogenpfad
und einen Rechteckschaft mit vertikalem SVG-Verlauf. Verlaufsausrichtung,
Abmessungen und registrierte Parameter werden mitgedreht; das gespeicherte SVG
benötigt keine Transformation. Die beiden bisherigen vertikalen Richtungen
behalten ihre ursprünglichen Ausführungspfade.

Es gibt keine neue Runtime-Katalogkennung, gespeicherte Motivvorlage,
Konturkopie oder Rastereinbettung. Die bestehende Suche mit höchstens 578
Renderbewertungen und sämtliche Qualitätsgrenzen bleiben unverändert.
Der Nachweis gilt für einen linken offenen Bogen mit getrenntem Schaft auf
weißem Hintergrund. Andere Richtungen und zusätzliche Objekte sind nicht
Teil dieser Abnahme.

## Frische Abnahme und Wiederholbarkeit

Vor der Runtime- und XML-Änderung wurden alle 14 Originalbeschreibung-SVGs
mit neutralen Dateinamen eingefroren. Zwei vollständige CLI-Abnahmen verwenden
Wegwerfkopien und reproduzieren sämtliche 28 Vorher-/Nachher-SVGs,
Pixelmessungen und Gateentscheidungen. Alle Vorlauf-SVGs sind bytegleich
mit den tatsächlich vor der Änderung eingefrorenen Dateien. Quellhashes
werden kontrolliert; Referenz-SVG-Zugriffe bleiben gesperrt, null Zugriffe.

Der unabhängige Semantikcheck verlangt genau den nach links offenen rechten
Halbbogen, den schmaleren mittigen Schaft rechts davon, den weißen Abstand und
den vertikalen Verlauf mit hellerer Mitte. Bewertet wird das erneut mit dem
Produktionsrenderer gerenderte gespeicherte SVG. Prozessabschluss allein
zählt nicht als Qualitätsabnahme; CLI-Restfehlerwarnungen bleiben sichtbar.

| Bild | Mean-Delta² vorher, neutral | Mean-Delta² nachher |
|---|---:|---:|
| GE9022_2M | 10904.975586 | 186.701660 |
| GE9022_1M | 11117.042969 | 191.147507 |
| GE9022_1S | 8320.559570 | 120.949997 |
| GE9022_2S | 6439.293457 | 112.273331 |
| GE9022_3M | 7168.730957 | 116.671669 |
| GE9022_3S | 4333.740234 | 73.176666 |
| GE9022_4M | 4052.540039 | 73.418335 |
| GE9022_4S | 2000.503296 | 32.566666 |
| GE9022_5M | 7494.796875 | 98.361664 |
| GE9022_5S | 5436.069824 | 65.486664 |
| GE9022_6M | 13156.853516 | 208.399994 |
| GE9022_6S | 8595.046875 | 122.426666 |
| GE9022_7M | 9474.244141 | 138.250839 |
| GE9022_7S | 8081.776855 | 97.110001 |

**14/14 bestehen beide regulären Gates und sämtliche strengeren Pixelgrenzen;
null Pflichtmetrikregressionen.** Der historische Kandidatenwert
`11451.323242` ist keine frische Baseline.

Ein gesonderter Vergleich verwendet echte Katalognamen und die vollständige
Originalbeschreibungstabelle aus Commit `478c6f047`. Er läuft auf der neuen
Runtime; die ursprüngliche Quadratbeschreibung aktiviert den neuen Bogenpfad
nicht. Der frische Zielvorlauf beträgt dort `11431.225586`, gegenüber
`10904.975586` im neutralen Kontext. Diese unterschiedlichen Baselines werden
getrennt ausgewiesen. Auch im vollständigen Katalogkontext bestehen alle 14
beide regulären und strengeren Gates; alle Nachher-SVGs sind bytegleich mit
den neutralen Ergebnissen.

## Perception-Lerneffekt und Bestandsschutz

Die unabhängige Vorlage wurde mit anderer Geometrie, Lage, Auflösung und
Farbe konstruiert. Original plus 16 Zufallsvarianten bestehen mit Seed
`20261012` zweimal **17/17** über die echte CLI. Sämtliche Eingabe-/Ausgabehashes,
Pixelmessungen, Komplexitätsprüfungen und Gateentscheidungen stimmen zwischen
den beiden Läufen überein. Zusätzliche Rastertests prüfen halbe und doppelte
Auflösung, eine verschobene Geometrie, andere Radien, Strichbreiten und Farben. Eine zusätzliche Probe mit ungleichen Verlaufsendfarben und
verschobener heller Mitte besteht ebenfalls und bestätigt die Farbausrichtung.
Fehlende Teile, ein geschlossener Kreis, ein eckiges U, ein unterbrochener Bogen,
zusätzliche Markierungen, umgekehrte Öffnung, widersprüchliche Beschreibungen,
fehlendes Rendering und nicht endliche Daten werden verworfen.

Die Erfolgsübersicht enthält **230 Paare**. Alle 216 bisherigen Indexeinträge
bleiben identisch. Die Archivprüfung verwendet für jede semantische Familie
einen frischen Prozess und erhält den gemeinsamen Kontext aller 48
Kompatibilitätsfälle; der bereits dokumentierte Windows-I/O-Befund bleibt
als eigene Aufgabe offen.

Die getrennte Archivprüfung besteht mit **230/230** erneuten Review-Pässen.
Alle 216 bisherigen erneut gemessenen Mean-Delta²-Werte sind exakt gleich;
die Liste der 22 bekannten älteren Kompatibilitätsdrifts ist unverändert.

Die 59 neuen fokussierten Tests und die beiden zusätzlichen
AC08-/AC0100-Smoke-Tests bestehen. Syntaxprüfung für `src`, `tests`, `tools`
und die neuen Nachweisskripte, CLI-Hilfe und Runtime-ID-Nullprüfung bestehen.
Der vollständige Standardtestlauf besteht mit **2465 Tests und 30 bestehenden
Skips**, null Fehlern. Der vollständige Lauf, die getrennten Smoke-Tests und
sämtliche Paketnachweise sind in `validation_2026-10-12.json` dokumentiert.

## Nächste Rotation und Reproduktion

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare.
Alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten
Reviewgrenze. Die bisherigen Ausschlüsse werden fortgeschrieben, einschließlich
aller 14 erledigten GE9022-Varianten. Es folgen **`AC0920_L`**, `AC1000_S`,
`GE0022`, `GE9024_1M` und `GE0300`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_side_arc_shaft_recheck artifacts/evaluation/side_arc_shaft_recheck_v1/manifest.json --output-dir .tmp/side-arc-reproduce
.venv/Scripts/python.exe artifacts/evaluation/side_arc_shaft_recheck_v1/recheck_catalog_context.py --output-dir .tmp/side-arc-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/side_arc_shaft_recheck_v1/independent.svg --description-file artifacts/evaluation/side_arc_shaft_recheck_v1/independent.txt --seed 20261012 --output-dir .tmp/side-arc-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/side_arc_shaft_recheck_v1/recheck_archive_families.py --output-dir .tmp/side-arc-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/side-arc-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools artifacts/evaluation/side_arc_shaft_recheck_v1
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Rechecks benötigen frische Ausgabeverzeichnisse. Manifest, eingefrorene
Vektoren, beide regulären Gates, strengere Pixelberichte, Katalogkontextvergleich,
unabhängige Vorlage, Plan-B-Eingaben/-Vektoren und reproduzierbare Messwerte
stehen unter `artifacts/evaluation/side_arc_shaft_recheck_v1/`. Die detaillierten
Arbeitslogs liegen unter `.tmp/side-arc-*.log`.
