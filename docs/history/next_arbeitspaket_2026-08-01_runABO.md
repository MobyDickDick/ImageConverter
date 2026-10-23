# Nächstes Arbeitspaket – Optimierungsdeadline für Renderkandidaten Run ABO (2026-08-01)

Run ABO setzt den in Run ABN dokumentierten nächsten Schritt um. Das bereits
für die semantische Validierung konfigurierte Zeitbudget wird nun als absolute,
monotone Deadline an die beiden subprocess-intensiven Optimierungsoperationen
weitergereicht: globale Vektorsuche und abschließendes Farb-Bracketing.

Beide Optimierer prüfen die Deadline unmittelbar vor jeder noch nicht gecachten
Kandidatenauswertung. Nach Budgetablauf wird kein weiterer SVG-Renderprozess
gestartet; die globale Suche verwirft den ausstehenden Track kontrolliert und
das Farb-Bracketing beendet die laufende Kandidatenfolge ohne unvollständige
Parameter zu übernehmen. Ohne konfiguriertes Validierungsbudget bleibt das
bisherige vollständige Suchverhalten erhalten. Die interne Deadline wird nach
jeder Operation auch bei Fehlern aus den Parametern entfernt.

Helper-Regressionstests setzen eine bereits abgelaufene monotone Deadline und
belegen für beide Suchpfade, dass keine Kandidaten-Renderfunktion mehr
aufgerufen und ein aussagekräftiger Budgetabbruch protokolliert wird. Die
Elementvalidierungs- und Optimierungshelper-Suiten bleiben grün.

Als nächster Schritt kann die Render-Subprozessschnittstelle selbst einen
pro Aufruf reduzierten Timeout übernehmen. Damit ließe sich zusätzlich ein
bereits gestarteter einzelner Render an das kleinere Restbudget koppeln, statt
nur weitere Kandidaten zuverlässig zu unterbinden.
