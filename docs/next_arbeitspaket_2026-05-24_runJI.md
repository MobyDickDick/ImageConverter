# Nächstes Arbeitspaket – Run JI (2026-05-24)

## 1) Nächste dokumentierte Aufgabe (TB-A3)
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Ergebnis:
  - `1 skipped, 5 warnings`, Exit `0`.

## 2) Finale Zusatzaufgabe (Qualitäts-Gate für `images_to_convert`)
- Ziel:
  - Alle Bilder im Ordner `artifacts/images_to_convert` müssen in der geforderten Qualität nach SVG konvertierbar sein.
- Verbindliche Regel bei Nichterfüllung:
  - Wenn ein Bild *nicht* in ausreichender Qualität konvertierbar ist, wird es **nicht automatisch** entfernt.
  - Die Entfernung erfolgt ausschließlich manuell und konsistent durch dich:
    1. Bilddatei aus `artifacts/images_to_convert` entfernen.
    2. Zugehörigen Eintrag in den Bildbeschreibungen (`artifacts/images_to_convert/Finale_Wurzelformen_V3.xml`) entfernen.
- Prüfschritt für die Arbeitsroutine:
  - Die Liste `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv` wird als kuratierte Nacharbeitsliste verwendet.

## 3) Zusätzlicher Testlauf
- Befehl:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest tests/test_satisfactory_regression_battery.py -q`
- Ergebnis:
  - `1 passed, 2 skipped, 5 warnings`, Exit `0`.

## Fazit
Das nächste dokumentierte Arbeitspaket wurde ausgeführt. Zusätzlich ist die finale Qualitätsaufgabe für `images_to_convert` als verbindliche, manuell zu kuratierende Gate-Regel dokumentiert (ohne Auto-Löschung).
