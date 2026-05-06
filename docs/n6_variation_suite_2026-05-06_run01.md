# N6 Variationssuite – Run 01 (2026-05-06)

## Anlass
Erste reproduzierbare Ausführung des N6-Basisgenerators, um den Szenario-Katalog und die Testartefakte konsistent aus dem aktuellen Repository-Stand zu erzeugen.

## Befehl
```bash
python -m tools.generate_svg_variation_suite
```

## Ergebnis
- Exit-Code: `0`
- Generierte SVG-Varianten: `6`
  - N6A (`circle_letter`): `N6A_CIRCLE_01..03`
  - N6B (`centered_cross`): `N6B_CROSS_01..03`
- Ausgabeordner: `artifacts/images_to_convert/n6_variations`
- Katalog: `artifacts/converted_images/reports/n6_variation_catalog.csv`

## Kurzfazit
Die Variationssuite ist reproduzierbar generierbar und liefert den dokumentierten Startkatalog als Grundlage für den nächsten Schritt (automatisierbarer Vergleichslauf inkl. Qualitätsmetriken).
