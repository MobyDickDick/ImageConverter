# AC0811 Debug-Analyse (2026-04-27)

## Ziel

Eine Debug-Version für AC0811 erstellen, die zusätzlich zu den bisherigen Element-Diff-Bildern auch einen strukturierten Konvertierungs-Dump (JSON) je Variante schreibt, um Ursache und Engpass transparent zu machen.

## Ausgeführter Diagnoselauf

```bash
set -o pipefail
timeout 420 python -u -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0811 \
  --end AC0811 \
  --isolate-svg-render \
  --deterministic-order \
  --debug-ac0811-dir artifacts/debug/ac0811 \
  | tee artifacts/converted_images/reports/AC0811_debug_run_2026-04-27.log
```

- Lauf endet mit Timeout `124`, aber Debug-Artefakte für `AC0811_L`, `AC0811_M` und `AC0811_S` wurden erzeugt.

## Neue Debug-Artefakte

Pro AC0811-Variante wird jetzt zusätzlich geschrieben:

- `artifacts/debug/ac0811/<VARIANTE>/<VARIANTE>_conversion_debug.json`

Der JSON-Dump enthält u. a.:

- Dateipfade (`image_path`, `svg_path`, `diff_path`, `log_file`)
- Laufkontext (`iteration_budget`, `badge_rounds`, `status`, `convergence`)
- Ergebnisdaten (`best_iter`, `best_error`, `result_row` inkl. `mean_delta2/std_delta2`)
- `validation_details`
- vollständigen Inhalt von `<VARIANTE>_element_validation.log` als `validation_log_text`

## Kurzanalyse der AC0811-Dumps

Aus den neu erzeugten Dumps:

- `AC0811_L`: `semantic_ok`, aber `best_error=5.0196`, `mean_delta2=606.97`; Quality-Markierung bleibt `borderline` mit hohem Circle-Elementfehler.
- `AC0811_M`: `semantic_ok`, aber `best_error=8.63`, `mean_delta2=1292.16`; im Verlauf tritt zusätzlich „stem: Element konnte nicht extrahiert werden“ auf.
- `AC0811_S`: `semantic_ok`, aber `best_error=9.2987`, `mean_delta2=1066.46`; Quality-Markierung `borderline` mit hohem Stem-Elementfehler.

## Interpretation

Der aktuelle Engpass bei AC0811 ist laut Debug-Daten **nicht** primär das semantische Verstehen (das ist in allen drei Varianten `semantic_ok`), sondern die numerische/geometrische Feinpassung (hohe Elementfehler, teils Stagnation, teils instabile Stem-Extraktion).

## Vorschlag für den nächsten technischen Schritt

Um Deine Forderung „objektspezifische Restriktionen reduzieren“ kontrolliert umzusetzen, sollten wir als nächstes in einem klar abgegrenzten Patch:

1. AC0811-spezifische Guardrails einzeln per Feature-Flag abschaltbar machen (statt hartem Entfernen in einem Schritt),
2. denselben Diagnoselauf mit identischem Seed mehrfach vergleichen,
3. anhand der neuen JSON-Dumps messen, welche Restriktion wirklich verbessert bzw. verschlechtert.

So vermeiden wir, dass ein pauschales Entfernen von Speziallogik die robusten Fälle regressiv verschlechtert.
