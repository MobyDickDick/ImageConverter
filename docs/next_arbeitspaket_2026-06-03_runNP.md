# Nächstes Arbeitspaket – Run NP (2026-06-03)

Dieses Arbeitspaket schließt den nächsten Anschluss aus `docs/open_tasks.md` ab:
**FP-D5**. Wegen der Rückmeldung zum zu großen letzten Commit wurde der Scope
bewusst klein gehalten: keine breiten Artefakt-Refreshes, keine neuen
Massenoutputs, sondern nur Batch-Plan, zwei Messpunkte und Dokumentation.

## 1) Umsetzung

- `docs/fp_d5_batch_table_2026-06-03_runNP.md` definiert kleine N1/N2-Batches
  mit festem `timeout 180`.
- Zwei schnelle Referenzbatches wurden gegen `/tmp/ic-fpd5-runNP/...` ausgeführt,
  damit keine großen Output-Bäume in den Commit wandern:
  - `AC0800`: Exit `0`, Laufzeit `1.68s`.
  - `AC0814`: Exit `0`, Laufzeit `3.18s`.
- Die Top-3-Engpässe sind priorisiert: `AC0811`/Zeitbudget, kumulative
  `global-search`-Kosten und `AC0836`/native Stabilität.
- `docs/open_tasks.md` markiert FP-D5 als erledigt und verweist FP-D6 auf genau
  eine Gegenmaßnahme für Engpass #1.

## 2) Nachweis

- Befehl:
  - `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd5-runNP/ac0800 --start AC0800 --end AC0800 --deterministic-order`
- Ergebnis: Exit `0`, Laufzeit `1.68s`, Log `artifacts/converted_images/reports/FP_D5_AC0800_batch_2026-06-03_runNP.log`.

- Befehl:
  - `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd5-runNP/ac0814 --start AC0814 --end AC0814 --deterministic-order`
- Ergebnis: Exit `0`, Laufzeit `3.18s`, Log `artifacts/converted_images/reports/FP_D5_AC0814_batch_2026-06-03_runNP.log`.

## Kurzfazit

FP-D5 ist abgeschlossen, aber klein geschnitten: Die nächste Arbeit (`FP-D6`) hat
jetzt einen konkreten ersten Engpass (`AC0811`) und muss nicht erneut einen großen
Vollbereichscommit erzeugen.
