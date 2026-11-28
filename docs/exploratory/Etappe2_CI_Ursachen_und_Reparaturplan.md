# Etappe 2: CI-Ursachen und begrenzter Reparaturplan

**Stand:** 28. November 2026, 11:15 Uhr Europe/Zurich.
**Branch:** `codex/exploratory-ci-triage`, aufbauend auf der Demo aus PR 2085.

Die Diagnoseetappe ist abgeschlossen. Die gesamte Repository-CI ist weiterhin
rot. 18 der 20 fehlgeschlagenen AP-2-Jobs scheitern bereits auf dem passenden
`main`-Ausgangsstand. Zwei weitere Abweichungen bleiben ausdrücklich ungeklärt.
Die nächsten Reparaturen sind unten begrenzt; AP 3/4 bleiben danach eingeplant.

## Umfang und Aufwand

Dieses Paket erfasst alle Jobs dreier vorhandener Läufe, liest die Logs aller
20 fehlgeschlagenen Jobs des Ausgangsstands und aller 20 fehlgeschlagenen
AP-2-Jobs und untersucht drei vorhandene CI-Artefakte. Es verändert keine
Konvertierungslogik, Prüfer, Testdaten oder Qualitätsgrenzen.
Aufwandsrahmen: eine Diagnose- und Dokumentationsrunde, höchstens ungefähr eine
Stunde Entwicklungsarbeit, keine neue Katalogbatterie. Das ist eine
Arbeitsabschätzung, keine Verbrauchszusage für das Wochenkontingent.

Die vorhandenen Actions-Ergebnisse sind die Prüfevidenz dieses reinen
Diagnosepakets. Es wurden keine lokalen Tests, Testkonvertierungen oder
Benchmarks ausgeführt. Heruntergeladene Artefakte wurden ausschliesslich
gelesen; gespeicherte SVGs wurden nicht erneut gerendert. Neue CI-Ausführungen
werden mit `[skip ci]` für diesen Dokumentationscommit bewusst übersprungen.
Es gibt deshalb keinen neuen Testnachweis für diesen HEAD.

## Vollständiges Inventar statt erster Jobseite

Der GitHub-Connector für Workflow-Jobs liefert standardmässig nur die erste
Seite. Hier wurde je Lauf die REST-Abfrage `jobs?per_page=100&page=1` verwendet:
`total_count=49`, tatsächlich gelesen jeweils 49. Die
[versionierte Evidenz](../../artifacts/evaluation/exploratory_ci_triage_2026-11-28/summary.json)
enthält Commit, jeden Job mit Status und Link, fehlgeschlagene Schritte,
ausgewählte Logzeilen, Artefakt-Hashes und ausgelesene Deadline-Nachweise.
Jobzahlen sind keine Testzahlen; mehrere Jobs führen dieselben Tests aus.

| Lauf | Commit | Erfolg | Fehler | Abgebrochen | Laufend / wartend |
| --- | --- | ---: | ---: | ---: | ---: |
| [main, abgeschlossener Ausgangsstand](https://github.com/MobyDickDick/ImageConverter/actions/runs/46065788763) | `c241d3e424ddd47868585e4865ed51a7a65464f1` | 26 | 20 | 3 | 0 |
| [AP 2, abgeschlossen](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133) | `af518904fe2cb8c9cb4f5c12fa9b0c7c4536c07f` | 18 | 20 | 11 | 0 |
| [Etappe 1, Zwischenstand 11:15 Uhr](https://github.com/MobyDickDick/ImageConverter/actions/runs/46133560901) | `41c1ed751b7f193956f4d001167eb4ff3df1b43e` | 10 | 10 | 0 | 11 / 18 |

Der letzte Lauf ist **nicht abgeschlossen**. Sein Inventar ist eine datierte
Momentaufnahme, keine Endbilanz. Eine spätere Änderung seines Status verändert
die abgeschlossenen Vergleichsläufe nicht.

Die separate [Exploratory acceptance von Etappe 1](https://github.com/MobyDickDick/ImageConverter/actions/runs/46133560880)
ist auf Windows und Ubuntu 24.04 erfolgreich: jeweils **41 Tests**, einschliesslich
Galerieerzeugung und Upload. Diese kleine Abnahme ersetzt die rote Legacy-CI nicht.

## Vergleich mit dem Ausgangsstand

Zwischen `c241d3e4` und `41c1ed75` sind die betroffenen Legacy-Module, deren
Prüfwerkzeuge, Konfigurationen, bisherigen Tests und
`local-completion-checks.yml` unverändert. Die neuen explorativen Dateien
sind isoliert hinzugekommen. Das wurde anhand des Git-Diffs überprüft.
Die folgenden Aussagen unterscheiden dennoch Jobstatus, konkrete Fehlersignatur
und Ursache: unveränderter Code allein beweist keine identische Ausführung.

- **18 gemeinsame rote Jobs:** Die in der Tabelle aufgeführten Signaturen sind
  bereits auf `main` vorhanden. Fallzahlen schwanken, etwa bei `rounded-composition`,
  `component-splits` und `named-scene-references`. Das ist kein Beleg für eine
  neue deterministische Regression oder eine abgeschlossene Ursachenklärung.
- **Zwei zusätzliche rote Jobs im AP-2-Lauf:** `regression-checks` und
  `satisfactory-regression-battery` waren auf `main` grün. Beide vermissen ein
  AC0800-SVG. Der Smoke-Log zeigt zusätzlich eine Ablehnung mit
  `logical_object_count:all:1:2`. Ein Zusammenhang mit den bereits bestehenden
  Objektzählungsfehlern ist plausibel, aber nicht durch einen kontrollierten
  Seed-/Reihenfolgevergleich bewiesen. Priorität P1, keine Entwarnung.
- **Umgekehrte Unterschiede:** `mixed-gradient-scenes` ist auf `main` rot und
  im AP-2-Lauf grün. Katalog-Shard 0 ist auf `main` rot (CLI-Exit 1), im AP-2-Lauf
  abgebrochen und damit nicht vergleichbar. Beide Unterschiede werden nicht
  als behobene Fehler gezählt.
- **Abgebrochene AP-2-Jobs:** alle acht Katalog-Shards, `completion-profile`,
  `batch-artifact-drift-gate` und `pytest-profile-matrix (extended, 60)`.
  Abbruch ist weder eine Qualitätsabnahme noch eine bestätigte Produktursache.

## Befunde nach Ursache beziehungsweise offenem Ursachenverdacht

**D1 – Ergebnisloser Abschluss wird als unbestätigter Timeout behandelt (P1,
Prüferursache bestätigt; Grund der erfolglosen Suche nur teilweise erklärt).**
Im [Gradientenartefakt](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/artifacts/15258031448)
endet `gradient_00` nach `2.000645 s` mit `stop_reason=no_result`,
`gradient_03` nach `1.980746 s` ebenfalls ohne Ergebnis. Beide haben ein
Fünf-Sekunden-Limit. `gradient_04` erreicht dagegen tatsächlich `time_limit`
nach `5.024264 s`, ohne erhaltenes SVG. Der Prüfer
`tools/evaluate_layered_scene.py::verify_report` akzeptiert im Zweig ohne
Ergebniszeile nur einen belegten Timeout und meldet beim ersten Fall deshalb
`Unverified missing-output timeout`. Er erklärt damit den tatsächlichen
Fehlerzustand unzutreffend. Der Worker-Log von `gradient_00` zeigt einen
pixelqualitativ abgelehnten Fit (`edge_alignment=0.5389946103`), danach neun
verworfene IR-Kandidaten und `description_geometry_ir_no_valid_candidate`.
Eine Korrektur muss diesen negativen Ausgang belegt erhalten und darf daraus
keine erfolgreiche Konvertierung machen. Dasselbe Prüferproblem tritt bei
`layered-primitive-scenes` auf; dessen einzelne Workerursache ist noch offen.

**D2 – Fehlende SVGs oder Worker-Nachweise (P1, Symptome bestätigt,
gemeinsame Runtime-Ursache unbestätigt).**
Acht Szenenjobs enthalten `missing_or_ambiguous_output`; weitere Beispiele
sind `anonymous_square_02/after` und der fehlende Worker-Audit für `case_04`.
Ein Suchfehler, ein echter Timeout, fehlende Veröffentlichung und eine falsche
Dateiauswahl dürfen hier nicht ohne Einzelnachweis gleichgesetzt werden.
Das [Komponentenartefakt](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/artifacts/15257547330)
enthält Telemetrie für `case_00` bis `case_03`; der Lauf bricht beim Einsammeln
des Audits für `case_04` ab. Der hochgeladene Ausschnitt enthält nicht den
vollständigen Arbeitsordner mit dessen CLI-Log; die ursprüngliche Ursache
bleibt offen. `run_seeded_scene_check.py` entfernt seinen temporären Ordner
auch bei Fehlern und bewahrt bislang nur das Seed-Rezept. Das erschwert die
Analyse von `same-paint-overlap` und `mixed-overlap-composition` nachträglich.

**D3 – Laufzeit-Fingerprint verändert (P1, Integritätsabbruch bestätigt,
veränderte Datei unbestimmt).**
`semantic-wording-robustness` bricht auf beiden Ständen mit
`Runtime changed during measurement` ab. `source_hashes` umfasst alle Dateien
unter `src/` und `config/` ausser Python-Caches, also auch mögliche erzeugte
Daten. Das [Artefakt](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/artifacts/15258565437)
bewahrt den vorherigen Fingerprint, aber keinen benannten Nachher-Diff.
Eine konkrete Änderung durch einen Generator ist deshalb nur eine Hypothese.
Die 15 positiven Versuche im Log sind zusätzlich alle negativ, die neun
Negativkontrollen positiv. Ein reparierter Fingerprint allein würde die
Qualitätsabnahme also nicht erfüllen. Integritätskontrollen bleiben verbindlich.

**D4 – Speichern, Beschreibungsbindung und logische Objektzählung (P1/P2,
mehrere getrennte Ursachen).**
Der vollständige Incumbent löst in einem Test keinen Speicher-Callback aus.
Der AC0130-Test erwartet den älteren Sidecar-Text, erhält aber die Beschreibung
mit gestrichelten Sprühstrahlen. Daneben lehnt die AC08-Abnahme Objektzahlen
und Beschriftungen ab oder erwartet einen inzwischen anderen Statusmarker.
Die identischen neun Fehlertests der schweren Suite auf beiden Ständen sind
in der Evidenz aufgeführt (jeweils 397 bestanden, 3 übersprungen). Der
Safe-Baseline-Lauf wiederholt acht davon; diese sind nicht acht zusätzliche
unabhängige Ursachen. Ob Testvertrag oder Produktverhalten zu korrigieren ist,
muss pro Vertrag entschieden werden; blosses Ersetzen erwarteter Strings
oder Objektzahlen ist keine Reparaturabnahme.

**D5 – Tatsächliche Qualität oder Objekt-/Lokalprüfung ungenügend (P2).**
AR0030 scheitert schon beim Original an MSE, Kanten und IoU; die 16 Varianten
werden deshalb nicht gestartet. Alle zwölf gemeldeten Clipped-Parent-Fälle
verfehlen mindestens das Kantengate. `visibility_05 False []` bedeutet nur,
dass keine globale Fehlerliste ausgegeben wurde; die kombinierte Abnahme
schliesst auch Objekt- und Lokalprüfungen ein. Die genaue ablehnende Teilprüfung
ist im Folgepaket aus dem Bericht zu benennen. Der AC0130-Crop ist ein eigener
Geometriebefund. Diese Fälle bleiben getrennt von technischen Ablaufreparaturen.

## Vollständige Liste der 20 roten AP-2-Jobs

Commit für jede folgende Zeile: `af518904fe2cb8c9cb4f5c12fa9b0c7c4536c07f`.
Die Test-/Fallnamen dienen zusammen mit dem benannten Schritt und dem
unveränderten Workflow als Reproduktionsweg **ausschliesslich auf Actions**.
Die parallelen `main`-Joblinks und Fehlersignaturen stehen in der JSON-Evidenz.

| Job / direkter Loglink | Betroffener Test oder Fall; Fehlersignatur | Gruppe / nächster Schritt |
| --- | --- | --- |
| [same-paint-overlap](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373453) | `same_paint_outlined_rounded_overlap_07`, fehlendes SVG, Seed 915463 | D2: negativen Workerabschluss erhalten |
| [mixed-overlap-composition](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373507) | `rounded_mixed_overlap_02`, fehlendes SVG, Seed 983147 | D2: dieselbe Evidenzkette prüfen |
| [rounded-composition](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373685) | `rounded_00/02/04/05`, fehlende SVGs, Seed 942817 | D2: pro Fall Stopgrund und Ausgaben vergleichen |
| [component-splits](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373598) | `edit_05`, fehlendes SVG, Seed 918373 | D2: negativer Abschluss / Strukturänderung |
| [named-scene-references](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373623) | `reference_00`, fehlendes SVG, Seed 762915 | D2: Worker und Dateiauswahl |
| [fused-primitive-scenes](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373640) | `fused_02/05`, fehlende SVGs, Seed 871205 | D2: Worker und Dateiauswahl |
| [rounded-gradient-scenes](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373705) | `gradient_00/03/04` ohne SVG; `Unverified missing-output timeout`, Seed 628191 | D1 zuerst; Qualitätsfehler bleiben negativ |
| [layered-primitive-scenes](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373608) | `layer_00` Qualitätsfehler, `layer_04` ohne SVG; gleicher Prüferabbruch, Seed 197323 | D1/D5 getrennt prüfen |
| [svg-text-baseline](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373513) | `anonymous_square_02/after`: `Expected one saved CLI SVG` | D2: Manifest und tatsächliche Veröffentlichung |
| [component-value](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373616) | `case_04`: `Missing supervised worker audit` | D2: Audit muss auch beim negativen Abschluss erhalten sein |
| [semantic-wording-robustness](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373569) | drei Familien, `Runtime changed during measurement` | D3: Vorher-/Nachher-Dateidiff, danach Qualität |
| [clipped-rectangular-gradient-parent](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373486) | `test_only_semantically_complete_incumbents_are_saved_during_minimum_effort[False]`: `assert []`; 1 Fehler / 147 bestanden | D4: vollständigen Kandidaten und Callback verfolgen |
| [fallback-structure](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373660) | `test_catalog_sample_uses_its_source_bound_sidecar_instead_of_the_jpeg_description`; `test_exact_ci_crop_and_nearby_frame_edges_preserve_observed_structure[1237139773188156879-11]`; 2 Fehler / 106 bestanden | D4 und D5: Textbindung und Crop getrennt behandeln |
| [safe-baseline](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373656) | 8 Fehler: fehlende Fits/AC0812-Ausgabe, AC0800-/AC0837-Zählung, AC0820-Label, AC0811-Status | D4: kleine Vertragsprobe statt ganze Suite |
| [full-heavy-conversion-suite](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373721) | dieselben 8 plus `test_convert_range_uses_existing_conversion_rows_as_template_donors` (AC0833); 9 Fehler / 397 bestanden / 3 übersprungen | D4: identische Testnamen schon auf main |
| [regression-checks](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373645) | `test_ac08_regression_smoke_run_creates_expected_outputs`: AC0800_M fehlt | D4-Verdacht; neue Statusabweichung, kontrollierter Vergleich nötig |
| [satisfactory-regression-battery](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373679) | `test_satisfactory_baseline_reconversion_smoke`: AC0800 fehlt; 1 Fehler / 5 bestanden | D4-Verdacht; neue Statusabweichung, keine neue gesamte Archivprüfung |
| [dot-panel-registration](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373458) | AR0030-Original: MSE/Kanten/IoU; 8 vorangehende Tests bestanden; Seed 113996966622973259 | D5: eigenes Qualitätspaket |
| [clipped-gradient-parent](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373557) | zwölf `clipped_outlined_groups2_multi4_rounded_mixed_overlap_*` negativ, Seed 618293 | D5: Konturen/Geometrie separat |
| [visible-primitive-scenes](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133/job/140937373555) | `visibility_05 False []`, Seed 731829 | D5: ablehnende Objekt-/Lokalprüfung bestimmen |

## Nächste begrenzte Reparaturen (Etappe 3)

Die Reihenfolge priorisiert belastbare Diagnose und gemeinsame technische
Verträge. Die Wirkung ist eine Erwartung, keine Zusage grüner Jobs.

| Paket | Konkreter Umfang und erwartete Wirkung | Actions-Abnahme und Aufwand | Verbleibende Unsicherheit |
| --- | --- | --- | --- |
| R1, zuerst: negative Workerabschlüsse nachvollziehbar erhalten | D1: `no_result`, belegten Timeout und fehlende/mehrdeutige Ausgabe getrennt berichten. D2: im Seeded-Runner bei Fehlern kompakte Ursachen-/Auditdaten vor dem Aufräumen sichern; keine Rohdaten dauerhaft versionieren. | Gezielt `gradient_00`, `gradient_03`, `gradient_04` mit Generatorseed 628191 und Suchseed 17 / 5 s sowie ein betroffener Same-Paint-Fall (915463). Negative Fälle bleiben negativ, fehlender/tamperierter Audit wird weiter abgelehnt; JUnit/JSON/Log hochladen. Eine kurze Implementierungsrunde, ungefähr 1–3 Stunden; CI wenige Minuten. | Behebt Diagnose/Beweisverlust; die fehlenden Fits und Pixelqualität werden dadurch voraussichtlich nicht behoben. Auditverlust von `case_04` noch nicht erklärt. |
| R2: Fingerprint-Differenz benennen und Ursprung korrigieren | D3: vor und nach dem Lauf hinzugefügte, entfernte und geänderte Dateien mit Hashes benennen. Erzeugte Daten ausserhalb des Runtime-Baums ablegen, falls als Ursache bestätigt; Integritätsprüfung beibehalten. | Zuerst eine eingefrorene Familie mit Seed 17 / 10 s, plus absichtliche Code-/Konfigurationsänderung als Negativkontrolle. Erst danach drei bestehende Familien. Ungefähr 1–2 Stunden für Diagnose; Reparatur bei ungeklärtem Dateidiff neu schätzen. | Noch keine bestimmte Datei bestätigt; 15 negative Positivversuche bleiben separat offen. |
| R3: AC08-Verträge und zwei Statusabweichungen eingrenzen | D4: die beiden neu roten AC0800-Proben und einen reproduzierbaren Zählungsfehler unter gleichen Seeds, Reihenfolge, Abhängigkeiten und Budgets auf `c241d3e4` und Reparaturstand vergleichen. | Zuerst `test_conversion_regression_smoke.py::test_ac08_regression_smoke_run_creates_expected_outputs`, `test_satisfactory_regression_battery.py::test_satisfactory_baseline_reconversion_smoke` und `test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0800_L-semantic_ok]`; `RUN_HEAVY_CONVERSION_TESTS=1`. Ungefähr 2–4 Stunden bis zur eingegrenzten Ursache; Runtime-Reparatur erst danach schätzen. | Ein gemeinsamer Zählungsfehler ist plausibel, aber Varianten-/Seed-/Auswahlabhängigkeit nicht ausgeschlossen. |

R1 ist das nächste Arbeitspaket. Nach seinem gezielten Lauf folgt eine kleine
Regression der betroffenen Runner-/Deadline-Verträge und die bestehende
explorative AP-1/2-Abnahme. Erst nach einem sinnvollen Reparaturpaket wird
breiter geprüft. Die Katalogbatterie wird nicht zur Erstdiagnose wiederholt.

**Fortschreibung:** R1 ist im [ersten Reparaturpaket](Etappe3_R1_Workerabschluesse.md)
umgesetzt und gezielt geprüft. Die ursprüngliche Diagnosetabelle oben bleibt
als Ausgangsbefund erhalten. Nächstes Paket ist R2; die vier R1-Qualitätsproben
bleiben negativ und die übergeordnete CI bleibt ohne Gesamtfreigabe.

Nicht im ersten Reparaturpaket: geometrische Einzelfälle aus D5, Sidecar-
Vertrag und Incumbent-Callback aus D4, komplette Legacy-Bereinigung sowie
AP 3/4. Sie bleiben ausdrücklich offen und werden nach R1–R3 neu gewichtet.
Für diese Restliste gibt es noch keine belastbare Gesamtschätzung. Nach
Erreichen eines Paketrahmens werden Belege und Restunsicherheit gesichert;
eine mehrtägige Gesamtbereinigung wird daraus nicht stillschweigend abgeleitet.
