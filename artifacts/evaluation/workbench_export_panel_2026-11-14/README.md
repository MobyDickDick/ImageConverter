# Workbench-Export und fehlendes Minuszeichen

## Befund

Der Lauf `9527ed9526144ce594c84ddb7336348b` enthielt 17 Messungen:
5 bestanden, 12 Qualitätsfehler, keine Ausführungsfehler. CSV brach mit
`dict contains fields not in fieldnames: 'foreground_iou_binary'` ab.
Da ZIP denselben CSV-Export verwendet, war auch das vollständige Datenpaket
nicht mehr abrufbar. Der JSON-Endpunkt lieferte HTTP 200 mit Attachment-Header.
Der ursprüngliche Bericht und das ursprüngliche ZIP wurden separat gesichert.

Die Rekonstruktion verlor das obere Minus. Der spezielle Modellweg setzte das
Wort „Kreuz“ voraus, obwohl die Beschreibung ausdrücklich zwei dunkelgraue
Diagonalen nannte. Zusätzlich verhinderte „Minzuszeichen“ die Modellauswahl.
Bei einer Variante verteilte Antialiasing das kurze Minus auf drei Zeilen;
die binäre Belegung seines Begrenzungsrechtecks unterschritt den alten
Detektionswert von 70 %. Dieser Wert ist auf 60 % angepasst; horizontale
Form, Breite, Zusammenhang und die anschliessende lokale Renderprüfung
bleiben erforderlich.

## Änderung und Prüfung

- CSV enthält binäre IoU sowie zusätzliche Messwerte aus gespeicherten Berichten.
- JSON, CSV und ZIP teilen sich die Exporterzeugung. Unter Windows steht ein
  Speicherdialog zur Verfügung; Abbruch und Fehler werden sichtbar behandelt.
- Die Aktivitätsanzeige zeigt den laufenden Fall und die Zahl geprüfter Fälle
  und verlinkt direkt auf die tatsächlich laufende Aufgabe.
- Die exakte Benutzereingabe wird intern verstanden, bleibt aber unverändert
  gespeichert. Falsche Diagonalenzahl, Plus statt Minus und „ohne Kreuz“ werden
  weiterhin zurückgewiesen. Zitierte Beschriftungen werden nicht normalisiert.

37 Paneltests, 56 Sprachtests, 33 Workbenchtests und 15 Speicher-/GUI-
Wiederherstellungstests bestehen. Die 10 JavaScript-Prüfungen umfassen
Dateiformate, Speichern, Abbruch, Fehleranzeige, normalen Browserdownload,
Aktivitätsfortschritt und Freigabe nach Abschluss. Der PowerShell-Parser
bestätigt die Syntax des Speicherdialogs. Ein lokaler HTTP-Testlauf wurde
nach einem Windows-Socketabbruch unverändert erfolgreich wiederholt.

## Wiederholung desselben Rastersatzes

Seed, Quelle, Beschreibungen, Eingabehashes, 64 Iterationen und 60 Sekunden
Limit je Fall sowie die unabhängigen Qualitätsgrenzen bleiben erhalten.
Alle 17 neuesten Ergebnisse bestehen die MuPDF-Prüfung; die gespeicherten
Vektoren bestehen zusätzlich alle 17 Prüfungen mit librsvg. Das Minus bleibt
als natives Rechteck erhalten; beide Diagonalen sind native, geclippte Linien.
SVG-Vorlagen wurden vom Konverter nicht gelesen.

Der zweite Versuch wurde nach 14 abgeschlossenen Fällen unterbrochen. Die
restlichen drei Fälle wurden isoliert geprüft und erst nach Abschluss als
dritter Versuch übernommen. Die 17 neuesten Befunde sind deshalb eine
Diagnose über zwei Versuche, kein einzelner durchgängiger 17-Fälle-Lauf.
Der erste Versuch und seine Fehler sind unverändert erhalten.

Zusätzlich wurde der neu vom Benutzer gestartete Lauf
`fd9cf9a209cf4de4af6a4031eae7a315` mit Seed `506391347870035632`
abgewartet: **17/17 in einem vollständigen einzelnen Versuch bestanden**.
Erst danach wurde der untätige Webserver geordnet aktualisiert. JSON, CSV und
ZIP liefern am laufenden Server HTTP 200 mit Attachment-Header; beide ZIPs
lassen sich vollständig prüfen. Es bleibt keine laufende Workbench-Sperre.
Die Windows-Exportfunktion wird über eine eigene Serverfähigkeit angeboten,
sodass ein neuer Browsercode beim älteren Server keinen fehlenden Endpunkt aufruft.

`summary.json` enthält Vorher/Nachher, Hashes, Einzelmessungen und den zweiten
Renderer. Lokal liegen zusätzlich `report.json`, `workbench.csv` und
`plan-b-workbench.zip` des ursprünglichen Laufs sowie `report-fixed.json`,
`workbench-fixed.csv`, `plan-b-workbench-fixed.zip` und `comparison.png` bereit.
Die Rohartefakte bleiben gemäss Repository-Regeln unversioniert.
