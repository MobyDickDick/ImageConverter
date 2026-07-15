# Nächstes Arbeitspaket – AC0010/AC0100-Recheck (2026-07-03)

## Anlass

Die Rückmeldung aus `nextPrompt.txt` beschreibt eine erneute AC010/AC0100-
Regression: Die große Variante wirke plausibel, die Basis-/M-/S-Pfade dürften
aber nicht über fest abgelegte Sample-Daten gelöst werden. Ziel dieses Pakets
war deshalb eine allgemeine Prüfung des Algorithmuspfads aus Bildbeschreibung
und Rasterbild.

## Ergebnis

- Der isolierte AC0010-Lauf verwendet weiterhin den elementweisen
  Raster-/Beschreibungsfit (`status=non_composite_elementwise_symbol_fit`) und
  bleibt ohne Sample-Auswahl erfolgreich.
- Der Bereichslauf `AC0100..AC0100` verarbeitet die real vorhandenen Varianten
  `AC0100_L`, `AC0100_M` und `AC0100_S`; `AC0100_from_sample.jpg` bleibt als
  Sample-Artefakt außerhalb dieses Bereichs.
- Alle drei AC0100-Größenvarianten werden algorithmisch rekonstruiert. Die
  gemessenen Kurzlaufwerte lagen bei `best_error=11.360104/11.638704/12.977917`
  und `mean_delta2=949.427795/828.678345/1213.068726` für L/M/S.
- Zur Absicherung wurde ein Detailtest ergänzt, der die AC0100-Referenz-
  Beschreibung ausdrücklich in eine Heat-Exchanger-IR-Kette aus
  `HorizontalGradient`, `RectBorder`, genau einer `DiagonalBand`-Achse sowie
  `PlusGlyph`/`MinusGlyph` übersetzt. Damit ist die zugehörige Qualitätspflege
  an den allgemeinen Beschreibungsparser gebunden und nicht an gespeicherte
  SVG-Beispiele.

## Verifikation

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py -k ac0100`
  → `5 passed, 57 deselected`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py::test_ac0100_reference_description_builds_algorithmic_heat_exchanger_chain`
  → `1 passed`
- `timeout 90 env PYTHONPATH=vendor/linux-py310/site-packages:. python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml --output-dir /tmp/icctest --start AC0010 --end AC0010 --deterministic-order`
  → Exit `0`, `AC0010` erfolgreich konvertiert
- `timeout 120 env PYTHONPATH=vendor/linux-py310/site-packages:. python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml --output-dir /tmp/icctest2 --start AC0100 --end AC0100 --deterministic-order`
  → Exit `0`, `AC0100_L/M/S` erfolgreich konvertiert

## Nachtrag 2026-07-13

Beim erneuten Abarbeiten des Pakets fiel auf, dass der allgemeine gerahmte
Gradient-Panel-Fallback strukturelle Heizelement-Beschreibungen mit
Plus-/Minus-Glyphen und Diagonale zu früh übernehmen konnte. Dadurch wurde der
algorithmische Geometry-/Symbolpfad für kompakte AC0100-Varianten nicht mehr
zuverlässig erreicht; in einem reproduzierbaren Lauf endete dieser Pfad sogar
mit einem `UnboundLocalError`, weil der frühe Panel-Zweig kein gerendertes SVG
für die spätere Qualitätsberechnung initialisierte.

Die Korrektur bleibt allgemein: Beschreibungen mit strukturellen Symbolen
(`Plus`, `Minus`, Diagonalen/Andreaskreuz) werden nicht mehr vom simplen
Panel-Fallback abgefangen, sondern laufen weiter in den vorhandenen
beschreibungs- und rastergetriebenen Symbol-/Geometry-IR-Pfad. Falls der
Panel-Fallback für echte einfache Panels greift, rendert und bewertet er sein
SVG nun unmittelbar, bevor die gemeinsame Artefakt-/Qualitätslogik weiterläuft.
