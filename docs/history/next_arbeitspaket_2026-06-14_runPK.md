# Nächstes Arbeitspaket – T6.1.c AC08-Kombi-Smoke Run PK (2026-06-14)

## Ziel

Run PK schließt das älteste noch offene Teilpaket der priorisierten
Langläufer-Inventur: Der kombinierte AC08-Smoke-Test muss `AC0811_L` und
`AC0812_M` real konvertieren, darf keine `*_failed.svg` erzeugen und muss
isoliert unter dem T6.1-Budget von 240 Sekunden bleiben.

## Ursache des bisherigen Skips

Der Test erwartete beide Raster-Fixtures direkt unter
`artifacts/images_to_convert/`. `AC0811_L.jpg` liegt inzwischen jedoch im
Unterverzeichnis `nonconvertable/`, während `AC0812_M.jpg` weiterhin im
Hauptverzeichnis liegt. Dadurch endeten die bisherigen Verifikationen trotz
vorhandener Fixtures ausschließlich als `skipped`.

## Umsetzung

Der Smoke-Test löst die beiden dokumentierten Fixture-Pfade explizit auf und
kopiert nur die zwei Rasterbilder sowie die Beschreibungsdatei in ein
temporäres Eingabeverzeichnis. Damit bleibt der Produktionsbestand
unverändert, der Lauf ist von weiteren AC08-Dateien isoliert und
`selected_variants` prüft weiterhin ausschließlich die zwei vorgesehenen
Referenzen.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 240 env PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest \
tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg \
-q
```

| Kriterium | Gefordert | Run PK |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=240s` | `3.26s` |
| Wandzeit | `<=240s` | `4.059s` |
| `AC0811_L.svg` | vorhanden | vorhanden |
| `AC0812_M.svg` | vorhanden | vorhanden |
| `*_failed.svg` | keines | keines |

Die historische T6.1-Laufzeit von `377.98s` sinkt damit um rund `99.14 %`.
T6.1.a und T6.1.b waren bereits abgeschlossen; mit T6.1.c ist nun auch die
übergeordnete Aufgabe T6.1 erledigt.

## 5-Zeilen-Log

- **Getestet:** Realer kombinierter AC08-Smoke über `AC0811_L` und `AC0812_M` mit 240-Sekunden-Timeout.
- **Ergebnis:** Exit `0`, `1 passed in 3.26s`, beide regulären SVGs vorhanden und keine fehlgeschlagenen Fallback-SVGs.
- **Blocker:** Kein Blocker für T6.1; weitere eigenständige T6-Langläufer bleiben im Backlog.
- **Nächster Schritt:** T6.2 (`AC0837_L`) als nächsten sehr hoch priorisierten Langläufer isoliert unter das 120-Sekunden-Ziel bringen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]'`.
