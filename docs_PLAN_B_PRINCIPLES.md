# Plan-B Grundsätze für manuelle Rekonstruktionen

1. **Keine festen Stilparameter**: Geometrie-Parameter (z. B. Bandbreite von Diagonalen) dürfen nicht hartcodiert pro Symbol bleiben.
2. **Iterativ bestimmen**: Parameter werden aus Bildsignal + sprachlicher Beschreibung durch eine iterative Suche bestimmt.
3. **Fehlergetriebene Auswahl**: Kandidaten werden gerendert und über den Pixel-Fehler gegen das Zielbild bewertet; der beste Kandidat gewinnt.
4. **Autarkie**: Der Konverter soll aus **Beschreibung + Eingabebild + Software** ohne zusätzliche manuelle Nachdaten lauffähig sein.
5. **Dokumentation vor Änderung lesen**: Vor Anpassungen am Plan-B-Verhalten sind diese Grundsätze zu beachten.
