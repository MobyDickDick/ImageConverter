# Nächstes Arbeitspaket – IDO-08 Generische Fusionslogik Run QB (2026-06-16)

## Ziel

Run QB bearbeitet das nächste offene Arbeitspaket aus
`docs/image_description_only_tasks.md`: **IDO-08 – Generische Fusionslogik
implementieren**. Beschreibungs-Constraints und Bildkandidaten sollen ohne
Katalog- oder Bild-ID über gewichtete Kosten zusammengeführt werden.

## Umsetzung

- `fuse_description_constraints_with_perception_candidates(...)` erzeugt den
  katalogfreien Vertrag `description_perception_fusion_v1`.
- Die Fusion bewertet primitive Kompatibilität, Candidate-Confidence und – wenn
  vorhanden – normalisierte Bounding-Box-Überlappung.
- Der maschinenlesbare Entscheidungs-Trace unterscheidet erfolgreiche Matches,
  fehlende Bildevidenz, widersprüchliche Evidenz und mehrere plausible
  Kandidaten.
- Nicht gematchte Bildkandidaten werden weiterhin über die vorhandene
  Perception-IR-Abbildung als zusätzliche Seeds in die Geometry-IR übernommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tools tests/test_description_perception_fusion.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/test_description_perception_fusion.py tests/test_perception_geometry_ir_roundtrip.py tests/test_perception_detection_contract.py tests/test_perception_seeded_geometry_ir.py
```

Ergebnis: Exit `0`; der Ratchet bleibt auf der bestehenden Legacy-Baseline, und
der gezielte IDO-07/IDO-08-Testblock läuft mit `17 passed`.

## 5-Zeilen-Log

- **Getestet:** Fusion für Übereinstimmung, fehlende Bildevidenz, Widerspruch und Ambiguität.
- **Ergebnis:** Exit `0`; `17 passed` im gezielten Perception-/Fusion-Testblock.
- **Blocker:** Kein neuer Blocker; IDO-09 bleibt als nächster Unsicherheitsvertrag offen.
- **Dokumentation:** IDO-08 ist in `docs/image_description_only_tasks.md` abgeschlossen und dieser Run hält den Nachweis fest.
- **Nächster Schritt:** IDO-09 umsetzen: Review-/Unsicherheitsstatus für unzureichende oder widersprüchliche Evidenz verbindlich definieren.
