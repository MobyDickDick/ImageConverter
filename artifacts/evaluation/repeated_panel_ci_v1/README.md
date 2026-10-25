# Reparatur des fehlgeschlagenen Plan-B-Laufs aus PR #2066

Der [CI-Lauf 40176687737](https://github.com/MobyDickDick/ImageConverter/actions/runs/40176687737)
scheiterte fachlich mit **8/17**, nicht an GitHub-Infrastruktur. Die beiden
gezielten Jobs für #2004 und die bisherigen Verlaufspanels waren bereits grün.
Die Zufallsauswahl prüfte zunächst AC0838_M und AC0814_L erfolglos im Original,
dann AC0130_L mit 16 Varianten. Die beiden ersten Fehler bleiben als eigene
Backlogfälle erhalten; die Auswahl und ihre Qualitätsgrenzen bleiben unverändert.

## Ursache und getrennte Hypothesen

Das Sample-SVG ist bytegleich zur eingefrorenen Vorlage
`tests/fixtures/plan_b_templates/AC0130_L.svg`. Es enthält wiederholte Gruppen
aus drei Linien, einen linken Balken mit Queranschlüssen und einen rechten
Innenrahmen. Es erbte jedoch die Zickzackbeschreibung des anders aufgebauten
Katalog-JPEGs. Die echte CLI reproduziert die neun CI-Fehler mit demselben
vollständigen Seed und denselben Messwerten.

Die erste Hypothese korrigiert ausschließlich die Beschreibung: die bereits
vorhandene, passende Vorlagenbeschreibung verbessert den Lauf von **8/17 auf
15/17**. Sie gehört jetzt als Sidecar direkt zum Sample-SVG. Die Beschreibung
der Katalog-JPEGs bleibt erhalten; der Konverter bekommt ausschließlich das
gerasterte Bild und den zugeordneten Text.

Die zweite Hypothese ergänzt die Rasterregistrierung. Bei probe_04 liegt die
rechte Innenkante eine Spalte vor dem Bildrand und außerhalb der bisherigen
Suchspanne. Nur bei fehlender zweiter Innenkante wird diese zusätzliche,
beidseitig beobachtete lokale Senke geprüft. Bereits beobachtete Kantenpaare
werden erhalten. Bei probe_12 verfehlt die bisherige Achtelpixelregistrierung
die Vordergrund-IoU. Nur bei verfehlten unveränderten Pixelgates erfolgen zwei
zusätzliche Subpixelschritte. Das gemeinsame Zeitbudget bleibt maßgeblich;
ein bildgebundener Cache vermeidet doppelte Renderings, tatsächliche Versuche
werden im Suchstatus gezählt.

Ein zusätzlicher Seed zeigte einen durch Kantenglättung kaum sichtbaren
Wiederholungspeak. Bei inkonsistenter Periodenschätzung wird die kleinste
beobachtete Distanz als weitere Gitterhypothese geprüft; dieselben Grenzen
für Periode und Restabweichung gelten weiterhin. Dieser Fall wird ausdrücklich
als Entwicklungskontrolle erhalten, nicht als neue unabhängige Familie gezählt.

## Reproduktion

`manifest.json` bewahrt beide Beschreibungen, Quellhash, Ausgangscommit,
vollständige Auswahl-/Variationsseeds und das ursprüngliche 64/60-Budget.
`summary.json` dokumentiert die CI- und lokale Baseline, die reine
Beschreibungsänderung und die vollständige Reparatur. Die Rasterhashes bleiben
identisch; es gibt keine neue Referenz oder gelockerte Grenzwerte.

```powershell
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg-dir artifacts/samples --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir .tmp/repeated-panel-exact-selection --seed 6906637802001409049 --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/repeated_panel_ci_v1/manifest.json --output-dir .tmp/repeated-panel-holdout --seed 20261025
.venv/Scripts/python.exe -m pytest -q tests/test_zigzag_panel_runtime.py tests/detailtests/test_plan_b_variations.py
```

Ausgabeverzeichnisse müssen neu sein. Seit der vom Nutzer gewünschten Pause der
automatischen Zufallsläufe prüft der CI-Job die feste Quelle aus `manifest.json`
mit dem ursprünglichen und einem zusätzlichen Varianten-Seed, ohne Poolauswahl.
Die vollständige frühere Auswahl bleibt mit obigem CLI-Befehl manuell
reproduzierbar. Der zufällige Plan-B-Workflow ist nur manuell startbar.
Die Nachweise ersetzen keine
Abnahme aller 77 Motive des Pools und keine vollständige Katalogabnahme.

Lokale Abnahme: dieselbe vollständige Auswahl verbessert sich von **8/17 auf
17/17**, Zusatzseed **17/17**. Alle Rasterprüfsummen bleiben identisch, die
lokale Baseline weicht in keiner der vier Metriken von CI ab. **91 gezielte
Tests** und **42 Core-Tests** bestehen mit Exit-Code 0. Der zusätzliche Seed
wurde nach seinem dokumentierten Fehlversuch zum Entwicklungsfall.
