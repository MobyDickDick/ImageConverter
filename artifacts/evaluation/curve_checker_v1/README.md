# FALLBACK-GROUPS-CURVES-07 – separater Kurvenprüfer

[Umsetzung und Abnahmegrenzen](../../../docs/next_arbeitspaket_2026-11-15_curve_checker.md).

`manifest.json` enthält die extern konstruierten positiven XML-Szenen,
Annotationen und alle beschädigten XML-Gegenproben. `seal.json` bindet sie
zusammen mit `checker.py`, `constructions.py`, `evaluator.py` und den
unveränderten bisherigen Geradenprüfern an SHA-256-Prüfsummen. Die Ausführung
verlangt identische aktuelle und eingefrorene Quellen. Ein neuer Freeze
überschreibt keinen bestehenden Zielordner.

`results/summary.json`: 15/15 positive Szenen, 285/285 zurückgewiesene
Gegenproben, 45 davon mit MuPDF und librsvg rasteridentisch. In jedem
Rastervergleich werden Kandidat und Positivszene innerhalb desselben
Renderers verglichen. Daraus folgt keine allgemeine Pixelgleichheit
zwischen MuPDF und librsvg. Die lokalen PNGs der drei Grundkonstruktionen
sind zusätzliche Sichtkontrollen, keine Oracles.

`proposals/summary.json`: nach dem Freeze durchgeführte begrenzte Untersuchung
des bestehenden produktiven Gruppengenerators, 15 Eingaben und null Vorschläge.
Verwendete Runtimequellen, Studienwerkzeug und Prüfer-Freeze sind hashgebunden.
Keine vollständige Konvertierung, kein Produktionsumbau und keine Freigabe.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_curve_checker --output .tmp/curve-checker-replay
.venv/Scripts/python.exe -m tools.probe_curve_groups --output .tmp/curve-groups-replay
.venv/Scripts/python.exe -m pytest -q tests/test_curve_checker.py tests/test_segment_checker.py tests/test_fallback_checker.py tests/test_fallback_cleanup.py tests/test_real_composition_holdout_freeze.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` sind erforderlich.
Zielordner müssen neu sein. `--freeze NEUER_ORDNER` erstellt einen neuen
Entwicklungsfreeze. Ein Replay liest seine XMLs aus dem geprüften Manifest,
statt neue Szenen oder Beschädigungen zu generieren.

Die vollständige verdeckte Geometrie ist aus synthetischer Konstruktion
bekannt; ausgelassene Kurven bleiben Ablehnungen. Drei Konstruktionen mit
fünf Transformationen sind keine 15 realen Familien. Alle Reserven bleiben
gesperrt. Menschlicher Annotationsaudit und unabhängige reale Abnahme fehlen.
Produktive Kurven-/Anschlussvorschläge bleiben das nächste Paket.
