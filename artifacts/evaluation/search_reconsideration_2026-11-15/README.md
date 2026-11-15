# Struktursuche und Plan-B-Nachbesserung

Die native Nachbesserung gibt einen weiterhin unzureichenden Fit nach 96 neuen
Renderings ohne mindestens ein Prozent Fehlerverbesserung zur Strukturprüfung
zurück, spätestens nach 288 neuen Renderings pro Parameterabschnitt. Andere
Verlaufsachsen, unabhängig vermessene Breite/Höhe und ausgerichtete Linien sind
eigene Vorschläge. Der Seed steuert die Reihenfolge; identische Vorschläge werden
innerhalb derselben Bildsuche ausgelassen. Ein guter Endstand darf unabhängig vom
Seed gleich sein. Die beste vorhandene Ausgabe bleibt erhalten.

Gerahmte axiale Verläufe mit einer bis acht parallelen Innenlinien werden anhand
des Rasters neu rekonstruiert. Rahmen und einzelne Balken bestimmen ihre eigenen
Abmessungen; das Farbprofil bestimmt Richtung und Verlauf. Bei subpixelverschobenen
Rahmen werden zwei benachbarte Pixel betrachtet, weil die Kontur sonst über zwei
blasse Pixel verteilt und fälschlich verworfen werden kann. Zusätzliche synthetische
Größen, Anzahlen und beide Achsen sind geprüft. Fehlende oder zusätzliche Inhalte
bleiben durch den vollständigen Bildvergleich und die vorhandenen Aussagenprüfungen
begrenzt; eine allgemeine Freitextsemantik wird nicht behauptet.

Plan B nutzt jetzt nach einem unzureichenden ersten CLI-Versuch dieselbe native
Vektorsuche wie die Einzelkonvertierung. Der erste Abschnitt erhält standardmäßig
55 Prozent des vorhandenen Falllimits; explizite Suchbudgets haben Vorrang.
Nachbesserung und CLI teilen das bisherige äußere Zeitlimit. Beides läuft im selben
überwachten Worker mit unveränderter Sperre gegen fremde Referenz-SVGs. Die
unabhängige Abnahme misst anschließend die tatsächlich gespeicherte SVG-Datei.
Grenzwerte und Komplexitätsprüfung wurden nicht verändert.

## Wiederholungen auf identischen Eingaben

| Prüfstand | Vorher | Nachher |
| --- | ---: | ---: |
| AC0110, lokaler Workbench-Lauf, Original und 16 Varianten | 9/17 | 17/17 |
| AC0020_M aus dem bereitgestellten ZIP, Original und 16 Varianten | 14/17 | 17/17 |

`checks.json` enthält Seeds, Quellprüfsummen, die Bestätigung identischer
Eingabeprüfsummen und alle einzelnen Rastermessungen. Bei keiner Wiederholung
wurde ein Referenz-SVG gelesen. Das ursprüngliche AC0110-JPEG besteht zusätzlich
die Produktionsmessung und die unabhängige librsvg-Messung. `AC0110.svg` ist die
native neue Ausgabe. Historische Workbench-Läufe werden nicht überschrieben.

Die abschließenden fokussierten Tests bestehen: 60 Such-/Struktur-/Nachbesserungstests,
85 Plan-B-/Workbench-Integrationstests und fünf Tests der gemeinsamen Plan-B-Nachbesserung,
darunter ein echter überwachter Worker. Vier der fünf letzten Tests sind auch in
den 60 enthalten. Ein Bestandstest wurde ausgenommen: Die während der Sitzung
unabhängig gelöschte `artifacts/samples/AC0130_L.txt` fehlt weiterhin. Diese Änderung
wurde nicht zurückgesetzt. Die erste Sandbox-Ausführung konnte lokale HTTP-Aufrufe
und Testprozessabbrüche nicht ausführen; die Wiederholung mit den nötigen Rechten
bestand. Die beigelegten Logs dokumentieren den abschließenden Stand.

Die Suche bleibt eine endliche Menge von Konstruktionsvorschlägen. Die Korrektur
verbessert die Umschaltung und diese beiden nachgewiesenen Familien; sie garantiert
keine erfolgreiche Vektorisierung beliebiger Motive.
