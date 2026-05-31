# Nächstes Arbeitspaket – Run MV (2026-05-31)

Dieses Arbeitspaket setzt nach PF8 die normale Plan-B-Rotation fort und arbeitet
den nächsten dokumentierten Kandidaten `AC0224_S.jpg` vollständig ab. Der neue
Pflichtabschnitt „Perception-Lerneffekt“ wird dabei konkret genutzt.

## 1) Nächste dokumentierte Aufgabe: AC0224-S als rechts gedrehte Top-Kelle

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0224_S.jpg` als nächsten aktiven Kandidaten.
  - Die Beschreibung lautet: `Wie AC0221 ... Geometrische Variante: 90° nach rechts gedreht`.
  - PF8 fordert für diesen Kandidaten die Kreis-/Kellen-Erkennung vor der ersten Iteration.
- Umsetzung:
  - Die Description-Geometry-IR erkennt die rechts gedrehte AC0221-/AC0231-Variante als
    `RightRotatedTopKelleThreeWayValveGlyph`.
  - Der vorhandene Ventil-/Kellen-Renderer kann dieses neue Glyph über dieselben
    Gradienten, Body-Path-, Kreis- und Connector-Primitive ausgeben.
  - Die Semantic-Badge-Heuristik wird für dieses Geometry-IR-Glyph unterdrückt, damit
    AC0224 nicht mehr in den generischen `SEMANTIC: Kreis + Buchstabe`-Pfad fällt.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann die runde Kellen-/Kreisform vor der ersten Iteration als `CircleBackground` erkannt werden?“
- Ergebnis im echten Repro:
  - `status=non_composite_perception_seeded_geometry_ir`
  - `geometry_ir_element_1=CircleBackground`
  - `geometry_ir_element_2=RightRotatedTopKelleThreeWayValveGlyph`
  - `geometry_ir_element_3=HorizontalRule`
- Entscheidung:
  - `generalisiert`: Die Kreisform wird tatsächlich als Perception-Seed genutzt; das neue
    rechts gedrehte Kellen-Glyph deckt die beschreibungsgetriebene Symbolstruktur ab.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `80 passed`
- Befehl:
  - `rm -rf /tmp/ic-ac0224-runmv; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0224-runmv --start AC0224_S --end AC0224_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Element-Validation-Log enthält `status=non_composite_perception_seeded_geometry_ir`,
    `CircleBackground` und `RightRotatedTopKelleThreeWayValveGlyph`.

## 4) Kandidatenrotation

- `AC0224_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0231_S.jpg` ist nun die nächste reguläre Rotation.
- `AC0232_S.jpg` wurde als weiterer AC02-Folgekandidat ergänzt und erhält bereits einen
  eigenen Perception-Lerneffekt-Eintrag.

## 5) Fazit

Run MV schließt `AC0224_S.jpg` ab: Der Kandidat fällt nicht mehr in den generischen
Kreis-/Buchstaben-Pfad zurück, sondern nutzt Perception-Seeds und ein explizites
rechts gedrehtes Top-Kellen-Glyph. Das nächste Arbeitspaket kann mit `AC0231_S.jpg`
oder einem QR-Folgepunkt (`AC0838_M`/`AC0881_M`) fortfahren.
