# Nächstes Arbeitspaket – Restbudget pro Render-Subprozess Run ABP (2026-08-02)

Run ABP setzt den in Run ABO dokumentierten nächsten Schritt um: Ein bereits
gestarteter Optimierungsrender darf nicht mehr den statischen allgemeinen
Subprozess-Timeout ausschöpfen, wenn vom Validierungsbudget nur noch weniger
Zeit übrig ist.

## 1) Per-Call-Timeout im Rendervertrag

Der zentrale Render-Dispatch und seine Kompatibilitätswrapper akzeptieren nun
einen optionalen Timeout pro Aufruf. Der isolierte Renderer begrenzt diesen auf
den kleineren Wert aus allgemeinem Renderer-Timeout und Aufrufbudget; Aufrufe
ohne Override behalten unverändert den konfigurierten Standardwert.

## 2) Kopplung an das Validierungsrestbudget

Globale Vektorkandidaten und Farb-Bracketing berechnen unmittelbar vor ihrem
Render die verbleibende monotone Zeit bis zur Optimierungsdeadline. Diese
Restzeit wird nur für den betreffenden Aufruf weitergereicht. Damit beendet der
Subprozess auch einen bereits laufenden Kandidaten zeitnah, während die in Run
ABO ergänzten Prüfungen weiterhin verhindern, dass danach weitere Kandidaten
gestartet werden.

## 3) Regressionstests und nächster Schritt

Helper-Tests belegen die Restzeitübergabe für beide Optimierungspfade sowie die
Weitergabe durch den Render-Dispatch. Der bestehende Aufrufvertrag ohne
Deadline bleibt rückwärtskompatibel.

Als nächstes kann die Validierung Timeout-Rückgaben von regulären Renderfehlern
unterscheiden und in der Optimierungstelemetrie separat zählen. So wäre direkt
sichtbar, ob ein knappes Budget oder ein fehlerhaftes SVG einen Kandidaten mit
unendlichem Fehler beendet hat.
