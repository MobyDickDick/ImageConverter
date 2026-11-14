# Luftbefeuchter – gestrichelter Sprühnebel

- [Neue SVG](AC0130_L.svg)
- [Original, bisherige SVG und neue Strichelung im Vergleich](comparison.png)
- [Aktualisierte Bildbeschreibung](description.txt)
- [Sprühnebel als separate SVG-Gruppe](components/spray-mists.svg)
- [Umsetzung, Zahlen und Grenzen](../../../docs/spray_panel_dashed_mist_2026-11-14.md)

`before.svg` erhält die bereits akzeptierte v1-Ausgabe. `inputs/` und
`input_seal.json` sichern die vor dieser Präzisierung verwendeten Runtimequellen.
Das originale Raster bleibt hashgebunden unter `../spray_panel_v1/inputs/`.
`annotation.json` ergänzt den eigenständigen Vertrag für gestrichelte Strahlen.
`contract_seal.json` bindet Annotation und beide Geometrie-/Strichelungsprüfer.

`summary.json` enthält die frische echte CLI, beide Renderer, alle Teilregionen,
den Vergleich zur vorigen SVG und 48 negative Kontrollen. `registration.json`
bewahrt die tatsächlich protokollierten 28 Suchstufen und alle Strahlmuster.
`source_seal.json` bindet gespeicherte Dateien und ausgeführten Quellstand.
Der vollständige Laufbaum bleibt unter `.tmp/spray-dashed/cli` erhalten.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_dashed_spray --output .tmp/spray-dashed-replay
.venv/Scripts/python.exe -m pytest -q tests/test_dashed_spray.py tests/test_dashed_rectangles.py tests/test_spray_panel.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` sind erforderlich.
Der Zielordner muss neu sein. Der Lauf verwendet den neutralen Dateinamen
`anonymous_dashed_humidifier`, blockiert SVG-Vorlagenzugriffe und prüft jeden
Strahl auf tatsächliche innere Lücken. SVGs behalten drei Rechtecke, fünf
Düsenpolygone und 15 native Linien; die bisherigen Geometriekoordinaten bleiben
unverändert. V1-Dateien werden nicht überschrieben.
