# Nächstes Arbeitspaket – IDO-06 Constraint-Parser Run PZ (2026-06-16)

## Ziel

Run PZ bearbeitet das nächste offene Arbeitspaket aus
`docs/image_description_only_tasks.md`: **IDO-06 – Beschreibung ausschließlich in
Constraints übersetzen**. Der Parser soll aus Beschreibungstext einen
katalogfreien Constraint-Vertrag erzeugen, ohne Dateinamen oder Renderer-/Mode-
Entscheidungen in diesen Vertrag zu übernehmen.

## Umsetzung

- `buildDescriptionConstraintsImpl(...)` erzeugt jetzt den maschinenlesbaren
  Vertrag `description_geometry_constraints_v1` mit Element-Constraints,
  Relationen aus Referenzfeldern und einem Unsicherheitsblock.
- `Reflection.parse_description(...)` hängt den neuen
  `description_constraints`-Vertrag zusätzlich an die Parser-Parameter an; die
  bestehende `geometry_ir` bleibt für den aktuellen Runtime-Pfad erhalten.
- Neue Parser-Regressionstests verwenden ausschließlich erfundene Namen und
  prüfen, dass dieselbe Beschreibung unter unterschiedlichen Dateinamen
  identische Constraints ohne Dateinamensspuren, `mode` oder
  `semantic_badge`-Rendererauswahl erzeugt.
- Ein Negativtest sichert, dass unzureichend unterstützte Beschreibungstexte
  keinen Renderer wählen, sondern im Constraint-Vertrag als
  `needs_review`/`no_supported_geometry_constraint` markiert werden.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py
```

Ergebnis: Exit `0`; der Ratchet bleibt auf der bestehenden Legacy-Baseline, und
`tests/detailtests/test_description_contract_helpers.py` läuft mit `22 passed`.

## 5-Zeilen-Log

- **Getestet:** Parser-Constraint-Vertrag für erfundene Dateinamen und unsichere Beschreibung.
- **Ergebnis:** Exit `0`; `22 passed` im betroffenen Detailtestmodul.
- **Blocker:** Kein neuer Blocker; IDO-07 bleibt als nächster Schritt im P1-Track offen.
- **Dokumentation:** IDO-06 ist in `docs/image_description_only_tasks.md` abgeschlossen und dieser Run hält den Nachweis fest.
- **Nächster Schritt:** IDO-07 umsetzen: Perception-Kandidaten vollständig auf dieselbe IR-/Constraint-Struktur abbilden.
