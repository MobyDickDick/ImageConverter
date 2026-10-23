# Native Rechteckszenen mit Verlauf

Die Original-JPEGs und gespeicherten Vorher-/Nachher-SVGs belegen zwei Varianten
einer bekannten verschachtelten Paneltopologie. `manifest.json` bindet Quellen,
SVGs und eigenständige Beschreibungen an Prüfsummen. Die zwei regulären Gates
lassen sich unabhängig erneut ausführen:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene_acceptance artifacts/evaluation/gradient_scene_v1/manifest.json --output .tmp/gradient-gate-replay.json
```

`summary.json` enthält vollständige lokale CLI-Prüfgruppen einschließlich
gescheiterter Variantenversuche. Deren Rohdaten liegen unter `.tmp/real06/`;
ein frischer Checkout erzeugt finale Gegenproben gemäß
[Paketdokumentation](../../../docs/history/next_arbeitspaket_2026-10-22_gradient_scene.md).
`checks.json` dokumentiert Tests, Archivregressionen und erhaltene Prüfsummen.
Die beiden Einzelpanel-Fehler und die fehlende neue reale Familienabnahme
bleiben offen. GENERAL-SCENE-REAL-05 wird damit nicht abgeschlossen.
