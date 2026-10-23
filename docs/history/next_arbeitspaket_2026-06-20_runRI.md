# Nächstes Arbeitspaket – IDO-17 Centered-Circle-Text-Family-Entkopplung Run RI (2026-06-20)

## Ziel

Run RI setzt IDO-17 fort: Der connectorfreie AC08-Kreis-/Text-Badge-Tuningpfad
wird nicht mehr über konkrete Katalog-IDs ausgewählt, sondern über neutrale
Connector- und Text-/Geometrieparameter.

## Umsetzung

- `tuneAc08CircleTextFamilyImpl(...)` prüft keine konkrete AC08-ID-Liste mehr.
  Der Pfad greift nun bei `connector_direction=centered|none`,
  `connector_policy=forbid`, `suppress_stale_connector_geometry` oder bei
  sichtbarer Kreis+Text-Geometrie ohne Arm-/Stem-Evidenz.
- Die CO₂-Sondervorgabe hängt nicht länger an einem Symbolnamen, sondern am
  neutralen Metadatum `co2_index_mode=subscript`.
- Der Detailtest verwendet den neutralen Symbolnamen
  `NEUTRAL_CENTERED_TEXT_BADGE` und sichert die VOC-Grenzen über
  `connector_policy=forbid` und `draw_text=True` ohne Katalog-ID ab.
- Die Legacy-Ratchet-Baseline sinkt nach Entfernung der centered Circle/Text-
  Familienliste und bereits neutralisierter stale Baseline-Einträge von 281 auf
  273 Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src/iCCModules/imageCompositeConverterSemanticAc08Families.py tests/detailtests/test_semantic_ac08_family_helpers.py
pytest -q tests/detailtests/test_semantic_ac08_family_helpers.py
python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Exit `0`; der Detailtest läuft mit `5 passed`, und der Ratchet meldet
`273 legacy occurrences remain`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Detailtests für AC08-Family-Helper und Hardcoding-Ratchet.
- **Ergebnis:** Exit `0`; `5 passed`, Ratchet jetzt `273`.
- **Blocker:** IDO-17 ist weiterhin nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in horizontalen, Text-, Transfer- und Diagnosepfaden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und die parameterbasierte centered Circle/Text-Auswahl.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Family-/Finalisierungs-/SVG-/Optimierungs-Guards in struktur- oder beschreibungsgesteuerte Parameter überführen.
