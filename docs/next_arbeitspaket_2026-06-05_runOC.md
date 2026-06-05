# Nächstes Arbeitspaket – FP-Recovery Run OC (2026-06-05)

## Ziel

Run OC führt den in Run OB festgelegten vollständigen Wiederholungslauf aus:
der feste AC08-Satz mit 14 Varianten läuft segmentiert mit dem regulären
32-Iterations-Budget. Anschließend werden die drei harten FP-D14-Schwellen
erneut geprüft.

## Ausgeführter Abschlusslauf

```bash
RC_GATE_NAME=fp-recovery-run-oc \
RC_GATE_WORK_PACKAGE=FP-RECOVERY \
RC_GATE_OUTPUT_DIR=/tmp/ic-runoc-output \
RC_GATE_AC08_SEGMENTS_DIR=/tmp/ic-runoc-segments \
RC_GATE_EVIDENCE_DIR=/tmp/ic-runoc-evidence \
RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS=600 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
./tools/run_release_candidate_gate.sh
```

Das 600-Sekunden-Limit entspricht dem bereits in FP-D13 ermittelten Bedarf
für die langsamsten isolierten Varianten. Der Lauf verwendete keine
akzeptierten Ausnahmen und kein reduziertes Iterationsbudget.

## Gate-Ergebnis

| Schritt | Ergebnis | Befund |
| --- | --- | --- |
| Kernsuite | `PASS` | `714 passed in 53.59s` |
| AC08-Smoke | `PASS` | 14/14 Segmente Exit `0`, 14/14 Klassifikation `PASS`, 14/14 erwartete Zeilen in `Iteration_Log.csv` |
| Qualitätsgate | `BLOCKER` | `criterion_regression_set_improved=0`, deshalb `overall_success=0` |
| Gesamtgate | `FAIL` | Ausschließlich das fehlende Verbesserungs-Kriterium bleibt rot. |

Die vier in FP-D13 fehlenden Varianten `AC0811_L`, `AC0811_M`, `AC0811_S`
und `AC0831_L` besitzen nun auch im regulären 32-Iterations-Lauf jeweils einen
vollständigen Variantendatensatz. Der ursprüngliche stille 10/14-Erfolg ist
damit nicht wieder aufgetreten.

## Harte FP-D14-Schwellen nach Recovery

| Kriterium | Mindestwert | Run OC | Urteil |
| --- | ---: | ---: | --- |
| Varianten mit Iteration-Datensatz | `14/14` | `14/14` | erfüllt |
| Erhaltene Previously-Good-Anker | `6/6` | `6/6` | erfüllt |
| Gemessene Qualitätsverbesserungen | `>= 1` bei `0` akzeptierten Regressionen | `0` bei `0` akzeptierten Regressionen | nicht erfüllt |

Zusätzlich bestätigt die Metrik `0` semantische Mismatches, `0` Batch-/Render-
Fehler, `0` abgelehnte Regressionen und durchschnittlich `4.091`
Validierungsrunden pro Datei. Die sechs erhaltenen Anker sind `AC0800_L`,
`AC0800_M`, `AC0800_S`, `AC0811_L`, `AC0811_M` und `AC0811_S`.

## Neuer Root Cause des verbleibenden Blockers

Die Segmentierung löst die Laufzeitkopplung, zerlegt den festen Satz aber in
14 Ein-Datei-Batches. Jeder dieser Batches erzeugt einen initialen
Variantendatensatz, jedoch keine Zeile in `quality_tercile_passes.csv`:

1. Der konfigurierte offene Qualitätsgrenzwert beträgt `1.0`; alle 14
   initialen `error_per_pixel`-Werte liegen bereits darunter.
2. Deshalb liefert die Auswahl offener Qualitätsfälle keinen Kandidaten.
3. Der Fallback auf das mittlere/untere Terzil verlangt mindestens drei
   Ergebnisse; ein isoliertes Segment besitzt nur eines.
4. Für fokussierte `AC0811`-Batches sind globale Quality-Pässe zusätzlich
   ausdrücklich deaktiviert.

Die Finalisierung führt folgerichtig nur den Header des leeren optionalen
Quality-Pass-Reports zusammen. Die Erfolgsmetrik zählt Verbesserungen bewusst
nur aus akzeptierten Quality-Pass-Zeilen und setzt daher
`criterion_regression_set_improved=0`.

Damit ist die Releaseentscheidung weiterhin korrekt rot, aber der verbleibende
Blocker ist nun enger gefasst: nicht mehr Reportvollständigkeit oder
Regressionserhalt, sondern ein Widerspruch zwischen isolierter Ausführung und
der batchbasierten Verbesserungsmessung.

## Plan B / nächstes vollständiges Paket

Das nächste Paket muss die Verbesserungsmessung segmentierungsfest machen,
ohne den früheren globalen Timeout wieder einzuführen. Die bevorzugte Richtung
ist ein expliziter, isolierter Refinement-Versuch pro geeigneter Variante mit
Vergleich gegen deren initiales Segmentergebnis. Nur tatsächlich akzeptierte
Verbesserungen dürfen in den zusammengeführten Quality-Pass-Report eingehen;
Regressionen müssen verworfen und als solche protokolliert werden.

Abnahmekriterien für dieses Folgepaket:

1. Ein Test belegt, dass ein Ein-Datei-Segment einen echten Refinement-
   Kandidaten prüfen und eine Verbesserung protokollieren kann.
2. Ein Test belegt, dass eine schlechtere Refinement-Ausgabe den initialen
   Zustand nicht ersetzt.
3. Der segmentierte 14er-Lauf behält `14/14` Reports und `6/6` Anker.
4. Das Gate wird nur dann grün, wenn mindestens eine reale Verbesserung,
   `0` akzeptierte Regressionen und `overall_success=1` vorliegen.

## 5-Zeilen-Log

- **Getestet:** Vollständiges Release-Gate mit 714 Tests, 14 isolierten Varianten, 32 Iterationen und 600 Sekunden Segmentlimit.
- **Ergebnis:** Kernsuite und AC08-Smoke grün; 14/14 Reports und 6/6 Previously-Good-Anker wiederhergestellt.
- **Blocker:** Ein-Datei-Segmente erzeugen keine Quality-Pass-Zeilen; deshalb 0 gemessene Verbesserungen und `overall_success=0`.
- **Nächster Schritt:** Segmentierungsfesten isolierten Refinement-Pass mit Accept/Reject-Nachweis implementieren.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py -k 'quality_pass or success_metrics' tests/detailtests/test_local_completion_checks_tool.py`.
