# Nächstes Arbeitspaket – Run ML (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MK auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0214_S.jpg` und erweitert den beschreibungsgetriebenen
Geometry-IR-Pfad um die um 180° gedrehte 2-Wege-Ventil-Variante. Damit rendert
der echte Non-Composite-Call-Path die Beschreibung `Wie AC0212: ...
Geometrische Variante: 180° gedreht.` als strukturierte Vektorprimitive statt
als generisches Element-Fit-Symbol.

## 1) Nächste dokumentierte Aufgabe: AC0214-S-180°-2-Wege-Ventil als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0213_L.jpg` den nächsten Kandidaten
    `AC0214_S.jpg`.
  - Die XML-Beschreibung verweist auf AC0212, ergänzt aber die geometrische
    Variante `180° gedreht`; visuell liegt der Dreieckskörper rechts, der
    horizontale Griff führt zur linken Motorkelle mit `M`-Text.
- Umsetzung:
  - Die Geometry-IR erkennt AC0214-artige `2-Weg Ventil`-Beschreibungen mit
    `180° gedreht` nun als neues `Rotated180TwoWayValveMotorGlyph`.
  - Das Rendering zeichnet die stabilen Primitive
    `rotated_180_two_way_valve_motor_connector`,
    `rotated_180_two_way_valve_motor_body`,
    `rotated_180_two_way_valve_motor_circle` und
    `rotated_180_two_way_valve_motor_label` inklusive der bestehenden
    Ventil-Gradienten.
  - Die semantische Kreis+Buchstabe-Heuristik gibt auch diesen konkreten
    Geometry-IR-Fall frei, damit der echte Non-Composite-Fallback den
    `non_composite_description_geometry_ir`-Pfad wählt.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `67 passed in 0.72s`
- Abdeckung:
  - AC0214-artige Beschreibungen werden als
    `Rotated180TwoWayValveMotorGlyph` gemappt.
  - Das SVG-Rendering enthält stabile IDs für Body, Connector, Kreis und
    `M`-Label sowie die Ventil-Gradienten.
  - Der echte Non-Composite-Helfer wählt für `AC0214_S` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0214-S-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0214-runml; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0214-runml --start AC0214_S --end AC0214_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0214-runml/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=1` und `Rotated180TwoWayValveMotorGlyph`.
  - Das erzeugte SVG enthält die IDs `rotated_180_two_way_valve_motor_connector`,
    `rotated_180_two_way_valve_motor_body`,
    `rotated_180_two_way_valve_motor_circle` und
    `rotated_180_two_way_valve_motor_label`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `610 passed, 5 warnings in 4.55s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0214_S.jpg` auf
  `AC0221_S.jpg` rotiert und mit `AC0222_S.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0214_S.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit rechtem
2-Wege-Ventilkörper, horizontalem Connector, linker Kreis-Kelle und `M`-Label.
Die Kandidatenliste zeigt anschließend `AC0221_S.jpg` als nächste Rotation.
