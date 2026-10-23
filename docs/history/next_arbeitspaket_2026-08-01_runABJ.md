# Nächstes Arbeitspaket – AC0502-L/M Raster-Topologiedetektor Run ABJ (2026-08-01)

Run ABJ arbeitet den in Run ABI dokumentierten nächsten Schritt ab: Der
gemeinsame AC0502-L/M-Builder wird nicht mehr nur mit manuell ermittelten
Bounding-Boxen geprüft, sondern aus allgemeinen Kandidaten eines realen
Rasterbilds aufgerufen.

## 1) Katalogfreier Feld-/Topologiedetektor

`detect_diagonal_circle_cross_diagram_geometry_ir` sucht ohne Dateinamen- oder
Bild-ID-Wissen nach drei gemeinsam notwendigen Evidenzen:

- einem gesättigten, annähernd quadratischen Diagrammfeld,
- hellen Pixelspuren entlang beider Felddiagonalen und
- einem grössenplausiblen Kreiskandidaten links auf Höhe der Feldmitte.

Nur wenn alle drei Bedingungen erfüllt sind, übergibt der Detektor die
normalisierte Feld-Bounding-Box an
`build_diagonal_circle_cross_diagram_geometry_ir`. Eine isolierte rote Fläche
reicht ausdrücklich nicht zur Familienklassifikation. Kleine symmetrische
Ränder kompensieren JPEG-Antialiasing und die durch die weissen Diagonalen
unterbrochene Farbsättigungsmaske.

## 2) Anschluss an den allgemeinen Perception-Pfad

`build_perception_seeded_geometry_ir` prüft die erkannte Familientopologie vor
dem allgemeinen Einzelprimitive-Merge. Bei einem Match liefert der Pfad den
gemeinsamen normalisierten Sieben-Primitive-Seed aus Run ABI; andernfalls bleibt
das bisherige Description-/Perception-Verhalten unverändert.

## 3) Validierung und Laufzeit

- Beide realen Rasterreferenzen `AC0502_1L_sia.jpg` und
  `AC0502_1M_sia.jpg` aktivieren denselben Detektor und denselben Builder.
- Die erkannten Feld-Bounding-Boxen sind `0.7/0.25/0.25/0.5` (L) und
  `0.683333/0.233333/0.266667/0.533333` (M). Sie skalieren mit dem jeweiligen
  Viewport und enthalten keine absoluten Familienkoordinaten.
- Der fokussierte Testlauf benötigt 0.43 Sekunden und endet mit `7 passed`.
- Ein Negativtest bestätigt, dass ein rotes Quadrat ohne Kreuz- und
  Kreis-Topologie keinen Seed erzeugt.

## 4) Plan-B-/Perception-Lerneffekt und nächster Schritt

Der AC0502-L/M-Pfad ist jetzt auch auf Detektorebene **generalisiert**: reale
Rasterevidenz wählt die gemeinsame Topologie, und der normale Perception-Einstieg
ruft den skalierbaren Builder auf. Weder Sample-SVG noch Dateiname werden zur
Laufzeit gelesen.

Als nächstes folgt die in Run ABH abgegrenzte AC0538-Klassifikation. Der linke
Diagonal-/Kreisanker soll wiederverwendet werden; die rechte Feldtopologie muss
jedoch anhand der grauen Rahmenkontur und der weissen Stufenkurve vom
AC0502-Kreuz unterschieden werden.
