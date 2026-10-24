# Historische synthetische Auswertung

Die Messwerte in `checks.json` dokumentieren den damaligen Stand.
Die erzeugten Eingaben, SVG-Ausgaben, Logs und mehrfachen Archivhashlisten
wurden auf Benutzerwunsch am 24. Oktober 2026 entfernt. Sie sind nicht mehr
als gespeicherte CLI-Rohentscheidungen offline nachprüfbar.

Generatoren und Seeds stehen zentral in
[config/test_scene_replays.json](../../../config/test_scene_replays.json).
Ein dort ausdrücklich unbekannter historischer Seed erlaubt keine exakte
Reproduktion des damaligen Falls. Neue Ausgaben werden mit dem aktuellen
Code erzeugt und unabhängig geprüft, danach wieder gelöscht:

```powershell
python -m tools.run_seeded_scene_check GENERATOR --seed SEED GENERATOROPTIONEN
```

[Änderung, Grenzen und Bereinigungsregeln](../../../docs/next_arbeitspaket_2026-10-24_multilayer_cleanup.md).
