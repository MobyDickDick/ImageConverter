# Konvertierung mit unvollständig verstandener Beschreibung

Die manuelle Webkonvertierung verwendet `description_guided_v1`: Eine nicht
bestätigte Elementliste führt zu einem sichtbaren, speicherbaren Entwurf.
Pixelvergleich und Beschreibungsdiagnose bleiben sichtbar; «bestanden» wird
weiterhin nur nach erfolgreicher Gesamtprüfung vergeben. Der Hintergrundkatalog
verwendet weiterhin seine bisherige Freigaberegel.

Die Fünf- und Zehn-Minuten-Suche lehnt unbekannte Formulierungen nicht mehr vor
dem Start ab. Wenn der Grundformencompiler die Beschreibung nicht versteht,
erzeugt sie direkt einen Bildflächenentwurf, statt erfolglos das ganze Budget
zu verbrauchen. In den gewöhnlichen Profilen werden zuerst die bestehenden
Beschreibungsmodelle versucht. Für den Ausweichpfad bleiben bis zu zehn Sekunden
innerhalb des bisherigen Zeitlimits reserviert. Abbrechen beendet auch diesen
Worker als Prozessbaum.

Auch fehlende oder nicht auswertbare Ähnlichkeitsreferenzen blockieren manuelle
Aufträge nicht mehr. Der Originaltext und die Referenzdiagnose bleiben erhalten;
der Bildflächenpfad übernimmt dann direkt.

Der Ausweichpfad vergleicht bis zu fünf Farbquantisierungen (4–64 Farben),
übernimmt Löcher und dünne Linien und speichert die beste tatsächlich gerenderte
Version. Die Ausgabe enthält native SVG-Pfade ohne eingebettetes Bild. Grosse
Vorlagen werden für diesen Entwurf auf höchstens 256 Pixel Kantenlänge reduziert;
die SVG-Zeichenfläche behält die Originalgrösse. Solche Flächen sind noch keine
semantischen Grundformen; Farbverläufe und Buchstaben werden als Flächen angenähert.
Die Suche garantiert damit keine geometrisch perfekte Rekonstruktion.

`tests/test_description_guided_conversion.py` prüft echte Worker mit unbekannten
Texten, das gemeldete `AC0211_L.jpg`, Pixelvergleich, SVG-Export, Server-Neuladen,
die drei Ergebniswege (Konvertierung, Sample, Zwischenstand) und Zeitlimits.
Der gezielte Workflow **Description guided conversion** läuft ausschliesslich
auf GitHub Actions und legt Original, SVG, Messwerte und JUnit-Protokoll als
Artefakt `description-guided-evidence` ab. Lokale Tests oder Testkonvertierungen
werden nicht ausgeführt. CI-Ergebnisse werden im Pull Request verlinkt.

Nachweis: [GitHub Actions vom 28. November 2026](https://github.com/MobyDickDick/ImageConverter/actions/runs/46143184475)
bestätigt je 24 gezielte Python- und 16 Browser-Tests unter Ubuntu und Windows.
Der Vergleich der gesamten GUI-Datei ergibt zehn fehlgeschlagene Tests auf dem
Aufgabenbranch, zwölf auf der unveränderten Basis und keine zusätzlichen Fehler.
Diese zehn bestehenden Fehler sind damit ausdrücklich nicht behoben; die beiden
JUnit-Dateien und die vollständige Liste stehen im Artefakt
`gui-regression-comparison`. Die allgemeine Suite hat weitere fehlgeschlagene
und noch laufende Prüfungen und wird nicht als vollständig bestanden bezeichnet.

Für das gemeldete Bild mit unverändertem Benutzertext besteht der gespeicherte
SVG-Entwurf die Pixelprüfung: Vordergrund-IoU 0,9802, Kantenübereinstimmung 0,9323.
Die semantische Beschreibungsprüfung bleibt offen. Der direkte Bildflächenworker
wird auch als Prozess nach spätestens 15 Sekunden beendet, sodass ein unbekannter
Text in den freien Profilen keinen fünf- oder zehnminütigen Leerlauf verursacht.
