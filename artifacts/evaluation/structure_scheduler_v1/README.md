# Fortsetzbare Strukturhypothesen

Basis `b0e6cf8ab`, Branch `codex/search-structure-scheduling-2026-10-23`.
[Umsetzung, Gegenprobe und Restumfang](../../../docs/history/next_arbeitspaket_2026-10-23_structure_scheduler.md).

`cli/` enthält die echte neue CLI-Wiederholung aller neun bekannten synthetischen
Entwicklungseingaben aus `../residual_scene_v1/final-input`, mit fünf Sekunden
überwachtem Bildbudget und Seed 17. Ergebnis: **7/9**, unverändert gegenüber
dem früheren Endstand. Die kontrastarmen Fälle 06 und 07 bleiben negativ.
Das ist keine neue reale Übertragungsabnahme.

Gesichert sind Runtime-Prüfsummen, alle Entscheidungen, die sieben tatsächlichen
SVGs, Workerlogs, unabhängige Zugriffsbelege und Aufsichtsdateien. Die dauerhaft
abgelegten Dateien wurden unabhängig erneut geprüft; abgeleitete Vergleichs-PNGs
sind für diese Nachprüfung nicht erforderlich. Die Quellbilder und Objektmarkierungen
bleiben in der bereits versionierten Eingabeablage.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs artifacts/evaluation/residual_scene_v1/final-input --output artifacts/evaluation/structure_scheduler_v1/cli --verify-only
```

Die Fairnessgegenprobe mit echter Registrierung und injizierter Uhr steht in
`tests/test_residual_scene_search.py`: seriell kein Erfolg im gemeinsamen Budget,
verschränkt vollständiger Erfolg der zweiten Hypothese; Duplikatvermeidung und
Schließen der ersten Hypothese werden zusätzlich geprüft. Diese kontrollierte
Uhr ist keine reale Laufzeitmessung. Der abschließende Regressionslauf besteht
mit 339 Tests; vollständige Standardsuite und Archiv-Neukonvertierung wurden
in diesem Schritt nicht wiederholt.
