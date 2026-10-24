# Gemischte Überdeckung: synthetische P0-Entwicklungsnachweise

Die [Umsetzungsbeschreibung](../../../docs/next_arbeitspaket_2026-10-24_mixed_overlap.md)
erläutert Algorithmus, Lernschritte und Grenzen. `summary.json` enthält
Prüfsummen und identische native Markierungen des eingefrorenen CLI-Vergleichs:
**0/12 vorher, 12/12 endgültig**, zusätzlicher Rundungslauf **12/12**,
genau eine gekoppelte Plan-B-Vorlage **17/17**. Ein vorausgehender Rundungslauf
mit **11/12** bleibt separat dokumentiert.

`checks.json` bewahrt auch fehlgeschlagene Testläufe: Die breitere Regression
ist wegen bestehender Fünf-Sekunden-Fälle nicht vollständig grün; zwei Fälle
scheitern in der kontrollierten Gegenprobe ebenso auf dem Ausgangscode.
46 neue Prüfungen und 42 Kernprüfungen bestehen. Alle 379 Archivpaare bleiben
unverändert; keine neue reale Familienabnahme.

`generation.json` und das Seed-Protokoll in `config/test_run_seeds.jsonl`
enthalten die Rezepte. Wiederholung, einschließlich automatischer Bereinigung:

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 486213
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 983147 --rounded
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 624819 --rounded --variations
```

Rohbilder, Referenzvektoren, CLI-Ausgaben und Logs bleiben wegwerfbare Arbeitsdaten.
