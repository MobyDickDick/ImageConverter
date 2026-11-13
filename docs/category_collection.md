# Kategorien-Kollektion im lokalen Webserver

Unter **Kategorien-Kollektion** (`/collection`) steht je ein festes Originalbild
aus jeder der 15 geometrischen Kategorien bereit. Fotos und besonders dichte
Motive sowie reservierte Prüfbilder sind ausgenommen.

Der Bestandsbericht vom 13.11.2026 enthält für **14 von 15 Kategorien** mindestens
ein gespeichertes SVG mit bestandenem Rastervergleich beider Renderer. In der
Kategorie **Panel/Röhre mit Kurven oder räumlichem Effekt** gibt es noch keinen
solchen Nachweis. Die Auswahl enthält deshalb 14 Beispiele mit gespeichertem
Rasterpass und ein ausdrücklich offenes Röhrenbeispiel. Es wurde keine neue
Konvertierungsserie dieser 15 Beispiele als erfolgreich ausgegeben.

## Ein Exemplar nach dem anderen

1. Die Kollektion öffnen und **Zur Konvertierung laden** anklicken. Das lädt das
   Original mit der Beschreibung des ausgewählten Katalogeintrags in den normalen
   Konverter. Es startet noch keine Konvertierung und lädt kein gespeichertes SVG
   als Sample. Eigene Beschreibungskorrekturen bleiben für neue Versuche erhalten.
2. Beschreibung und Suchbudget prüfen und **In SVG konvertieren** anklicken.
3. Original und Ergebnis vergleichen. Nach bestandener Qualitätsprüfung über
   **Als erweiterte Plan-B-Aufgabe verwenden** die Workbench vorbereiten. Der
   gleiche Übergang ist auch auf der Kategorienkarte verfügbar.
4. In der Workbench Original und Varianten einzeln prüfen, Rückkonvertierungen
   starten und Beobachtungen festhalten. Die bestehende Qualitätsprüfung für
   die Übernahme eines Konvertierungsergebnisses bleibt verbindlich.
5. Über **Nächstes Beispiel laden** im Konverter oder zurück über die Kollektion
   zum nächsten Motiv wechseln.

Die Kollektion zeigt getrennt die vorhandenen Rasterbelege, den letzten neuen
Versuch, einen bestandenen neuen Versuch und die vorbereitete Plan-B-Aufgabe.
Auch nach weiteren Fehlversuchen oder einem Serverneustart bleiben frühere
bestandene Versuche und Plan-B-Aufgaben erreichbar. **Weiteren Versuch
vorbereiten** erzeugt einen neuen Auftrag; vorhandene Ergebnisse bleiben erhalten.

Ein fehlgeschlagener Versuch bedeutet nicht grundsätzliche Nichtkonvertierbarkeit.
Ein erfolgreiches Exemplar bestätigt umgekehrt nicht alle Unterformen der Kategorie.
Die Kategorie „Kurven/Röhren“ bleibt als gezielter offener Fall in derselben Folge.

## Auswahl und Herkunft

`config/catalog_conversion_collection.json` speichert Kategorie, Dateiname,
Bildprüfsumme und Auswahlhinweis für die 15 Beispiele. Vor dem Laden werden
Quelldatei, heutige Klassenzuordnung und aktuelle Reservierungen geprüft.
Veränderte oder neu reservierte Originale werden gesperrt. Der Dateipfad wird
aus dem Katalog ermittelt; die Schnittstelle nimmt nur eine bekannte Kategorie an.

Aufträge speichern die Zugehörigkeit zur Kollektion, auch bei Wiederholungen
oder Sample-Optimierungen. Gespeicherte SVGs dienen in der Kollektion nur zum
Anzeigen vorhandener Belege. Für den Erfolg eines neuen Versuchs gelten die
normalen Konverter- und Plan-B-Prüfungen.

Die drei Fortschrittsfilter zeigen offene Beispiele, neu bestandene Beispiele
und vorbereitete Plan-B-Aufgaben. Die Startseite, die Qualitätsliste und die
Workbench verlinken auf die Kollektion.
