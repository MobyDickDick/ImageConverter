# Vollständige Katalogübersicht

Die neue [geometrische Klassenliste](../catalog_classes/index.html) ordnet den
gesamten Bestand nach Bildaufbau und vorhandenen nativen Teilmodellen.
Der lokale Webserver zeigt diese Klassen zusätzlich als Filter und im Export.
[Befund und Grenzen](../../docs/catalog_geometry_classes_2026-11-13.md).

Die Liste ist auch im lokalen Webserver unter **Konvertierungsqualität**
(`http://127.0.0.1:8766/catalog`) verfügbar. Dort kann die Neumessung mit
Fortschrittsanzeige gestartet und abgebrochen werden; die letzte vollständige
Liste bleibt erhalten. [Bedienung](../../docs/catalog_quality_webserver.md).

Die durchsuchbare [Gesamtliste](index.html) verbindet jede vorhandene
Katalogbitmap mit ihrer aktuellen Beschreibung, gespeicherten SVG-Ausgaben,
historischen Archivnachweisen und nachgemessener Rasterqualität.

Dateiname und Beschreibung sind durchsuchbar. Filter unterscheiden
Qualitätsstand, Archivabnahme, fehlende/abweichende Beschreibungen und
Kataloggruppen. Jede Spaltenüberschrift sortiert auf- oder absteigend;
ein Pfeil zeigt die aktuelle Richtung. Die Rasterprüfung sortiert nach
Status und anschließend nach MSE. Der MSE lässt sich außerdem direkt über
die Sortierauswahl ordnen. Fehlende Werte stehen immer am Ende. Bild,
ausgewähltes SVG und vorhandener Abnahmebeleg sind direkt verlinkt.
Die Anzeige bietet 25, 75 oder 150 Zeilen pro Seite sowie „Alle“ für sämtliche
gefilterten Treffer. Suche, Filter und Sortierung umfassen stets alle Einträge.

Alle Tabellenzeilen, Übersichtskennzahlen und Beschreibungen stehen bereits
direkt im HTML. Führt die Anzeige JavaScript nicht aus, bleibt der vollständige
Bestand sichtbar; die dann nicht verfügbaren interaktiven Bedienelemente sind
ausgeblendet. Mit JavaScript wird die Liste um die Seitenauswahl und die
Filter-/Sortierfunktionen ergänzt. Fehler beim Start der interaktiven Ansicht
lassen die vollständige statische Tabelle erhalten.

## Nachführen

Im Projektverzeichnis mit der vorhandenen virtuellen Umgebung:

```powershell
.venv/Scripts/python.exe -m tools.build_catalog_inventory
```

Nach Arbeitspaketen mit geänderten Bitmaps, Beschreibungen, SVGs, Archivdaten
oder Renderer wird die Übersicht mit diesem Befehl aktualisiert. Vorhandene
Paarprüfungen werden nur bei identischen Bild-/SVG-Prüfsummen,
Runtime-/Werkzeughashes, Renderer-Versionen und unveränderten Gates
wiederverwendet. Fehler werden erneut geprüft. Eine vollständige Neumessung:

```powershell
.venv/Scripts/python.exe -m tools.build_catalog_inventory --force
```

Für reine Darstellungsänderungen kann das vorhandene Datenmanifest ohne neue
Messung erneut als HTML ausgegeben werden:

```powershell
.venv/Scripts/python.exe -m tools.build_catalog_inventory --render-only
```

Es werden gespeicherte SVGs gemessen. Der Befehl startet keine neue
Konvertierung und verändert weder Quellen noch Erfolgsarchiv. Die zwei
versiegelten realen Prüffamilien werden nicht vermessen.

## Bedeutung der Ergebnisse

- **Historisch archiviert:** Eintrag in `artifacts/satisfactory_conversions/index.json`.
  Das Archivbild, sein SVG und die aktuelle Quellbitmap werden an den
  gespeicherten Prüfsummen geprüft. Beschreibungsabweichungen und fehlende
  Belegdateien bleiben eigene Hinweise.
- **Rastergates erfüllt:** Mindestens ein gespeichertes SVG besteht heute
  die bestehenden strengen Plan-B-Pixel-, Größen- und Vektorgates mit MuPDF
  und unabhängigem librsvg. Diese Zusatzprüfung umfasst mehr als die ältere
  Archiv-MSE-Grenze. Sie ist keine fachliche Neubewertung aller Objekte und
  Beschreibungen und kein Nachweis einer neuen autonomen Konvertierung.
- **Rastergates verfehlt:** Die vorhandenen Ausgaben bestehen diese strenge
  Prüfung nicht. Einzelmetriken und verletzte Grenzen stehen in den Details.
- **Kein gespeichertes SVG:** Keine eindeutige Ausgabe in den ausgewerteten
  Konvertierungs-, Bestlisten-, Archiv- oder Baselineordnern. Die
  Konvertierbarkeit ist damit offen.
- **Messung fehlgeschlagen:** Ein vorhandener Kandidat konnte nicht
  vollständig geprüft werden; der konkrete Fehler bleibt sichtbar.
- **Reserviert:** Keine neue Messung oder Konvertierung der gesperrten
  realen Prüffamilie.

Pro Bitmap werden alle eindeutig nach Dateistamm zugeordneten gespeicherten
SVGs aus den dokumentierten Ausgabeordnern geprüft. Identische SVG-Bytes
werden einmal gemessen, alle Fundorte bleiben erhalten. Die Auswahl bevorzugt
beide bestandenen Rasterrenderer; anschließend entscheidet der niedrigste
schlechteste MSE beider Renderer. Die ausgewählte beste Ausgabe kann vom
historisch archivierten SVG abweichen. Sample-/Plan-B-Vorlagen werden nicht
als Konvertierungsausgaben gezählt.

Die Inventur erfasst den Hauptordner sowie vorhandene Unterordner für
erfolgreich markierte und nicht konvertierbare Quellen. Identische
Dateikopien werden zusammengeführt; widersprüchliche Kopien bleiben
ungeprüft und markiert. GIFs mit einem XML-Katalogeintrag gehören zum Katalog.
Sonstige GIFs erscheinen als Hilfsgrafiken außerhalb der Katalogquote.

`manifest.json` enthält sämtliche Zeilen, Kandidaten, Einzelmessungen,
Beschreibungen und Belegpfade. `summary.json` enthält die aktuelle Bilanz;
`sources.json` bindet sie an Quellen, Runtimehashes, Versionen und Gates.
`measurements.json` ist ausschließlich ein lokal regenerierbarer Cache.
Manuelle Sichtfreigaben werden im bisherigen Bestand nicht systematisch
erfasst und deshalb auch hier nicht behauptet.

[Erstaufnahme, Einordnung und Prüfungen](../../docs/catalog_inventory.md).
