# Portable Cleanup-Inventur und Ignore-Regeln

Der CI-Fehler ließ sich durch simuliert fehlendes `rg` exakt reproduzieren:
`test_cleanup_protects_checkouts_and_runs_changed_after_inventory[False]`
scheiterte an `Files changed`. Die erste Inventur hatte einen Python-Fallback,
das Anwenden rief dagegen zwingend `rg` auf. Dessen `FileNotFoundError` wurde
als Skip-Grund gespeichert. Die Daten blieben erhalten, aber der Vertrag war
verletzt. Beide Phasen verwenden jetzt denselben Python-Dateiwalker, mit
Fehlerweitergabe und Prüfung der Projektgrenzen. Die optionale Beschleunigung
der Metadatensuche bleibt erhalten.

Die Regression läuft mit und ohne `rg`; eine weitere Probe entfernt einen
unveränderten inventarisierten Lauf mit versteckten Dateien und sichert dessen
JSONL-Seed ohne `rg`. Lokal: 12 bestanden, ein Windows-Symlink-Skip.

Die gemeldeten rund 6.000 Dateien sind überwiegend die abgeschlossene
Bestandsbereinigung: Gegen seinen ersten Elternstand enthält Merge
`0bd8e896b` 6.326 Löschungen, neun neue und 26 geänderte Dateien, insgesamt 6.361.
Das war keine erneute Erzeugung von 6.000 Testdateien.

Die zentrale `.gitignore` schließt jetzt Rohdaten **aller** neuen
`artifacts/evaluation/<Studie>/` aus. Nur README, Ignore-Regeln und die
kompakten Dateien `summary.json`, `checks.json`, `generation.json` und
`manifest.json` werden freigegeben. Neue Batchausgaben unter
`artifacts/converted_images/`, `artifacts/pytest/` und weitere Python-Caches
bleiben ebenfalls lokal. Mit `git check-ignore --no-index` wurden neue
CLI-Bäume, Bilder, Logs und temporäre Ausgaben sowie die Gegenproben für
Metadaten, Quellen, Fixtures und akzeptierte SVGs geprüft.

Bereits versionierte historische Evidenz und Testfixtures bleiben versioniert.
Sie pauschal aus Git zu entfernen würde bestehende Abnahmen beschädigen.
Ignore-Regeln verhindern neue Git-Dateien, löschen aber keine Arbeitsdaten.
Für neue Szenenläufe entfernt `tools.run_seeded_scene_check` eigene temporäre
Daten auch nach Fehlern; Seeds bleiben im Journal. Bewusst gewählte
Diagnoseverzeichnisse können mit `cleanup.bat` erst inventarisiert und danach
über `--apply --from-inventory <Inventur>` bereinigt werden. Git-Arbeitskopien,
geänderte und unlesbare Ziele bleiben geschützt.
