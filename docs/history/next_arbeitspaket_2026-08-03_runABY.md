# Nächstes Arbeitspaket – Produktive Telemetrie-Baseline-Promotion Run ABY (2026-08-03)

Run ABY setzt den in Run ABX dokumentierten nächsten Schritt um: Der isolierte
CI-Workflow arbeitet nicht mehr mit einer synthetischen Leerbaseline, sondern
zeichnet einen auswählbaren echten Katalog-Shard auf und kann ihn nach bestandenem
Regression-Gate explizit als versionierte Baseline veröffentlichen.

## 1) Reproduzierbarer Katalog-Shard

Die manuellen Eingaben `shard_start` und `shard_end` begrenzen einen
deterministischen Referenzlauf; standardmäßig wird der kleine reale Shard
`AC0100_S` verwendet. Der Lauf aktiviert zusätzlich
`--fail-on-batch-failures`. Nur eine Summary v1 mit mindestens einer tatsächlich
verarbeiteten Konvertierung wird als Baseline-Kandidat hochgeladen. Damit kann
eine leere Sentinel-Auswahl nicht versehentlich zur produktiven Baseline werden.

## 2) Abnahme und explizite Promotion

Ein unabhängiger Folgejob lädt den Kandidaten, konvertiert denselben Shard erneut
und aktiviert das strikte Optimierungs-Telemetrie-Gate. Die optionale Promotion
läuft erst nach einem bestandenen Gate und nur, wenn beim manuellen Start
`promote_baseline=true` gewählt wurde.

Das veröffentlichte Artefakt trägt Run-ID und Run-Attempt im Namen und enthält
neben der unveränderten Summary eine `provenance.json` mit Commit-SHA, Quelllauf,
Versuch und Shard-Grenzen. Kandidaten und Diagnosereports bleiben kurzlebig;
promotete Baselines werden 30 Tage aufbewahrt.

## 3) Restbestand und nächster Schritt

Der nach derselben Zählregel aktualisierte Tracker enthält weiterhin **27 offene
Markdown-Checkboxen**. Die Schätzung von etwa 25 ist damit nur um zwei zu niedrig.
Run ABY schließt einen dokumentierten Anschluss aus Run ABX, der nicht als eigene
Checkbox in diesem Tracker geführt war; deshalb sinkt dessen Checkbox-Zähler nicht.

Als nächster Schritt kann ein dauerhafter Baseline-Kanal eingeführt werden, der
eine explizit benannte promotete Version auswählt, statt einen Pfad innerhalb
desselben Workflow-Laufs zu verwenden.
