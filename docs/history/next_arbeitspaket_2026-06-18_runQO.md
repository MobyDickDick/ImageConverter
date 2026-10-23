# Nächstes Arbeitspaket – IDO-14 Primitive und Transformationen Run QO (2026-06-18)

## Ziel

Run QO startet IDO-14 aus `docs/image_description_only_tasks.md`: Ventil-/Kellen-
Spezialpfade sollen im Beschreibungspfad zusätzlich als katalogfreie Primitive
und generische Transformationen ausgedrückt werden, ohne neue Bild-ID-Dispatches
einzuführen.

## Umsetzung

- Top-Kellen-/3-Wege-Ventil-Geometry-IR trägt nun eine maschinenlesbare
  `primitive_decomposition` mit Polygonkörper, Kreisgriff, Linien-Connector und
  optionalem Text-Glyph.
- Rotierte und gespiegelte Top-Kellen-Varianten erhalten einen generischen
  `transform`-Vertrag mit `rotation_deg` beziehungsweise `mirror_axis`, sodass
  Rotation und Spiegelung nicht mehr nur im spezialisierten Kind-Namen stecken.
- Der Beschreibungspfad akzeptiert zusätzlich neutrale, katalogfreie
  Formulierungen für 3-Wege-Kellenventile mit Kreisgriff und Dreiecks-/Polygon-
  Ventilkörper.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py && pytest -q tests/detailtests/test_description_contract_helpers.py
python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Beide Checks enden mit Exit `0`; der gezielte Description-Contract-
Testblock läuft mit `39 passed`, und der Ratchet bleibt bei `368 legacy
occurrences remain` ohne neue Runtime-ID-Vorkommen.

## 5-Zeilen-Log

- **Getestet:** Compileall, gezielte Description-Contract-Regressionen und Hardcoding-Ratchet.
- **Ergebnis:** Exit `0`; `39 passed` im gezielten Testblock, Ratchet weiterhin `368`.
- **Blocker:** Kein neuer technischer Blocker; weitere Ventil-/Kellen-Familien müssen noch auf dieselbe Primitive-/Transformations-IR gehoben werden.
- **Dokumentation:** IDO-14 besitzt jetzt den ersten katalogfreien Primitive-/Transformationsvertrag für Top-Kellen-/3-Wege-Ventile.
- **Nächster Schritt:** Weitere Kellen-/Ventilvarianten und Rendererpfade schrittweise an den generischen Primitive-/Transformationsvertrag koppeln.
