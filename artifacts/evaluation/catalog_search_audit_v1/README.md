# Audit des erhaltenen Kataloglaufs vom 10.11.2026

Vollständiger Befund, Ursachen und abgeleitete Arbeiten:
[Katalog-Suchaudit vom 11.11.2026](../../../docs/catalog_search_audit_2026-11-11.md).

`summary.json` enthält die 38 gespeicherten Ergebnisse, ihre Suchwege,
unabhängige erneute Pixelprüfungen, Eingabe-/Ausgabe-/Protokollhashes,
den getrennten historischen Git-Vergleich und die diagnostische
Linienergänzung. Die Daten stammen aus den zugehörigen Workerprotokollen,
nicht aus der über mehrere Läufe angesammelten globalen Suchdatei.

38 SVGs wurden geschrieben, zehn vom Konverter modellbestätigt und 13
bestehen die hier erneut gemessenen reinen Pixelgates. 28 Bilder laufen
durch die Nachoptimierung vorhandener SVG-Strukturen; keine dieser 28
erreicht die Modellfreigabe. 77.895 Bot-Parametervorschläge sind reale
Arbeit, aber kein Nachweis verschiedener vollständiger Bildkonstruktionen.
Die allgemeine strukturelle Szenensuche wurde in diesen Protokollen nicht
gestartet. Der aktive Modus verwendet kein dauerhaftes Strategielernen
zwischen diesen Bildern oder Läufen.

Der frühere Benutzerlauf ist überschrieben. Der historische Git-Vergleich
ersetzt ihn nicht. Es wurde kein neuer Konvertierungslauf gestartet;
vorhandene Ergebnisse und Produktionscode bleiben unverändert.

Beim Abschluss begann ein weiterer Lauf im selben Zielordner. Seine neuen
Daten wurden nicht eingemischt. Die fünf alten Übersichtsdateien wurden
dadurch nach Erstellung dieses Nachweises ersetzt; 152 noch unveränderte
Einzeldateien des untersuchten Laufs wurden mit Hashprüfung lokal unter
`.tmp/catalog-run-audit/frozen-20261110T201918Z/` gesichert. `summary.json`
dokumentiert diese nachträgliche Ersetzung und jede gesicherte Datei.
