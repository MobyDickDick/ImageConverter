# Nächstes Arbeitspaket – AC0100 referenzbasierte Heizelement-Varianten Run TY (2026-06-28)

Run TY greift die aktuelle AC0100-Rückmeldung auf: `AC0100_L` ist brauchbar,
`AC0100_M` und `AC0100_S` dürfen aber nicht durch fest abgespeicherte
Bilddaten stabilisiert werden. Der Fix bleibt deshalb katalogfrei und erweitert
den allgemeinen Non-Composite-Pfad für beschreibungsbasierte Heizelemente.

## Änderungen

- Referenzbasierte Heizelement-Beschreibungen (`Wie AC0010: Heizelement ...`)
  werden weiterhin nicht hart gegenüber dem gemessenen Raster-Fit bevorzugt.
- Gleichzeitig dürfen solche Varianten nun den allgemeinen Geometry-IR-
  Rasterregistrierer durchlaufen. Damit ist die Beschreibung weiterhin der
  Algorithmus-Seed, während größen-/rasterabhängige Anpassungen lokal anhand des
  Eingabebildes optimiert werden können.
- Ein Detailtest sichert die beabsichtigte Kombination aus Referenzvariantenerkennung,
  Heizelement-Geometry-IR und pixelbasierter Kandidatenauswahl ohne neue Bild-ID-
  Sonderfälle.

## Sicherung

- `pytest -q tests/detailtests/test_non_composite_runtime_helpers.py tests/detailtests/test_description_contract_helpers.py`
  läuft grün mit `111 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py`
  läuft grün und meldet `0 occurrences`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0100-final --start AC0100 --end AC0100 --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml --deterministic-order`
  läuft grün. Die isolierten AC0100-Metriken bleiben stabil: `AC0100_L`
  `Mean-Delta²=949.427795`, `AC0100_M` `Mean-Delta²=828.678345`, `AC0100_S`
  `Mean-Delta²=1213.068726`.

## Ergebnis

Der AC0100-Pfad speichert keine Varianten-Pixeldaten ab und führt keine neue
Bild-ID-Weiche ein. Referenzbasierte Heizelemente behalten die pixelbasierte
Auswahlmöglichkeit, können aber zusätzlich über die generische Geometry-IR-
Registrierung angepasst werden. Weitere Qualitätsverbesserung sollte als
allgemeine Erweiterung der Heizelement-Elementprobes erfolgen.
