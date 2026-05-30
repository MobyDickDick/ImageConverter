# Nächstes Arbeitspaket – Run MK (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MJ auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0213_L.jpg` und erweitert den beschreibungsgetriebenen
Geometry-IR-Pfad um die um 90° nach links gedrehte 2-Wege-Ventil-Variante.
Damit rendert der echte Non-Composite-Call-Path die Beschreibung `Wie AC0212: ...
Geometrische Variante: 90° nach links gedreht.` als strukturierte
Vektorprimitive statt als generisches Element-Fit-Symbol.

## 1) Nächste dokumentierte Aufgabe: AC0213-L-rotiertes 2-Wege-Ventil als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0212_L.jpg` den nächsten Kandidaten
    `AC0213_L.jpg`.
  - Die XML-Beschreibung verweist auf AC0212, ergänzt aber die geometrische
    Variante `90° nach links gedreht`; visuell liegt der Dreieckskörper oben,
    der vertikale Griff führt zur unteren Motorkelle mit `M`-Text.
- Umsetzung:
  - Die Geometry-IR erkennt AC0213-artige `2-Weg Ventil`-Beschreibungen mit
    `90° nach links gedreht` nun als neues `LeftRotatedTwoWayValveMotorGlyph`.
  - Das Rendering zeichnet die stabilen Primitive
    `left_rotated_two_way_valve_motor_connector`,
    `left_rotated_two_way_valve_motor_body`,
    `left_rotated_two_way_valve_motor_circle` und
    `left_rotated_two_way_valve_motor_label` inklusive der bestehenden
    Ventil-Gradienten.
  - Die semantische Kreis+Buchstabe-Heuristik gibt auch diesen konkreten
    Geometry-IR-Fall frei, damit der echte Non-Composite-Fallback den
    `non_composite_description_geometry_ir`-Pfad wählt.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `63 passed in 0.42s`
- Abdeckung:
  - AC0213-artige Beschreibungen werden als
    `LeftRotatedTwoWayValveMotorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für Body, Connector, Kreis und
    `M`-Label sowie die Ventil-Gradienten.
  - Der echte Non-Composite-Helfer wählt für `AC0213_L` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0213-L-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0213-runmk; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0213-runmk --start AC0213_L --end AC0213_L --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0213-runmk/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=1` und `LeftRotatedTwoWayValveMotorGlyph`.
  - Das erzeugte SVG enthält die IDs `left_rotated_two_way_valve_motor_connector`,
    `left_rotated_two_way_valve_motor_body`,
    `left_rotated_two_way_valve_motor_circle` und
    `left_rotated_two_way_valve_motor_label`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `606 passed, 5 warnings in 4.38s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0213_L.jpg` auf
  `AC0214_S.jpg` rotiert und mit `AC0221_S.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0213_L.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit oberem
2-Wege-Ventilkörper, vertikalem Connector, unterer Kreis-Kelle und `M`-Label.
Die Kandidatenliste zeigt anschließend `AC0214_S.jpg` als nächste Rotation.
