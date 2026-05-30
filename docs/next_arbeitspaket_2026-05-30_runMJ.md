# Nächstes Arbeitspaket – Run MJ (2026-05-30)

Dieses Arbeitspaket rotiert nach Run MI auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0212_L.jpg` und erweitert den beschreibungsgetriebenen
Geometry-IR-Pfad um das vertikale 2-Wege-Ventil mit rechter Motorkelle. Damit
rendert der echte Non-Composite-Call-Path die Beschreibung `2-Weg Ventil
vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, "M" als Text
(M = Motor), zwei spitze Dreiecke ...` als strukturierte Vektorprimitive statt
als generisches Element-Fit-Symbol.

## 1) Nächste dokumentierte Aufgabe: AC0212-L-2-Wege-Ventil als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0211_S.jpg` den nächsten Kandidaten
    `AC0212_L.jpg`.
  - Die XML-Beschreibung nennt eine Kelle mit Kreis rechts, horizontaler
    Verbindungslinie, `M`-Text und zwei mittig berührenden Dreiecken mit grauer
    Umrandung und diagonalem Hell-Dunkel-Verlauf.
- Umsetzung:
  - Die Geometry-IR erkennt AC0212-artige `2-Weg Ventil vertikal`-Beschreibungen
    als neues `VerticalTwoWayValveMotorGlyph`.
  - Das Rendering zeichnet die stabile Primitive
    `vertical_two_way_valve_motor_connector`,
    `vertical_two_way_valve_motor_body`, `vertical_two_way_valve_motor_circle`
    und `vertical_two_way_valve_motor_label` inklusive Body-/Circle-Gradienten.
  - Die semantische Kreis+Buchstabe-Heuristik gibt diesen konkreten
    Geometry-IR-Fall frei, damit der echte Non-Composite-Fallback den
    `non_composite_description_geometry_ir`-Pfad wählt.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `59 passed in 0.36s`
- Abdeckung:
  - AC0212-artige Beschreibungen werden als `VerticalTwoWayValveMotorGlyph`
    gemappt.
  - Das SVG-Rendering enthält stabile IDs für Body, Connector, Kreis und
    `M`-Label sowie die Ventil-Gradienten.
  - Der echte Non-Composite-Helfer wählt für `AC0212_L` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0212-L-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0212-runmj; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0212-runmj --start AC0212_L --end AC0212_L --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0212-runmj/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=1` und `VerticalTwoWayValveMotorGlyph`.
  - Das erzeugte SVG enthält die IDs `vertical_two_way_valve_motor_connector`,
    `vertical_two_way_valve_motor_body`, `vertical_two_way_valve_motor_circle`
    und `vertical_two_way_valve_motor_label`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `602 passed, 5 warnings in 6.07s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0212_L.jpg` auf
  `AC0213_L.jpg` rotiert und mit `AC0214_S.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0212_L.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit explizitem
2-Wege-Ventilkörper, horizontalem Connector, rechter Kreis-Kelle und `M`-Label.
Die Kandidatenliste zeigt anschließend `AC0213_L.jpg` als nächste Rotation.
