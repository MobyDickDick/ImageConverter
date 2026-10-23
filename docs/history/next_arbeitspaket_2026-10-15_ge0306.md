# Arbeitspaket – drei waagerechte Streifen auf Verlaufsscheibe (2026-10-15)

Branch: `codex/ge0306-quality-2026-10-15`, Basis `0f71005f2`.
`GE0306` ist der nach AC0421 dokumentierte nächste reguläre Kandidat.
Das tatsächliche Flaggenbild besteht beide unveränderten regulären Gates
und die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellen und allgemeine Registrierung

Nur `GE0306.jpg` zeigt die beschriebene Flagge: eine Kreisscheibe mit heller
Randkontur und vertikalem Verlauf sowie ein eingeschlossenes Rechteck aus drei
lückenlos aneinanderliegenden waagerechten Streifen. Die drei im selben Eintrag
verzeichneten Bilder `GE0306_{L,M,S}` zeigen gekreuzte Werkzeuge und Tropfen.
Sie sind keine Größen-Holdouts der Flagge. Das Quelleninventar bewahrt alle
vier Rasterhashes, Abmessungen und ursprünglichen Beschreibungen.
`GE0306-TOOLS-SOURCE` bleibt dafür als separate Aufgabe offen.

Beide XML-Kataloge enthalten einen eigenständigen Flaggen-Eintrag ausschließlich
für das tatsächliche Flaggenbild. Die drei Werkzeugbilder behalten ihre bisherigen
Beschreibungen. Der Loader verknüpft Bilddetails mit der Eintragsbeschreibung;
ein separater Eintrag verhindert daher, dass die alte Verweisbeschreibung der
neuen Beschreibung vorangestellt wird. Ein erster Test entdeckte diese
Verknüpfung; nach der Korrektur bestehen alle 42 fokussierten Tests.

Die neue Registrierung regressiert Kreis und Farbverlauf aus der äußeren
Silhouette und freien Bereichen oberhalb und unterhalb des Rechtecks.
Zusammenhängende Kontrastbereiche bestimmen die Rechteckgrenzen. Eine
stückweise konstante Regression der robusten Zeilenfarben findet zwei
Streifenübergänge; gleiche Streifenhöhen oder eine bestimmte Palette werden
nicht vorausgesetzt. Die Prüfung der Streifeninnenflächen und freien
Kreisbereiche verwirft Lücken, Zusatzmarkierungen und falsche Topologien.
Eine begrenzte Pixelsuche verfeinert Geometrie, Kontur und Farben. Der
Ausgangsfehler bleibt eine harte Obergrenze.

Die Ausgabe enthält ein Hintergrundrechteck, einen Kreis mit nativem SVG-Verlauf
und drei analytische Rechtecke. Es werden keine gemessenen Pixelkonturen,
Bildkennungen, Rastereinbettungen oder Referenz-SVGs in der Runtime verwendet.
Die Registrierung ist für die geprüfte Familie mit drei kontrastreichen,
einfarbigen waagerechten Streifen innerhalb einer Verlaufsscheibe auf nahezu
weißem Hintergrund `generalisiert`. Andere Streifentopologien und die
Werkzeugbilder gehören nicht zu dieser Abnahme.

## CLI-Nachweis und unabhängige Fälle

Die echte CLI-Baseline mit Originalbeschreibung und neutralem Dateinamen wurde
vor den Änderungen an Runtime und Katalog eingefroren. Beide Seiten erhalten
frische Wegwerfkopien; der Runner prüft Quellhashes und sperrt fremde SVG-Lesezugriffe.
Eine Wiederholung reproduziert die ursprüngliche Baseline und den finalen Vektor
bytegenau. Der vollständige Originalkatalog aus dem Basiscommit sowie der
revidierte Katalog reproduzieren dieselbe finale Ausgabe unter echtem Dateinamen.
Die Katalogbaseline wird dabei eigenständig eingefroren und verglichen.

Bewertet werden gespeicherte SVGs nach erneutem Rendern mit dem Produktionsrenderer.
Mean-Delta² sinkt von **10398.578125 auf 776.863281**. Beide regulären Gates und
alle strengeren Pixelgrenzen bestehen. Es gibt null Pflichtmetrikregressionen
und null fremde Referenz-SVG-Zugriffe. Eine eigenständige Semantikprüfung
kontrolliert Kreis, Verlauf, drei gleiche Streifenbreiten, positive Streifenhöhen,
lückenlose Anschlüsse und den vollständigen Einschluss der Rechteckfläche.

Die unabhängige Vorlage verändert Canvas, Lage, Kreis-/Rechteckproportionen,
Streifenhöhen und Palette: grüner Kreis mit violetten, cremefarbenen und dunkelgrünen
Streifen. Zwei echte CLI-Läufe mit Seed `20261015` bestehen jeweils **17/17**.
Eingangs-/Ausgangshashes, Metriken, Komplexität und Gateentscheidungen sind identisch.
Direkte Rastertests prüfen zusätzlich halbe und doppelte Auflösung, Verschiebung,
andere Paletten, fehlende Primitive, senkrechte Streifen, Lücken, Fremdobjekte,
abweichende Streifenbreiten, widersprüchliche Texte und ungültige Messungen.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **263 Paare**. Alle 262 bisherigen Indexeinträge
bleiben identisch. Die vollständige Archivprüfung in getrennten Prozessen
besteht mit **263/263** erneuten Review-Pässen. Alle 262 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen bleiben
unverändert. Die fokussierte Suite besteht mit **42 Tests**, die
AC08-/AC0100-Smoke-Prüfung mit zwei Tests. Die vollständige Standardsammlung
besteht in vier frischen Prozessen mit **2.756 Tests und 30 bestehenden Skips,
null Fehlern**. Alle 2.786 gesammelten Testknoten sind nach Abgleich der
JUnit-Berichte genau einmal enthalten. Die vollständigen Abschlusszahlen,
Archivprüfung und Artefakthashes stehen in
`artifacts/evaluation/striped_panel_disk_recheck_v1/validation_2026-10-15.json`.

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare. Alle 48
bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Bestehende Ausschlüsse werden fortgeschrieben; ausschließlich `GE0306.jpg`
wird zusätzlich ausgeschlossen. Es folgen **`GE0346`**, `AC0850_L`, `GE0017`,
`GE0001_L` und `GE9031_6M`. Bestehende offene Aufgaben bleiben erhalten.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/striped_panel_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_striped_panel_disk_recheck artifacts/evaluation/striped_panel_disk_recheck_v1/manifest.json --output-dir .tmp/stripes-reproduce
.venv/Scripts/python.exe artifacts/evaluation/striped_panel_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/stripes-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/striped_panel_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/striped_panel_disk_recheck_v1/independent.txt --seed 20261015 --output-dir .tmp/stripes-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/stripes-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/stripes-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_regression_smoke.py --basetemp .tmp/stripes-smoke-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert
Manifest, Baselines, finale Vektoren, Quelleninventar, Gateberichte, unabhängige
Vorlage und kompakte Belege beider Plan-B-Läufe. Vollständige Unterprozessartefakte
und frühere Diagnosen bleiben unter `.tmp/stripes-*` erhalten.
