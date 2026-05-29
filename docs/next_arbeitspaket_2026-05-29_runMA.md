# Nächstes Arbeitspaket – Run MA (2026-05-29)

Dieses Arbeitspaket rotiert nach Run LZ zurück auf das dokumentierte
Bild-/Testhygiene-Paket und sichert den AC0011-Einzelrun gegen externe
Output-Verzeichnisse ab.

## 1) Nächste dokumentierte Aufgabe: AC0011-Einzelrun ohne Repo-gebundenes Output-Layout

- Anlass:
  - `docs/open_tasks.md` dokumentiert als nächstes Bildpaket die
    AC0011-Stabilisierung: `AC0011.jpg` soll als reguläres SVG enden und nicht
    als `Failed_AC0011.svg` bzw. `raster_embedded_svg` im Failure-Summary.
  - Beim vorgeschalteten Smoke mit einem temporären Output-Verzeichnis stürzte
    die Finalisierung ab, weil `_removeSuccessfulVariantsFromOpenTasks(...)`
    starr `parents[3]` als Repository-Wurzel annahm.
- Umsetzung:
  - Die Open-Tasks-Nachpflege sucht nun vom `reports_out_dir` aus aufwärts nach
    dem nächsten vorhandenen `docs/open_tasks.md` und beendet sich ohne Aktion,
    wenn ein externer Output-Baum keine Repository-Dokumentation enthält.
  - Dadurch bleibt die automatische Nachpflege für normale Repo-Ausgaben
    erhalten, während isolierte Batch-/Smoke-Läufe unter `/tmp` nicht mehr durch
    ein zu flaches Verzeichnislayout abbrechen.

## 2) Sichernder Detailtest

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_conversion_finalization_helpers.py`
- Ergebnis:
  - Exit `0`
  - `18 passed in 0.24s`

## 3) Externer AC0011-Smoke

- Befehl:
  - `rm -rf /tmp/ic-batch-test && PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-batch-test --start AC0011 --end AC0011 --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `/tmp/ic-batch-test/converted_svgs/AC0011.svg` wurde erzeugt.
  - `/tmp/ic-batch-test/reports/batch_failure_summary.csv` enthält keinen
    `AC0011`-Fehlereintrag.

## 4) Repo-AC0011-Repro

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0011 --end AC0011 --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Während des Laufs wurde `artifacts/converted_images/converted_svgs/AC0011.svg`
    erzeugt und kein `AC0011`-Eintrag im Failure-Summary gefunden.
  - Die generierten Laufartefakte wurden nicht als Quelländerung übernommen; der
    Codepfad ist durch den Detailtest und den Repro-Befehl abgesichert.

## Fazit

Der nächste dokumentierte AC0011-Anschluss ist abarbeitbar: Die Finalisierung
ist nicht mehr an ein festes Repository-Output-Layout gekoppelt, externe
Einzelruns brechen nicht mehr mit `IndexError` ab, und der AC0011-Repro erzeugt
ein reguläres SVG statt eines Failure-Eintrags.
