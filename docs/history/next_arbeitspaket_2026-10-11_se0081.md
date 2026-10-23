# Arbeitspaket – Quadrat mit unterem Stiel und M (2026-10-11)

Branch: `codex/se0081-quality-2026-10-11`.
Das nächste dokumentierte Ziel `SE0081` besteht beide unveränderten regulären
Qualitätsgates und die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Ursache und Korrektur

Die bisherige Beschreibung verweist auf `SE0041` und ersetzt dort `T` durch `M`.
Sie beschreibt die sichtbare Quadrat-/Stielstruktur nicht eigenständig. Das
historische Sammel-SVG zeigt einen Kreis mit `T`; der frische CLI-Vorlauf unter
neutralem Namen hat ebenfalls die falsche Topologie. Beide XML-Kataloge nennen
jetzt ein gefülltes Quadrat mit Kontur, mittigem senkrechtem Stiel nach unten
und waagerechtem Text `M`. Maße, Lage, Schriftgröße und Farben bleiben Rasterbefunde.

Die bereits vorhandene allgemeine Quadrat-/Textregistrierung erzeugt damit
einen nativen Griffpfad, ein Rechteck und ein Textelement. **Runtime, Renderer,
Suchbudgets und Qualitätsgrenzen bleiben unverändert.** Es gibt keine neue
Katalogkennung im Runtime-Code, gespeicherte Motivvorlage oder Rastereinbettung.

## Frische Abnahme und Wiederholbarkeit

Vor der Katalogänderung wurden Ziel und unabhängig konstruierter blauer Holdout
über die echte CLI mit neutralen Namen eingefroren. Beim Holdout ist die
Beschreibung bereits eigenständig; seine Baseline prüft Bestandsschutz.
Der vorhandene Recheck-Runner prüft Quellhashes, verwendet Wegwerfkopien und
sperrt Referenz-SVG-Zugriffe. Zwei neue Abnahmen reproduzieren alle vier SVGs
und Gateentscheidungen exakt; beide Vorlauf-SVGs stimmen bytegleich mit dem
vor der Änderung eingefrorenen Lauf überein. Verbotene Referenzzugriffe: null.
Der echte Katalogname mit der vollständigen Beschreibungstabelle liefert
dasselbe End-SVG wie der neutrale Name.

Zusätzlich wird die vollständige ursprüngliche XML aus dem unveränderten
Ausgangscommit mit dem echten Namen `SE0081` geprüft. Hier übernimmt der
Altpfad aus dem Verweis auf `SE0041` das falsche `T`; ohne diese zusätzliche
Tabelle unterscheidet sich der neutrale Vorlauf. Da die Runtime unverändert
bleibt, prüft dieser gesonderte Vergleich denselben ursprünglichen Algorithmus.
Auch beide echten Katalog-SVGs wurden in einem zweiten Lauf bytegleich
reproduziert. Die beiden Baselinekontexte werden getrennt ausgewiesen.

Die Messung rendert die gespeicherten SVGs mit dem Produktionsrenderer erneut.
Der unabhängige Semantikcheck verlangt Quadrat, verbundenen mittigen unteren
Stiel und den exakten horizontalen Kontrasttext `M` im Quadrat.

| Fall | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| SE0081, echter Name und vollständiger ursprünglicher Katalog | 11891.464844 | 702.781555 |
| SE0081, neutraler Name und Originalbeschreibung | 8904.907227 | 702.781555 |
| Unabhängiger blauer Holdout | 39.704979 | 39.704979 |

**Ziel und Holdout bestehen beide regulären Gates und die strengeren Pixelgrenzen;
null Pflichtmetrikregressionen.** Beim Ziel erreichen Kantenübereinstimmung
`0.876647`, Objektmasken-IoU `0.876506` und strenger Vordergrund-IoU `0.865826`
die unveränderten Grenzen. CLI-Restfehlerwarnungen bleiben sichtbar.
Der historische Kandidatenwert `11975.778320` ist keine frische Baseline.

## Perception-Lerneffekt: generalisiert, bereits vorhanden

Die unabhängig konstruierte blaue Vorlage hat andere Geometrie, Konturfarbe,
Lage und Auflösung als das graue Ziel. Mit Seed `20261011` besteht sie Original
plus 16 Zufallsvarianten über die echte CLI (**17/17**). Ein zweiter Lauf
reproduziert alle Ausgabehashes und Qualitätswerte. Der unveränderte Registrierer
verwendet ausschließlich Rasterbild und Beschreibung; die Referenzvektoren sind
im Konvertierungsprozess gesperrt. Das Paket erweitert die nachgewiesene
Katalogabdeckung durch Datenpräzisierung, nicht durch einen neuen Algorithmus.

Der Nachweis gilt für die geprüfte Quadrat-/Unterstiel-/Einzelzeichenstruktur.
Die anderen Richtungen `SE0082` bis `SE0084` gehören nicht zu dieser Abnahme.
OCR und beliebige Beschriftungen oder zusätzliche Topologien sind nicht belegt.

## Erfolgsübersicht und nächste Rotation

Das angenommene Originalbild-/SVG-Paar liegt mit Beschreibung, Messwerten und
Hashes in der Erfolgsübersicht. Diese enthält **213 Paare**; alle 212 bisherigen
Indexeinträge bleiben identisch. Der neue Eintrag wurde aus einer Wegwerfkopie
erneut konvertiert und besteht die Reviewgrenze ohne Metrikdrift. Für dieses
reine Beschreibungspaket wird kein neuer vollständiger Archivlauf behauptet.
Ältere Archivdrifts und `ARCHIVE-WINDOWS-IO` bleiben separat offen.

Der erneuerte Review erfasst 1.000 Einträge und 993 renderbare Paare. Alle
48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Nach Ausschluss von `SE0081` folgt **`GE0039_M`**, danach `GE9022_2M`,
`AC0920_L`, `AC1000_S` und `GE0022`.

Die fokussierte Suite besteht mit **134 Tests**. Syntaxprüfung für `src`,
`tests` und `tools`, CLI-Hilfe und Runtime-ID-Nullprüfung bestehen.
Der vollständige Standardtestlauf besteht mit **2356 Tests und 30
bestehenden Skips**, null Fehlern, in 2117.94 Sekunden. Die Standard-
und fokussierten Logs sowie die maschinenlesbare Zusammenfassung sind im
Nachweisordner versioniert.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_labeled_description_recheck artifacts/evaluation/motor_square_recheck_v1/manifest.json --output-dir .tmp/motor-square-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/motor_square_recheck_v1/independent.svg --description-file artifacts/evaluation/motor_square_recheck_v1/independent.txt --seed 20261011 --output-dir .tmp/motor-square-plan-b-reproduce --keep-debug-artifacts
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/motor-square-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Rechecks benötigen frische Ausgabeverzeichnisse. Manifest, eingefrorene
Vektoren, Gateberichte, unabhängige Vorlage, Plan-B-Ausgaben, Archivbestandsschutz
und Review-Aufruf stehen unter `artifacts/evaluation/motor_square_recheck_v1/`.
Lokale vollständige Logs liegen unter `.tmp/motor-square-*.log`.
