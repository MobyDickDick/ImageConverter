# Bot-Suche: tatsächliche lokale Nachweise

- `checks.json`, `tests.xml`: 274 bestandene Tests aus den betroffenen Modulen,
  keine übersprungenen oder fehlgeschlagenen Tests. Kein vollständiger Testlauf
  des Repositories. Prüfsummen und Datensätze aller 377 bestehenden Archivpaare
  stimmen mit dem vorherigen Archivstand überein; keine neue Archivkonvertierung.
- `report.json`: acht echte CLI-Fälle im festen und adaptiven Modus mit Seed
  20261018. Alle acht adaptiven Ausgaben bestehen unabhängige strenge Pixel-
  und Objekt-/Textprüfungen. Beide Läufe melden keine verbotenen SVG-Lesezugriffe.
- `sources/`, `outputs/`: neutrale Eingaben und tatsächliche Ausgaben;
  Prüfsummen stehen im Bericht.
- `adaptive.log`, `fixed.log`, `progress.jsonl`: echte Produktionsprotokolle,
  darunter 20 Verbesserungsnachrichten und sechs individuelle Abschaltungen.
- `bots/`: alle Vorschläge der zwei zusätzlich benötigten Botsuchen mit
  Bewertungen und Bot-Zuständen. Dies ist Suchbeweismaterial mit ausstehender
  Modellabnahme und wird nicht als Vorlagenbibliothek eingelesen.

CLI-Reproduktion aus dem Projektstamm (einen freien Ausgabeordner verwenden):

```powershell
.venv/Scripts/python.exe artifacts/evaluation/adaptive_search_v1/run_evidence.py --output-dir .tmp/bot-search-cli-v1
```

Betroffene Tests:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_search_bots.py tests/test_search_portfolio.py tests/test_adaptive_conversion_search.py tests/test_motor_valve_runtime.py tests/test_primitive_scene_runtime.py tests/test_short_label_disk_runtime.py tests/test_labeled_disk_runtime.py tests/test_filled_symbols_runtime.py tests/test_bottom_stem_letter_disk_runtime.py tests/test_run_catalog_conversion.py tests/detailtests/test_cli_helpers.py tests/detailtests/test_conversion_quality_pass_helpers.py tests/detailtests/test_early_quality_gate_helpers.py
```

Die Fälle umfassen drei Ventilgrößen, Q mit Griff, rF, Lux und zwei unabhängige
Szenen aus Grundformen. Beim ausgewählten Lux-Fit wurden 250 Renderaufrufe im
adaptiven Modus und 492 im festen Modus gemessen. Das ist keine Aussage über
eine allgemeine Beschleunigung oder universelle Szenenrekonstruktion.
