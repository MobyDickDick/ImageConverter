# Sample Pair Validation Run (N5) — 2026-05-06 Run 01

- Anlass: N5-Akzeptanzkriterium (reproduzierbarer Batch-Check inkl. Report) weiter bearbeiten.
- Kommando:
  - `python -m tools.validate_sample_pairs artifacts/images_to_convert/samples --render-missing-jpeg --reference-dir artifacts/images_to_convert --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-06.csv`
- Ergebnis:
  - Ausgabe meldet zunächst `svg_count=15 jpeg_count=15` (Render-Schritt erzeugt fehlende JPEGs).
  - Lauf endet anschließend mit `ImportError: cannot import name '_imaging' from 'PIL'` aus `vendor/linux-py310/site-packages/PIL`, da die vendored Pillow-Binaries nicht zur aktiven Python-Version passen.
  - Exit-Code: `1`.
- Fazit:
  - Der Batch-Check ist funktional bis zum Diff-Schritt, aber im aktuellen Laufumfeld durch ABI-Mismatch der vendored Pillow-Extension blockiert.
  - N5 bleibt offen; nächster Schritt ist eine lauffähige Pillow/Interpreter-Kombination (z. B. passendes venv) für den automatischen Vergleichslauf mit CSV-Report.
