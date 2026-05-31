# Nächstes Arbeitspaket – Run NC (2026-05-31)

Dieses Arbeitspaket arbeitet nach Run NB den nächsten dokumentierten Plan-B-
Kandidaten `AC0835_S.jpg` ab. Der Kandidat war aktiv, weil das runde `VOC`-
Badge laut XML ausdrücklich keinen Griff besitzt, der bisherige AC0835-
Startpfad aber noch aus der rechten VOC-Connector-Familie kam.

## 1) Nächste dokumentierte Aufgabe: AC0835-S als grifflose VOC-Kreis/Text-Form

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0835_S.jpg` als nächsten regulären
    Kandidaten.
  - Die Beschreibung lautet: `Grauer Kreis ... Text im Kreis: "VOC". Kein Griff,
    keine Kelle und keine weiteren Anbauteile.`
  - PF8 fordert für diesen Kandidaten, Kreis- und Label-Signal vor der ersten
    Iteration abzusichern.
- Umsetzung:
  - `makeAc08BadgeParamsImpl` behandelt `AC0835` nun als connectorfreie
    Kreis/Text-Familie auf Basis des AC0870-Plain-Circle-Defaults.
  - Die bildbasierte Initialisierung nutzt für AC0835 jetzt den generischen
    Kreis/Text-Fit statt des AC0814-Rechtsarm-Fits; AC0836/AC0839 bleiben die
    expliziten VOC-Connector-Folgeformen.
  - `applyVocLabelImpl` setzt zusätzlich zum `text_mode=voc` das semantische
    Label `VOC`, damit Default-, Test- und Rendering-Metadaten konsistent sind.
  - Der Regressionstest für AC0835 prüft nun explizit, dass weder `arm_enabled`
    noch `stem_enabled` gesetzt sind.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann der dominante VOC-Kreis vorab als `CircleBackground` und das Label als
    `TextGlyph`-Hinweis festgehalten werden?“
- Ergebnis:
  - `AC0835_S` wurde aus der aktiven Plan-B-Liste rotiert, weil die semantische
    Familienzuordnung nun der XML-Beschreibung entspricht und der Einzellauf
    grifflose SVG-Geometrie erzeugt.
  - Die aktive Liste enthält nun `AC0820_S`, `AC0870_S` und neu `AC0850_M` aus
    der AC08-Weak-Family-Rotation.
  - Der PF8-Linkage-Report wurde neu geschrieben und weist für alle drei aktiven
    Badge-Kandidaten eine `generalisiert`-Entscheidung mit `CircleBackground`-
    Seed aus.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0835-runnc2 --start AC0835_S --end AC0835_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `conversion_bestlist.csv`: `error_per_pixel=0.13673086`,
    `mean_delta2=6717.546875`, `std_delta2=12115.065430`
  - Das SVG enthält nur `circle` und `text`; das Element-Validation-Log meldet
    `small_variant_mode_active` mit `arm_min_ratio=0.000` und
    `stem_min_ratio=0.000`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0820_S`, `AC0870_S` und `AC0850_M`, jeweils
    `decision=generalisiert`.
- Befehl:
  - `python -m pytest -q tests/test_image_composite_converter.py::test_make_badge_params_ac0835_uses_plain_voc_circle_geometry tests/test_image_composite_converter.py::test_tune_ac0835_voc_badge_lowers_tiny_variant_text tests/test_image_composite_converter.py::test_finalize_ac08_style_leaves_ac0835_s_voc_unbounded tests/detailtests/test_semantic_ac08_family_helpers.py::test_tune_circle_text_family_applies_voc_bounds_for_small_badges tests/test_plan_b_perception_linkage.py`
- Ergebnis:
  - Exit `0`
  - `6 passed`

## 4) Kandidatenrotation

- `AC0835_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0820_S.jpg` ist nun der nächste reguläre Kandidat.
- `AC0870_S.jpg` bleibt als Priorität-A-Weak-Family-Kandidat aktiv.
- `AC0850_M.jpg` wurde als nächster AC08-Weak-Family-Kandidat ergänzt.

## 5) Fazit

Run NC schließt `AC0835_S.jpg` semantisch ab: Die VOC-Plain-Circle-Familie ist
nicht länger versehentlich mit einer rechten Connector-Geometrie gekoppelt, die
PF8-Kopplung wurde auf die nächsten aktiven Badge-Kandidaten rotiert, und die
gezielten Regressionstests sichern die grifflose AC0835-Form ab.
