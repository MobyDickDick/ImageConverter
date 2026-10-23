# Nächstes Arbeitspaket – SE0041_1 Square-Badge-Parametrisierung Run TA (2026-06-26)

Run TA rotiert nach Run SZ auf den in `PLAN_B_KANDIDATEN.md` dokumentierten
Folgekandidaten `SE0041_1`. Fokus ist, den in Run SU eingeführten katalogfreien
Square-Badge-Contract nicht nur im Parser und Renderer, sondern auch im
Semantic-Badge-Parametrisierungspfad nutzbar zu machen.

## Änderungen

- Aliasbasierte Semantic-Badge-Beschreibungen merken sich nun ihre neutrale
  Referenzquelle als `badge_param_source_ref`, damit Varianten mit erfundenem
  oder nicht direkt unterstütztem Namen weiterhin die Referenzparametrisierung
  verwenden können.
- Der Semantic-Badge-Runtimepfad kann für Varianten mit dokumentierter
  Referenzquelle Badge-Parameter aus dieser Quelle erzeugen und anschließend den
  lokalen `head_style=square_badge` anwenden, ohne eine neue Bild-ID in `src/`
  einzuführen.
- Für Square-Badge-Varianten wird die Kreis-Elementvalidierung durch einen
  neutralen Geometrie-Seed übersprungen, weil die Beschreibung ausdrücklich eine
  viereckige Kopfkontur statt einer runden Kopfkontur verlangt.
- Die erklärende Square-Badge-Elementnotiz wurde so neutralisiert, dass sie nicht
  erneut eine Kreis-Erwartung in der semantischen Strukturprüfung auslöst.

## Artefakte

- Isolierter Repro-Ausgabeordner: `/tmp/ic-se0041-runTA5`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py -k 'se0041_square_badge_override or square_badge_head'` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und meldet weiterhin `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0041-runTA5 --start SE0041 --end SE0041 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün.

## Ergebnis

`SE0041_1` besitzt nun einen ausführbaren katalogfreien Semantic-Badge-Pfad für
aliasbasierte Square-Badge-Varianten. Der Lauf fällt für die Variante nicht mehr
auf `manual_review_elementwise_symbol_fit` zurück, sondern rendert direkt über
`head_style=square_badge`. Die isolierte harte Pixelmetrik bleibt mit
`Mean-Delta²=30585.052734` noch oberhalb der vorherigen elementweisen Annäherung;
das nächste Paket sollte daher entweder den Square-Badge-SVG-Seed weiter an
Rasterfläche, Stiel-/Armgeometrie und Antialiasing anpassen oder auf
`GE9012_6M` rotieren.
