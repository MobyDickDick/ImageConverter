# Nächstes Arbeitspaket – IDO-17 Vertikaler VOC-Ringfloor Run QY (2026-06-19)

## Ziel

Run QY setzt IDO-17 fort: Ein weiterer AC08-Spezialguard wird aus der Runtime-
Katalog-ID-Migration entfernt. Der Ring-Floor für vertikale VOC-Connector-Badges
wird nicht mehr über eine konkrete Bildfamilie ausgewählt, sondern über messbare
Badge-Merkmale aus Geometrie und Beschreibung.

## Umsetzung

- Der bisherige familienbezogene VOC-Radiusfloor wurde durch die generische
  Bedingung `vertical_text_connector_badge && text_mode == "voc"` ersetzt.
- `vertical_text_connector_badge` entsteht ausschließlich aus vorhandener
  Connector-Geometrie (`arm_enabled`, nahezu gleiche `arm_x1`/`arm_x2`) und
  Text-/Kreismerkmalen; der Template-Radius liefert die untere Ringgrenze.
- Die berechneten Floor-Werte werden nach dem allgemeinen Lock-Key-Cleanup für
  diese Geometrieklasse wieder in die finalisierten Parameter übernommen.
- Ein neutraler Test mit katalogfremdem Namen `AC08XX_VERTICAL_VOC` sichert, dass
  der Ring-Floor über Geometrie statt über eine konkrete Bild-ID entsteht.
- Die Legacy-Ratchet-Baseline wurde nach Entfernen des Familienguards und der
  ID-haltigen Runtime-Kommentare von 328 auf 324 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/test_image_composite_converter.py && pytest -q tests/test_image_composite_converter.py::test_finalize_ac08_style_applies_vertical_voc_radius_floor_without_catalog_id tests/test_image_composite_converter.py::test_validate_badge_by_elements_runs_ac0838_phase2_unlock_and_relock && python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Exit `0`; `2 passed`, der Ratchet meldet `324 legacy occurrences remain`.

## 5-Zeilen-Log

- **Getestet:** Compileall, gezielte vertikale VOC-/AC0838-Regressionen und Hardcoding-Ratchet.
- **Ergebnis:** Exit `0`; `2 passed`, Ratchet jetzt `324`.
- **Blocker:** IDO-17 bleibt offen; weitere Runtime-Katalog-IDs sind noch vorhanden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und den geometriebasierten VOC-Ringfloor.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere kleine Finalisierungs-/Validierungsguards auf messbare Strukturparameter umstellen.
