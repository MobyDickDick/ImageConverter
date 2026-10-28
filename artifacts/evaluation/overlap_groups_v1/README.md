# SEARCH-STRUCTURE-01: getrennte Überdeckungsgruppen

Branch `codex/search-structure-composition-2026-10-28`, Basis `50e4009d1`.
[Umsetzung, Grenzen und Reproduktion](../../../docs/next_arbeitspaket_2026-10-28_overlap_groups.md).

| Echte CLI-Kohorte | Vorher | Nachher |
| --- | --- | --- |
| Seed 731429, zwei Gruppen, Rundung, helle Konturen | 0/12 | 12/12 |
| Seed 962713, drei Gruppen | nicht gemessen | 12/12 |
| Seed 482391, vier Gruppen | nicht gemessen | 12/12 |
| Seed 853197, Original und 16 Varianten | nicht gemessen | 14/17 |

Alle Fälle verwenden Suchseed 17, fünf Sekunden pro Bild und unveränderte
native Objekt-/Reihenfolge-, Regions- und Pixelprüfungen. Drei durch die
Varianten angeschnittene Elternkreise bleiben Fehlversuche im Nenner.
Kein Wechsel des Seeds oder Abschwächen der Grenzen nach diesem Befund.

`summary.json` enthält gepaarte Eingabehashes, Runtime-Hashes, kompakte
Entscheidungen und die drei Variantenfehler. `checks.json` enthält tatsächliche
Prüfbefehle, Exit-Codes und das finale Ergebnis: 236 Regressionen bestanden,
eine Überspringung; Kernprofil 42/42. Die vollständige Standardsuite und
Archiv-Neukonvertierung wurden nicht ausgeführt.

Rohberichte und generierte Bild-/SVG-Dateien bleiben lokal unter
`.tmp/overlap-groups*-20261028-*`. Allgemeine P0-Abnahme und unabhängiger
Realtransfer bleiben offen; gespeicherte Archivpaare werden nicht verändert.
