# Kreis mit linkem Griff: zusätzlicher schräger Strich

Der Webauftrag `f93cc385355b4d1c85cadfdf5d6f4a53` zu `AC0812_L.jpg`
bestand die Pixelprüfung, enthielt aber neben dem Kreis und Griff einen
zusätzlichen schrägen Strich. Die Struktursuche hatte neun Rasterpixel am
Kreisrand als Restlinie interpretiert. Die anschliessende Parameteroptimierung
behielt diese falsche Objektstruktur bei. Die GUI meldete deshalb einen Entwurf
mit bestandener Pixelprüfung und offener Modellprüfung.

Der neue allgemeine Kreis-/Griff-Fit vermisst die sichtbaren Kreisbögen getrennt
vom Griff. Er passt Mittelpunkt, Radius, beide Strichbreiten, Griffende und
Farben direkt an das Raster an. Das SVG enthält genau einen nativen Kreis,
eine durch dessen Mittelpunkt verlaufende Grifflinie und die Hintergrundfläche.
Er unterstützt alle vier Achsenrichtungen. Die vollständige, begrenzte
Beschreibungsprüfung und lokale Rasterprüfungen schliessen Beschriftungen,
Zusatzobjekte sowie abgesetzte oder versetzte Griffe aus. Es werden keine
Referenz-SVGs oder bildnamenabhängigen Koordinaten verwendet.

Das bestätigte Modell begrenzt auch die spätere Nachoptimierung auf genau
einen Kreis und eine Linie. Zusätzliche Restlinien können deshalb auch bei
besseren globalen Pixelwerten nicht in die gespeicherte Ausgabe gelangen.
Andere Modelle und deren Struktursuche bleiben unverändert.

Alle drei Originalgrössen S/M/L bestehen die unveränderten Qualitätsgrenzen
mit MuPDF und unabhängig mit librsvg. Zwölf zusätzliche synthetische Fälle
prüfen andere Farben, Geometrie, Grössen und alle vier Griffrichtungen;
Gegenproben prüfen Zusatzobjekte, versetzte/abgesetzte Griffe und Zusatztext.
Ein eigener Test lehnt das Speichern einer zweiten Linie trotz bestätigtem
Kreis-/Griff-Modell ab. Ein echter GUI-Test verwendet einen neutralen Dateinamen.

Der neue Auftrag `c9d2204a943249899fbf7a2be57b7e57` im laufenden Webserver
verwendet dieselben Originalpixel und dieselbe unveränderte Benutzerbeschreibung
wie der Fehllauf. Er besteht nach 4,4 Sekunden die Pixel- und Modellprüfung
und speichert `artifacts/converted_images/converted_svgs/AC0812_L.svg`.
Der alte Fehllauf bleibt erhalten. Quellhashes, Prüfwerte beider Renderer,
SVGs und Vorschau liegen unter `artifacts/evaluation/stem_disk_2026-11-14/`.

Die neue Registrierung gilt für unbeschriftete, einfarbig gefüllte Kreise mit
einem geraden axialen Griff innerhalb der unterstützten Beschreibungsgrammatik.
Sie ist kein Nachweis für beliebige Kellen, Beschriftungen oder freie Anbauten.

Regression: 159 Tests aus Kreis-/Griff-Fit, einfachem Kreis, Textausschluss,
Beschreibungssprache, Bild-ID-Verbot, Initialisierung und GUI bestehen.
Vier GUI-Tests benötigten einen separaten Lauf mit lokalem Socketzugriff und
Erlaubnis zum Beenden ihres eigenen Testprozesses; alle vier bestehen dort.
