# SVG-Textbaseline: unabhängige Bestandsprüfung und sechs reparierte Archivpaare

Nachtrag: Die ursprünglichen Windows-Messungen unten bestanden den ersten
Linux-CI-Lauf für AC0721_M nicht. Die aus Originalpixeln bestimmte dünne
Textkontur und die explizite Liberation-Gegenprobe stehen in der
[Folgeevidenz](../svg_text_coverage_v1/README.md). `manifest.json` erhält
zusätzlich die drei geprüften Textkonturen; `summary.json` und `checks.json`
bewahren die ursprüngliche Baseline-Messung.

- `summary.json`: ursprüngliches 60er-Textinventar mit Vorher-/Nachher-Hashes,
  unveränderten Pixelgrenzen, beiden unabhängigen Messungen, tatsächlichen
  Glyphengrenzen und dem Nachweis pixelgleicher Produktionsrenderings.
- `checks.json`: sechs frisch gespeicherte echte CLI-Ausgaben, Originalhashes,
  librsvg-Pixelabnahme und Glyphenvergleich mit den Originalrasterdaten.
- `manifest.json`: genau sechs hashgebundene AC0721-Baselinekorrekturen für
  die reproduzierbare Archiv-Erneuerung. Historische Evidenz bleibt erhalten.

Ergebnis: reguläre Gates 6/6, unabhängige CLI 6/6; die separate interne
Plan-B-Prüfung bleibt wegen AC0721_L-IoU 5/6. Ursprüngliches Inventar:
60 Text-SVGs, 39 `middle`-Angaben, unabhängige Kandidatenprüfung 17/60 → 34/60.
Keine vollständige Abnahme aller Textmodelle; 33 historische Baselineangaben
bleiben zur individuellen Bearbeitung im Archiv. Kein Katalogzahlanstieg.

Die versionierten JSONs speichern jeden Fall in einer Zeile. Wiederholte
Grenzwerte und Komplexitätsprofile stehen einmal auf Berichtsebene;
`complexity_profile` verweist auf den entsprechenden Index. In `checks.json`
stehen die regulären Einzelfälle unter `regular_satisfaction_cases`, ihre
gemeinsamen Gateangaben unter `regular_satisfaction_gate.gate_definitions`.
Messwerte, Hashes und Entscheidungen bleiben vollständig erhalten. Die
ursprünglichen ausführlichen Berichte liegen lokal unter
`.tmp/svg-text-full-evidence-before-compact/`; neue ausführliche Läufe gehören
ebenfalls in `.tmp/`, nicht in einen Commit.

[Umsetzung, Grenzen, Befehle und Tests](../../../docs/next_arbeitspaket_2026-10-28_svg_text_baseline.md).
