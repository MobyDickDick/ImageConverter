# Etappe 3, R1: Negative Workerabschlüsse und Fehlernachweise

**Stand:** 28. November 2026. Eigener Aufgabenbranch:
`codex/exploratory-r1-worker-evidence`, aufbauend auf der Diagnose in PR 2086.

Das erste begrenzte Reparaturpaket korrigiert die Diagnose fehlender Ausgaben
und sichert kompakte Fehlerbelege vor dem Löschen generierter Testdaten.
Konvertierungslogik und Qualitätsgrenzen bleiben unverändert.

## Änderung und Wirkung

`tools/evaluate_layered_scene.py::verify_report` unterscheidet jetzt zwei
belegte negative Abschlüsse ohne Ergebniszeile: `no_result_no_output` nach
regulär beendeter erfolgloser Suche und `time_limit_no_output` nach tatsächlich
erreichtem Fünfsekundenlimit. Beide benötigen die Prozessisolation, unveränderte
Zeitgrenzen, endliche passende Laufzeit, leere Ausgabeverzeichnisse sowie
unabhängige Eltern-/Worker-Nachweise ohne verbotenen Vektorzugriff. Ein als
erhalten markiertes Ergebnis widerspricht der belegten Ausgabeabwesenheit.
Unbekannter Stopgrund, fehlender Audit und vorhandene oder mehrdeutige SVGs
werden weiterhin abgelehnt.

Diese Einträge bleiben `accepted=False` und im Nenner der Prüfung.
`--require-all` scheitert auch dann, wenn die negative Ursache korrekt erklärt
ist. Die bestehende unabhängige Neuberechnung gespeicherter SVGs und ihre
Manipulationskontrollen bleiben erhalten.

`tools/run_seeded_scene_check.py` schreibt bei Fehlern und Unterbrechungen vor
dem Aufräumen nach `.tmp/scene-failures/<Laufname>/`: Fehlerart, Seed-Rezept,
bereinigten Ergebnisbericht, vorhandene Verifikation, Eltern-/Worker-Audits,
Deadline-/Timingdaten und Logauszüge. Die Dateien tragen Quell-/Speicherhashes
und sichtbare Kürzungskennzeichen. Textdaten sind auf 256.000 Byte pro Datei
und insgesamt 2.000.000 Byte begrenzt; die zusätzliche kleine Inventardatei ist
separat. Referenz-SVGs werden aus dem Bericht entfernt. Generierte Raster,
SVG-Dateien und Worker-Pickles werden nicht kopiert. Der ursprüngliche Fehler
wird nach dem Sichern erneut ausgelöst; ein Diagnosepaket erteilt keine Freigabe.

Das Seed-Journal speichert das Rezept weiterhin vor der Generierung und
ergänzt bei Fehlern den Diagnosepfad. `--case-id` erlaubt gezielte Ausschnitte
eines unveränderten Generatorseeds; die gewählten IDs stehen im Rezept.
Die bestehenden Seeded-Actions-Jobs laden Diagnoseordner auch bei Fehlern hoch,
einschliesslich des zuvor uploadlosen Mixed-Overlap-Jobs. Rohdaten bleiben
temporär und werden nicht versioniert.

## Gezielte Actions-Abnahme

Der Workflow `Scene failure evidence R1` führt zuerst genau vier echte
CLI-Proben mit Suchseed 17 und fünf Sekunden aus:

- `gradient_00`, `gradient_03`, `gradient_04`: Generatorseed 628191,
  sechs generierte Fälle, gleiche Beschreibungsparaphrase wie im Ausgangslauf.
- `same_paint_outlined_rounded_overlap_07`: Generatorseed 915463,
  `--rounded --outlines --same-fill`.

Die Qualitätsproben behalten ihre strenge Abnahme und bleiben bei negativem
Ergebnis rote Tests. Anschliessend laufen auch bei roten Proben auf Ubuntu 24.04
und Windows die Runner-/Deadline-/Manipulationsregressionen, die bestehenden
gespeicherten SVG-Kontrollen und die AP-1/2-Abnahme einschliesslich Galerie.
Python ist auf 3.10.11 festgelegt. JUnit, JSON und Logs werden hochgeladen;
die kleine Offline-Galerie ist ebenfalls enthalten. Keine Katalogbatterie.

Der [Actions-Lauf für Implementierungscommit `7322017f9`](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233)
ist vollständig abgeschlossen: zwei erfolgreiche Regressionsjobs und ein roter
Qualitätsjob, keine ausstehenden oder abgebrochenen Jobs. Der Gesamtlauf ist
**rot**, weil die vier Qualitätsproben unverändert scheitern.

| Prüfung | Ubuntu 24.04 | Windows |
| --- | --- | --- |
| Negative Evidenz, Runner, Aufräumen, Prozessdeadlines | 53 bestanden, 1 xfail; 55,63 s | 54 bestanden; 93,43 s |
| Bestehende SVG-Abnahme und Manipulationskontrollen | 6 bestanden; 0,18 s | 6 bestanden; 0,37 s |
| Exploratory AP 1/2 und Galerieprüfung | 41 bestanden; 0,37 s | 41 bestanden; 0,69 s |

Direkte Logs: [Ubuntu](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233/job/140966741566),
[Windows](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233/job/140966741545).
Der Ubuntu-`xfail` ist der bestehende
`test_production_cli_does_not_render_in_parent_reporting`: Die vorhandene
A5-Regel markiert Tests über 30 Sekunden entsprechend. Er zählt nicht als
bestanden; auf Windows besteht auch dieser Test. Die übrigen Deadline-Proben
einschliesslich echtem Prozessabbruch, `no_result`, Checkpoint- und
Manipulationskontrollen bestehen auf beiden Plattformen.

Die [vier echten CLI-Tests](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233/job/140966538597)
scheitern in 17,03 s ausschliesslich an der unveränderten vollständigen Abnahme,
nachdem die negativen Abschlüsse erfolgreich verifiziert und gespeichert wurden:

| Fall | Beobachteter Abschluss | Gemessene Suchzeit | Abnahme |
| --- | --- | ---: | --- |
| `gradient_00` | `no_result_no_output` | 1,861938 s | negativ |
| `gradient_03` | `no_result_no_output` | 1,819201 s | negativ |
| `gradient_04` | `time_limit_no_output` | 5,008280 s | negativ |
| `same_paint_outlined_rounded_overlap_07` | `time_limit_no_output` | 5,009996 s | negativ |

[Fehlerartefakt mit JUnit, vier Diagnosepaketen, JSON und Logs](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233/artifacts/15261299424),
[Ubuntu-Berichte und Galerie](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233/artifacts/15261817249),
[Windows-Berichte und Galerie](https://github.com/MobyDickDick/ImageConverter/actions/runs/46140951233/artifacts/15261354896).
Aufbewahrung: 14 Tage. Die [kompakte versionierte Bilanz](../../artifacts/evaluation/exploratory_r1_2026-11-28/summary.json)
enthält Commit, Job-/Artefakt-IDs, ZIP-Hash und originale Supervisionswerte.

Die Diagnosepakete enthalten auch nach dem Aufräumen jedes ursprünglichen
Arbeitsordners die Deadline-, Zugriffs- und Timingdateien. Das Fehlerartefakt
wurde lokal ausschliesslich als ZIP/JSON gelesen; kein SVG wurde neu gerendert.
Es wurden keine lokalen Tests, Testkonvertierungen oder Benchmarks gestartet.

Der anschliessende Dokumentations-/Evidenzcommit verwendet `[skip ci]`, damit
die PR-Eröffnung keine vollständige Katalogbatterie startet. Der CI-Nachweis
gilt ausdrücklich für den oben genannten unveränderten Implementierungsstand;
für den reinen Dokumentations-HEAD wird kein neuer Testlauf behauptet.

## Grenzen und nächstes Paket

R1 erklärt negative Abschlüsse und erhält ihre Belege. Es behebt weder
fehlende Fits noch Bildqualität und erklärt den früheren Auditverlust bei
`case_04` noch nicht. Die gesamte Legacy-CI ist damit nicht abgenommen.
R2 bleibt als nächstes Paket vorgesehen: konkrete Fingerprint-Differenzen
benennen und die Ursache nachweisen, zuerst an einer eingefrorenen Familie
mit Negativkontrolle. Der bisherige Rahmen von ungefähr ein bis zwei Stunden
für die Diagnose bleibt eine Arbeitsschätzung; eine Runtime-Reparatur wird
erst nach einem bestätigten Dateidiff geschätzt. R3, geometrische Einzelfälle,
Sidecar-/Incumbent-Verträge sowie AP 3/4 bleiben offen.
