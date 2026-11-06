# Gerundete Elternrechtecke: synthetische Komposition und Renderergrenze

Paket **SEARCH-STRUCTURE-ROUNDED-PARENT**, Ausgangscommit `fbb86fa59`.
[Umsetzung, Testsignal und Grenzen](../../../docs/next_arbeitspaket_2026-11-06_rounded_parent.md).
Status: **Review**, synthetischer Teilabschluss mit gesondert offenem Rendererfehler.

| Kohorte | Seed | CLI-Abnahme mit bisherigem MuPDF-Rasterweg |
| --- | ---: | ---: |
| Vorher, zwölf eingefrorene synthetische Eingaben | 624873 | 0/12 |
| Nachher, dieselben Raster/Beschreibungen/Markierungen | 624873 | 12/12 |
| Zusätzlicher Entwicklungsseed | 981347 | 12/12 |
| Eine gekoppelte Plan-B-Variantenkohorte | 853291 | 17/17 |

Alle 41 neuen Ausgaben bestehen zusätzlich die unabhängigen nativen
Radius-/Objekt-/Box-/Kontur-/Verlaufs-/Reihenfolgeprüfungen und lokalen/globalen
Rastergates. Beide Vektorzugriffswächter bleiben aktiv. Das Bildbudget beträgt
fünf Sekunden; die Strukturagenda bleibt auf 96 Zustände und acht Kinder begrenzt.

**Zusätzliche unabhängige Renderer-Gegenprobe: keine vollständige Abnahme.**
librsvg besteht 41/41 globale Prüfungen, aber nur 121/164 lokale Elternecken;
28/41 Bilder bestehen alle vier Ecken. Mit MuPDF bestehen dieselben lokalen
Prüfungen 164/164. Ein gleichmäßig gefülltes natives Rechteck mit Radius 30
reproduziert den bestehenden Fehler ohne Konverter: Eckverlust analytisch
193,1417 Quadratpixel, MuPDF 234,9529, librsvg 193,8471.
Die Korrektur ist das [nächste P0-Paket](../../../docs/next_arbeitspaket_2026-11-06_rounded_renderer.md).

`summary.json` sichert Eingabe-/Beschreibungs-/Markierungs-/Ausgabehashes,
Vorher-/Nachher-Metriken, Runtimehashes, Bildzeiten und alle unabhängigen
Renderer-Eckprüfungen. `checks.json` enthält Befehle, Exitcodes und
Regressionsergebnisse. Rohdaten, CLI-Bäume und Logs bleiben lokal in
`.tmp/rounded-parent/`; die Generatoren erlauben eine Wiederholung in frischen
Ordnern. Die gemeinsame Regression besteht 1.070/1.070 Prüfungen, eine zusätzliche
Budgetgegenprobe 1/1 und das separate Kernprofil 42/42, jeweils Exit 0 ohne
Überspringung. 50 neue Prüfungen sind damit abgedeckt. Der große Lauf endet nach
754 Sekunden unter einem äußeren 1.500-Sekunden-Guard. Python-Syntax, Diff- und
Verweisprüfung sowie die schreibfreie historische Reserveprüfung bestehen.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --prepare .tmp/rounded-parent-replay-inputs --seed 624873
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --inputs .tmp/rounded-parent-replay-inputs --output .tmp/rounded-parent-replay-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --inputs .tmp/rounded-parent-replay-inputs --output .tmp/rounded-parent-replay-cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.audit_rounded_parent_renderers --inputs .tmp/rounded-parent-replay-inputs --output .tmp/rounded-parent-replay-cli --report .tmp/rounded-parent-replay-renderers.json
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_rounded_parent --seed 981347
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_rounded_parent --seed 853291 --variations
```

Nur synthetische Entwicklung; keine neue reale Familienabnahme. HC0010 und Rail
bleiben `sealed_unrun` ohne Konvertierungsversuch. Übergeordnete P0-Komposition
und reale Gesamtabnahme bleiben offen. Katalog und Konvertierungsarchiv werden
nicht verändert. Die CI wiederholt die neuen Szenentests und den Zusatzseed;
die librsvg-Gegenprobe ist eine lokal gespeicherte zusätzliche Diagnose.
