# FP-D5 Batch-Tabelle – Run NP (2026-06-03)

## Ziel

FP-D5 zerlegt die bisher zu groben N1/N2-Vollbereichsläufe in kleine,
messbare Batches. Damit bleibt das Arbeitspaket bewusst klein: kein neuer
Vollbereichslauf, keine neuen Massenartefakte, sondern ein reproduzierbarer
Batch-Plan plus zwei schnelle Messpunkte.

## Batch-Schnitt

| Batch | Range | Zweck | Timeout-Guard |
| --- | --- | --- | --- |
| `B-AC08-plain-circle` | `AC0800..AC0800` | schneller Plain-Ring/Kreis-Referenzpunkt | `timeout 180` |
| `B-AC08-right-handle` | `AC0814..AC0814` | schneller Kreis-mit-Griff-Referenzpunkt | `timeout 180` |
| `B-AC08-risk-0811` | `AC0811..AC0811` | historischer Zeitbudget-/Global-Search-Engpass | `timeout 180` |
| `B-AC08-risk-0836` | `AC0836..AC0836` | historischer nativer Render-/Stabilitäts-Engpass | `timeout 180` |
| `B-AC08-rf-followup` | `AC0835..AC0862` in Einzel-IDs | rF-/Connector-Folgepunkte, nur noch einzeln messen | `timeout 180` je ID |

## Gemessene Batches in Run NP

| Batch | Befehl | Exit | Laufzeit | Fehlertyp | Log |
| --- | --- | ---: | ---: | --- | --- |
| `B-AC08-plain-circle` | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd5-runNP/ac0800 --start AC0800 --end AC0800 --deterministic-order` | `0` | `1.68s` | keiner | `artifacts/converted_images/reports/FP_D5_AC0800_batch_2026-06-03_runNP.log` |
| `B-AC08-right-handle` | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd5-runNP/ac0814 --start AC0814 --end AC0814 --deterministic-order` | `0` | `3.18s` | keiner | `artifacts/converted_images/reports/FP_D5_AC0814_batch_2026-06-03_runNP.log` |

## Top-3 Engpässe

1. **`AC0811`/Zeitbudget:** Historische AC0800..AC0899-Läufe endeten formal teils mit Exit `0`, lieferten aber keinen belastbaren Vollbereichsnachweis; der letzte sichtbare Engpass war wiederholt `validation_time_budget_exceeded` bei `AC0811_L`.
2. **Kumulative `global-search`-Kosten:** Die Timeout-Analyse vom 2026-05-07 bewertet nicht einen einzelnen Hänger, sondern die Summe vieler teurer `global-search`-Runden als Hauptursache der 300s-Timeouts.
3. **`AC0836`/native Stabilität:** Der historische Microbatch-Rest enthielt native Exit-`139`-Signale; spätere Re-Runs waren grün, bleiben aber als separater Risikobatch sinnvoll.

## Entscheidung

FP-D5 ist für den nächsten Schritt ausreichend abgeschlossen: Der Batch-Schnitt
ist klein genug für einzelne Commits, zwei Referenzbatches sind gemessen, und die
Top-3-Risiken sind priorisiert. FP-D6 soll **nur Engpass #1 (`AC0811`)**
bearbeiten und denselben Batch-Schnitt für den Vorher/Nachher-Repro verwenden.
