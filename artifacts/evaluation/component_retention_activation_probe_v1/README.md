# Vorheriger Prüfbestand vor der vollständigen Initialisierungsabschaltung

Dieser frühere Lauf bleibt als Audit-Beleg erhalten. Die definitive
Wiederholung mit dem abschließend korrigierten Schaltpunkt steht unter
`../component_retention_v1`. Die folgenden Angaben beschreiben diesen früheren Lauf.

## Damaliger Bericht

27 echte überwachte Konvertierungen: neue kWh-, mPa- und dB-Raster mit anderen
Größen, Farben und Zeichenabständen; vollständiges Portfolio, ohne
Feinregistrierung und ohne Bots; jeweils drei Seeds und fünf Sekunden Bildbudget.

Alle 27 SVGs bestehen die unabhängig erneut gerenderten Pixel-/Komplexitäts-
und Text-/Strukturprüfungen. Die 377 Archivpaare bleiben unverändert.

Auf diesen Quellen genügen bereits die vorgelagerten Registrierungen. Die
zusätzlichen Bots erzeugen in allen Armen null Vorschläge. Das ist ein
Bestandsschutznachweis für die Beibehaltung, kein positiver Nachweis einer
entbehrlichen oder notwendigen seltenen Fähigkeit. Die drei Familien reichen
auch statistisch nicht für eine Gleichwertigkeitsaussage. Alle Einstufungen
bleiben deshalb unklar; keine Komponente wird entfernt oder nachtrainiert.

```powershell
.venv/Scripts/python.exe -m tools.run_component_value --suite retention --output-dir .tmp/retention-replay --work-dir .tmp/retention-replay-work
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir artifacts/evaluation/component_retention_v1
```
