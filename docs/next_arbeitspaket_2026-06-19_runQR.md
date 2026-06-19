# Nächstes Arbeitspaket – IDO-16 Globale Konfiguration v1 Run QR (2026-06-19)

## Ziel

Run QR startet nach IDO-15 das nächste dokumentierte Arbeitspaket aus
`docs/image_description_only_tasks.md`: Eine kleine, versionierte globale
Konfiguration soll Primitive-Schwellen, Kostenfunktionsgewichte, Budgets und
Unsicherheitsgrenzen beschreiben, ohne bild- oder variantenbezogene Bereiche zu
erlauben.

## Umsetzung

- `docs/vision/global_converter_config_v1.schema.json` definiert den
  katalogfreien JSON-Schema-Vertrag für globale Primitive-Schwellen,
  Kostenfunktionsgewichte, Budgets und Unsicherheitsgrenzen mit
  `additionalProperties: false`.
- `config/global_converter_config_v1.json` hält die reproduzierbaren
  Standardwerte versioniert im Repository fest.
- `imageCompositeConverterQualityConfig` enthält Loader, Standardwerte und eine
  leichte Schema-/Policy-Validierung, die unbekannte Top-Level-Schlüssel und
  bildbezogene Schlüssel wie `image_overrides`, `variant_name` oder
  `catalog_id` ablehnt.
- Neue Regressionstests prüfen gültige Defaults, Ablehnung unbekannter oder
  bildbezogener Schlüssel und den Fallback auf Defaults bei fehlender oder
  ungültiger lokaler Konfiguration.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_quality_config_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_quality_config_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet unverändert `367 legacy occurrences
remain`, und der gezielte Quality-/Global-Config-Testblock läuft mit `8 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Quality-/Global-Config-Regressionen.
- **Ergebnis:** Exit `0`; `8 passed`, Ratchet weiterhin `367`.
- **Blocker:** Kein neuer technischer Blocker; die Konfiguration ist zunächst als validierter Vertrag und Default-Lader eingeführt.
- **Dokumentation:** IDO-16 besitzt jetzt Schema, Default-Datei und Tests gegen bildbezogene Konfigurationsbereiche.
- **Nächster Schritt:** IDO-17 fortsetzen und verbleibende Runtime-Katalog-IDs aus `src/` schrittweise in generische Pfade oder reine Test-/Reportingdaten verschieben.
