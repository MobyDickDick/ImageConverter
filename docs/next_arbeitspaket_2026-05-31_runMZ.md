# Nächstes Arbeitspaket – Run MZ (2026-05-31)

Dieses Arbeitspaket setzt nach Run MY die normale Plan-B-/Perception-Rotation fort
und prüft den nächsten dokumentierten Kandidaten `AC0838_M.jpg` vollständig gegen
den Qualitätsreview-Befund. Der Pflichtabschnitt „Perception-Lerneffekt“ bleibt
Teil der Abnahme, wird hier aber als Review-/Re-Konvertierungsnachweis genutzt,
weil der vorhandene semantische VOC-Pfad inzwischen unter der Review-Grenze liegt.

## 1) Nächste dokumentierte Aufgabe: AC0838-M als VOC-Kreis mit oberem Griff

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0838_M.jpg` als nächsten aktiven Kandidaten.
  - Der ursprüngliche Qualitätsreview-Befund lag bei `normalized_mse=0.04729276`
    und damit oberhalb der damaligen Review-Grenze.
  - PF8 forderte für diesen Kandidaten, den dominanten VOC-Kreis und ein mögliches
    Label-Signal vor der ersten Iteration festzuhalten.
- Umsetzung / Befund:
  - Der echte Einzellauf über `artifacts/images_to_convert/nonconvertable` findet
    `AC0838_M.jpg` und bleibt im bestehenden semantischen Badge-Pfad.
  - Die erkannte Beschreibung lautet weiterhin `SEMANTIC: senkrechter Strich oben vom Kreis`
    plus `SEMANTIC: Kreis + Buchstabe VOC`.
  - Die aktuelle Konvertierung erreicht `error_per_pixel=0.04151429` und liegt damit
    unter dem dokumentierten Review-Grenzwert `0.045945679012345676`; der frühere
    Plan-B-Qualitätsbefund ist für `AC0838_M.jpg` dadurch nicht mehr aktiv.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann der dominante VOC-Kreis vorab als `CircleBackground` und Label-Signal festgehalten werden?“
- Ergebnis im echten Repro:
  - Element-Validation-Status: `semantic_ok`
  - Semantik: `SEMANTIC: senkrechter Strich oben vom Kreis`, `SEMANTIC: Kreis + Buchstabe VOC`
  - Bestlist: `error_per_pixel=0.04151429`, `mean_delta2=7789.174316`
- Entscheidung:
  - `generalisiert`: Der PF8-Linkage-Report erkennt weiterhin ein Kreis-Signal als
    `CircleBackground`-Seed; für den produktiven AC0838-M-Lauf reicht der vorhandene
    semantische VOC-Pfad bereits unter die Review-Grenze. Der Kandidat wird deshalb
    aus der aktiven Plan-B-Liste rotiert, ohne einen weiteren Sonder-Glyph zu erzwingen.

## 3) Sichernde Tests und Checks

- Befehl:
  - `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_plan_b_perception_linkage.py tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
- Ergebnis:
  - Exit `0`
  - `3 passed`
- Befehl:
  - `rm -rf /tmp/ic-ac0838-runmz; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --output-dir /tmp/ic-ac0838-runmz --start AC0838_M --end AC0838_M --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Element-Validation-Log enthält `status=semantic_ok`.
  - Bestlist enthält `error_per_pixel=0.04151429`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält nun `2` evaluierte Samples und `all_have_perception_lerneffekt=true`.

## 4) Kandidatenrotation

- `AC0838_M.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0881_M.jpg` ist nun die nächste reguläre Rotation.
- `AC0234_S.jpg` bleibt als AC02-Folgekandidat mit eigenem Perception-Lerneffekt erhalten.
- Der maschinenlesbare PF8-Linkage-Report wurde auf `AC0881_M` und `AC0234_S` aktualisiert.

## 5) Fazit

Run MZ schließt `AC0838_M.jpg` als aktiven Plan-B-Kandidaten ab: Der vormals
auffällige VOC-Kreis-Kandidat rendert im aktuellen isolierten Lauf wieder unter der
Review-Grenze und behält zugleich einen dokumentierten `CircleBackground`-Lerneffekt
im PF8-Kontext. Das nächste Arbeitspaket kann mit `AC0881_M.jpg` oder dem
Folgekandidaten `AC0234_S.jpg` fortfahren.
