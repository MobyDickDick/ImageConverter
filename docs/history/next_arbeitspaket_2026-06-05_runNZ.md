# Nächstes Arbeitspaket – FP-D13 Run NZ (2026-06-05)

## Ziel

FP-D13 führt nach der Segmentierungs-Recovery den finalen End-to-End-Lauf aus,
vergleicht das Ergebnis quantitativ mit der AC08-Baseline und dokumentiert auch
einen roten Abschluss ohne stumme Freigabe.

## Ausgeführter Abschlusslauf

```bash
RC_GATE_NAME=fp-d13-run-nz \
RC_GATE_WORK_PACKAGE=FP-D13 \
RC_GATE_OUTPUT_DIR=/tmp/ic-fpd13-ac08 \
RC_GATE_AC08_SEGMENTS_DIR=/tmp/ic-fpd13-ac08-segments \
RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS=600 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
./tools/run_release_candidate_gate.sh
```

Der erste 240-Sekunden-Lauf hatte `AC0882_S` und `AC0820_L` mit Exit `124`
klassifiziert. Mit 600 Sekunden endeten alle 14 isolierten Prozesse mit Exit
`0`. Damit wurde bestätigt, dass die Segmentierung den früheren globalen
900-Sekunden-Abbruch auflöst; zwei Einzelvarianten benötigen jedoch mehr als
240 Sekunden.

## Gate-Ergebnis

| Schritt | Ergebnis | Evidenz |
| --- | --- | --- |
| Kernsuite | Nach den FP-D13-Fixes `710 passed`; im dokumentierten NZ-Lauf stand wegen eines inzwischen behobenen, durch geerbten Testkontext ausgelösten neuen Regressionstests zunächst Exit `1` im Gate-Status. | Der korrigierte Detailtest und anschließend die gesamte Kernsuite laufen grün. |
| AC08-Segmente | 14/14 Prozesse Exit `0`; Aggregation deckt 4 fehlende Varianten im zusammengeführten `Iteration_Log.csv` auf. | `AC0811_L`, `AC0811_M`, `AC0811_S`, `AC0831_L` fehlen reportseitig. |
| Qualitätsgate | `FAIL` | Vier harte Kriterien bleiben rot: keine neuen Batch-Abbrüche, Regression-Set verbessert, stabile Familien nicht schlechter, Gesamtstatus. |

Die Finalisierung wurde nach dem Fix für das optionale Qualitätsreporting auf
der vollständigen Segmentartefaktkette erneut ausgeführt:

```bash
python tools/finalize_ac08_segmented_run.py \
  /tmp/ic-fpd13-ac08-segments /tmp/ic-fpd13-ac08 \
  --input-dir artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --iterations 32
python tools/check_ac08_success_metrics_gate.py \
  /tmp/ic-fpd13-ac08/reports/ac08_success_metrics.csv
```

Finalisierung: Exit `0`; Qualitätsgate: Exit `1`.

## Quantitativer Baselinevergleich

| Kennzahl | Wert | Bewertung |
| --- | ---: | --- |
| Erwartete Varianten | 14 | fester AC08-Satz vollständig gestartet |
| Reportseitig konvertiert | 10 | unvollständig |
| Fehlende Varianten | 4 | `AC0811_L/M/S`, `AC0831_L` |
| Previously-Good erwartet / erhalten | 6 / 3 | drei Anker fehlen |
| Previously-Good regressiert | 0 | keine nachgewiesene Verschlechterung unter den vorhandenen Ankern |
| Verbesserungen `error_per_pixel` / `mean_delta2` | 0 / 0 | Baseline-Verbesserung nicht belegt |
| Akzeptierte Regressionen | 0 | No-silent-regression bleibt gewahrt |
| Semantische Mismatches | 0 | in vorhandenen Validierungslogs keine |
| Mittlere Validierungsrunden | 4,143 | Validierungsrunden sind messbar |
| `overall_success` | 0 | keine Release-Freigabe |

## Während FP-D13 geschlossene Tooling-Lücken

1. Der Release-Gate-Runner exportiert Output-, Evidence-, Timeout- und
   Work-Package-Variablen an den segmentierten Smoke. Dadurch liegen
   `ac08_segment_status.csv` und Segmentlogs im benannten Evidence-Verzeichnis
   statt im generischen Standardpfad.
2. `quality_tercile_passes.csv` ist fachlich optional, wenn kein Quality-Pass
   stattgefunden hat. Die Finalisierung erzeugt in diesem Fall einen leeren
   Report mit kanonischem Header, erfindet aber keine Verbesserung. Das
   nachgelagerte Qualitätsgate bleibt korrekt rot.
3. Regressionstests sichern beide Fälle ab.

## Entscheidung und Recovery

FP-D13 ist als Arbeitspaket vollständig ausgeführt und dokumentiert, endet aber
mit **FAIL/BLOCKER**. Eine Release-Freigabe wäre stumm falsch. Vor einer grünen
Abschlussentscheidung sind mindestens diese Punkte erforderlich:

1. Für `AC0811_L/M/S` und `AC0831_L` klären, warum der Segmentprozess Exit `0`
   liefert, aber keinen Varianten-Datensatz in `Iteration_Log.csv` schreibt.
2. Segmentvollständigkeit künftig nicht nur am Prozess-Exit, sondern zusätzlich
   am erwarteten Reportdatensatz festmachen.
3. Danach den 14er-Satz erneut ausführen und mindestens eine echte Verbesserung
   gegenüber der Baseline bei vollständig erhaltenen Previously-Good-Ankern
   nachweisen.

## 5-Zeilen-Log

- **Getestet:** Kernsuite, 14 isolierte AC08-Segmente, Aggregation und Qualitätsgate.
- **Ergebnis:** Prozesse vollständig, fachliche Reportkette nur 10/14; `overall_success=0`.
- **Blocker:** Vier Exit-0-Segmente ohne Iteration-Datensatz und kein gemessener Baselinegewinn.
- **Nächster Schritt:** Reportvollständigkeit der vier Varianten reparieren und Segmentmarker verschärfen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_local_completion_checks_tool.py`.
