# Nächstes Arbeitspaket – IDO-13 Text-/Glyph-Evidenz und Textlagen Run QN (2026-06-18)

## Ziel

Run QN setzt den nach Run QM dokumentierten IDO-13-Anschluss fort: Kreis-/Text-
Badges sollen neben dem Labelinhalt auch explizite Text-/Glyph-Evidenz und
Lageformulierungen ohne Bild-ID-Dispatch in der Geometry-IR tragen.

## Umsetzung

- Die Kreis-Badge-Erkennung normalisiert Labeltexte jetzt über einen gemeinsamen
  Label-Normalisierungspfad und erkennt zusätzlich Formulierungen wie `T oben im
  Kreis`.
- Text-Glyphen erhalten maschinenlesbare `glyph_evidence` mit Quelle,
  normalisiertem Text und erkannter Lage.
- Zentrierte Labels behalten die Relation `centered_in`; nicht-zentrierte Labels
  werden über lagebezogene Relationen wie `top_inside` sowie einen normierten
  `text_anchor` beschrieben.
- Die Erweiterung bleibt dateinamen-/katalogfrei und verändert die Legacy-
  Hardcoding-Baseline nicht.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `368 legacy occurrences remain`, und der
gezielte Beschreibung-/Semantik-Testblock läuft mit `50 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-Regressionen.
- **Ergebnis:** Exit `0`; `50 passed` im gezielten Testblock.
- **Blocker:** Kein neuer technischer Blocker; echte Raster-/Perception-Glyph-Detektion bleibt ein Folgeausbau.
- **Dokumentation:** Kreis-/Text-Badges tragen jetzt Label-Evidenz und Lage-Constraints statt nur zentrierter Textannahmen.
- **Nächster Schritt:** IDO-14 starten und die generische Badge-IR an Perception-Glyph-/OCR-Signale sowie Render-Parameter-Kalibrierung koppeln.
