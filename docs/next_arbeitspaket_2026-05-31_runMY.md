# Nächstes Arbeitspaket – Run MY (2026-05-31)

Dieses Arbeitspaket setzt nach Run MX die normale Plan-B-/Perception-Rotation fort
und arbeitet den nächsten dokumentierten Kandidaten `AC0233_S.jpg` vollständig ab.
Der Pflichtabschnitt „Perception-Lerneffekt“ bleibt Teil der Abnahme.

## 1) Nächste dokumentierte Aufgabe: AC0233-S als 180° gedrehte Top-Kelle mit `M`

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0233_S.jpg` als nächsten aktiven Kandidaten.
  - Die Beschreibung lautet: `Wie AC0231 ... Geometrische Variante: 180° gedreht`.
  - PF8 fordert für diesen Kandidaten, Kreis-/Kellen- und `M`-Signal vor der ersten Iteration abzusichern.
- Umsetzung:
  - Die Description-Geometry-IR erkennt AC0233 nun als `Rotated180TopKelleThreeWayValveGlyph` mit `label=M`.
  - Das neue Glyph nutzt dieselbe Ventil-Rendering-Strecke wie die bestehenden AC0231-/AC0232-/AC0224-Glyphs und rendert Body-Pfade, Connector, Kreis und Label in 180° gedrehter Lage.
  - Die Semantic-Badge-Heuristik wird für dieses Geometry-IR-Glyph unterdrückt, damit AC0233 nicht in den generischen `SEMANTIC: Kreis + Buchstabe`-Pfad fällt.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann die gedrehte `M`-Beschriftung oder die runde Kelle vorab als `TextGlyph`/`CircleBackground` dokumentiert werden?“
- Ergebnis im echten Repro:
  - `status=non_composite_perception_seeded_geometry_ir`
  - `geometry_ir_element_1=CircleBackground`
  - `geometry_ir_element_2=Rotated180TopKelleThreeWayValveGlyph`
  - `geometry_ir_element_3=HorizontalRule`
- Entscheidung:
  - `generalisiert`: Die Kreisform wird als Perception-Seed genutzt; das `M`-Label wird durch das beschreibungsgetriebene 180° gedrehte Top-Kellen-Glyph abgedeckt.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `91 passed`
- Befehl:
  - `rm -rf /tmp/ic-ac0233-runmy; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0233-runmy --start AC0233_S --end AC0233_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Element-Validation-Log enthält `status=non_composite_perception_seeded_geometry_ir`, `CircleBackground`, `Rotated180TopKelleThreeWayValveGlyph` und `HorizontalRule`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält nun `3` evaluierte Samples und `all_have_perception_lerneffekt=true`.

## 4) Kandidatenrotation

- `AC0233_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0838_M.jpg` ist nun die nächste reguläre Rotation.
- Der maschinenlesbare PF8-Linkage-Report wurde auf `AC0838_M`, `AC0881_M` und `AC0234_S` aktualisiert.

## 5) Fazit

Run MY schließt `AC0233_S.jpg` ab: Der Kandidat nutzt im echten Einzellauf einen
`CircleBackground`-Perception-Seed und ein explizites 180° gedrehtes
Top-Kellen-Glyph mit `M`-Label. Das nächste Arbeitspaket kann mit `AC0838_M.jpg`
oder den Folgepunkten `AC0881_M`/`AC0234_S` fortfahren.
