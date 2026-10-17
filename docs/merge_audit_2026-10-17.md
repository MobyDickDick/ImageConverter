# Prüfung der jüngsten Zusammenführungen (2026-10-17)

Geprüft wurde der lokale Stand `0f443a67f` einschließlich der letzten
Entwicklungszweige seit `4a72a18a9`. `main` und `origin/main` zeigten beim Start
auf denselben Commit; ein neuer Remoteabruf ist nicht Teil dieses Nachweises.
Die Prüfung vergleicht Dateiinhalte, Archivdatensätze und Quellhashes, nicht
nur die Erreichbarkeit von Commits.

## Befund

Die Änderungen wurden teilweise durch ältere Metadaten überlagert. Die
Produktionsdateien, Werkzeuge, Tests, Konfiguration und Workflows sind gegenüber
dem neueren Hauptzweig `ca1dc99c0` vollständig identisch geblieben. Auch der
Primitive-Scene-Weg aus `4a72a18a9` und die linke Quadratregistrierung sind
erhalten. Die zusätzlichen SE0082-Validierungsartefakte sind berechtigte
Ergänzungen und werden beibehalten.

| Stand | Zähler im Index | Tatsächliche Paare | Beschreibungen | SE0082 im Index |
|---|---:|---:|---:|:---:|
| `85e92c7ba` | 356 | 356 | 356 | ja |
| `3dd5f2353` | 355 | 355 | 355 | nein |
| `44ab883fa` (anderer Zweig) | 356 | 356 | 356 | ja |
| `488b4fe82` | 355 | 355 | 355 | nein |
| `ca1dc99c0` | 365 | 365 | 365 | ja |
| `65ce72225` / `0f443a67f` | 356 | 365 | 356 | ja |

SE0082 war nach `3dd5f2353` nicht mehr im Archivindex. `ca1dc99c0` hat diesen
Eintrag wiederhergestellt und neun AC0411-Paare ergänzt. Der spätere Merge
`65ce72225` hat alle 365 Datensätze und zugehörigen Dateien erhalten, aber den
Zähler und die Beschreibungstabelle auf den älteren 356er-Stand gesetzt. Die
neun AC0411-Beschreibungen fehlten dadurch. Alle 365 Datensätze sind gegenüber
`ca1dc99c0` identisch; sämtliche Bild- und SVG-Hashes stimmen.

Zusätzlich gingen der AC0411-Changelog-Eintrag, dessen Link im Dokumentationsindex,
der aktuelle Projektstand sowie die Checkboxen für die AC0411-Abnahme und den
offenen Folgepunkt `AC0411-PB-GREY` verloren. Der überlebende Absatz „Neuester
Abschluss“ widersprach damit den zurückgesetzten Zählern. Die Kandidatenliste
zeigte wieder die bereits erledigte Aufgabe AC0411 als nächstes Ziel.

## Wiederherstellung

Indexzähler, vollständige Beschreibungstabelle, Archivübersicht, README und
Projektstand stammen wieder aus `ca1dc99c0`. Changelog und Aufgabenliste
enthalten beide Abschlüsse SE0082 und AC0411. Der offene graue IoU-Fall ist
wieder sichtbar; die Checkboxzähler wurden aus der tatsächlichen Liste neu
berechnet. Die aktuelle Rotation beginnt mit `AC0910_L`, danach `GE0204_M`,
`AC0921_M` und `AC0232_M`.

Es wurden keine Bestresultate ersetzt und keine Quellraster geändert. Die
maschinenlesbare Inventur mit allen abweichenden Dateipfaden steht unter
`artifacts/evaluation/merge_audit_2026-10-17/audit.json`. Der vorhandene Test
`test_archive_contains_complete_immutable_pairs` prüft Zähler, eindeutige
Einträge, sämtliche Bild-/SVG-Hashes und die vollständige Beschreibungstabelle.
Er hätte den ursprünglichen widersprüchlichen Mergezustand zurückgewiesen.

Das anschließende Arbeitspaket wird auf dem separaten Branch
`codex/merge-audit-ac0910-2026-10-17` bearbeitet.
