# Nächstes Arbeitspaket – IDO-17 CO₂-Layout-Profil-De-ID Run RX (2026-06-22)

## Anlass

Run RX setzt nach Run RW das nächste kleine IDO-17-Bereinigungspaket fort:
verbleibende Katalog-ID-Vorkommen in `src/` werden weiter reduziert, ohne
konkrete Bildgeometrie in neue Konfiguration auszulagern.

## Umsetzung

- Das CO₂-Layout entscheidet die Breitenbegrenzung für zentrierte tiefgestellte
  CO₂-Badges nicht mehr über `badge_symbol_name` oder `variant_name`, sondern
  über das neutrale Parameterprofil `co2_width_profile=centered_subscript`.
- Die bestehende AC08-Finalisierung setzt dieses Profil nur dort, wo bereits die
  semantischen Eigenschaften `text_mode=co2` und tiefgestellter Index aktiviert
  werden.
- Der Detailtest verwendet einen katalogfreien Badge-Namen und prüft die gleiche
  Breitenbegrenzung über das neutrale Profil.

## Nachweis

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_label_helpers.py tests/test_no_new_image_id_hardcoding.py` → `8 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` → `PASS`, `147 legacy occurrences remain`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py --update` aktualisiert die Legacy-Baseline von 148 auf 147 Runtime-ID-Vorkommen.

## Ergebnis

IDO-17 ist weiter reduziert: Die CO₂-Layout-Hilfslogik enthält kein konkretes
Badge-Symbol mehr für die zentrierte Subscript-Breitenkappe. Die verbleibenden
Vorkommen betreffen weiterhin echte Runtime-Dispatches, historische APIs und
Metadatenpfade, die separat neutralisiert werden müssen.
