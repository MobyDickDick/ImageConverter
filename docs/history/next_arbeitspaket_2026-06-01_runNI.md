# Nächstes Arbeitspaket – Run NI (2026-06-01)

Dieses Arbeitspaket bearbeitet die nächste dokumentierte Aufgabe aus
`docs/open_tasks.md`: **TH2/AC0100-QA**.

## 1) Dokumentierte Aufgabe

- **Ziel:** AC0100_L/M/S dürfen nicht über fixe Sample-Daten oder generischen
  Template-Transfer stabilisiert werden. Die Qualitätsverbesserung muss aus dem
  vorhandenen algorithmischen Geometry-/Symbol-Fit kommen.
- **Befund:** Die starke Qualitätsabweichung wurde durch die SVG-Renderer-
  Behandlung des `linearGradient`-Füllobjekts verstärkt: beim Rendern entstanden
  große schwarze Pixelbereiche, obwohl die Beschreibung nur ein graues Rechteck
  mit horizontalem Dunkel-Hell-Dunkel-Verlauf verlangt.
- **Umsetzung:** Der horizontale Geometry-IR-Verlauf wird beim SVG-Rendering nun
  in deterministische Grauband-Primitive zerlegt. Der elementweise Symbol-Fit
  nutzt dieselbe renderer-stabile Bandstrategie statt eines nativen SVG-
  Gradients. Das bleibt algorithmisch: Farben, Zentrum und Linienbreiten werden
  weiterhin aus dem Raster abgeleitet und elementweise verbessert.

## 2) Gekoppelte Plan-B-Aufgabe

- **Plan-B/Regression:** Ein neuer AC0100-Smoke prüft alle drei Größenvarianten
  und akzeptiert nur den algorithmischen Status
  `non_composite_elementwise_symbol_fit`; Sample-SVG-Auswahl und Template-
  Transfer dürfen im Validierungslog nicht auftauchen.
- **Qualitätsgrenze:** Der Lauf muss pro Variante `best_error < 31.0` und
  `mean_delta2 < 4000.0` erreichen. Das ersetzt nicht die globale strenge
  `threshold_mean_delta2=18`, dokumentiert aber eine automatisierte neue
  Qualitätsmetrik für diese stark komprimierten Kleinvarianten.

## 3) Nächstes Bild / Testdelegation

- Das kostenintensive Gesamt-Gate bleibt für GitHub Actions delegiert. Lokal
  wurden nur gezielte Detail-/Smoke-Checks ausgeführt.

## Ergebnis

- AC0100_L/M/S verbessern sich im lokalen Kurzlauf von vormals ca.
  `mean_delta2≈53k` auf ca. `3.2k–3.7k`.
- Die offene TH2-Aufgabe bleibt in `docs/open_tasks.md` bewusst offen, weil das
  historische globale `images_with_mean_delta2_le_threshold=3` noch nicht erfüllt
  ist; der neue Regressionstest hält die akzeptierte Zwischenmetrik fest.
