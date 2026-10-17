# Projektstand und Sichtprüfung am 2026-10-17

**Nachtrag SE0082:** Das unabhängig geprüfte Quadrat mit linkem Griff und M
ergänzt das Archiv auf **356 von 1.785 Bildern (19,9 %)**. Alle 355 bisherigen
Einträge bleiben unverändert; 1.429 Bilder haben keine ausdrückliche Archivabnahme.
Details: [SE0082-Arbeitspaket](next_arbeitspaket_2026-10-17_se0082.md).
Die folgenden Nachträge und Tabellen bleiben historische Snapshots.

**Nachtrag AC0840:** S/M/L ergänzen drei unabhängig geprüfte Bild-/SVG-Paare.
Der aktuelle Archivstand beträgt **355 von 1.785 Bildern (19,9 %)**; alle 352
bisherigen Indexeinträge sind unverändert. 1.430 Bilder haben weiterhin keine
ausdrückliche Archivabnahme. Das ist keine Zahl nachgewiesen gescheiterter Bilder.
Details: [AC0840 und Suchportfolio](next_arbeitspaket_2026-10-17_ac0840_search.md).
Die folgenden Tabellen und CSV-Verweise dokumentieren den vorherigen Snapshot
mit 352 Paaren und wurden als historischer Beleg erhalten.

Vor den Paketen GE9033 und AC0424 waren **329 Bild-/SVG-Paare ausdrücklich abgenommen**.
Die dokumentierten Pakete GE9033 und AC0424 ergänzen 14 beziehungsweise neun
Farb-/Größenvarianten: damit sind es **352 von 1.785 Katalogbildern
(19,7 %)**. Diese Abnahme bezieht sich auf die regulären Qualitätsgates.
Einige zusätzliche strengere Plan-B-Prüfungen bleiben als eigene Aufgaben offen.
Die persönliche Sichtprüfung und Nachbearbeitung für `artifacts/samples/`
ist davon getrennt; ihr Abschluss wird bisher nicht systematisch erfasst.

## Wie viele Bilder sind noch unzureichend?

**Eine aktuelle Gesamtzahl tatsächlich scheiternder Bilder ist nicht belegt.**
1.433 Katalogbilder haben noch keine ausdrückliche Archivabnahme. Diese Zahl
umfasst sowohl brauchbare ältere Ausgaben als auch Fehler und ungeprüfte Bilder.
Sie darf nicht als Zahl gescheiterter Konvertierungen gelesen werden.

Der zuletzt dokumentierte Bestandsreview enthält 1.000 Datensätze, aber nur
969 verschiedene Bildnamen: 31 identische Paare stehen in zwei Quelllisten.
993 Datensätze sind renderbar, 896 liegen unter der Pixel-Reviewgrenze,
97 darüber und sieben haben kein auswertbares Paar. Diese ältere Pixelprüfung
ist kein frischer Kataloglauf und keine vollständige semantische Abnahme.
54 der 97 damaligen Fehlerfälle waren schon vor dieser Aufgabe ausdrücklich
abgenommen; mit GE9033 und AC0424 kommen zwei weitere hinzu. Es bleiben **41 ältere
Pixel-Fehlerfälle**. Von den sieben fehlenden Paaren gehören sechs zum hier
gezählten JPG-Katalog; ein Revieweintrag liegt außerhalb dieses Inventars.

| Gegenseitig ausschließende Kataloggruppe | Bilder |
|---|---:|
| Ausdrücklich abgenommen und archiviert | 352 |
| Nur ältere Pixelprüfung unter der Reviewgrenze | 692 |
| Ältere Pixelprüfung über der Reviewgrenze, ohne spätere Abnahme | 41 |
| Älteres Reviewpaar nicht auswertbar | 6 |
| Weder im Bestandsreview noch im Abnahmearchiv | 694 |
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
enthält ausschließlich die 352 abgenommenen Paare, sortiert nach absteigendem
Pixel-Fehlerwert. Damit lassen sich zunächst die auffälligeren Fälle vergleichen.
Sie enthält Pfade zu Original, akzeptiertem SVG und Abnahmenachweis.
Die leeren Spalten `manual_decision` und `notes` nehmen persönliche Entscheidungen
und Änderungswünsche auf. Vor dem Ausfüllen eine Arbeitskopie speichern:
der Generator überschreibt diese Bestandsaufnahme bei erneuter Ausführung.
Der Fehlerwert ist eine Sortierhilfe, keine Garantie für die visuelle Auffälligkeit.

Im Samples-Ordner liegen derzeit 93 SVGs, einschließlich vier bereits vor
dieser Aufgabe vorhandener unversionierter Dateien. Nur acht Namen stimmen
mit dem Abnahmearchiv überein; 344 archivierte Fälle haben noch kein gleichnamiges
Sample. Gleichnamigkeit belegt weder gleiche Inhalte noch persönliche Freigabe.
Die vorhandenen Samples wurden durch diese Aufgabe nicht verändert.

Für eine handliche erste Runde bietet sich an, zunächst ein großes Bild je
Formenfamilie zu prüfen und anschließend die zugehörigen Farb- und Größenvarianten.
Die Prüfliste kann dafür nach dem Bildnamen gefiltert werden. Ein automatisches
Verschieben nach `samples` würde die noch ausstehende persönliche Prüfung nicht ersetzen.

## Nächstes Paket

AC0411 ist nach SE0082 abgeschlossen; Nachweise, Grenzen und Reproduktion
stehen im [Arbeitspaket](next_arbeitspaket_2026-10-17_ac0411_1_m.md).
Danach folgen regulär `AC0910_L`, `GE0204_M`, `AC0921_M` und `AC0232_M`.
Die übrigen offenen Aufgaben bleiben erhalten.
