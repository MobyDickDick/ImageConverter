# Nächstes Arbeitspaket – ZG3 Good-Solution-Gate v1 (2026-10-03)

Dieses Paket arbeitet nach ZG2 die nächste offene Leitaufgabe aus
`docs/open_tasks.md` ab: **ZG3 – Good-Solution-Gate v1 implementieren**.

## Versionierter Entscheidungsvertrag

`tools/evaluate_good_solution_gate.py` stellt den Vertrag
`good_solution_gate_v1` bereit. Die Defaultschwellen sind bewusst zentral und
werden sowohl auf Reportebene als auch in jeder Dateientscheidung ausgegeben:

- `error_per_pixel <= 0.05`,
- `semantic_score >= 0.85`,
- `dimension_match >= 0.99`.

Sind alle Pflichtmetriken vorhanden und erfüllen die Schwellen, lautet der
Status `good`. Eine Schwellenverletzung ergibt `suboptimal`. Fehlende oder
nicht-endliche Pflichtmetriken sowie terminale Quellstatus wie
`conversion_failed`, `semantic_mismatch` oder `semantic_conflict` ergeben
`not_reachable`. Jeder Ausgang enthält eine nichtleere, stabile Gründenliste.
Damit werden unvollständige Daten nicht stillschweigend als schlechte, aber
erreichbare Lösung fehlklassifiziert.

## Report und CLI

Die CLI liest eine `conversion_result_map.json` und schreibt optional mit
`--output` einen Gesamtbericht. Jede Datei enthält darin den dreistufigen
Status, die normalisierten Eingabemetriken, die konkret angewandten Schwellen
und Gründe. Die Summary zählt alle drei Statusklassen; die Reihenfolge der
Dateien ist deterministisch.

```bash
python tools/evaluate_good_solution_gate.py \
  artifacts/converted_images/reports/conversion_result_map.json \
  --output /tmp/good_solution_gate_v1.json
```

Historische Result-Maps ohne `semantic_score` und `dimension_match` bleiben
dabei korrekt sichtbar, werden aber als `not_reachable` klassifiziert. Sie
werden nicht durch erfundene Ersatzwerte aufgewertet.

## Absicherung und nächster Schritt

Fixture-Tests sichern alle drei Zustände, mehrere gleichzeitige Gründe, die
vollständigen Dateinachweise und die JSON-CLI ab. ZG3 ist damit abgeschlossen.
Die nächste offene Leitaufgabe ist **ZG4 – Dimensionstreue als harte Regel
erzwingen**; sie soll die heute bereits ausgewertete `dimension_match`-Metrik
verbindlich aus den tatsächlichen Raster-/SVG-Abmessungen erzeugen.
