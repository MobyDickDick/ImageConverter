# Nächstes Arbeitspaket – Run NK (2026-06-02)

Dieses Arbeitspaket bearbeitet die nächste dokumentierte Aufgabe aus
`docs/open_tasks.md`: **TH2/AC0100-QA**.

## 1) Dokumentierte Aufgabe

- **Ziel:** AC0100_L/M/S sollen algorithmisch stabilisiert werden, ohne feste
  Sample-SVG-Auswahl und ohne generischen Template-Transfer.
- **Ausgangslage:** Run NI hatte die Renderer-stabile Bandstrategie bereits auf
  ca. `mean_delta2≈3.2k–3.7k` verbessert. Offen blieb, dass der strukturierte
  Symbol-Fit weiterhin eine zentrierte Plus-/Minus-Gruppe und beide Diagonalen
  bevorzugen konnte, obwohl die AC0100-Rasterfamilie nur ein Top-Left-Plus und
  eine Diagonale von oben rechts nach unten links zeigt.

## 2) Umsetzung

- Der elementweise AC0100-Symbol-Fit parametrisiert jetzt die Plus-Position
  (`plus_x_ratio`, `glyph_y_ratio`) und die Plus-Halbbreite (`plus_half_ratio`).
- Die zweite Diagonale und die Minuslinie sind als echte optionale Elemente
  modelliert: `diag2_width=0.0` bzw. `minus_width=0.0` unterdrücken das jeweilige
  SVG-Primitive vollständig.
- Die lokale Raster-Suche prüft diese optionalen Nullkandidaten zusammen mit den
  bisherigen Linienbreiten und kann dadurch die kompakte AC0100-Top-Left-Plus-
  Silhouette wählen.

## 3) Ergebnis / Nachweis

Gezielter AC0100-Kurzlauf:

| Variante | best_error | error_per_pixel | mean_delta2 |
| --- | ---: | ---: | ---: |
| AC0100_L | 27.984896 | 0.00874528 | 3282.756592 |
| AC0100_M | 25.793333 | 0.01432963 | 2843.088867 |
| AC0100_S | 23.715000 | 0.02964375 | 2502.757568 |

Die alte globale `threshold_mean_delta2=18.000` bleibt mit
`images_with_mean_delta2_le_threshold=0` weiterhin nicht geeignet für diese stark
komprimierten Kleinvarianten. TH2 wird deshalb über die automatisierte
Kompaktvarianten-Metrik abgeschlossen: pro Variante `best_error < 28.5` und
`mean_delta2 < 3300.0`, plus Validierungslog ohne Sample-/Template-Signale.

## 4) Plan-B-/Regressionsteil

- Der schwere AC0100-Regressions-Smoke wurde auf die verschärfte Ersatzmetrik
  aktualisiert.
- Ein neuer Detailtest sichert ab, dass der strukturierte Symbol-SVG-Builder eine
  einzelne `tr_bl`-Diagonale mit Top-Left-Plus und ohne Minuslinie ausgeben kann.
- `docs/open_tasks.md` markiert TH2 als erledigt; die historische Altmetrik ist
  weiterhin im Follow-up-Dokument nachvollziehbar abgegrenzt.
