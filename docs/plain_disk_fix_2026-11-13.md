# Einfacher Kreis: Web-Konvertierung vom 13.11.2026

Der Web-Auftrag für `AC0800_M.jpg` mit der unveränderten Beschreibung
«Grauer Kreis mit grauem Rand und hellgrauem Hintergrund» erzeugte ein Rechteck
mit zusätzlichen Strichen. Beide gespeicherten Fehlversuche liegen unter
`artifacts/gui/5d9c3ddabee74d8a8987ad69892ce6e5` und
`artifacts/gui/e62e392886c749cda7a5c72a670e041d`.

Die allgemeinen Szenenparser verlangen quantifizierte Formulierungen wie
«Ein Kreis»; der reine Konturweg setzt zusätzlich weisse Innenflächen und
Abstand zum Bildrand voraus. Die Ersatzsuche verlangt wiederum einen
hinreichend grossen, erodierbaren Farbflächenkern. Der dünne Kreisrand des
20×20-JPEGs erfüllt diese Voraussetzung nicht. Deshalb fehlte ein passender
Kreiskandidat; mehr Optimierung konnte nur den falschen Aufbau verbessern.

`imageCompositeConverterPlainDisk.py` ergänzt hinter den bestehenden
Szenenmodellen einen allgemeinen nativen Kreisfit. Die vollständige
Beschreibung begrenzt ihn auf einen einzelnen Kreis mit einfarbiger Füllung
und Rand. Mittelpunkt und Radius werden aus dem beobachteten Rand geschätzt,
Füllung, Kontur und Hintergrund aus den Pixeln. Geometrie und Farben werden
mit dem bestehenden Suchbudget angepasst. Lokale Prüfungen im Inneren und
ausserhalb der Kontur verhindern, dass kleine Zeichen oder Zusatzobjekte
verschwinden. Es gibt weder Dateinamenregeln noch neue Qualitätsgrenzen.

Alle drei Originalgrössen S/M/L bestehen die unveränderten Pixel-,
Vordergrund-, IoU- und Kantengrenzen mit MuPDF und unabhängig mit librsvg.
Vier synthetische Farb-/Grössenfälle mit verschobenem Mittelpunkt bestehen;
zusätzlicher Beschreibungsinhalt, kleine Bilddetails und ein Rechteck werden
abgelehnt. Der echte GUI-Test verwendet einen neutralen Dateinamen.

Der erneut gestartete Auftrag im laufenden Webserver
`cef0a786816247eb8594b126e716a46e` besteht nach 2,5 Sekunden, mit 73 bewerteten
Kandidaten und genau einem nativen Kreis über einer Hintergrundfläche.
Der unabhängige librsvg-Check besteht ebenfalls (Vordergrund-IoU 0,9895).
Historische Fehlversuche bleiben erhalten. Kompakte lokale Belege und SVGs
liegen unter `artifacts/evaluation/plain_disk_2026-11-13/`.

Regression: 156 Tests aus Kreisfit, GUI, Primitivszenen, geschichteten Szenen,
Ersatz-Struktursuche und Kurztextkreisen bestehen. Zwei GUI-Tests benötigten
wegen Sandboxbeschränkungen einen separaten Lauf mit lokalem Socketzugriff
und Erlaubnis zum Beenden ihres eigenen Testprozesses; beide bestehen.
