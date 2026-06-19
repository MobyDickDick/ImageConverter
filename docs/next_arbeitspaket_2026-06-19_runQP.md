# Nächstes Arbeitspaket – IDO-14 Primitive und Transformationen Run QP (2026-06-19)

## Ziel

Run QP setzt IDO-14 aus `docs/image_description_only_tasks.md` fort: Nach den
Top-Kellen-/3-Wege-Ventilen sollen auch vertikale 2-Wege-Motorventile im
Beschreibungspfad als katalogfreie Primitive plus generische Transformationen
repräsentiert werden.

## Umsetzung

- Vertikale 2-Wege-Motorventile erhalten eine maschinenlesbare
  `primitive_decomposition` mit zwei Polygonkörper-Hälften, Kreisgriff,
  Linien-Connector und Motor-Textglyph.
- Die bestehenden 0°-, Linksrotation- und 180°-Varianten tragen denselben
  generischen `transform`-Vertrag wie die 3-Wege-Kellenvarianten.
- Zwei neutrale, katalogfreie Description-Tests sichern Grundform und 180°-
  Rotation ohne neue Bild-ID-Regel ab.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py && pytest -q tests/detailtests/test_description_contract_helpers.py
python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Beide Checks enden mit Exit `0`; der gezielte Description-Contract-
Testblock läuft mit `41 passed`, und der Ratchet sinkt auf `367 legacy
occurrences remain` ohne neue Runtime-ID-Vorkommen.

## 5-Zeilen-Log

- **Getestet:** Compileall, gezielte Description-Contract-Regressionen und Hardcoding-Ratchet.
- **Ergebnis:** Exit `0`; `41 passed` im gezielten Testblock, Ratchet `367`.
- **Blocker:** Kein neuer technischer Blocker; Renderer-/Fit-Pfade können weitere Ventilvarianten schrittweise an den Vertrag koppeln.
- **Dokumentation:** IDO-14 deckt nun Top-Kellen-/3-Wege- und vertikale 2-Wege-Motorventile mit Primitive-/Transformations-IR ab.
- **Nächster Schritt:** Weitere Kellen-/Ventilvarianten und adaptive Optimierungsprofile weiter katalogfrei migrieren.
