# AC0100 Quality Follow-up (2026-05-31)

## Anlass

Der AC0100-L/M/S-Kurzlauf wurde nach der Entfernung der festen Sample-Fallbacks
und nach dem Schutz beschreibungsgetriebener Geometry-IR gegen Template-Transfer
erneut geprüft. Die Konvertierung läuft technisch durch und erzeugt SVG/PNG/Diff-
Artefakte, erreicht aber weiterhin nicht die strenge `pixel_delta2`-Qualität.

## Repro-Kommando

```bash
rm -rf /tmp/ac010_verify_task && mkdir -p /tmp/ac010_verify_task
for v in L M S; do
  PYTHONPATH=vendor/linux-py310/site-packages:. \
    python -m src.iCCModules.imageCompositeConverterCli \
    artifacts/images_to_convert \
    --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
    --output-dir /tmp/ac010_verify_task \
    --start AC0100_${v} \
    --end AC0100_${v} \
    --deterministic-order || exit $?
done
cat /tmp/ac010_verify_task/reports/conversion_bestlist.csv
cat /tmp/ac010_verify_task/reports/pixel_delta2_summary.txt
```

## Aktueller Befund

Der Lauf endet für alle drei Varianten mit Exitcode `0`, aber die Qualitäts-
Summary bleibt rot:

```text
images_total=3
threshold_mean_delta2=18.000
images_with_mean_delta2_le_threshold=0
```

Die beobachteten Werte aus `conversion_bestlist.csv`:

| Variante | best_error | error_per_pixel | mean_delta2 |
| --- | ---: | ---: | ---: |
| AC0100_L | 102.655000 | 0.03207969 | 53731.589844 |
| AC0100_M | 101.765556 | 0.05653642 | 53063.234375 |
| AC0100_S | 105.422500 | 0.13177812 | 53333.390625 |

Die Element-Logs zeigen weiterhin den gewünschten algorithmischen Pfad
`non_composite_perception_seeded_geometry_ir` mit `CircleBackground`,
`HorizontalGradient`, `RectBorder`, `DiagonalBand`, `PlusGlyph` und `MinusGlyph`.
Damit ist der Sonderfall-/Template-Transfer-Fehler strukturell entschärft; offen
bleibt die parametrische Qualitätsarbeit.

## Aufgabe / Akzeptanzkriterien

- Die AC0100-Familie darf nicht erneut über feste Sample-Auswahl oder generischen
  Template-Transfer gelöst werden.
- Die Lösung muss die Parameter der vorhandenen Geometry-IR allgemein optimieren
  (mindestens Rechteck-BBox, Verlauf-Stopps/Farben, Diagonalbreite/-lage,
  Plus/Minus-Position und ggf. valide Perception-Seeds).
- Der obige Kurzlauf muss entweder `images_with_mean_delta2_le_threshold=3`
  erreichen oder eine fachlich begründete, automatisiert geprüfte neue
  Qualitätsmetrik für diese stark komprimierten Kleinvarianten dokumentieren.
- Ein Regressionstest soll sicherstellen, dass AC0100_L/M/S nicht wieder auf
  fixe Sample-Daten oder donor-transformierte Varianten zurückfallen.
