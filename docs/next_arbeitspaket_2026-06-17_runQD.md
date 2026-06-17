# Nächstes Arbeitspaket – IDO-10 Linker Kreis-Connector Run QD (2026-06-17)

## Ziel

Run QD führt das nächste offene IDO-10-Paket aus `docs/image_description_only_tasks.md`
fort: Der linke Kreis-Connector soll nicht nur bei der Formulierung „Linie links
vom Kreis“, sondern auch bei inversen und synonymen Relationstexten katalogfrei
aus Beschreibung und Relation ableitbar sein.

## Umsetzung

- Die Beschreibungsauswertung für Geometry-IR akzeptiert zusätzliche
  katalogfreie Relationstexte wie „links neben dem Kreis“, „linker Anschluss“,
  „linke Anschlusslinie“ und die inverse Relation „Kreis rechts von der Linie“.
- Die semantischen Badge-Regeln verwenden dieselben zusätzlichen Synonyme und
  inversen Texte für den linken horizontalen Kreis-Connector.
- Neue neutrale Regressionen sichern den inversen Beschreibungspfad ohne
  AC08-Familien-ID: `CircleBackground` + `HorizontalRule`,
  `target_ref=described_circle` und explizite `left_of`-Relation.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tools tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet keine neuen Runtime-Bild-IDs über der
Legacy-Baseline, und der gezielte Beschreibung-/Semantik-Testblock läuft mit
`33 passed`.

## 5-Zeilen-Log

- **Getestet:** Katalogfreie inverse Relation „Kreis rechts von der Linie“ im Constraint- und Semantikpfad.
- **Ergebnis:** Exit `0`; `33 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; vollständiger IDO-10-Baseline-Abbau bleibt offen.
- **Dokumentation:** Dieser Run erweitert den linken Connector auf synonyme und inverse Relationstexte ohne neue Bild-ID-Abhängigkeit.
- **Nächster Schritt:** Verbleibende AC08-Linksconnector-Familien von Familien-ID-Listen auf den generischen Relationspfad umstellen und Legacy-Baseline reduzieren.
