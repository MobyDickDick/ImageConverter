# Reale Sprachrobustheit: begrenzter Nachweis

`summary.json` bindet die Ergebnisse an vollständige lokale CLI-Ausgaben,
eingefrorene Raster/Texte, den exportierten Ausgangsstand und die geprüfte
Runtime. Zehn bekannte Topologien sind zehn Familien; Formulierungen und
Wiederholungen sind keine weiteren unabhängigen Familien.

Der Bericht enthält die gepaarten Endstände und den zusätzlich vollständig
aufbewahrten Entwicklungslauf mit einem Zeitabbruch. Dieser Fehlversuch wird
nicht aus der Gesamtzahl entfernt. Seine Ursache ist nicht isoliert;
`SEARCH-DEADLINE-OVERRUN-AUDIT` bleibt offen. Die Texte/Markierungen stammen vom
implementierenden Agenten; eine unabhängige menschliche Sprachprüfung wird
nicht behauptet. Es gibt keine neue Katalog- oder allgemeine Sprachabnahme.

`tools.summarize_semantic_robustness --verify-only` rendert sämtliche gespeicherten
Ausgaben erneut, erzeugt Löschkontrollen und prüft Tests, Originalarchiv,
Archiv-Neukonvertierungen sowie Provenienz. Die Rohdaten unter
`.tmp/semantic01/` werden nicht versioniert. Ein frischer Checkout muss sie
anhand der [Paketdokumentation](../../../docs/next_arbeitspaket_2026-10-22_semantic_robustness.md)
neu erzeugen; diese kompakte Zusammenfassung ersetzt die vollständige Prüfung
nicht. Laufzeiten und Rohbericht-Prüfsummen können bei Wiederholung abweichen.
