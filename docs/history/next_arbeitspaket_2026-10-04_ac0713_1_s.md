# Nächstes Arbeitspaket – AC0713_1_S 180°-Quadrat-Kelle (2026-10-04)

## Anlass

Nach Abschluss von ZG7.6 beginnt die Plan-B-Rotation mit `AC0713_1_S`.
Der bisher gespeicherte Lauf fiel trotz der Beschreibung "Kelle, aber mit
Quadrat anstelle von Kreis oben; 180° gedreht" auf einen falschen
Kreis-/Text- bzw. generischen Rechteckpfad zurück. Dadurch lag die Baseline bei
`mean_delta2=24899.021484` und `normalized_mse=0.127638`.

## Änderung

Der Beschreibungspfad erkennt nun katalogfrei die Kombination aus:

- Kelle,
- Quadrat/Viereck statt Kreis,
- 180°-Rotation.

Daraus entsteht eine neue `Rotated180SquareKelleGlyph` mit oberem Connector und
unterem Quadratkörper. Zusätzlich respektiert die freie Semantic-Badge-Heuristik
explizite Square-Kellen-Geometry-IR und überschreibt sie nicht mehr nur wegen
des Beschreibungstexts "Symmetrieachse des Kreises" als Kreis-Badge.

Es wurde keine neue Runtime-Katalog-ID in `src/` ergänzt.

## Ergebnis

Isolierter Recheck:

```text
AC0713_1_S.jpg
output: artifacts/tmp_ac0713_codex_run2
status: non_composite_perception_seeded_geometry_ir
geometry_ir_element_1=CircleBackground
geometry_ir_element_2=Rotated180SquareKelleGlyph
geometry_ir_element_3=OrthogonalPolyline
```

| Metrik | Vorher | Nachher |
|---|---:|---:|
| mean_delta2 | 24899.021484 | 11805.333008 |
| normalized_mse | 0.127638 | ca. 0.06054 |
| spatial_quality_score | 61105.136140 | 34054.345163 |

Der Lauf verbessert die Pixelmetrik deutlich, ist aber noch kein
Satisfaction-Pass. Die Fehler bleiben strukturiert
(`error_energy_concentrated_in_worst_tiles`, `localized_error_fraction=0.773328`).
`AC0713_1_S` bleibt deshalb in der Plan-B-Rotation offen.

## Verifikation

```text
pytest tests/detailtests/test_geometry_ir_helpers.py -k square_kelle
pytest tests/detailtests/test_description_contract_helpers.py -k 180_rotated_square_kelle
pytest tests/detailtests/test_semantic_family_rules_helpers.py -k square_kelle
pytest tests/test_no_new_image_id_hardcoding.py
```

Alle fokussierten Tests waren grün. Die lokale `.venv` ist auf diesem Rechner
defekt; die Tests liefen mit temporär unter `.codex-test-deps` installierten
Abhängigkeiten und isoliertem Python-Start.

## Folgepaket: Runtime-Registrierung und harte Abnahme

Der neue Typ fehlte noch in `DESCRIPTION_DRIVEN_GEOMETRY_IR_KINDS` und
`SEMANTIC_GEOMETRY_IR_KINDS`. Deshalb war eine reine Quadrat-Kellen-Beschreibung
kein vollständiger algorithmischer Runtime-Pfad; mit dem zusätzlichen Wort
"Kreis" aus der XML-Beschreibung konnten fälschlich eingefügte Kreis-/Linien-
Seeds die Kandidatenauswahl gewinnen. Die Ergänzung in beiden Sets aktiviert
den bestehenden Rasterregistrierer und die semantische Auswahl. Es wurden
keine neuen Formkoordinaten, Stilwerte oder Runtime-Katalogkennungen ergänzt.

Die Abnahme misst die gespeicherten SVGs des echten `semantic-only`-CLI-Laufs
nach erneutem Rendern. Der eingefrorene Vorlauf verwendet dieselben Raster,
eine katalogfreie Beschreibung und die Runtime vor dieser Ergänzung. Die
Abweichung zum früheren Zwischenwert `11805.333008` kommt aus dem nun
deterministischen Recheck; die alte Sammel-SVG-Baseline `24899.021484` bleibt
historische Evidenz.

| Rolle | Größe | mean_delta2 vorher | mean_delta2 nachher | normalized MSE nachher | Edge-Alignment | Beide Gates |
|---|---|---:|---:|---:|---:|---|
| Ziel | S | 11887.522461 | 2194.829346 | 0.011251 | 0.734084 | bestanden |
| Holdout | M | 13475.615234 | 1856.842896 | 0.009519 | 0.802460 | bestanden |
| Holdout | L | 10955.747070 | 1972.475586 | 0.010111 | 0.781110 | bestanden |

Alle drei Fälle verbessern Pixelmetrik, Kantenmetrik, Vordergrund-IoU und
Semantik ohne Regression. Der Report nutzt die unveränderten Good-Solution-
und Quality-Complexity-Grenzen. Die Semantikprüfung kontrolliert einen
annähernd quadratischen Körper mit angeschlossenem, zentriertem oberen Stiel
und verwirft zusätzliche Kreis-/Textprimitive. Sie bewertet den beschriebenen
unbeschrifteten Quadrat-/Stiel-Vertrag; sie behauptet keine Erkennung der
nicht beschriebenen hellen Innenmarkierung.

**Verbleibende Qualität:** Die Innenmarkierung ist im SVG noch nicht enthalten.
Der CLI-Lauf meldet weiterhin
`upper_quartile_error_pixels_form_large_connected_component`. Der Gate-Pass
schließt das Runtime-Registrierungspaket ab, nicht diesen visuellen Folgepunkt.
Die S-Kantenmetrik liegt zudem nur knapp über der Grenze `0.72`.

**Perception-Lerneffekt: generalisiert.** Vorhandene Bild-Seeds dürfen die
explizite Quadrat-Kellen-Geometrie nicht verdrängen. Dieselbe Beschreibung
und derselbe Runtime-Pfad funktionieren ohne Katalogkennung für drei Größen;
der Regressionstest bestätigt außerdem identische Ausgabe bei Umbenennung
und verbietet den Zugriff auf Sample-SVGs.

Der betroffene Testblock einschließlich der vier neuen Runtime-Regressionen
und der absoluten Runtime-ID-Prüfung läuft mit `218 passed`, ohne Skips oder
Warnings. Die defekte lokale `.venv` wurde dafür über temporäre Abhängigkeiten
unter `.tmp/task-deps` umgangen; die Projektumgebung wurde nicht verändert.

Reproduktion in einer funktionierenden Python-Umgebung mit
`requirements-dev.txt` (für deterministische Ausgaben
`TINY_ICC_OUTPUT_VARIATION=0` setzen):

```bash
python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir /tmp/square-kelle-recheck \
  --start AC0713_1_L --end AC0713_1_S --deterministic-order
python -m tools.evaluate_square_kelle_recheck \
  artifacts/evaluation/rotated_square_kelle_recheck_v1/manifest.json \
  --output /tmp/square-kelle-gates.json
python -m tools.review_conversion_quality \
  --output-dir /tmp/square-kelle-full-review \
  --exclude AC0554_2_L --exclude AC0713_1_S
python -m pytest -q -p no:cacheprovider \
  tests/test_rotated_square_kelle_runtime.py \
  tests/detailtests/test_non_composite_runtime_helpers.py \
  tests/detailtests/test_geometry_ir_helpers.py \
  tests/detailtests/test_description_contract_helpers.py \
  tests/detailtests/test_semantic_family_rules_helpers.py \
  tests/test_no_new_image_id_hardcoding.py
```

Der Gate-Replay verwendet die eingefrorenen Vorher-/Nachher-SVGs mit SHA256-
Provenienz. Für die Abnahme eines neuen CLI-Laufs müssen dessen gespeicherte
SVGs als `after_svg` im Manifest eingetragen werden. Die vollständige Rotation
prüft `688` Paare und schließt die beiden separat belegten Gate-Passes aus,
weil die historische Sammelausgabe noch deren alte SVGs enthält. Sie füllt die
aktive Liste auf fünf Kandidaten; nächster Kandidat ist `DLG0010_1`.
