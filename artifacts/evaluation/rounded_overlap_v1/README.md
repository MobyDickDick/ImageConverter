# Gerundete Überdeckung im Verlaufskreis

Ausgangsstand `414da01c0`.
[Aufgabe, Implementierung, Abnahme und Grenzen](../../../docs/next_arbeitspaket_2026-10-24_rounded_overlap.md).

`inputs/` enthält zwölf vor der Runtime-Änderung gespeicherte Raster,
Beschreibungen, Objektmarkierungen und Prüfsummen. `before/` besteht 0/12,
`after/` mit neutralen Namen 12/12. `additional/` und `additional_cli/`
enthalten zwölf zusätzliche Fälle (Seed 381217), Ergebnis 12/12.
`plan_b/` und `plan_b_cli/` enthalten genau eine gekoppelte Vorlage mit
16 Varianten, Ergebnis 17/17. Alle CLI-Vergleiche haben fünf Sekunden
Bildbudget und Suchseed 17; die Referenzvektorwächter bleiben leer.

Die fünf `existing_*_cli/`-Ordner verwenden die versionierten Eingaben aus
den bisherigen Überdeckungs-, Kontur-, Rundungs-, Split- und Restbildpaketen.
Die Ergebnisse bleiben 12/12, 12/12, 12/12, 20/20 und 7/9. Die beiden bekannten
kontrastarmen Fehlschläge bleiben im Nenner. `regression-comparison.json`
belegt 63 bytegleiche erfolgreiche Bestandsausgaben. `archive-hashes.json`
belegt 758 unveränderte Prüfsummen von 379 gespeicherten Paaren, keine neue
Archivkonvertierung.

`tests.log` und `contracts.log` dokumentieren 176 bzw. 196 bestandene Tests,
darunter 26 neue Tests. `checks.json` fasst diese und die lokale 12/12-Probe
des CI-Seeds 391827 zusammen. Die komplette Standardsuite wurde nicht erneut
ausgeführt. `package-verification.json` dokumentiert die unabhängige Abnahme
aus den für Git sichtbaren Dateien in einer separaten Kopie.
`regression.log` erhält einen falschen Evidenzpfad im ersten Vergleichsskript;
`regression-resume.log` dokumentiert die erfolgreiche Fortsetzung nach Korrektur.

Abgeleitete Raster und redundante Berichte bleiben lokal. Die gespeicherten
Quellen, tatsächlichen Ausgaben, Ergebniszeilen, Zugriffswächter und
Deadlinebelege sind mit folgendem Befehl erneut abnehmbar:

```powershell
.venv/Scripts/python.exe artifacts/evaluation/rounded_overlap_v1/verify.py
```

Keine neue reale Familien- oder Katalogabnahme. Das extrahierte Teilpaket ist
abgeschlossen; das übergeordnete SEARCH-STRUCTURE-01 bleibt offen.
