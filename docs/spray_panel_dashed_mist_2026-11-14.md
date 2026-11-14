# Luftbefeuchter: gestrichelte Sprühstrahlen

Die Nutzerkorrektur präzisiert die fünf Sprühnebel von `AC0130_L.jpg`:
Ihre insgesamt 15 Strahlen bestehen aus kurzen Strichen mit kleinen sichtbaren
Zwischenräumen. Die erste getrennte Rekonstruktion zeichnete sie durchgehend.
Die [bisherigen v1-Belege](../artifacts/evaluation/spray_panel_v1/README.md)
bleiben unverändert erhalten.

## Änderung und tatsächlicher Lauf

Der produktive Sprühpanel-Fitter erkennt die entsprechende Beschreibung und
passt nach den bisherigen 13 Bauteilschritten jeden einzelnen Strahl zusätzlich
an. Strichlänge, Abstand, Phase, Breite und Grauton erhalten eigene Parameter;
das ergibt 28 protokollierte Suchstufen. Gekoppelte Strich-/Grautonvorschläge
verhindern, dass die sichtbaren Lücken den gesamten Strahl nur blasser machen.
Die Parameter stammen aus dem vollständigen Raster. Die Runtime liest weder
Dateinamen noch die früher konvertierte SVG als Vorlage.

Gehäuse, Balken, Innenrahmen, fünf Düsen und die Koordinaten aller 15 Strahlen
sind gegenüber der bereits akzeptierten v1-Ausgabe bytegleich in den nativen
Elementattributen. Die neuen Linien tragen explizit `stroke-dasharray` und
`stroke-dashoffset`. Die Beschreibung ohne gestrichelten Sprühnebel verwendet
weiter den bisherigen Pfad; das alte v1-Verhalten wird separat geprüft.

Auch native Linienstrichelungen werden von MuPDF ignoriert. Der private
Renderweg materialisiert deshalb ihre geraden Strichstücke unter Erhaltung
von Richtung, geerbter Farbe, Breite und Phase. Waagrechte, senkrechte, schräge
und umgekehrt gerichtete Linien sowie positive/negative Offsets sind gegen
librsvg geprüft. Die gespeicherte SVG behält 15 logische native Linien und
keine eingebetteten Raster. Ungültige oder übergroße Muster sowie nicht
unterstützte Endkappen werden nicht geraten.

Die frische überwachte `semantic-only`-CLI benutzt eine neutral benannte
Rasterkopie, Seed 0 und dieselbe korrigierte Beschreibung wie der Katalog.
Das Bildbudget beträgt 150 Sekunden, höchstens 180 Sekunden. Tatsächlich
benötigt der gespeicherte Lauf **64,4 Sekunden und 8.118 Renderprüfungen**;
ein direkter Entwicklungslauf erzeugt dieselben SVG-Bytes. Es gibt keine
Referenz-SVG-Zugriffe.

| Strenger Rastervergleich | Bisher | Gestrichelte Strahlen |
| --- | ---: | ---: |
| Normalisierter Bildfehler, MuPDF | 0,000352 | 0,000302 |
| Normalisierter Bildfehler, librsvg | 0,000366 | 0,000318 |
| Vordergrund-IoU, MuPDF | 0,9923 | 0,9923 |
| Vordergrund-IoU, librsvg | 0,9927 | 0,9927 |

Alle bisherigen globalen Gates, 13 externen Teilregionen und beide
Rahmen-Strichelungsprüfungen bleiben bestanden. Der neue separate
Entwicklungsvertrag verwendet unverändert den v1-Geometrieprüfer für die
Linienhüllen und ergänzt die verbindliche Strichelung aller 15 Strahlen:
positive Muster, erkennbare Zwischenräume und mindestens zwei tatsächlich
innerhalb der jeweiligen Linie liegende Lücken. Damit genügt ein bloßes
Attribut mit unsichtbarer oder weit außerhalb liegender Unterbrechung nicht.
Der v1-Prüfer wird nicht gelockert oder überschrieben.

48 Gegenproben werden abgelehnt, darunter jeder einzeln durchgezogen ersetzte
Strahl, vollständig durchgezogene Sprühnebel, unsichtbare Zwischenräume,
fehlende Einzelteile und zusätzliche verdeckte Geometrie. 46 gezielte
Strichelungs-/Ausgabeprüfungen bestehen. Die bisherigen Sprühpanel- und
Rendererregressionen sowie die Kerntests wurden erneut ausgeführt.

## Beschreibung und Lieferung

Beide Katalog-XMLs beschreiben jetzt ausdrücklich „drei voneinander getrennte,
fein gestrichelte hellgraue Linien“ je Sprühnebel. Ergänzend wird festgehalten,
dass jeder der 15 Strahlen aus mehreren kurzen Strichen mit sichtbaren kleinen
Zwischenräumen besteht. Sichtzuordnung und Kollektion weisen ebenfalls darauf hin.

[Neue SVG, Vergleich, Beschreibung und Einzelgruppen](../artifacts/evaluation/spray_panel_dashed_v2/README.md).
Die Abnahme gilt für das bekannte L-Original. Die Grenzen des v1-Pakets,
insbesondere die noch fehlende M-/S-Detektion und allgemeine fremde
Sprühkompositionen, bleiben bestehen. Keine automatische Archivpromotion
und keine neue unabhängige reale Familie.
