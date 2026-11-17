# Randbezüge und gekoppelte Linien

Die gemeldete Beschreibung gehört im Arbeitsverzeichnis zu `AC0150_1.jpg`.
Das Original ist 40 × 80 Pixel gross und deutlich JPEG-komprimiert. Die
Beschreibung ist verständlich: grauer Rahmen, roter horizontaler Verlauf und
zwei an der horizontalen Mittelachse gespiegelte Geraden mit gemeinsamem Ende
am rechten Rand. „Graues Rechteck“ ist dabei eine unnötige mögliche
Mehrdeutigkeit; „Rechteck mit grauem Rahmen und rotem Hintergrundverlauf“ ist
eindeutiger.

## Ursache und gemeinsame Änderung

Der bisherige Suchweg für Dach-/V-Linien verlangt überwiegend eine Spitze oben
oder unten und einen vertikalen Verlauf. Eine seitlich angeordnete Verbindung
mit horizontalem Verlauf wird dadurch nicht als dieselbe Kombination einfacher
Elemente erkannt. Unabhängige Verschiebungen vorhandener Teilstücke beheben
diese fehlende Beziehung nicht.

`imageCompositeConverterRelations.py` übersetzt explizite Randmittelpunkte in
Bezüge auf ein gemeinsames Rechteck. Die Linie speichert keine unabhängig zu
ratenden Endkoordinaten. Doppelt genannte Endpunkte teilen dieselbe Position;
eine verlangte Spiegelung koppelt die zugehörigen Anschlüsse. Verlaufsausrichtung
und Farben sind davon unabhängig. Die Einbindung erfolgt über die bestehende
Primitivrekonstruktion und deren gemeinsame Registry für frische Konvertierung,
Vorlagen und native Nachbesserung. Es gibt keinen Schalter für einen Dateinamen.

Der derzeitige Wortschatz umfasst benannte Linien, die zwischen den Mittelpunkten
des oberen, unteren, linken und rechten Rechteckrandes verlaufen. Er ist endlich;
beliebiger Freitext oder alle möglichen geometrischen Beziehungen werden damit
noch nicht vollständig verstanden. Derselbe Solver verarbeitet alle vier
Ausrichtungen, beide Verlaufsachsen und auch andere Linienanzahlen. Gleichmässig
gefüllte Rechtecke und eine einzelne Linie benötigen ebenfalls keinen eigenen
Motiv-Suchweg; bei einer flachen Füllung wird kein Verlauf erzeugt.

Für gerasterte, nicht als „genau“ beschriebene Mittelpunkte dürfen die Anschlüsse
höchstens sechs Prozent der betreffenden Rechteckseite abweichen. Im realen
JPEG beträgt die gemeinsam geschätzte Abweichung der oberen und unteren
Anfänge ungefähr einen Pixel nach links. Die gemeinsame Spitze bleibt auf der
Symmetrieachse. „Genau … Mitte“ fixiert den Bezug ohne diese Anpassung.

Vollständige schmale Strichpolygone werden geometrisch mit dem Rechteck
geschnitten. Der Rahmen wird darüber gezeichnet. Dieselbe Schnittfunktion wird
auch bei den innen ausgesparten Diagonalen verwendet. Die allgemeine Formzählung
erkennt lange, schmale Strichpolygone anhand ihres Seitenverhältnisses auch dann,
wenn sie etwas breiter als drei Pixel sind.

## Prüfung auch nach weiteren Suchschritten

Ein erster realer Durchlauf zeigte einen weiteren Fehler: Die spätere native
Nachbesserung konnte eine einzelne Linie stauchen und verschieben. Der dadurch
kleinere Pixelfehler setzte sich gegen die beschriebene Symmetrie durch.

Die Beschreibungsprüfung vergleicht jetzt die dargestellten Strichgeometrien im
Koordinatensystem ihres Rechtecks. Gemeinsame Endpunkte, gespiegelte Endlagen und
Strichbreiten müssen zusammenpassen. Die Rasterprüfung verlangt zusätzlich
sichtbare Linien entlang der verlangten Strecken. Ein Kontrollrendering ohne
die Vordergrundstriche belegt deren tatsächlichen sichtbaren Beitrag. Verdeckte
Elemente, eine helle Stelle der Füllung oder Metadaten reichen nicht aus. Die
Prüfung berücksichtigt auch Verlaufsrichtung, Füllfarbklasse, angegebenen
Helligkeitsgipfel, sichtbare Begrenzung und die Lage des Rahmens über den Linien.

Verletzt eine Parameter-Nachbesserung die Beschreibung, bleibt die zuvor gültige
Konstruktion erhalten. Die Konvertierung bricht deshalb nicht mehr wegen eines
schlechteren letzten Versuchs ab. Das gilt allgemein für die native
Parameter-Nachbesserung. Auch die normale GUI-Ergebnisübernahme prüft das
gespeicherte SVG jetzt direkt gegen die Beschreibung. Die Nachprüfversion alter
Ergebnisse steigt auf 9.

## Nachweis am Original

Ein regulärer GUI-Lauf im Profil „quick“ erhielt das Original-JPEG unter dem
neutralen Uploadnamen `unrelated.jpg` und die unveränderte Beschreibung. Der
isolierte Projektordner enthielt zu Beginn kein vorhandenes Ergebnis. Es wurde
kein Sample angehängt. Der Lauf endet mit `status=done`, `quality=passed` und
bestandener nachträglicher Beschreibungsprüfung. Das Ergebnis enthält zwei
vollständige, gespiegelte Strichpolygone.

Der normalisierte Pixelfehler beträgt 0.00615, die Kantendeckung 0.8298 und die
Vordergrund-IoU 0.9562. Eine frühere unsymmetrische Variante hatte einen kleineren
Pixelfehler, besteht die neue Beziehungsprüfung aber ausdrücklich nicht.
Die Messwerte belegen keine exakte Rekonstruktion des komprimierten JPEGs.

[Original und neuer GUI-Lauf](../artifacts/evaluation/anchor_relations_2026-11-17/comparison.png),
[SVG](../artifacts/evaluation/anchor_relations_2026-11-17/gui-result.svg),
[Messbericht](../artifacts/evaluation/anchor_relations_2026-11-17/summary.json).

Die Tests umfassen unabhängige Motive in vier Ausrichtungen mit horizontalem
und vertikalem Verlauf, mehrere Farben, eine zusätzliche dritte Linie und
Gegenbeispiele für fehlende oder verdeckte Linien, falsche Endpunkte, Farben,
Verlaufsrichtungen, Begrenzungen und Zeichenreihenfolgen. Zusätzliche Prüfungen
stellen sicher, dass unabhängig veränderte Linien trotz bestandenem Pixeltest
abgelehnt werden und ein ungültiger Parameter-Versuch den gültigen Stand erhält.

Abschliessend bestanden 396 verschiedene gezielte Tests: 195 Such-, Form-,
Beschreibungs- und Strukturprüfungen, 186 weitere Anwendungsregressionen,
26 Beziehungsprüfungen (davon 23 bereits im ersten Lauf enthalten) und 12
ausgewählte GUI-Abnahmeprüfungen. Die Protokolle liegen im Vergleichsverzeichnis.
