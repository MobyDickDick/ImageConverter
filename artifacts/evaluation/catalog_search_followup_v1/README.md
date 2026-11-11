# Zweiter Katalogaudit vom 11.11.2026

Lauf `catalog-20261111T121521Z-d7a16496`, gesicherter Zwischenstand:
36 begonnene Eingaben, 32 gespeicherte Ergebnisse, drei Fehler im Ereignislog,
ein noch nicht abgeschlossener Fall. Drei Ausgaben sind modellbestätigt;
elf bestehen die unabhängig erneut gemessenen reinen Pixelgates.

Windows bestätigt drei automatische Modern-Standby-Intervalle von zusammen
155,18 Minuten im 171,54 Minuten langen beobachteten Batchfenster.
Die drei Zeitüberschreitungen fallen mit dem jeweiligen Aufwachen zusammen.
Die abgeschlossenen Ergebniszeilen summieren sich auf rund 16,5 Minuten
gemeldete Bildlaufzeit. Standbyintervalle sind keine exakten Grenzen jeder
CPU-Aktivität; die Aufsichtslücken und CPU-Differenzen stützen die Zuordnung.

28 von 32 Bildern verwenden weiterhin die Nachoptimierung eines festen
SVG-Aufbaus; keines dieser 28 erhält eine Modellfreigabe. 73.551
Bot-Parametervorschläge belegen daher keine breite Strukturvariation.
Zusätzlich sind veraltete `best_error`-Werte und ein fehlender unmittelbarer
Fehler-Checkpoint dokumentiert.

Vollständige Einordnung und priorisierte Konsequenzen:
[Zweiter Katalogaudit](../../../docs/catalog_search_followup_2026-11-11.md).

`summary.json` enthält die eingefrorene Quellenbeschreibung, Einzeldateihashes,
alle gemessenen Rastermetriken, Suchzähler, kompakten Zeit-/Standbynachweis
und den Vergleich mit dem ersten Audit. Die Rohdaten einschließlich der
exportierten Systemereignisse liegen lokal unter
`.tmp/catalog-search-audit-20261111-long/`. Produktionscode, Energieoptionen
und vorhandene Konvertierungsergebnisse bleiben unverändert.
