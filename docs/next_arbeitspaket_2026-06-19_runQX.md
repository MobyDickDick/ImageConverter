# Nächstes Arbeitspaket – IDO-17 Plain-Left-Arm-Global-Search-Entkopplung Run QX (2026-06-19)

## Ziel

Run QX setzt das nächste kleine IDO-17-Paket aus
`docs/image_description_only_tasks.md` fort: Ein weiterer AC08-Runtime-Guard wird
von einer konkreten Katalog-ID auf messbare Badge-Geometrie umgestellt.

## Umsetzung

- `finalizeAc08StyleImpl(...)` deaktiviert den teuren Global-Search-Sampler für
  einfache linke Kreis-Arm-Badges nicht mehr über `AC0812`, sondern über
  Parameter: aktivierter Arm, kein Text und linke Anschlussrichtung bzw. eine
  aus den Arm-/Kreis-Koordinaten ableitbare linke Lage.
- Die Diagnosequelle heißt nun `plain_left_arm_local_fit` und beschreibt die
  Geometrieklasse statt die frühere Katalogfamilie.
- Ein neutraler Test mit dem katalognamenfreien Symbol `AC08XX_LEFT_ARM` sichert,
  dass die Auswahl ohne konkrete Bild-ID greift.
- Die Legacy-Ratchet-Baseline wurde nach Entfernung des `AC0812`-Guards von 329
  auf 328 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python tools/check_no_new_image_id_hardcoding.py --update
python tools/check_no_new_image_id_hardcoding.py
pytest -q tests/test_image_composite_converter.py::test_finalize_plain_left_arm_badge_disables_expensive_global_search_without_catalog_id
```

Ergebnis: Exit `0`; der Ratchet meldet `328 legacy occurrences remain`, und der
gezielte Plain-Left-Arm-Test läuft mit `1 passed`.

## 5-Zeilen-Log

- **Getestet:** Hardcoding-Ratchet-Update, Ratchet-Check und gezielte Plain-Left-Arm-Regression.
- **Ergebnis:** Exit `0`; `1 passed`, Ratchet jetzt `328`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und die geometriebasierte Global-Search-Auswahl für einfache linke Arm-Badges.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Finalisierungs-/SVG-/Optimierungs-Guards in struktur- oder beschreibungsgesteuerte Parameter überführen.
