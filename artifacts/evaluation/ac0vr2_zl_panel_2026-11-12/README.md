# Erweiterte Plan-B-Prüfung AC0VR2_ZL_M, 12.11.2026

Die echte CLI hat das unveränderte Original und alle 16 Varianten mit der
vorgegebenen Beschreibung verarbeitet: **13/17 bestanden, Gesamtabnahme verfehlt**.
Das Original besteht. Die Qualitätsgrenzen wurden unverändert übernommen.
Es gab keine technischen Ausführungsfehler oder verbotenen SVG-Zugriffe.

Seed: `4470433890649107824`; 64 Iterationen, Timeout 60 Sekunden pro Fall;
aufsummierte Konvertierungszeit 487,843 Sekunden. Konverter-/Rendererstand:
Git `03e930111829b4c50384d65332822f519d5d0e6b`, zunächst sauberer Checkout.
Während des Laufs wurden ausschliesslich die separate SVG-Uploadprüfung und
ihre Tests geändert, keine Konverter- oder Rendererimplementierung.

| Fall | Verfehlte Messung | Wert | Grenze |
|---|---|---:|---:|
| probe_01 | Vordergrund-IoU | 0,836389 | mindestens 0,85 |
| probe_05 | Konturübereinstimmung | 0,000000 | mindestens 0,72 |
| probe_13 | Konturübereinstimmung | 0,537673 | mindestens 0,72 |
| probe_16 | Konturübereinstimmung | 0,134765 | mindestens 0,72 |

Sämtliche Fälle bestehen beide globalen Pixelfehlergrenzen. Die Vergleichsbilder
zeigen lokale Randfehler. Insbesondere probe_16 zeigt zusätzlich unpassende
Helligkeitsbänder; das zentrale Maximum liegt im Ergebnis bei Zeile 5 statt 9.
Die generische Pixelabnahme allein belegt deshalb keine vollständige inhaltliche
Übereinstimmung. `analysis.json` enthält ergänzende lokale Profilmessungen;
diese verändern keine Abnahmegrenze.

## Diagnose und offene Folgearbeit

Der präzise gerahmte Verlaufsfit akzeptiert die freie Aufgabenbeschreibung
derzeit nicht (`panel_contract` liefert `None`). Die Rückkonvertierung verwendet
den allgemeineren Panel-Fallback und dessen Fortsetzung. Zwei prüfbare Hypothesen:

1. Den vorhandenen präzisen Fit für frei formulierte Graustufenbeschreibungen
   öffnen und seine Initialisierung für verschobene/angeschnittene Rahmen
   verbessern. Ein isolierter Versuch mit den Rasterbytes von probe_01 und
   bereits unterstützter Beschreibungsform liefert ebenfalls `None`; eine
   reine Umformulierung genügt für diesen Fall somit nicht.
2. Im allgemeinen Fallback Rahmen und Verlaufsprofil gemeinsam aus dem sichtbaren
   Raster registrieren und zusätzliche Randlinien/Flächen nur mit lokalem
   Rand- und Profilbeleg zulassen. Das zielt auf die sichtbaren Randabweichungen
   sowie die künstlichen Bänder bei probe_16.

Diese Algorithmuskorrekturen sind offen. Die automatisiert erfasste lokale
Folgeaufgabe steht in `failure_summary.md` und `failure_tasks.json` und wurde
nicht auf GitHub veröffentlicht. Nach einer Korrektur denselben Seed über alle
17 unveränderten Eingaben prüfen, danach unabhängige Fälle und Gegenproben.

## Belege und Wiederholung

`report.json`: alle Messwerte, Beschreibungen, Quell-/Ausgabehashes und CLI-Befehle.
`overview.png`: Eingabe, Ergebnis und vierfach verstärkte absolute Differenz.
Unter jedem Fall bleiben Eingabe, Ausgabe-SVG, Vergleichsbild, CLI-Log,
Suchdiagnosen und Zugriffsaudit lokal erhalten. Grosse Arbeitsdateien bleiben
über die lokale `.gitignore` ausserhalb der Versionskontrolle.

```powershell
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/samples/AC0VR2_ZL_M.svg --description-file artifacts/evaluation/ac0vr2_zl_panel_2026-11-12_description.txt --seed 4470433890649107824 --iterations 64 --timeout-seconds 60 --keep-debug-artifacts --output-dir artifacts/evaluation/ac0vr2_zl_panel_2026-11-12_replay
```
