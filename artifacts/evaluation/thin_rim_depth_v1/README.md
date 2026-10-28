# SEARCH-STRUCTURE-01: dünne Kontur-Tiefenbelege

Branch `codex/search-structure-thin-depth-evidence-2026-10-27`, Basis `76087bcdb`.
[Umsetzung und Keras-Einordnung](../../../docs/next_arbeitspaket_2026-10-27_thin_rim_depth.md).

| Echte CLI-Kohorte | Vorher | Nachher |
| --- | --- | --- |
| Seed 529713, zwei Kinder, eckig, helle Konturen, gleiche Füllfarbe | 11/12 | 12/12 |
| Zusätzlicher Seed 853197, gleicher Umfang | nicht gemessen | 12/12 |
| Seed 529713, Original und 16 Varianten | nicht gemessen | 17/17 |

Alle Konvertierungen verwenden fünf Sekunden pro Bild und Suchseed 17.
Native Objektzahl/-geometrie/-Reihenfolge, lokale Regionen und vollständige
Rasterqualität werden mit den unveränderten unabhängigen Prüfern bewertet.
Die Eingaben wurden vor der Runtime-Änderung erzeugt. Der vollständige
Vorherlauf wurde mit dem ursprünglichen Produktionsmodul wiederholt;
ein früherer, während der Entwicklung gestarteter Lauf zählt nicht als
kontrollierter Vergleich. Zusatzseed und Varianten sind zusätzliche
synthetische Kontrollen, keine neuen unabhängigen realen Familien.

`summary.json` enthält Eingabehashes, Runtime-Hashes und die zwölf gepaarten
Ergebnisse. `checks.json` enthält Prüfbefehle, Laufzeiten und Exit-Codes.
Der vollständige finale Regressionsblock besteht **215/215**, das Kernprofil
**42/42**, jeweils Exit 0. Ein früherer unterbrochener Regressionsträger ohne
Endergebnis wird nicht als Abnahme gezählt. Die vollständige Standardsuite
wurde nicht ausgeführt.
Die Rohberichte, Raster, SVGs und Logs liegen lokal unter `.tmp/thin-depth-*`.
Zum Wiederholen neue, noch nicht vorhandene Zielverzeichnisse wählen:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --prepare .tmp/thin-depth-inputs --seed 529713 --children 2 --outlines --same-fill
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/thin-depth-inputs --output .tmp/thin-depth-after --require-all
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 853197 --children 2 --outlines --same-fill
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 529713 --children 2 --outlines --same-fill --variations
```

Gegenproben erhalten konservative Ablehnungen bei fehlenden oder
widersprüchlichen Konturen, Drittobjektverdeckung, weniger als fünf
Rasterpixeln, zu geringer Randfläche und Fremdfarben.
Die übergeordnete P0-Aufgabe, allgemeine Komposition und unabhängige reale
Abnahme bleiben offen. Archivpaare werden weder erweitert noch geändert.
