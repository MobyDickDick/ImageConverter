# Konturen bei eckiger und gerundeter Überdeckung

Ausgangsstand `4c1e52ba2`.
[Aufgabe, Implementierung und Grenzen](../../../docs/next_arbeitspaket_2026-10-24_overlap_outlines.md).

`inputs/` und `rounded_inputs/` enthalten 24 vor der Runtime-Änderung
gespeicherte Eingaben mit unabhängigen Objektmarkierungen. `before/` und
`rounded_before/` bestehen jeweils 0/12. Die endgültigen Ausgaben in
`after_final/` und `rounded_after_final/` bestehen jeweils 12/12 unter
neutralen Dateinamen. `additional/` und `rounded_additional/` (Seed 927381)
bestehen in den entsprechenden `*_cli_final/`-Ordnern jeweils 12/12.

`plan_b/` enthält genau eine gekoppelte Vorlage plus 16 Varianten.
Der erste vollständige Lauf `plan_b_cli/` besteht 16/17; `probe_08` scheitert
wegen eines durch Mischpixel verzerrten Konturfarbschätzers. Die allgemeine
Korrektur besteht im vollständigen neuen `plan_b_cli_final/`-Lauf 17/17.
Alle Versuche verwenden fünf Sekunden überwachte Bildzeit und Suchseed 17;
Vektorreferenzen sind für die Konvertierung gesperrt.

Die fünf `existing_*_cli_final/`-Kohorten verwenden vorhandene versionierte
Eingaben und bestehen 12/12, 12/12, 12/12, 20/20 und 7/9.
`regression-comparison.json` belegt 63 bytegleiche erfolgreiche SVGs;
`archive-hashes.json` 758 unveränderte Prüfsummen von 379 Archivpaaren.
`tests-final.log` enthält 241 Tests, `contracts.log` 268 weitere Tests.
`rim-tests.log` ist eine darin enthaltene Teilprüfung, keine zusätzliche Zahl.
Zwischenläufe wurden nach der Konturfarbkorrektur vollständig wiederholt;
ihre redundanten erfolgreichen Ausgaben bleiben lokal.
`checks.json` fasst die Ergebnisse zusammen; `package-verification.log`
belegt dieselben 13 Kohorten aus einer separaten Kopie der für Git sichtbaren
Dateien, ohne Zugriff auf die vorherigen unversionierten Nachweise.

Die gespeicherten Eingaben, Ausgaben, Quellprüfsummen, Ergebniszeilen,
Zugriffswächter und Deadlinebelege werden unabhängig nachgeprüft mit:

```powershell
.venv/Scripts/python.exe artifacts/evaluation/overlap_outlines_v1/verify.py
```

Keine neue unabhängige reale Familien- oder Katalogabnahme. Das extrahierte
Teilpaket ist abgeschlossen; SEARCH-STRUCTURE-01 bleibt offen.
