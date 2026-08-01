# Nächstes Arbeitspaket – Rasterappearance und AC0538-Größenvarianten Run ABM (2026-08-01)

Run ABM arbeitet den in Run ABL dokumentierten Folgepunkt ab: Feldfüllfarbe,
Rahmenfarbe und Kreisanker-Geometrie werden aus Rasterkandidaten in den
gemeinsamen AC0538-Builder übernommen.

## 1) Katalogfreie Appearance-Messung

Der Stufendetektor bildet robuste Farbmediane getrennt für die gesättigte
Feldfläche und die dunkleren Randpixel. JPEG-Säume und die weiße Stufenspur
gehen damit nicht als dominante Farbwerte ein. Der passendste linke
Kreiskandidat liefert eine feldrelative Bounding-Box. Weder Dateiname noch
Viewportmaße werden an den Builder übergeben.

## 2) Qualitätsgesicherter Builder-Vertrag

`build_diagonal_circle_step_diagram_geometry_ir` akzeptiert nun optionale
Feld-/Rahmenfarben und eine feldrelative Kreis-Bounding-Box. Die Lage und Größe
des Kreises bleiben in engen Topologiefenstern; ohne Messwerte bleiben die
neutralen Defaults vollständig rückwärtskompatibel. Die gemessene Rahmenfarbe
wird zugleich für Rahmen, Kreis und beide Verbindungsstrecken verwendet.

## 3) Größen- und Farbvarianten

Die kompakte Klassifikation berücksichtigt, dass vertikale Stufenecken bei
kleinen Rastern in beide breiten Diagonalbänder aliasen können. Die strengere
Kreuzschwelle erhält den AC0502-Negativvertrag und klassifiziert zusätzlich
`AC0538_1M_sia.jpg`. Der Appearance-Vertrag läuft über `AC0538_1L_sia.jpg`,
die kompakte M-Variante und das grüne `AC0538_2L_sia.jpg`; alle drei liefern
vom neutralen Seed abweichende Farben und Kreisgeometrien.

Der fokussierte Vertrag umfasst 15 grüne Tests.

## 4) Perception-Lerneffekt und nächster Schritt

Der AC0538-Seed ist nun für lokale Geometrie **und** Appearance rastergeführt.
Als nächstes sollte die Feldkandidatensuche von der Sättigungsmaske entkoppelt
werden, damit auch graue AC0538-Felder sowie die noch stärker aliasenden
S-Größen dieselbe katalogfreie Topologie aktivieren.
