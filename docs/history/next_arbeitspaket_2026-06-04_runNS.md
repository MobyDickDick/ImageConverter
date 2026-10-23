# Nächstes Arbeitspaket – FP-D8 Run NS (2026-06-04)

## Ziel

FP-D8 startet die erste Semantik-Fokusfamilie aus den AC08-Prioritäten. Gewählt
wurde die Fokusfamilie **kleine AC08-Kreisvarianten**, weil der Verbesserungsplan
`AC0811_S`, `AC0814_S` und `AC0870_S` ausdrücklich als Varianten nennt, bei
denen die Kreisdetektion vor der Semantikprüfung abgesichert werden soll.

## Gegenmaßnahme

Die bisher hart codierten Einzelfälle für die Small-Variant-Kreis-Fallbackquelle
wurden zu `AC08_SMALL_CIRCLE_FALLBACK_FAMILIES` gebündelt. Der Semantic-
Primitive-Check nutzt diese Familie nur, wenn alle Schutzbedingungen erfüllt
sind:

1. `ac08_small_variant_mode` ist aktiv,
2. der Kreis ist semantisch nicht deaktiviert,
3. die Basisfamilie gehört zur AC08-Small-Circle-Fallbackliste,
4. Hough- und Foreground-Mask-Kreisdetektion haben keinen Kreis geliefert,
5. die erwartete Kreisringregion enthält genügend Foreground-Belegung und
   Winkelsektorabdeckung.

Damit bleibt der Fallback ein abgesicherter Notpfad statt einer generellen
Kreisannahme, ist aber nicht mehr auf drei verstreute Sonderfälle beschränkt.

## Sicherung

| Check | Befehl | Exit | Ergebnis |
| --- | --- | ---: | --- |
| Fokus-Regression | `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_detect_semantic_primitives_reports_small_circle_family_fallback_source tests/detailtests/test_semantic_family_rules_helpers.py tests/detailtests/test_semantic_ac08_family_helpers.py` | `0` | `12 passed in 2.14s`; der neue parametrische Test belegt `circle_detection_source=family_fallback` für `AC0811_S`, `AC0814_S` und `AC0870_S`, wenn Hough-/Foreground-Kreisdetektion bewusst deaktiviert sind. |
| Kernsuite | `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs` | `0` | `695 passed in 8.05s`; keine neue Kernregression. |
| Syntaxcheck | `python -m compileall src tests` | `0` | Alle Python-Dateien in `src` und `tests` kompilieren erfolgreich. |

## Ergebnis

- FP-D8-1 ist erfüllt: Die Fokusfamilie ist gewählt und explizit als kleine
  AC08-Kreis-Fallbackfamilie im Code abgebildet.
- FP-D8-2 ist erfüllt: Der gezielte Regressionstest deckt die drei priorisierten
  Startvarianten der Familie gemeinsam ab.
- FP-D8-EXIT ist erfüllt: Familienänderung, Schutzbedingungen und grüner Test
  sind gemeinsam dokumentiert.

## 5-Zeilen-Log

- **Getestet:** Parametrisierter Small-Circle-Fallback-Test, bestehende
  Semantic-Family-Detailtests, vollständige Pytest-Kernsuite und Compileall.
- **Ergebnis:** Fokus-Regression `12 passed`, Kernsuite `695 passed`; alle drei
  Prioritätsvarianten melden im künstlichen Fallbackpfad weiterhin
  `circle_detection_source=family_fallback`.
- **Blocker:** Kein FP-D8-Blocker; die Fallbackfamilie bleibt durch Small-Variant-
  Modus, `circle_enabled` und Ring-/Sektorbeleg begrenzt.
- **Nächster Schritt:** FP-D9 startet mit Plain-Ring `AC0800_*` und einer
  Familienkonsistenzmetrik.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
