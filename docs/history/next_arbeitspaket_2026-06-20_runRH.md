# Nächstes Arbeitspaket – IDO-17 Vertical-Connector-Family-Entkopplung Run RH (2026-06-20)

## Ziel

Run RH setzt IDO-17 fort: Der vertikale AC08-Badge-Tuningpfad wird nicht mehr
über konkrete Katalog-IDs ausgewählt, sondern über messbare beziehungsweise aus
Beschreibung/Perception stammende Connector-Parameter.

## Umsetzung

- `tuneAc08VerticalConnectorFamilyImpl(...)` prüft keine konkrete AC08-ID-Liste
  mehr. Der Pfad greift nun bei `connector_direction`/`connector_family_direction`
  `vertical`, `top`, `bottom`, `up` oder `down` sowie bei bereits gesetzter
  `stem_enabled`-/`arm_enabled`-Geometrie.
- Top-/Up-Richtungen aktivieren den oberen Arm, Bottom-/Down-Richtungen den
  unteren Stem. Bestehende Kreis-, Text-, Radius- und Längen-Guardrails laufen
  danach weiter über dieselbe generische Vertikal-Connector-Geometrie.
- Die Diagnosegruppe heißt nun `vertical_connector_badge` und beschreibt die
  Geometrieklasse statt eine Katalogfamilie.
- Die Detailtests verwenden neutrale Symbolnamen (`NEUTRAL_VERTICAL_BADGE`,
  `NEUTRAL_TOP_VOC_BADGE`) und sichern Stem- sowie Top-Arm-Auswahl ohne
  Katalog-ID ab.
- Die Legacy-Ratchet-Baseline sinkt nach Entfernung der vertikalen
  Familienliste von 295 auf 281 Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
pytest -q tests/detailtests/test_semantic_ac08_family_helpers.py
python tools/check_no_new_image_id_hardcoding.py --update
python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Exit `0`; der Detailtest läuft mit `5 passed`, und der Ratchet meldet
`281 legacy occurrences remain`.

## 5-Zeilen-Log

- **Getestet:** Detailtests für AC08-Family-Helper sowie Hardcoding-Ratchet-Update und Ratchet-Check.
- **Ergebnis:** Exit `0`; `5 passed`, Ratchet jetzt `281`.
- **Blocker:** IDO-17 ist weiterhin nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in horizontalen, Text- und Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und die parameterbasierte Vertikal-Connector-Auswahl.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Family-/Finalisierungs-/SVG-/Optimierungs-Guards in struktur- oder beschreibungsgesteuerte Parameter überführen.
