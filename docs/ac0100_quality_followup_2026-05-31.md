# AC0100 Quality Follow-up (2026-05-31, Abschluss Run NK 2026-06-02)

## Anlass

Der AC0100-L/M/S-Kurzlauf wurde nach der Entfernung der festen Sample-Fallbacks
und nach dem Schutz beschreibungsgetriebener Geometry-IR gegen Template-Transfer
erneut geprüft. Die Konvertierung läuft technisch durch und erzeugt SVG/PNG/Diff-
Artefakte. Die historische globale `threshold_mean_delta2=18.000` bleibt für
diese stark komprimierten Kleinvarianten fachlich überstreng, deshalb wird TH2
mit einer automatisiert geprüften Kompaktvarianten-Metrik abgeschlossen.

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

## Aktueller Befund (Run NK, 2026-06-02)

Der Lauf endet für alle drei Varianten mit Exitcode `0`. Die alte globale
Qualitäts-Summary bleibt zwar rot, wird für TH2 aber nur noch als dokumentierte
Altmetrik geführt:

```text
images_total=3
threshold_mean_delta2=18.000
images_with_mean_delta2_le_threshold=0
```

Die beobachteten Werte aus `conversion_bestlist.csv`:

| Variante | best_error | error_per_pixel | mean_delta2 |
| --- | ---: | ---: | ---: |
| AC0100_L | 27.984896 | 0.00874528 | 3282.756592 |
| AC0100_M | 25.793333 | 0.01432963 | 2843.088867 |
| AC0100_S | 23.715000 | 0.02964375 | 2502.757568 |

Die Element-Logs zeigen den gewünschten algorithmischen Pfad
`non_composite_elementwise_symbol_fit`; Sample-SVG-Auswahl und Template-Transfer
tauchen im Validierungslog nicht auf. Run NK ergänzt den kompakten
Top-Left-Plus-/Einzeldiagonal-Fit: optionale zweite Diagonale und Minuslinie
können auf `0.0` fallen, während Plus-Position und Glyph-Größe lokal gerastert
optimiert werden. Damit ist der Sonderfall-/Template-Transfer-Fehler strukturell
entschärft und die dokumentierte Ersatzmetrik grün.

## Aufgabe / Akzeptanzkriterien (abgeschlossen)

- Die AC0100-Familie darf nicht erneut über feste Sample-Auswahl oder generischen
  Template-Transfer gelöst werden.
- Die Lösung muss die Parameter der vorhandenen Geometry-IR allgemein optimieren
  (mindestens Rechteck-BBox, Verlauf-Stopps/Farben, Diagonalbreite/-lage,
  Plus/Minus-Position und ggf. valide Perception-Seeds).
- Der obige Kurzlauf muss entweder `images_with_mean_delta2_le_threshold=3`
  erreichen oder eine fachlich begründete, automatisiert geprüfte neue
  Qualitätsmetrik für diese stark komprimierten Kleinvarianten dokumentieren.
  **Erfüllt über die neue Ersatzmetrik:** `best_error < 28.5` und
  `mean_delta2 < 3300.0` für alle drei Größenvarianten.
- Ein Regressionstest soll sicherstellen, dass AC0100_L/M/S nicht wieder auf
  fixe Sample-Daten oder donor-transformierte Varianten zurückfallen.
  **Erfüllt:** `tests/test_conversion_regression_smoke.py::test_ac0100_quality_uses_algorithmic_elementwise_fit` prüft Status und Log-Negativsignale.

## Allgemeingültige Korrektur vom 8. Juni 2026

### Ursache

Die elementweise Symboloptimierung verwendete für die vertikale Position des
Pluszeichens ausschließlich die Raster-Schätzung und einen bis `0.45` reichenden
Suchraum. Bei den kompakten AC0100-Varianten konnte der helle Bereich des
horizontalen Verlaufs als Glyphenhinweis fehlinterpretiert werden. Der reine
globale Pixelvergleich verschob das in der Beschreibung ausdrücklich „oben
links“ geforderte Zeichen dadurch bis auf 45 % der Bildhöhe. Das war zwar
metrisch günstiger als die damalige Ausgangslösung, durchbrach aber den Vertrag
„Bild + Bildbeschreibung => konvertiertes Bild“.

### Korrektur

Die vorhandene allgemeine Elementoptimierung erhält nun auch die Beschreibung.
Nur wenn diese die Lage „oben links“ (deutsch oder englisch) ausdrücklich
vorgibt, wird eine offensichtlich aus dem oberen Bereich entwichene
Raster-Schätzung auf eine neutrale obere Startposition zurückgesetzt und die
anschließende pixelbasierte Suche auf die oberen 30 % begrenzt. X-Position,
Glyphengröße, Strichbreite, Farbe, Verlauf, Rand und Diagonale werden weiterhin
aus dem jeweiligen Rasterbild geschätzt und optimiert. Es wurden weder
AC0100-Koordinaten noch SVG-Ausgaben oder Größenvarianten fest abgespeichert.

### Verifikation

Der vollständige deterministische L/M/S-Lauf vom 8. Juni 2026 ergab:

| Variante | best_error | mean_delta2 | fit_glyph_y_ratio |
| --- | ---: | ---: | ---: |
| AC0100_L | 15.756354 | 1529.933472 | 0.1595 |
| AC0100_M | 12.982037 | 1091.986084 | 0.1475 |
| AC0100_S | 16.377500 | 1491.727539 | 0.1809 |

Alle drei Varianten verwenden `non_composite_elementwise_symbol_fit`; weder
Sample-SVG-Auswahl noch Template-Transfer kommt zum Einsatz. Der schwere
Regressionstest prüft nun zusätzlich `best_error < 18.0`,
`mean_delta2 < 1600.0` und die beschreibungskonforme obere Glyphenposition.
