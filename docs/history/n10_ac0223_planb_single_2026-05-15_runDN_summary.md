# N10 – Plan-B-Einzelprobe für `AC0223_L_sia.svg` (Run DN, 2026-05-15)

## Ziel
- Die neu hinzugefügte Beispieldatei `artifacts/images_to_convert/samples/AC0223_L_sia.svg` in eine konkrete Plan-B-Aufgabe überführen.
- Zusätzlich den nächsten dokumentierten, leichtgewichtigen Umsetzungsschritt als isolierten Einzelrun ausführen (AC0223).

## Ausführung
- Primäraufgabe (Einzelrun):
  - `python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0223 --end AC0223`
- Log-Artefakt:
  - `artifacts/converted_images/reports/AC0223_single_2026-05-15_runDN.log`

## Ergebnis
- Prozess beendet mit Exit `0`.
- Damit liegt ein reproduzierbarer, kleiner AC0223-Referenzlauf vor, der als Baseline für Folgeschritte genutzt werden kann.

## Abgeleitete Plan-B-Aufgabe (gekoppelt)
- **N10-PB:** Synthetische Mini-Repro für AC0223 aus Textbeschreibung erzeugen
  (`description -> SVG -> JPG -> noise -> convert`) via
  `python -m tools.plan_b_synthetic_probe --variant AC0223 "Kelle mit links liegendem Griff und Label rF"`.
- Zweck: Falls der direkte AC0223-Pfad zukünftig blockiert, steht ein kleinerer, kontrollierter Repropfad mit identischer Varianten-ID zur Verfügung.

## Korrekturhinweis (Run DN2)
- Zusätzlich wurde der Einzelrun auf den korrekten Eingabepfad `artifacts/images_to_convert/nonconvertable` ausgeführt (Regel: immer auch `nonconvertable` prüfen).
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -m src.imageCompositeConverter artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0223 --end AC0223 --deterministic-order`
- Log-Artefakt: `artifacts/converted_images/reports/AC0223_single_nonconvertable_retry_2026-05-15_runDN2.log`
- Ergebnis: Exit `0` bei tatsächlichem Trefferpfad für `AC0223*` in `nonconvertable`.
