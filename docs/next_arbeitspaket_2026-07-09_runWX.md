# Nächstes Arbeitspaket – GE1410_L Persistenz- und Seed-Check Run WX (2026-07-09)

Run WX rotiert nach Run VW auf den dokumentierten Plan-B-Kandidaten `GE1410_L`
und koppelt ihn mit einer Laufzeitprüfung der Konvertierungsdurchgänge. Anlass
war die Vermutung, dass zwischen Aufgaben nicht ausreichend gespeichert wird und
mehrere Konvertierungsdurchgänge möglicherweise identische Seed-Parameter nutzen.

## 1) Umsetzung

- Der Initialdurchlauf setzt vor jeder Datei einen eigenen `pass_seed_offset`
  anhand der Variantenposition. Damit bekommen mehrere Dateien innerhalb eines
  Batchs nicht mehr denselben effektiven Stochastic-Seed-Kontext.
- Qualitätsdurchgänge setzen vor jedem Kandidaten einen eindeutigen Offset nach
  dem Schema `pass * 100000 + candidate_index`. Dadurch unterscheiden sich
  wiederholte Nachbesserungsversuche auch dann, wenn sie dieselbe Variante erneut
  konvertieren.
- Nach jedem erfolgreich bewerteten Initial- oder Qualitätskandidaten wird ein
  `conversion_checkpoint.json` geschrieben und die wichtigsten resumierbaren
  Artefakte (`conversion_bestlist.csv`, `batch_failure_summary.csv`,
  `quality_tercile_passes.csv`) werden sofort aktualisiert. Ein abgebrochener
  langer Lauf verliert dadurch nicht mehr den gesamten Stand seit Batch-Start.

## 2) Perception-Lerneffekt

`GE1410_L` bleibt ein neutraler Fallback-/Geometry-IR-Fall mit Diagrammlinie,
Achsen, grauer Linie und farbigen Dreiecken. Run WX erweitert nicht die
Perception-Erkennung, sondern stabilisiert die Ausführungsparameter und die
Zwischenspeicherung für alle Plan-B-Konvertierungen katalogfrei.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_conversion_initial_pass_helpers.py tests/detailtests/test_conversion_quality_pass_helpers.py` läuft grün mit `11 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runWX --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; `GE1410_L` bleibt stabil bei `Fehler/Pixel=0.010179` und `Mean-Delta²=759.441589`.
- Der Checkpoint `/tmp/ic-ge1410-runWX/reports/conversion_checkpoint.json` weist den letzten Qualitätskandidaten mit `pass_seed_offset=200001`, `run_seed=0`, `processed_result_count=1`, `bestlist_count=1` und `batch_failure_count=0` aus.

## 4) Ergebnis / nächster Schritt

Run WX schließt den GE1410_L-Schritt mit einer allgemeinen Persistenz- und
Seed-Korrektur ab. Die verschiedenen Durchgänge verwenden nun sichtbar
unterschiedliche effektive Seed-Offsets, und der Zwischenstand wird nach jedem
abgeschlossenen Kandidaten auf Platte gespiegelt. Das nächste Arbeitspaket kann
wieder in der aktiven Plan-B-Rotation fortfahren oder gezielt prüfen, ob weitere
langen Batch-Artefakte ebenfalls frühzeitig gespiegelt werden sollen.
