# FALLBACK-GROUPS-COMPOSITION-03 – synthetische Szenenkomposition

[Umsetzung und Grenzen](../../../docs/next_arbeitspaket_2026-11-13_fallback_composition.md).
`manifest.json` enthält die sechs vor Runtimeänderung eingefrorenen synthetischen
Ziel-/Ausgangsszenen, feste Rasterregionen und Hashes. `inputs/` bewahrt die drei
tatsächlich damaligen Runtime-Dateien; sie werden beim Baseline-Replay importiert.
`summary.json` enthält 18 alte und 18 neue direkte Messungen, 30 beschädigte
Kontrollen und die sechs überwachten CLI-Ergebnisse mit beiden Renderern.

Die drei Seeds konfigurieren das Portfolio; analytische Vorschläge bleiben
deterministisch. Die Szenen variieren Farbe und fehlerhafte Ausgangsobjekte,
nicht die zwei grundlegenden Konstruktionsfamilien. Da die CLI kein Ausgangs-SVG
verwendet, sind ihre sechs Bilder wiederholte Integrationsfälle dreier
Farbvarianten derselben Anordnung. Direkte Studie: höchstens fünf Sekunden/32 Vorschläge; CLI:
8/10 Sekunden mit fünf Sekunden Mindestaufwand. Keine neue reale Familienabnahme.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_fallback_composition --baseline --output .tmp/composition-baseline-replay
.venv/Scripts/python.exe -m tools.evaluate_fallback_composition --output .tmp/composition-replay
.venv/Scripts/python.exe -m tools.evaluate_fallback_composition --cli --output .tmp/composition-cli-replay
.venv/Scripts/python.exe -m pytest -q tests/test_fallback_composition.py tests/test_fallback_groups.py tests/test_fallback_structure.py tests/detailtests/test_semantic_family_rules_helpers.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10 und die Pakete aus `requirements-dev.txt` sowie `rsvg-convert` werden
benötigt. Zielordner müssen neu sein. Neue positive Studien und CLI-Aufrufe
brechen bei Vollständigkeits-, Budget-, Gegenproben- oder Freigabefehlern ab.
`--freeze` dient ausschließlich der erstmaligen Vorbereitung eines neuen
Entwicklungsstands; die eingecheckten Eingaben werden nicht überschrieben.

Raw-SVGs, Protokolle und vollständige CLI-Bäume liegen lokal unter
`.tmp/fallback-composition-*`. Der ursprüngliche CLI-Fehler vor der
Beschreibungskorrektur ist separat in `summary.json` festgehalten. Weitere
Zwischenversuche bleiben lokal erhalten und zählen nicht als erfolgreiche Abnahme.
Runtime-Verbindungsprüfungen ergänzen die unabhängigen Rastermessungen. Ein
vollständig unabhängiger Semantikprüfer fehlt weiterhin; reale Reserven bleiben
ungetestet und gesperrt. Der bei der erstmaligen Vorbereitung erfasste
Evaluatorhash bezeichnet den damaligen Entwicklungsstand; der finale ausführbare
Evaluator ist separat über `source_sha256` in der Ergebnisdatei gebunden.
