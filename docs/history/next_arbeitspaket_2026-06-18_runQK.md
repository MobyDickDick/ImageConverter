# Nächstes Arbeitspaket – IDO-12 Vertikale Kreis-Connectoren Run QK (2026-06-18)

## Ziel

Run QK startet den nach Run QJ dokumentierten Anschluss aus
`docs/image_description_only_tasks.md`: Obere und untere Kreis-Connectoren sollen
im Beschreibungspfad nicht mehr nur über AC08-Familienanker stabilisiert werden,
sondern über katalogfreie Relationssignale wie „oben vom Kreis“, „unterhalb des
Kreises“ und inverse Formulierungen wie „Kreis über der Linie“.

## Umsetzung

- Der Beschreibung-zu-Geometry-IR-Pfad erkennt nun vertikale Kreis-Connectoren
  oberhalb und unterhalb eines Kreises und erzeugt dafür ein generisches
  `VerticalRule`-Element mit `top_of`- beziehungsweise `bottom_of`-Relation.
- Der generische Geometry-IR-SVG-Renderer rendert `VerticalRule` als vertikalen
  Pfad aus normalisierten BBox-Koordinaten; die Geometrie bleibt damit
  dateinamen- und katalog-ID-frei.
- Die Semantic-Badge-Heuristik leitet obere und untere vertikale Connectoren aus
  expliziten und inversen Relationsformulierungen ab und protokolliert sie als
  `description_heuristic` statt als neue Familien-ID-Regel.
- Neue Rename-/Neutraltests sichern, dass obere vertikale Kreis-Connectoren mit
  erfundenen Dateinamen dieselben Constraints und dieselbe Geometry-IR erzeugen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Beide Checks enden mit Exit `0`; der gezielte Beschreibung-/Semantik-
Testblock läuft mit `43 passed`, und der Ratchet bleibt bei `368 legacy
occurrences remain` ohne neue Runtime-ID-Vorkommen.

## 5-Zeilen-Log

- **Getestet:** Compileall, gezielte Beschreibung-/Semantik-Regressionen und Hardcoding-Ratchet.
- **Ergebnis:** Exit `0`; `43 passed` im gezielten Testblock, Ratchet weiterhin `368`.
- **Blocker:** Kein neuer Blocker; verdeckte/Z-Order-Fälle sind noch nicht fachlich ausgebaut.
- **Dokumentation:** IDO-12 besitzt jetzt den ersten katalogfreien Vertikal-Connector-Pfad für oben/unten inklusive Rename-Sicherung.
- **Nächster Schritt:** IDO-12 mit teilweise verdeckten Anschlüssen und connector-freien Negativfällen erweitern.
