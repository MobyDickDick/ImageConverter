# Nächstes Arbeitspaket – FP-Recovery Run OB (2026-06-05)

## Ziel

Dieses Paket bearbeitet den in FP-D13/FP-D14 dokumentierten ersten
Wiederaufnahmepunkt: `AC0811_L`, `AC0811_M`, `AC0811_S` und `AC0831_L`
beendeten ihre isolierten Prozesse mit Exit `0`, erzeugten aber keinen
Variantendatensatz in `Iteration_Log.csv`.

## Root Cause

Alle vier Quellbilder liegen unter
`artifacts/images_to_convert/nonconvertable/`, während der segmentierte Smoke
jedes Segment unverändert mit `--input-dir artifacts/images_to_convert`
startete. Die explizite Variantenauswahl durchsucht absichtlich nur den direkt
angegebenen Eingabeordner. Dadurch war der jeweilige Batch leer; ein leerer
Batch ist auf CLI-Ebene kein Prozessfehler und endete deshalb mit Exit `0`.
Der Segment-Runner setzte anschließend allein aufgrund dieses Exitcodes den
`.segment-complete`-Marker.

## Umsetzung

1. Der segmentierte Runner ermittelt für jede feste Variante rekursiv den
   tatsächlichen Quellordner. Eine Datei im Eingabewurzelverzeichnis hat dabei
   Vorrang; andernfalls wird deterministisch der kürzeste passende Pfad
   verwendet. Der Konverter erhält weiterhin einen flachen Eingabeordner und
   behält damit seinen bestehenden Dateinamen-/Ausgabevertrag.
2. Ein Segment erhält den `.segment-complete`-Marker nur noch, wenn
   `reports/Iteration_Log.csv` tatsächlich eine Zeile für die erwartete
   Variante enthält. Exit `0` ohne Zeile wird als
   `BLOCKER_MISSING_REPORT` klassifiziert und hält die Aggregation zurück.
3. Die Finalisierung prüft dieselbe Invariante unabhängig erneut. Manuell oder
   veraltet vorhandene Marker können daher keine unvollständige Reportkette
   freigeben.
4. Detailtests decken Prozessfehler, Exit-0-ohne-Report, vollständig grüne
   Segmente sowie Marker-ohne-Variantendatensatz ab.

## Reale Recovery-Probe

Die vier zuvor fehlenden Varianten wurden mit einem reduzierten
Ein-Iterations-Budget über den echten segmentierten Pfad ausgeführt:

```bash
RC_GATE_AC08_VARIANTS='AC0811_L,AC0811_M,AC0811_S,AC0831_L' \
RC_GATE_AC08_SEGMENTS_DIR=/tmp/ic-runob4-segments \
RC_GATE_OUTPUT_DIR=/tmp/ic-runob4-output \
RC_GATE_EVIDENCE_DIR=/tmp/ic-runob4-evidence \
RC_GATE_AC08_ITERATIONS=1 \
RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS=300 \
RC_GATE_AC08_FINALIZE_CMD=true \
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
timeout 1200 ./tools/run_ac08_segmented_smoke.sh
```

Ergebnis: alle vier Segmente Exit `0`, Klassifikation `PASS`, Marker vorhanden
und je genau der erwartete Variantendatensatz:

| Variante | Beste Iteration | Diff-Score | FehlerProPixel |
| --- | ---: | ---: | ---: |
| `AC0811_L` | 1 | 6.93 | 0.00615822 |
| `AC0811_M` | 1 | 10.52 | 0.01502449 |
| `AC0811_S` | 1 | 9.30 | 0.02479644 |
| `AC0831_L` | 1 | 15.42 | 0.01370627 |

Damit ist der konkrete 10/14-Reportvollständigkeitsfehler behoben. Diese
reduzierte Recovery-Probe ist bewusst noch keine neue Releaseentscheidung:
Der vollständige feste 14er-Satz mit dem regulären Budget muss als nächstes
erneut laufen und zusätzlich den in FP-D14 geforderten Qualitätsgewinn
nachweisen.

## Plan B / No-silent-success

Falls eine zukünftige Quellordnerauflösung oder Konvertierung wieder eine
leere Reportkette erzeugt, beendet der Runner den Smoke nun unmittelbar mit
`BLOCKER_MISSING_REPORT`. Falls ein Marker außerhalb des Runners erzeugt wird,
verweigert zusätzlich die Finalisierung die Aggregation. Damit existieren zwei
unabhängige Sicherungen gegen den ursprünglichen stillen Erfolg.

## 5-Zeilen-Log

- **Getestet:** Detailtests, Shell-Syntax und echter Vierer-Recovery-Smoke.
- **Ergebnis:** Vier zuvor fehlende Varianten liefern jetzt 4/4 Iteration-Zeilen und PASS-Marker.
- **Blocker:** Die vollständige 14er-Qualitätsmetrik wurde in diesem Root-Cause-Paket noch nicht neu erhoben.
- **Nächster Schritt:** Vollständigen 14er-Satz mit regulärem Budget ausführen und FP-D14-Schwellen prüfen.
- **Startbefehl:** `RC_GATE_NAME=fp-recovery-run-oc RC_GATE_WORK_PACKAGE=FP-RECOVERY PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 ./tools/run_release_candidate_gate.sh`.
