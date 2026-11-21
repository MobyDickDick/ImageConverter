# Korrektur des Konvertierungsabbruchs bei vorhandener Vorlage

Der Benutzer meldete einen Abbruch in `imageConverterSample.refine` mit
`logical_object_count:all:1:4`. Der gespeicherte Fall ist `AC0253_2.jpg`.
Die aufgelöste Beschreibung nennt einen Kreis und ein kontrastierendes
gefülltes Dreieck. Die vorhandene Vorlage enthält diese beiden Formen und
zusätzlich zwei Linien.

Die vorherige Änderung enthielt zwei Fehler:

1. Der Parser übersah das Dreieck wegen der Adjektivfolge. Er deklarierte
   trotzdem die unvollständig erkannte Elementliste als vollständig.
2. Eine nicht passende optionale Vorlage führte vor dem ersten Fit zu einer
   unbehandelten Ausnahme. Die eigentliche Beschreibungskonvertierung wurde
   deshalb gar nicht gestartet.

Die Korrektur erkennt die Adjektivfolge und einfache artikellose Formnennungen.
Verneinte Formnennungen bleiben ausgeschlossen. „Rechteck mit Diagonalen“ wird
als Rechteck mit seinen zwei Diagonalen verstanden. Eine vorgegebene gemeinsame
Linienstärke wird vor der Vorlagenprüfung auf die vorhandenen Linien angewendet.

Passt die Vorlage trotzdem nicht, wird sie als Ausgangspunkt verworfen. Der
Worker startet stattdessen die normale erste Beschreibungskonvertierung im
verbleibenden Zeitbudget. Er verwendet weder die entfernte Raster-Nachsuche noch
die falschen Zusatzlinien. Ein nicht lösbarer Fall liefert einen strukturierten
Fehlerbericht; ein ungültiges Ergebnis wird nicht freigegeben. Erwartbare
Eingabefehler werden auch am CLI-Einstieg ohne Traceback gemeldet.

Die Originaldateien, Beschreibung und alte Vorlage wurden nicht geändert.

## Reproduktion und Ergebnis

Der ursprüngliche lokale Auftrag `25940ca9de1041288ee3dc8fe8d7d70e` wurde mit
seinem gespeicherten Rasterbild, seiner Vorlage und seinem Beschreibungstext
erneut verarbeitet; die Ausgabe liegt getrennt unter diesem Prüfverzeichnis.
Der Lauf liefert nach etwa zwei Sekunden einen SVG-Entwurf mit genau einem
Kreis und einem Dreieck. Die zwei Zusatzlinien sind nicht enthalten. Das
eigenständige CLI-Ergebnis ist als **nicht bestanden** gekennzeichnet, weil
sein Vordergrund-IoU von etwa 0.835 die Rastergrenze verfehlt. Der wieder
funktionierende Start bedeutet daher keine behauptete erfolgreiche
Qualitätskonvertierung.

Ein zusätzlicher Test führt den Fall über `Jobs.start`, den echten GUI-Worker,
den Sample-Worker und die erste CLI-Konvertierung aus. Er prüft das angebotene
Ergebnis, die unveränderte Vorlage, die Elementliste, die Qualitätskennzeichnung
und das Fehlen eines Tracebacks. Weitere Tests prüfen fehlgeschlagene Starts,
Verneinungen, gemeinsame Linienstärken und skalierte Baugruppen.

Die Korrektur erweitert keine allgemeine Sprachinterpretation. Sie beseitigt
den gemeldeten Abbruch und lässt eine unpassende Vorlage die normale
Konvertierung nicht mehr verhindern. Die umfassenderen Grenzen des bisherigen
Parsers bestehen weiterhin.

## Prüfstand

172 gezielte Tests bestehen, darunter der echte GUI-Start mit der gemeldeten
Pumpe, der CLI-Fehlerbericht ohne Traceback, die Vorlagenanpassung als Baugruppe
und die Inventarprüfungen. `git diff --check` und die Nullprüfung für Bild-ID-
Sonderfälle bestehen ebenfalls. [Kompakter Nachweis](summary.json).

Ein zusätzlicher, weiter gefasster Prüflauf zeigte weiterhin Fehler bei zwei
alten `sample_contrast`-Konvertierungen: Deren zusammengesetzter Kurvenpfad wird
nicht als zwei beschriebene Diagonalen erkannt. Auch reine Linienstärken-
Validatorproben ohne Elementliste scheitern noch an der zuvor eingeführten
Inventarpflicht. Diese Fälle wurden nicht als bestanden gezählt. Sie sind
verbleibende Grenzen der strikten Inventarprüfung und werden durch den
behobenen Startabbruch der gemeldeten Pumpe nicht als gelöst behauptet.
