# Getrennte Abnahme nach vollständiger Initialisierungsabschaltung

27 echte überwachte Konvertierungen: neue kWh-, mPa- und dB-Raster mit anderen
Größen, Farben und Zeichenabständen; vollständiges Portfolio, ohne
Feinregistrierung und ohne Bots; jeweils drei Seeds und fünf Sekunden Bildbudget.

Alle 27 SVGs bestehen die unabhängig erneut gerenderten Pixel-/Komplexitäts-
und Text-/Strukturprüfungen. Die 377 Archivpaare bleiben unverändert.

Die vorgelagerten Registrierungen genügen hier bereits. Kein zusätzlicher Bot
erzeugt Vorschläge. Das belegt Bestandsschutz, aber weder die Entbehrlichkeit
noch eine seltene notwendige Fähigkeit der Bots. Die drei Familien reichen
auch statistisch nicht für eine Gleichwertigkeitsaussage. Die Entscheidung
bleibt Beibehaltung aller sechs Bots bei unklarer Beitragsbewertung.

Versioniert sind diese README, `manifest.json`, `checks.json` und `summary.json`.
Die Zusammenfassung bewahrt Ergebnisse, Unsicherheiten und Quell-/Berichthashes.
Raster, SVGs, Rohereignisse und der vollständige Bericht bleiben lokal erhalten
und werden von Git ignoriert. Ein frischer Checkout muss vor `--verify-only`
zunächst eine eigene Messung erzeugen.

```powershell
.venv/Scripts/python.exe -m tools.run_component_value --suite retention --output-dir .tmp/retention-replay --work-dir .tmp/retention-replay-work
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir .tmp/retention-replay
```
