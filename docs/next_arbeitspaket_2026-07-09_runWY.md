# Nächstes Arbeitspaket – Batch-Checkpoint Result-Map-Spiegelung Run WY (2026-07-09)

Run WY setzt den nach Run WX dokumentierten Persistenz-Folgepunkt um: Neben den
bereits früh geschriebenen CSV-/Report-Artefakten wird nun auch der aktuelle
`result_map`-Stand nach jedem abgeschlossenen Initial- oder Qualitätskandidaten
maschinell gespiegelt. Damit kann ein abgebrochener längerer Batch nicht nur die
Bestliste und Fehlerzusammenfassung, sondern auch die aktuell verarbeiteten
Varianten direkt aus einem JSON-Snapshot nachvollziehen.

## 1) Umsetzung

- Der inkrementelle Checkpoint schreibt zusätzlich
  `reports/conversion_result_map.json` mit der vollständigen aktuellen
  `result_map`.
- `reports/conversion_checkpoint.json` enthält das neue Feld
  `result_map_path`, sodass der Snapshot vom Checkpoint aus eindeutig auffindbar
  ist.
- Die Änderung ist katalogfrei und hängt nicht an einer Bild-ID; sie greift für
  Initial- und Quality-Pass-Checkpoints gleichermaßen.

## 2) Perception-Lerneffekt

Run WY erweitert keine Perception-Erkennung. Der Lerneffekt bleibt operativ:
Plan-B- und lange Batch-Läufe sind nach einem Abbruch besser auditierbar, weil
Zwischenstände der Kandidatenergebnisse nicht erst am finalen Laufende in einem
impliziten Python-Zustand verbleiben.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_conversion_initial_pass_helpers.py tests/detailtests/test_conversion_quality_pass_helpers.py` läuft grün mit `11 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runWY --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte GE1410_L-Einzellauf erzeugt neben `conversion_checkpoint.json` auch `conversion_result_map.json`.

## 4) Ergebnis / nächster Schritt

Run WY schließt den zusätzlichen Persistenz-Folgepunkt ab. Checkpoint und
Result-Map-Snapshot werden nun synchron geschrieben; weitere Arbeitspakete
können wieder in der aktiven Plan-B-Rotation fortfahren oder zusätzliche
Resume-Reader auf Basis dieses Snapshots ergänzen.
