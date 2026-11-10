# Katalogbestand, Beschreibungen und Konvertierungsqualität

Die [vollständige durchsuchbare Übersicht](../artifacts/catalog_inventory/index.html)
ist die gemeinsame Liste für Projektstand und Bildnachweise.
[Aktuelle maschinenlesbare Bilanz](../artifacts/catalog_inventory/summary.json)
und [vollständige Einzelliste](../artifacts/catalog_inventory/manifest.json)
werden vom selben Werkzeug erzeugt. Eine ältere Liste vom 17.10.2026 bleibt
als historische Momentaufnahme erhalten; sie enthielt keine Beschreibungen.

## Erste vollständige Bestandsaufnahme vom 07.11.2026

| Befund | Anzahl |
| --- | ---: |
| Katalogbitmaps | 1.787 |
| Davon JPEGs / GIFs | 1.785 / 2 |
| Mit Katalogbeschreibung | 1.786 |
| Historisch archivierte Bild-/SVG-Paare | 379 (21,2 %) |
| Archivpaare mit passenden Quell-/Bild-/SVG-Prüfsummen | 379 |
| Beste gespeicherte Ausgabe besteht beide strengen Rasterrenderer | 345 (19,3 %) |
| Gespeicherte Ausgaben verfehlen mindestens ein strenges Rastergate | 1.314 |
| Ohne zugeordnete gespeicherte SVG-Ausgabe | 124 |
| Vorhandene SVGs nicht vollständig messbar | 2 |
| Reale Prüffamilien reserviert, nicht vermessen | 2 |

Die beiden GIFs `top.gif` und `bottom.gif` sind ebenfalls im XML-Katalog
aufgeführt und werden deshalb mitgezählt. Die frühere Gesamtzahl 1.785
bezog sich auf JPEGs. `AC0100_from_sample.jpg` besitzt keine zugeordnete
Katalogbeschreibung; dieser fehlende Text wird ausdrücklich angezeigt.

Alle 379 archivierten Paare sind bytegenau intakt. Acht archivierte
Beschreibungen weichen textlich vom heutigen Katalog ab. Drei verlinkte
historische Belegdateien für AC0840_L/M/S fehlen, obwohl die archivierten
Bild-/SVG-Paare und ihre Indexwerte vorhanden sind. Die zwei Messfehler
betreffen `DLG0050.jpg` und `DLG0051.jpg` mit ungültigen gespeicherten SVGs.

Die 345 Rastererfolge sind keine neue formale Katalogabnahme. Unter den
379 historisch archivierten Bitmaps erfüllen 288 mit ihrer jeweils besten
gespeicherten Ausgabe die aktuelle Zusatzprüfung; genau die archivierte
SVG-Datei erfüllt sie in 287 Fällen. Die frühere Archiv-MSE-Grenze
`0,045945679012345676` und die strengeren Plan-B-Gates sind unterschiedliche
Prüfungen. Die Einzelwerte stehen getrennt in der Übersicht.

Der Fortschritt lässt sich damit konkret einordnen: Historisch dokumentiert
abgenommen sind 21,2 Prozent des Bestands; 1.408 Einträge besitzen keine
Archivabnahme. Viele davon haben bereits SVG-Entwürfe. Die aktuelle zusätzliche
Rasterprüfung liefert für 345 Bitmaps einen positiven Befund. Eine neue
vollständige Konvertierung aller Bilder und eine fachliche/menschliche
Gesamtabnahme sind weiterhin offen.

## Nachführung und Verwendung

```powershell
.venv/Scripts/python.exe -m tools.build_catalog_inventory
```

Nach Änderungen an Quellen, Beschreibungen, Konvertierungen oder Runtime
wird derselbe Bericht aktualisiert. Identische, weiterhin gültige Messungen
werden per Prüfsumme wiederverwendet; `--force` erzwingt die Neumessung.
Die Ausgabe ist eine datierte Momentaufnahme des gespeicherten Bestands.

Für die weitere Arbeit lassen sich insbesondere archivierte Einträge mit
negativem aktuellem Rasterbefund, abweichende/fehlende Beschreibungen,
positive Rasterkandidaten ohne Archivabnahme und Einträge ohne SVG filtern.
Qualitätsgrenzen und archivierte Nachweise werden durch die Inventur nicht
verändert. HC0010 und Rail bleiben versiegelt und ohne neuen Versuch.

[Werkzeugvertrag, Quellenwahl und Auswahlregel](../artifacts/catalog_inventory/README.md).

## Prüfung der Erstaufnahme

12 gezielte Tests bestehen, einschließlich echter isolierter Rastermessung
mit beiden Renderern, Hash-/Beschreibungskonflikten, Cache-Invalidierung und
HTML-Escaping. Alle 1.787 Dateinamen und aktuellen Bildprüfsummen sowie die
ausgewerteten SVG-Prüfsummen wurden unabhängig mit dem erzeugten Manifest
abgeglichen. Die versiegelten Prüffamilien und Originalquellen bleiben
unverändert.

Die tatsächlich erzeugte JavaScript-Logik besteht Offline-Prüfungen für Suche,
Archiv-/Qualitäts-/Reservefilter, fehlende Beschreibungen, MSE-Sortierung und
Seitennavigation. Eine visuelle Browserprüfung war in dieser Umgebung wegen
der blockierten lokalen Datei-URLs nicht möglich. Ergebnisse und
Berichtsprüfsummen stehen in
[`checks.json`](../artifacts/catalog_inventory/checks.json).

## Nachtrag: Einträge ohne JavaScript sichtbar

Die erste Darstellung erzeugte sämtliche Tabellenzeilen erst per JavaScript.
Der Nutzer-Screenshot zeigte deshalb die leere Tabelle, wenn die Anzeige
die interaktive Initialisierung nicht ausführt. Die bisherigen Offline-Tests
deckten den Fall ohne Skriptausführung nicht ab.

Der Generator schreibt jetzt alle 1.787 Zeilen und die Kennzahlen direkt ins
HTML. JavaScript ergänzt diese vollständige Ansicht um Filter, Sortierung und
Seitenauswahl. Ohne Skriptausführung bleibt die gesamte Liste sichtbar;
ein Initialisierungsfehler erhält die statischen Zeilen ebenfalls.

Die Prüfung des tatsächlich erzeugten HTML bestätigt alle Dateinamen und
1.787 Tabellenzeilen vor jeder Skriptausführung. Vier neue Regressionstests
prüfen statische Zeilen/Links, Escaping, die Sichtbarkeit reservierter Einträge
ohne Miniaturbild sowie Bestände oberhalb der Seitengrenze. Zusammen bestehen
16 Tests. Die 41 Offline-Funktionsprüfungen der interaktiven Anzeige bestehen
weiterhin. Das Datenmanifest und die bisherigen Qualitätsmessungen bleiben
unverändert. `--render-only` aktualisiert die Darstellung aus dem Manifest.
