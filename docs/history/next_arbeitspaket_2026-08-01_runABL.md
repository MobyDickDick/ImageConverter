# Nächstes Arbeitspaket – Rasterparametrisierte AC0538-Stufenspur Run ABL (2026-08-01)

Run ABL arbeitet den in Run ABK dokumentierten Folgepunkt ab: Die vier
Knickpunkte und die Konturbreite der Stufenspur werden aus dem Raster geschätzt,
statt ausschließlich die initialen normalisierten Familienrelationen zu nutzen.

## 1) Katalogfreie Rastermessung

Der Stufendetektor trennt die hellen Pixel der rechten oberen und linken unteren
Vertikalspur. Robuste Median- und Quantilschätzungen liefern deren x-Lagen sowie
äußere und mittlere y-Endpunkte. Eine Distanztransformation schätzt zusätzlich
die Konturbreite. Alle Werte bleiben relativ zur erkannten Feld-Bounding-Box;
Dateiname, Sample-Pfad und Viewportgröße gehen nicht in die Entscheidung ein.

## 2) Qualitätsgesicherte Grenzen

Der wiederverwendbare Builder akzeptiert optionale Messwerte, begrenzt jeden
Knickpunkt aber auf ein enges, topologiespezifisches Fenster. Die relative
Konturbreite bleibt zwischen 0,03 und 0,09. Ohne Rastermessung erzeugt derselbe
Builder weiterhin den neutralen Seed aus Run ABK.

## 3) Tests und Ergebnis

- Der Builder-Test erzwingt die Punkt- und Breitenbegrenzung mit synthetischen,
  absichtlich überzogenen Messwerten.
- Der reale Rastertest weist nach, dass `AC0538_1L_sia.jpg` nicht mehr die
  neutralen vier Punkte und die neutrale Konturbreite übernimmt.
- Die Kreuzfamilie bleibt ein Negativfall; der allgemeine Perception-Einstieg
  wählt weiterhin den Stufenpfad ohne Katalognamenwissen.
- Der fokussierte Vertrag umfasst elf grüne Tests.

## 4) Perception-Lerneffekt und nächster Schritt

Die Stufenspur ist nun nicht nur auf Klassen-/Seed-Ebene, sondern auch für ihre
lokale Rastergeometrie **generalisiert**. Als nächstes sollten Feldfüllfarbe,
Rahmenfarbe und Ankergeometrie aus ihren jeweiligen Rasterkandidaten in den
gemeinsamen Builder übernommen und gegen weitere AC0538-Größenvarianten geprüft
werden.
