# Beobachtete offene Kurven im produktiven Fallback

[Umsetzung und Grenzen](../../../docs/next_arbeitspaket_2026-11-15_curve_proposals.md).

`manifest.json` und `seal.json` sichern die vor der Runtimeänderung erstellten
sechs sichtbaren Konstruktionen, unabhängigen Annotationen, PNGs und drei
bisherigen Runtimequellen. `baseline/` bleibt als ursprüngliche lokale
Messung erhalten. Die Kurvenprüfer und ihre alten Freezes wurden nicht geändert.

`results/review/replay_baseline` und `results/review/replay_current` sind der gepaarte
Vergleich mit dem endgültigen Evaluator: 18 identische Eingaben/Seeds,
fünf Sekunden und höchstens 32 Strukturvorschläge. Beide Rastergates
verbessern sich von 0/18 auf 18/18; der vollständige unabhängige native
Vertrag von 0/18 auf 3/18. `results/baseline` und `results/current` halten
die erste Wiederholungsmessung lokal fest und werden nicht versioniert.

`results/review/controls`: 54 unabhängige Ablehnungen; 42 lokale Ablehnungen
unter beiden Renderern und sechs rasteridentische verdeckte Inventarfehler.
`results/review/legacy`: 15 alte Szenen, vier Vorschläge, null vollständige Inventare.
Die Runtime liest keine dieser Annotationen.

`results/review/cli` enthält SVGs und Zusammenfassung der ersten echten CLI-Reihe
unter gleichzeitiger Testlast, darunter zwei Zeitlimits mit erhaltenen SVGs.
`results/review/cli_serial`
ist die separat erhaltene serielle Wiederholung mit denselben Eingaben,
Seed 17 und fünf Sekunden; alle sechs Prozesse schliessen regulär ab.
`results/review/process_summary.json` sichert die ursprünglichen
`batch_failure_summary.csv`-Einträge und `clean_process_completion`.
Sie unterscheiden Prozessabschluss und nachträgliche
Prüfung gespeicherter SVGs. Die SVG-Prüfung beider Reihen ergibt 6/6
Rasterpässe und 1/6 vollständige unabhängige Kurvenverträge. Keine
SVG-Referenzzugriffe und keine Modellfreigaben.

`results/review/seal.json` bindet 123 kompakte Belege: SVGs, Zusammenfassungen,
Runtimequellen, Evaluator,
Konstruktionen und Testnachweise an SHA-256. Die Tests und
`tools.verify_curve_proposal_evidence.verify_results()` prüfen diese Belege.
Die vollständigen CLI-Rohbäume bleiben lokal ausserhalb des versionierten
Reviewordners erhalten; sie sind keine zusätzliche Kohorte.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_curve_proposals --baseline --output .tmp/curve-baseline-replay
.venv/Scripts/python.exe -m tools.evaluate_curve_proposals --output .tmp/curve-current-replay
.venv/Scripts/python.exe -m tools.evaluate_curve_proposals --controls --output .tmp/curve-controls-replay
.venv/Scripts/python.exe -m tools.evaluate_curve_proposals --legacy --output .tmp/curve-old-scenes-replay
.venv/Scripts/python.exe -m tools.evaluate_curve_proposals --cli --output .tmp/curve-cli-replay
.venv/Scripts/python.exe -m pytest -q tests/test_curve_proposals.py
.venv/Scripts/python.exe -m tools.verify_curve_proposal_evidence
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` sind erforderlich.
Zielordner müssen neu sein. Die schmale synthetische Entwicklung ersetzt
weder Katalogmessung noch menschlichen Annotationsaudit. Reserven bleiben
gesperrt; keine automatische Archivpromotion.
