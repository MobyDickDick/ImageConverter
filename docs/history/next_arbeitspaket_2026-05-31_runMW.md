# Nächstes Arbeitspaket – Run MW (2026-05-31)

Dieses Arbeitspaket setzt nach Run MV die normale Plan-B-Rotation fort und
arbeitet den nächsten dokumentierten Kandidaten `AC0231_S.jpg` vollständig ab.
Der Pflichtabschnitt „Perception-Lerneffekt“ wird erneut konkret genutzt.

## 1) Nächste dokumentierte Aufgabe: AC0231-S als Top-Kelle mit senkrechtem `M`

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0231_S.jpg` als nächsten aktiven Kandidaten.
  - Die Beschreibung lautet: `3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, "M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten ...`.
  - PF8 fordert für diesen Kandidaten, die obere `M`-Kelle über Label- oder Kreis-Signal vor der ersten Iteration abzusichern.
- Umsetzung:
  - Die Description-Geometry-IR erkennt AC0231 nun als `TopKelleThreeWayValveGlyph` mit `label=M`.
  - Das bestehende AC0221-Top-Kellen-Glyph bleibt unverändert als gleiche Geometrie ohne Label erhalten.
  - Der Renderer gibt für AC0231 zusätzlich `top_kelle_three_way_valve_label` aus und verwendet eine kleinere, auf den oberen Kreis zentrierte Schriftgröße.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann die obere `M`-Beschriftung oder die runde Kelle vorab als `TextGlyph`/`CircleBackground` dokumentiert werden?“
- Ergebnis im echten Repro:
  - `status=non_composite_perception_seeded_geometry_ir`
  - `geometry_ir_element_1=CircleBackground`
  - `geometry_ir_element_2=TopKelleThreeWayValveGlyph`
- Entscheidung:
  - `generalisiert`: Die Kreisform wird als Perception-Seed genutzt; die `M`-Beschriftung wird durch das beschreibungsgetriebene Top-Kellen-Glyph abgedeckt und bleibt im PF8-Linkage als TextGlyph-Hinweis dokumentiert.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `83 passed`
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_plan_b_perception_linkage.py`
- Ergebnis:
  - Exit `0`
  - `2 passed`
- Befehl:
  - `rm -rf /tmp/ic-ac0231-runmw; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0231-runmw --start AC0231_S --end AC0231_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Element-Validation-Log enthält `status=non_composite_perception_seeded_geometry_ir`, `CircleBackground` und `TopKelleThreeWayValveGlyph`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält weiter `4` evaluierte Samples und `all_have_perception_lerneffekt=true`.

## 4) Kandidatenrotation

- `AC0231_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0232_S.jpg` ist nun die nächste reguläre Rotation.
- `AC0233_S.jpg` wurde als weiterer AC02-Folgekandidat ergänzt und erhält bereits einen eigenen Perception-Lerneffekt-Eintrag.
- Der maschinenlesbare PF8-Linkage-Report wurde auf `AC0232_S`, `AC0233_S`, `AC0838_M` und `AC0881_M` aktualisiert.

## 5) Fazit

Run MW schließt `AC0231_S.jpg` ab: Der Kandidat fällt nicht mehr in den generischen
Kreis-/Buchstaben-Pfad zurück, sondern nutzt einen `CircleBackground`-Perception-Seed
und ein explizites Top-Kellen-Glyph mit `M`-Label. Das nächste Arbeitspaket kann mit
`AC0232_S.jpg` oder einem QR-Folgepunkt (`AC0838_M`/`AC0881_M`) fortfahren.
