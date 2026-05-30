# Nächstes Arbeitspaket – Run MM (2026-05-30)

Dieses Arbeitspaket rotiert nach Run ML auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0221_S.jpg` und erweitert den beschreibungsgetriebenen
Geometry-IR-Pfad um das 3-Wege-Ventil mit oberer Kelle ohne `M`-Text. Damit
rendert der echte Non-Composite-Call-Path die Beschreibung `Wie AC0231, jedoch
ohne "M" in der Kelle oben.` als strukturierte Vektorprimitive statt als
generisches Element-Fit-Symbol.

## 1) Nächste dokumentierte Aufgabe: AC0221-S-3-Wege-Ventil ohne M als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` benennt nach `AC0214_S.jpg` den nächsten Kandidaten
    `AC0221_S.jpg`.
  - Die XML-Beschreibung verweist auf AC0231, entfernt aber das `M` in der
    oberen Kelle; visuell liegt die Kreis-Kelle oben, darunter ein vertikaler
    Griff zum dreiflügeligen Ventilkörper.
- Umsetzung:
  - Die Geometry-IR erkennt AC0221-artige `AC0231`-/`3-Weg Ventil`-Beschreibungen
    mit `ohne "M"` und oberer Kelle nun als neues
    `TopKelleThreeWayValveGlyph`.
  - Das Rendering zeichnet die stabilen Primitive
    `top_kelle_three_way_valve_connector`,
    `top_kelle_three_way_valve_body_1`, `top_kelle_three_way_valve_body_2`,
    `top_kelle_three_way_valve_body_3` und
    `top_kelle_three_way_valve_circle` inklusive der bestehenden
    Ventil-Gradienten, aber bewusst ohne Label-Primitive.
  - Die semantische Kreis+Buchstabe-Heuristik und der echte
    Non-Composite-Fallback geben diesen konkreten Geometry-IR-Fall frei, damit
    `non_composite_description_geometry_ir` gewählt wird.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `71 passed in 0.41s`
- Abdeckung:
  - AC0221-artige Beschreibungen werden als `TopKelleThreeWayValveGlyph`
    gemappt.
  - Das SVG-Rendering enthält stabile IDs für die drei Body-Flügel, Connector
    und Kreis sowie die Ventil-Gradienten, jedoch kein `M`-Label.
  - Der echte Non-Composite-Helfer wählt für `AC0221_S` den
    `non_composite_description_geometry_ir`-Pfad.

## 3) AC0221-S-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0221-runmm; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0221-runmm --start AC0221_S --end AC0221_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Kein Failure-Eintrag in `/tmp/ic-ac0221-runmm/reports/batch_failure_summary.csv`.
  - Element-Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=1` und `TopKelleThreeWayValveGlyph`.
  - Das erzeugte SVG enthält die IDs `top_kelle_three_way_valve_connector`,
    `top_kelle_three_way_valve_body_1`, `top_kelle_three_way_valve_body_2`,
    `top_kelle_three_way_valve_body_3` und `top_kelle_three_way_valve_circle`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `614 passed, 5 warnings in 6.55s`

## 5) Kandidatenrotation

- `PLAN_B_KANDIDATEN.md` wurde nach erledigtem `AC0221_S.jpg` auf
  `AC0222_S.jpg` rotiert und mit `AC0224_S.jpg` als weiterem AC02-Kandidaten
  aufgefüllt.

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0221_S.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit oberer Kreis-Kelle,
vertikalem Connector und dreiflügeligem Ventilkörper ohne `M`-Text. Die
Kandidatenliste zeigt anschließend `AC0222_S.jpg` als nächste Rotation.
