# Projektstand und Sichtprüfung am 2026-10-17

Zu Beginn dieser Aufgabe waren **329 Bild-/SVG-Paare ausdrücklich abgenommen**.
Das nächste dokumentierte Paket GE9033 ergänzt 14 Farb-/Größenvarianten auf
`codex/ge9033-quality-2026-10-17`: damit sind es **343 von 1.785 Katalogbildern
(19,2 %)**. Diese Abnahme bezieht sich auf die regulären Qualitätsgates.
Einige zusätzliche strengere Plan-B-Prüfungen bleiben als eigene Aufgaben offen.
Die persönliche Sichtprüfung und Nachbearbeitung für `artifacts/samples/`
ist davon getrennt; ihr Abschluss wird bisher nicht systematisch erfasst.

## Wie viele Bilder sind noch unzureichend?

**Eine aktuelle Gesamtzahl tatsächlich scheiternder Bilder ist nicht belegt.**
1.442 Katalogbilder haben noch keine ausdrückliche Archivabnahme. Diese Zahl
umfasst sowohl brauchbare ältere Ausgaben als auch Fehler und ungeprüfte Bilder.
Sie darf nicht als Zahl gescheiterter Konvertierungen gelesen werden.

Der zuletzt dokumentierte Bestandsreview enthält 1.000 Datensätze, aber nur
969 verschiedene Bildnamen: 31 identische Paare stehen in zwei Quelllisten.
993 Datensätze sind renderbar, 896 liegen unter der Pixel-Reviewgrenze,
97 darüber und sieben haben kein auswertbares Paar. Diese ältere Pixelprüfung
ist kein frischer Kataloglauf und keine vollständige semantische Abnahme.
54 der 97 damaligen Fehlerfälle waren schon vor dieser Aufgabe ausdrücklich
abgenommen; mit GE9033 kommt ein weiterer hinzu. Es bleiben **42 ältere
Pixel-Fehlerfälle**. Von den sieben fehlenden Paaren gehören sechs zum hier
gezählten JPG-Katalog; ein Revieweintrag liegt außerhalb dieses Inventars.

| Gegenseitig ausschließende Kataloggruppe | Bilder |
|---|---:|
| Ausdrücklich abgenommen und archiviert | 343 |
| Nur ältere Pixelprüfung unter der Reviewgrenze | 696 |
| Ältere Pixelprüfung über der Reviewgrenze, ohne spätere Abnahme | 42 |
| Älteres Reviewpaar nicht auswertbar | 6 |
| Weder im Bestandsreview noch im Abnahmearchiv | 698 |
| **Gesamt** | **1.785** |

Die vollständige Zuordnung steht in
[`catalog_status.csv`](../artifacts/evaluation/conversion_status_2026-10-17/catalog_status.csv),
die Zählregeln, Eingabehashes und maschinenlesbaren Summen in
[`summary.json`](../artifacts/evaluation/conversion_status_2026-10-17/summary.json).
Zählbasis sind unterschiedliche JPG-Dateinamen unter `images_to_convert/`,
rekursiv ohne `samples`; Kopien desselben Dateinamens zählen einmal.
Alle archivierten Raster und SVGs wurden gegen ihre Indexhashes geprüft.

## Persönliche Sichtprüfung organisieren

Die [Prüfliste](../artifacts/evaluation/conversion_status_2026-10-17/manual_review_queue.csv)
enthält ausschließlich die 343 abgenommenen Paare, sortiert nach absteigendem
Pixel-Fehlerwert. Damit lassen sich zunächst die auffälligeren Fälle vergleichen.
Sie enthält Pfade zu Original, akzeptiertem SVG und Abnahmenachweis.
Die leeren Spalten `manual_decision` und `notes` nehmen persönliche Entscheidungen
und Änderungswünsche auf. Vor dem Ausfüllen eine Arbeitskopie speichern:
der Generator überschreibt diese Bestandsaufnahme bei erneuter Ausführung.
Der Fehlerwert ist eine Sortierhilfe, keine Garantie für die visuelle Auffälligkeit.

Im Samples-Ordner liegen derzeit 93 SVGs, einschließlich vier bereits vor
dieser Aufgabe vorhandener unversionierter Dateien. Nur acht Namen stimmen
mit dem Abnahmearchiv überein; 335 archivierte Fälle haben noch kein gleichnamiges
Sample. Gleichnamigkeit belegt weder gleiche Inhalte noch persönliche Freigabe.
Die vorhandenen Samples wurden durch diese Aufgabe nicht verändert.

Für eine handliche erste Runde bietet sich an, zunächst ein großes Bild je
Formenfamilie zu prüfen und anschließend die zugehörigen Farb- und Größenvarianten.
Die Prüfliste kann dafür nach dem Bildnamen gefiltert werden. Ein automatisches
Verschieben nach `samples` würde die noch ausstehende persönliche Prüfung nicht ersetzen.

## Nächstes Paket

GE9033 ist auf dem separaten Branch umgesetzt; Details, Grenzen und
Reproduktion stehen im [Arbeitspaket](next_arbeitspaket_2026-10-17_ge9033_6m.md).
Danach folgt regulär `AC0424_2_M`, anschließend `AC0840_S`, `AC0840_M`,
`SE0082` und `AC0411_1_M`. Die übrigen offenen Aufgaben bleiben erhalten.
