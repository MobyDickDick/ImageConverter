# Nächstes Arbeitspaket – Run ND (2026-05-31)

Dieses Arbeitspaket arbeitet nach Run NC den nächsten dokumentierten Plan-B-
Kandidaten `AC0820_S.jpg` ab. Der Kandidat war aktiv, weil das runde CO2-Badge
laut XML-Beschreibung ausdrücklich eine tiefgestellte `2` verlangt, während die
bisherige AC0820-Spezialisierung die Ziffer als Superscript gerendert hat.

## 1) Nächste dokumentierte Aufgabe: AC0820-S als tiefgestelltes CO2-Badge

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0820_S.jpg` als nächsten regulären
    Kandidaten.
  - Die Beschreibung lautet: `Text "CO^2" (Die 2 ist hochgestellt)`.
  - PF8 fordert für diesen Kandidaten, Kreis- und Label-Signal vor der ersten
    Iteration abzusichern.
- Umsetzung:
  - Die AC0820-Finalisierung rendert die Familie nun wieder mit
    `co2_index_mode=subscript` statt mit der AC0831/AC0833-artigen
    Superscript-Spezialisierung.
  - Superscript-spezifische Offset-/Gap-Parameter werden bei AC0820 entfernt;
    die spezialisierten Connector-Familien behalten ihre eigenen
    Superscript-Tuner.
  - Die Regressionstests für AC0820 prüfen jetzt explizit, dass die Ziffer
    unterhalb der CO-Baseline liegt.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann der dominante CO2-Kreis vorab als `CircleBackground` und das kurze
    Label als `TextGlyph`-Hinweis festgehalten werden?“
- Ergebnis:
  - `AC0820_S` wurde aus der aktiven Plan-B-Liste rotiert, weil die
    semantische CO2-Indexlage nun der dokumentierten XML-Beschreibung folgt.
  - Die aktive Liste enthält nun `AC0870_S`, `AC0850_M` und neu `AC0836_S` aus
    der AC08-Weak-Family-Rotation.
  - Der PF8-Linkage-Report wurde neu geschrieben und weist für alle drei
    aktiven Kandidaten eine `generalisiert`-Entscheidung mit
    `CircleBackground`-Seed aus.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0820-rund --start AC0820_S --end AC0820_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `conversion_bestlist.csv`: `error_per_pixel=0.13116049`,
    `mean_delta2=5785.013184`, `std_delta2=9320.757812`
  - Das SVG rendert `CO` und die `2` als getrennte Textknoten; die `2` liegt
    mit `y=9.9200` unterhalb der CO-Baseline `y=8.4800`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0870_S`, `AC0850_M` und `AC0836_S`, jeweils
    `decision=generalisiert`.
- Befehl:
  - `python -m pytest -q tests/test_plan_b_perception_linkage.py tests/test_image_composite_converter.py::test_finalize_ac0820_variant_name_keeps_default_anchor_mode tests/test_image_composite_converter.py::test_finalize_ac0820_m_enforces_lowered_index_placement tests/test_image_composite_converter.py::test_make_badge_params_ac0833_uses_superscript_index tests/test_image_composite_converter.py::test_finalize_ac0833_keeps_superscript_after_fit tests/test_image_composite_converter.py::test_co2_layout_keeps_subscript_inside_inner_circle_for_centered_badges tests/test_image_composite_converter.py::test_co2_layout_vertical_centering_ignores_subscript_for_main_text tests/test_image_composite_converter.py::test_co2_layout_keeps_subscript_inside_circle_without_changing_main_center tests/test_image_composite_converter.py::test_co2_layout_can_shrink_subscript_before_moving_co`
- Ergebnis:
  - Exit `0`
  - `10 passed`

## 4) Kandidatenrotation

- `AC0820_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0870_S.jpg` ist nun der nächste reguläre Kandidat.
- `AC0850_M.jpg` bleibt als Priorität-A-/Text-Grauwert-Kandidat aktiv.
- `AC0836_S.jpg` wurde als nächster AC08-Weak-Family-Kandidat ergänzt.

## 5) Fazit

Run ND schließt `AC0820_S.jpg` semantisch ab: AC0820 folgt nun dem
dokumentierten CO2-Subscript statt einem hochgestellten Connector-CO²-Stil, die
Regressionen sichern diese Familienentscheidung ab, und die Plan-B-/PF8-
Rotation ist auf `AC0870_S.jpg` weitergezogen. Der reine Pixel-Fehler bleibt
weiterhin ein Text-/Antialiasing-Folgeproblem und wird nicht als neuer Blocker
für die semantische Indexlage gewertet.
