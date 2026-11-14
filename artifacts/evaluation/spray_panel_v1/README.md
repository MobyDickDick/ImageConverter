# Luftbefeuchter mit getrennten Bauteilgruppen

[Umsetzung, Messwerte und Grenzen](../../../docs/spray_panel_composition_2026-11-14.md).

- [Fertige native SVG](AC0130_L.svg)
- [Original und SVG im Vergleich](comparison.png)
- [Beschreibung für neue Konvertierungen](description.txt)
- Einzelgruppen: [Hintergrund](components/background.svg),
  [Balken](components/left-rail.svg), [gestrichelter Rahmen](components/dashed-frame.svg),
  [Düsen](components/nozzles.svg), [Sprühnebel](components/spray-mists.svg)

`inputs/` bewahrt das Original, die zwei vom Nutzer erläuterten Bildausschnitte
und die vor der Änderung kopierten damaligen Panel-/Runtimequellen.
`input_seal.json` bindet deren Bytes. Die Runtime benutzt nur das vollständige
Raster und den Beschreibungstext. Die Ausschnitte sind Anschauungsbelege.

`annotation.json` enthält den separaten geometrischen Entwicklungsvertrag aus
Nutzerkorrektur und Sichtprüfung. `source_seal.json` bindet die finalen Quellen,
Annotation und gespeicherten Nachweise; der Replay verweigert veränderte
Prüfer-/Annotationsbytes. `summary.json` enthält die echte CLI, beide unabhängigen
Rastermessungen, den Vergleich der alten Ausgabe und alle 29 Gegenproben.
`registration.json` enthält die tatsächlich protokollierten 13 Suchstufen.
Die alten Pixelpass-/SVG-Bytes bleiben unter `baseline.json`/`baseline.svg`
erhalten; sie erfüllen den korrigierten Bauteilvertrag nicht.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_spray_panel --output .tmp/spray-panel-replay
.venv/Scripts/python.exe -m pytest -q tests/test_dashed_rectangles.py tests/test_spray_panel.py tests/test_zigzag_panel_runtime.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` werden benötigt.
Zielordner müssen neu sein. Der CLI-Lauf verwendet einen neutralen Dateinamen,
Seed 0, 120/180 Sekunden Bildzeit und blockiert Referenz-SVG-Zugriffe.
Der vollständige finale Laufbaum mit der präzisierten Bildbeschreibung bleibt
lokal unter `.tmp/spray-panel/final-description`;
vorherige Entwicklungsstände sind separat erhalten.

Abgenommen ist das gezeigte L-Bild mit fünf Düsen und fünf dreistrahligen
Sprühnebeln. `variants.json` dokumentiert die noch negativen direkten M-/S-
Entwicklungsproben. Keine Aussage über unabhängige neue Familien und keine
automatische Archivpromotion. Die bestehende Kategorienauswahl bezeichnet
dieses Motiv jetzt ausdrücklich als komplexe Komposition.
