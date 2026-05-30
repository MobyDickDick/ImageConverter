# Nächstes Arbeitspaket – Run MC (2026-05-29)

Dieses Arbeitspaket rotiert nach Run MB auf den nächsten dokumentierten
Plan-B-Kandidaten `AC0150_L.jpg` und nutzt die vorhandene Ketten-/Geometry-IR-
Architektur, damit der echte Non-Composite-Call-Path die fachliche Beschreibung
als strukturierte Vektorkette statt als generisches Diagonal-/Plus-Minus-Symbol
rendert.

## 1) Nächste dokumentierte Aufgabe: AC0150-L-Beschreibung als Geometry-IR

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führt `AC0150_L.jpg` als nächsten einfachen
    L-Kandidaten.
  - Der vorgeschaltete Einzelrun erzeugte zwar ein SVG, protokollierte aber noch
    `status=non_composite_elementwise_symbol_fit` und nutzte damit die generische
    strukturierte Symbolannäherung statt der konkreten AC0150-Beschreibung.
- Umsetzung:
  - Die Geometry-IR erkennt nun hochkante Rechtecke mit horizontalem
    dunkel-hell-dunkel-Verlauf als schmalere vertikale Box.
  - Beschreibungen mit drei horizontalen Linien erzeugen ein neues
    `HorizontalRuleSet`-IR-Element.
  - Die AC0150-Formulierung `Oben-Mitte nach Rechts-Mitte nach Unten-Mitte`
    erzeugt ein neues `OrthogonalPolyline`-IR-Element.
  - Der Non-Composite-Fallback bevorzugt beschreibungsgetriebene Geometry-IR für
    diese erweiterten Elemente und fällt nur sonst auf die bisherige generische
    Element-Fit-Annäherung zurück.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py tests/detailtests/test_chain_telemetry_helpers.py`
- Ergebnis:
  - Exit `0`
  - `35 passed in 0.35s`
- Abdeckung:
  - AC0150-artige Beschreibungen werden als `HorizontalGradient`, `RectBorder`,
    `HorizontalRuleSet`, `OrthogonalPolyline` gemappt.
  - Das SVG-Rendering enthält stabile IDs für die drei Horizontalregeln und die
    rechte orthogonale Linie.
  - Der echte Non-Composite-Helfer wählt den neuen
    `non_composite_description_geometry_ir`-Pfad für AC0150-artige Beschreibungen.

## 3) AC0150-L-Repro im externen Output-Verzeichnis

- Befehl:
  - `rm -rf /tmp/ic-ac0150-runmc; PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0150-runmc --start AC0150_L --end AC0150_L --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `/tmp/ic-ac0150-runmc/converted_svgs/AC0150_L.svg` wurde erzeugt.
  - Kein Failure-Eintrag in `/tmp/ic-ac0150-runmc/reports/batch_failure_summary.csv`.
  - Validation-Log enthält `status=non_composite_description_geometry_ir`,
    `geometry_ir_element_count=4`, `HorizontalRuleSet` und `OrthogonalPolyline`.
  - Das SVG enthält die IDs `horizontal_rule_set_1..3` und
    `right_side_orthogonal_line`.

## 4) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `571 passed, 5 warnings in 6.38s`

## Fazit

Der nächste dokumentierte Plan-B-Kandidat `AC0150_L.jpg` nutzt im echten
Call-Path nun eine beschreibungsgetriebene Geometry-IR mit den konkret benötigten
Horizontal- und Rechtslinien-Primitiven. Der Einzelrun bleibt grün und die
Vollsuite ist weiterhin stabil.
