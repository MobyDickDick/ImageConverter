# Verbindliche geometrische Formen

Die Anforderung gilt für jedes beschriebene Objekt: Die Suche darf seine
Parameter anpassen, muss dabei aber seine geometrische Form erhalten.
Rasterähnlichkeit allein bestätigt keine Gerade, keinen Kreis und kein Quadrat.

## Ursache und gemeinsame Korrektur

Das gemeldete Original ist AC0150_L (60 × 400 Pixel). Seine gespeicherte
Beschreibung verlangt einen ungefüllten Kreis. Die bisherige Rekonstruktion
des schmalen Panels unterstützte nur die Variante mit einer Raute. Der
allgemeine Suchweg konnte deshalb auf ungeeignete freie Konturen ausweichen.

Daneben besass die gemeinsame Formzählung zu grosse geometrische Toleranzen:
bis zu drei Prozent Achsenunterschied bei Kreisen und bis zu fünfzehn Prozent
Seiten- beziehungsweise Winkelabweichung bei Vierecken. Ein langes, schmales
Polygon konnte auch mit einem Anhängsel noch als Linie zählen.

Die gemeinsame Prüfung verwendet jetzt eine relative numerische Toleranz von
`1e-5`. Sie prüft die dargestellten Koordinaten nach Gruppentransformationen:

- Kreise müssen gleiche Halbachsen behalten. Eine passende Ellipse darf durch
  eine Transformation zu einem Kreis werden; ein gestreckter Kreis ist eine Ellipse.
- Rechtecke brauchen rechte Winkel, Quadrate zusätzlich gleiche Seiten und
  gerade Ecken. Eine beliebige vierseitige Kontur ersetzt diese Formen nicht.
- Rauten werden als eigene Form mit vier gleichen Seiten geprüft.
- Geraden dürfen auch sehr kleine Knicke nicht als Rasterungenauigkeit übernehmen.
  Beschnittene Bänder brauchen parallele Seiten und gerade Schnittkanten.
- Formen mit verschwindender Grösse oder ungültigen Koordinaten belegen kein Objekt.

Diese Prüfung ist in der vorhandenen gemeinsamen Beschreibungsabnahme
verankert und gilt deshalb für frische Konvertierungen, Vorlagen, die native
Nachbesserung und die abschliessende GUI-Bewertung. Geometrisch ungültige
Entwürfe erhalten durch einen bestandenen Pixelvergleich keine Freigabe.

## Rekonstruktion des gemeldeten Motivs

Das Panel unterstützt jetzt einen echten SVG-Kreis mit Mittelpunkt und einem
Radius. Das Quadrat verwendet ebenfalls nur einen Grössenparameter; seine
horizontalen und vertikalen Diagonalen lassen sich nicht unabhängig verzerren.
Die drei sichtbaren Diagonalstriche sind vollständige gerade Bänder, die mit
dem Rechteck geschnitten werden. Die Aussparung entsteht durch zwei getrennte
parallele Bänder. Es sind keine zusätzlichen Konturstücke nötig.

Die sichtbare Detailprüfung bleibt zusätzlich erhalten: Ein verborgenes
Formelement ersetzt die sichtbare Kontur nicht, und die Aussparung muss im
gerenderten Bild vorhanden sein. Die Prüfung der gesamten Panelstruktur lehnt
zusätzliche nicht zugehörige Geometrie ab.

Alle drei realen Neuaufbauten bestehen die unveränderten Rastergates sowie die
neue Geometrieprüfung:

| Original | Mittlere quadratische Pixelabweichung | Kantendeckung |
| --- | ---: | ---: |
| AC0150_L, Kreis | 0.0000845 | 0.9639 |
| AC0140_L, Quadrat | 0.0000725 | 0.9426 |
| AC0140_M, Quadrat | 0.0001609 | 0.9315 |

[Vergleichsbild](../artifacts/evaluation/exact_geometric_forms_2026-11-18/comparison.png),
[Messbericht](../artifacts/evaluation/exact_geometric_forms_2026-11-18/summary.json),
[Kreis-SVG als neue Vorlage](../artifacts/samples/AC0150_L.svg).
Beschreibungen und vorhandene Benutzeränderungen wurden nicht ersetzt.

## Prüfungen und Grenzen

Die Regressionen enthalten unabhängige Kreispanels auf verschiedenen
Zeichenflächen, das echte Original mit unverändertem Text, den Wechsel von
einer falschen Quadratvorlage zum Kreis und die mathematischen Eigenschaften
der unterstützten Grundformen. Ein zusätzlicher Test besitzt einen kleinen
Knick an der Diagonale: Der Pixelvergleich besteht, die Geometrieprüfung
verweigert die Abnahme.

Die synthetische Quadratvorlage für die bisherigen Paneltests wurde korrigiert:
Sie skalierte zuvor Breite und Höhe unabhängig und verlangte gleichzeitig ein
Quadrat. Sie erzeugt jetzt auch auf unterschiedlich proportionierten
Zeichenflächen ein tatsächliches Quadrat.

Das ist eine gemeinsame verbindliche Formprüfung der unterstützten Grundformen,
keine vollständige Interpretation beliebigen Freitexts oder beliebiger
Freiformkurven. Die bestehenden Prüfungen für Farben, Füllungen, Strichbreiten
und Beziehungen bleiben eigene Bedingungen; diese Änderung erweitert deren
Sprachverständnis nicht. Unvollständige Suchentwürfe können weiterhin fehlende
Objekte enthalten und sind damit noch kein abgenommenes Ergebnis.

Die GUI-Nachprüfversion steigt auf 10. Nach Abschluss laufender Konvertierungen
den Webserver neu starten, damit gespeicherte Erfolgsbewertungen erneut geprüft
werden. Historische SVGs werden dabei nicht umgeschrieben.
