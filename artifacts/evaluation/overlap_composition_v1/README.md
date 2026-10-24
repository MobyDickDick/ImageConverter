# Teilweise überlappende Rechteckkinder im Verlaufskreis

Ausgangsstand `6bd8e2406`, Branch `codex/search-structure-overlap-2026-10-23`.
[Aufgabe, Ursachenvergleich, Umfang und Grenzen](../../../docs/next_arbeitspaket_2026-10-23_overlap_composition.md).

`inputs/` enthält die zwölf vor Runtime-Änderung eingefrorenen Raster,
Beschreibungen, native Objektmarkierungen und Prüfsummen. `before/` erreicht
0/12; `after/` erreicht mit neutralen Namen 12/12. `additional/` und
`additional_cli/` enthalten zwölf zusätzliche Fälle (Seed 381217), Ergebnis
12/12. `plan_b/` und `plan_b_cli/` enthalten genau eine gekoppelte Vorlage
mit 16 Größen-/Lagevarianten, Ergebnis 17/17.

Die vier `existing_*_cli/`-Ordner verwenden die versionierten Eingaben aus
`../rounded_outlines_v1/inputs/`, `../rounded_composition_v1/development/`,
`../component_splits_v1/input/` und `../residual_scene_v1/final-input/`.
Ergebnisse: 12/12, 12/12, 20/20 und 7/9. Die beiden kontrastarmen Fehlschläge
bleiben im Nenner. `regression-comparison.json` belegt 51 bytegleiche
erfolgreiche Bestandsausgaben; `archive-hashes.json` belegt 758 unveränderte
Prüfsummen von 379 gespeicherten Paaren, keine neue Archivkonvertierung.

Alle Vergleiche verwenden fünf Sekunden Bildbudget und Suchseed 17.
Der unabhängige Nachprüfer bindet die erwartete Hinter-/Vordergrundrelation
an die tatsächlich geschriebenen nativen SVG-Instanzen. Lokale/globale
Rastergates und die beiden Referenzvektorwächter bleiben verbindlich.
`cli-summary.json` enthält die Kohortenzähler und den Abgleich der
Runtime-Prüfsummen; `checks.json` und `logs/` enthalten die Abschlussprüfungen.
Die Standardsuite besteht mit 4.064 bestandenen und 30 übersprungenen Tests,
ohne Fehler. Die 36 neuen gezielten und insgesamt 183 Szenen-/Strukturtests
bestehen ebenfalls; fünf Kontrollen wurden erst nach der Gesamtsammlung
ergänzt und sind in diesen separaten Läufen enthalten. Die Gesamtdauer von
5.520,58 Sekunden enthält eine dokumentierte lokale Ausführungsunterbrechung
von rund 50 Minuten und ist keine Messung aktiver Konvertierungszeit.
`wrong_order/` enthält ausschließlich beschädigte Kontrollausgaben mit
vertauschten Kindern, keine Konvertierungserfolge. `wrong-order-audit.json`
zeigt sieben von zwölf falsche Reihenfolgen innerhalb der bisherigen
produktiven Regionsgrenzen und zwölf von zwölf Ablehnungen durch die native
Reihenfolgeprüfung.
Abgeleitete Raster und redundante Reports bleiben lokal; alle zur erneuten
Abnahme erforderlichen Dateien sind erhalten.

Keine neue reale Familie oder Katalogabnahme. Der geordnete Überdeckungsbaustein
ist abgeschlossen; das übergeordnete P0-Paket bleibt für weitere Kompositionen
und unabhängige reale Übertragung offen.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs artifacts/evaluation/overlap_composition_v1/inputs --output artifacts/evaluation/overlap_composition_v1/before --verify-only
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs artifacts/evaluation/overlap_composition_v1/inputs --output artifacts/evaluation/overlap_composition_v1/after --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs artifacts/evaluation/overlap_composition_v1/additional --output artifacts/evaluation/overlap_composition_v1/additional_cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs artifacts/evaluation/overlap_composition_v1/plan_b --output artifacts/evaluation/overlap_composition_v1/plan_b_cli --verify-only --require-all
```
