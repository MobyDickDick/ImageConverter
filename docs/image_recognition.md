# Lokale Bilderkennung und gespeicherte Beschreibungen

Stand 15. November 2026. Die Weboberfläche untersucht Bilder mit leerer
Beschreibung nach dem Hochladen oder der Windows-Dateiauswahl automatisch.
**Bild erkennen** lässt sich auch bei vorhandener Beschreibung verwenden.
Eigene Texte werden dabei nicht überschrieben.

Die erste Stufe vergleicht Bildpunkte mit rund 500 verwendbaren, bereits
pixelgeprüften Katalogpaaren. Identische Bildpunkte liefern die aktuelle
Beschreibung unabhängig vom Dateinamen und Bildformat. Widersprüchliche
Beschreibungen identischer Referenzbilder verhindern eine automatische Übernahme.
Die zweite Stufe erkennt einzelne nicht angeschnittene Kreise, Rechtecke,
Quadrate und Dreiecke mit einfarbiger Fläche auf einfarbigem Hintergrund;
einfache gleichmässige Konturen sind teilweise unterstützt. Sie erzeugt eine
deutsche Beschreibung aus dem aktuellen Raster. Zusätzliche Komponenten,
Innenzeichen, deutliche Verläufe, unsichere Farben und unregelmässige Konturen
führen zum Verzicht. Diese begrenzten Prüfungen ersetzen keine allgemeine
Objekt- oder Schrifterkennung. Die Grundformerkennung arbeitet nur an Bildern
mit 18 bis 1024 Pixeln je begrenzender Kante und ausreichend grossen Formen;
grössere Bilder bleiben für Referenzsuche und manuelle Beschreibung verfügbar.

Bis zu drei ähnliche Referenzen erscheinen mit Original, geprüftem SVG und
Beschreibung. Der Vergleich berücksichtigt Farbe, Kanten und Seitenverhältnis.
Die Rangfolge ist keine kalibrierte Erkennungswahrscheinlichkeit. Nur
**Beschreibung übernehmen** setzt den Text eines ungefähren Nachbarn ein.
Insbesondere Buchstaben, Farben, Anschlusslinien und Pfeilrichtungen müssen
am aktuellen Original geprüft werden. Das Referenz-SVG wird nicht als
Konvertierungsergebnis oder als Suchgeometrie kopiert.

Die Vergleichsbasis stammt aus dem aktuellen Qualitätsbericht. Beide Renderer
müssen das gespeicherte Paar akzeptiert haben; Original und SVG müssen ihre
gespeicherten SHA-256-Prüfsummen weiterhin erfüllen. Nicht native SVGs,
Quellkonflikte, unbrauchbare Beschreibungen und reservierte Prüfbestände bleiben
ausgeschlossen. SVG-Strukturdaten werden tatsächlich aus dem konvertierten
Dokument gelesen. Neue bestandene Katalogpaare und Beschreibungskorrekturen
werden beim nächsten Erkennungsaufruf berücksichtigt. Ein Netztraining und
zusätzliche Downloads sind nicht erforderlich. Alle Arbeit bleibt lokal.

Die Konvertierung verwendet anschliessend den vorhandenen Suchpfad und alle
bisherigen Qualitätsgrenzen. Eine Erkennung meldet niemals allein einen
Konvertierungserfolg. Ein unbekannter synthetischer Kreis wurde im echten
GUI-Arbeiter ohne Referenzbestand und ohne manuell eingegebene Beschreibung
konvertiert und akzeptiert. Der reproduzierbare Test steht in
`tests/test_image_recognition.py`.

Der begrenzte Vergleich mit 24 bekannten Familien steht in
`artifacts/evaluation/image_recognition_v1/summary.json`. Wiedererkennung und
Grössenänderung sind getrennt ausgewiesen; daraus folgt keine Genauigkeit auf
unbekannten Familien. Wiederholung:

```text
python -m tools.evaluate_image_recognition --output artifacts/evaluation/image_recognition_v1 --limit 24
```

Textänderungen werden nach einer kurzen Eingabepause, beim Verlassen des Felds
und vor einem Bildwechsel oder Konvertierungsstart gespeichert. **Text speichern**
ermöglicht einen sofortigen Versuch. Die Rückmeldung unter dem Feld bestätigt
die Speicherung oder meldet den Fehler; bei einem fehlgeschlagenen Speichern
bleibt der Text stehen und ein angeforderter Bildwechsel/Start wird zurückgehalten.
Beim Verlassen der Seite wird zusätzlich ein lokaler Keepalive-Aufruf versucht.
Ein bereits bestätigter Text übersteht Serverneustart und erneuten Upload
desselben Bildinhalts unter anderem Namen. Die letzte gespeicherte Bearbeitung
hat Vorrang vor dem Erstellungsdatum des Auftrags.

Bei einem Original mit gleichem Namen und identischen normalisierten Bildpunkten
wird genau dessen `<bild>`-Eintrag in beiden vorhandenen XML-Tabellen mit
`beschreibung_modus="ersetzen"` aktualisiert. Die Familienbeschreibung und andere
Grössenvarianten bleiben erhalten. Ein gleichnamiger anderer Upload ändert den
Katalog nicht. Die Katalogansicht berücksichtigt die Beschreibungsrevision beim
regelmässigen Nachladen. Ein abgeschlossener Auftrag behält seinen historischen
Eingabetext und Prüfstatus; die Bearbeitung erzeugt einen neuen bereiten Auftrag.
Leere Texte werden lokal gespeichert und löschen keine Katalogbeschreibung.

Die einmalige Wiederherstellung hat 19 jüngere explizite Korrekturen aus
gespeicherten GUI-Aufträgen in beide XML-Tabellen übernommen. Ältere Experimente
als die bisherige gepflegte Tabelle bleiben ausgeschlossen. Der Nachweis steht in
`artifacts/evaluation/description_persistence_v1/summary.json`; jede Änderung ist
an das passende Original gebunden. Noch nie an den bisherigen Server gesendete
Browsertexte lassen sich nachträglich nicht aus Auftragsdateien wiederherstellen.

Für die neuen Funktionen den Webserver nach laufenden Konvertierungen neu starten
und die Browserseite neu laden. Ein alter Server kann die neue Speicher-API nicht
bedienen; die Oberfläche weist unter dem Beschreibungsfeld darauf hin.
