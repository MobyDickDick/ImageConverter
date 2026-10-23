# Plan-B Grundsätze für manuelle Rekonstruktionen

1. **SVG→Bild→SVG-Roundtrip**: Eine Plan-B-Aufgabe mit vorgegebenem SVG rendert nicht nur das unveränderte SVG, sondern erzeugt zuerst ein rasterisiertes Zielbild und konvertiert dieses anschließend wieder in SVG zurück.
2. **Semantische Parametervariation vor dem Rendern**: Vor der Rasterisierung werden SVG-Parameter systematisch variiert, z. B. Skalierung im Bereich `0.5..2.0` oder relative Lageverschiebungen von Teilmotiven. Die Variation darf ein Motiv bewusst über die erwartete Symbolgrenze hinausschieben, damit der Konverter Bildelemente aus dem Raster erkennt statt nur Beschreibungswerte abzuschreiben.
3. **Relative Beschreibung statt Zahlenkopie**: Falls die Bildbeschreibung zur Variation angepasst werden muss, beschreibt sie nur die semantische Lagebeziehung (z. B. „P rechts von der Kelle“) und enthält nicht die konkreten numerischen SVG-Parameter.
4. **Keine festen Stilparameter**: Geometrie-Parameter (z. B. Bandbreite von Diagonalen) dürfen nicht hartcodiert pro Symbol bleiben.
5. **Iterativ bestimmen**: Parameter werden aus Bildsignal + sprachlicher Beschreibung durch eine iterative Suche bestimmt.
6. **Fehlergetriebene Auswahl**: Kandidaten werden gerendert und über den Pixel-Fehler gegen das Zielbild bewertet; der beste Kandidat gewinnt.
7. **Autarkie**: Der Konverter soll aus **Beschreibung + Eingabebild + Software** ohne zusätzliche manuelle Nachdaten lauffähig sein.
8. **Dokumentation vor Änderung lesen**: Vor Anpassungen am Plan-B-Verhalten sind diese Grundsätze zu beachten.
