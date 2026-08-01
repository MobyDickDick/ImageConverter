# Nächstes Arbeitspaket – AC08-Kompaktvalidierung ohne Render-Long-Tail Run ABN (2026-08-01)

Run ABN korrigiert den nach Run ABM beobachteten Stillstand beim realen
`AC0834_S`-Testlauf. Die letzte sichtbare Meldung nannte die Textoptimierung,
die Stack-Diagnose zeigte aber anschließend zwei andere Kostentreiber: globale
Vektorsuche und abschließendes Farb-Bracketing renderten jeweils viele nahezu
identische SVG-Kandidaten in separaten Subprozessen.

Kleine AC08-Varianten verwenden jetzt ausschließlich die bereits vorhandenen
lokalen Element-Brackets, höchstens drei Validierungsrunden und anschließend
direkt ihre kanonischen Farben. Standardgroße Varianten behalten die globale
Suche und den vollständigen Farbpass. Die Auswahl beruht auf der vorhandenen
Geometrieklassifikation (`_S` oder minimale Rasterdimension), nicht auf
`AC0834` oder einer anderen Katalog-ID.

Die exakte Reproduktion mit 92 Iterationen und neun angeforderten
Validierungsrunden endet nun in rund sieben Sekunden mit drei ausgeführten
Runden und Exit-Code 0. Vorher überschritt derselbe Lauf den 30-Sekunden-Guard
bereits in der ersten globalen Suche beziehungsweise im finalen Farbpass.

Als nächstes sollte die Subprozess-Renderzeit als allgemeines Budget direkt an
globale und Farb-Kandidateniterationen weitergereicht werden, damit auch
Standardgrößen innerhalb einzelner Optimierungsoperationen hart abbrechen
können.
