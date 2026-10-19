# Abgewiesene Kontrolle mit Verzögerung je Renderaufruf

24 tatsächliche feste Kontrollversuche mit 15 Sekunden Bildbudget. Die
Renderer-Zugänge sind austauschbar; die wiederholten kurzen Windows-Wartezeiten
im Zusatzaufwand-Arm führen aber bei drei Versuchen zu einem Zeitabbruch ohne
gültige Ausgabe. Die Kontrolle weist deshalb keine reine Qualitätsgleichheit
nach. Die verwendete Hilfsquelle liegt als `component_controls.py` bei.

Alle Versuche bleiben erhalten und zählen nicht als bestandene Kontrollabnahme.
Die abschließende Kontrolle unter `../component_value_v1` verwendet stattdessen
eine einmalige Verzögerung pro Worker.
