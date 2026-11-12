# FALLBACK-STRUCTURE-01: Entwicklungsvergleich

Vier vor der Runtimeänderung eingefrorene bekannte Auditfehler; keine neue
unabhängige Familie. `inputs/manifest.json` bindet Originale, Beschreibungen,
damalige generierte SVGs und den alten Fortsetzungscode per SHA-256.
`summary.json` enthält 48 Fortsetzungsvergleiche plus acht echte überwachte
CLI-Läufe, Budgets, aktuelle Codehashes und Kandidatenherkunft. `checks.json`
enthält erneute Originalpixel-/lokale Detailmessungen aller 56 Ausgaben mit
MuPDF und librsvg sowie 16 beschädigte Gegenproben mit beiden Renderern.

Ergebnis: bisheriger Fallback / nur Grundformen / nur Linien / kombiniert
bestehen 0/12, 0/12, 0/12, 3/12 reine Pixelgates. Die Kombination rekonstruiert
AC0303_1_M als Kreis mit zwei lokal bestätigten Innenlinien. CLI-Ablation:
0/4 → 1/4 Pixelpass. Alle Ergebnisse bleiben fachlich unbestätigte Entwürfe.
Die anderen drei Motive bestehen weiterhin nicht vollständig. Alle beschädigten
Gegenproben werden global oder lokal abgelehnt; acht ihrer 32
Rendererprüfungen würden allein die globalen Pixelgates noch bestehen.

Reproduktion in frischen Ausgabeordnern, vom Repository aus:

```powershell
python -m tools.evaluate_fallback_structure --inputs artifacts/evaluation/fallback_structure_v1/inputs --output .tmp/fallback-baseline --arms baseline
python -m tools.evaluate_fallback_structure --inputs artifacts/evaluation/fallback_structure_v1/inputs --output .tmp/fallback-comparison --arms primitives lines combined
python -m tools.evaluate_fallback_structure --inputs artifacts/evaluation/fallback_structure_v1/inputs --output .tmp/fallback-cli --cli
```

Für eine erneute vollständige unabhängige Studie die drei frischen Ausgaben
unter einem gemeinsamen Studienordner als `baseline/`, `comparison/`, `cli/`
anlegen und die unveränderten `inputs/` daneben kopieren. Dann:

```powershell
python -m tools.evaluate_fallback_structure --review STUDIENORDNER
python -m pytest -q tests/test_fallback_structure.py tests/test_search_minimum_effort.py tests/test_image_converter_sample.py
python -m tools.run_pytest_profile core-green
python -m tools.check_no_new_image_id_hardcoding
```

Lokale Abnahme: 139/139 gezielte Regressionen, ein ausdrücklich abgewählter
vollständiger Archiv-Neukonvertierungstest; 42/42 Kerntests. Die Gruppen werden
nicht als unabhängige Gesamtzahl addiert. Der größere Regressionsbefehl lautet:

```powershell
python -m pytest -q tests/test_fallback_structure.py tests/test_search_minimum_effort.py tests/test_image_converter_sample.py tests/test_search_portfolio.py tests/test_conversion_search_scheduler.py tests/test_adaptive_conversion_search.py tests/test_conversion_persistence.py tests/detailtests/test_iteration_initialization_helpers.py tests/detailtests/test_iteration_runtime_helpers.py tests/test_satisfactory_archive.py -k "not every_archived_satisfactory_image_is_reconverted_and_checked"
```

Der eingefrorene Vorhercode reproduziert außerdem den früheren Fehler der
Sample-Regression mit der überschriebenen Produktionsdatei. Die jetzt feste
Fixture `tests/fixtures/accepted_square_damper.svg` besitzt exakt den bereits
am 29.10. dokumentierten SHA-256
`29f5662c7bfa6e1aa5bc8a1d2b44acc2fdbf9afbb94790847a4e954069252eab`.
Kein aktueller Konvertierungsentwurf wurde dafür ersetzt. Der neue CI-Job ist
ergänzt; ein GitHub-Lauf ist noch nicht erfolgt.

Die Fortsetzungsvergleiche verwenden den identischen historischen Ausgangsentwurf,
fünf Sekunden reguläres/maximales Bildbudget und Seeds 17/29/43. Die CLI bekommt
ausschließlich ein PNG der unveränderten dekodierten Original-JPEG-Pixel und die
eingefrorene Beschreibung unter neutralem Dateinamen; keine historischen SVGs.
CLI-Budgets sind acht/zehn Sekunden bei fünf Sekunden Mindestaufwand, Seed 17.
`ICC_FALLBACK_STRUCTURE_MODE=off|primitives|lines|combined` steuert die Ablation;
ohne Variable ist `combined` aktiv. librsvg muss für `--cli` und `--review`
installiert sein. Ausgaben/Protokolle bleiben lokal, die kleinen eingefrorenen
Eingaben und kompakten Belege werden versioniert.

Die ursprüngliche Snapshotquelle liegt lokal unter
`.tmp/catalog-search-audit-20261111-long/`. Sie wird zur Reproduktion nicht
benötigt. `--freeze` dient ausschließlich einer neuen, vor Entwicklung
festgelegten Studie, nicht dem Ersetzen dieser bereits eingefrorenen Eingaben.

[Umsetzung, Ergebnisse, Regressionen und offene Grenzen](../../../docs/next_arbeitspaket_2026-11-12_fallback_structure.md).
