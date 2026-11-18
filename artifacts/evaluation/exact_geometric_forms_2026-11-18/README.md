# Geometrische Formtreue, 18. November 2026

AC0150_L enthält laut Original und unverändert gespeicherter Beschreibung einen
Kreis. Die native Rekonstruktion erzeugt jetzt einen ungefüllten SVG-Kreis.
Die Quadratvarianten AC0140_L und AC0140_M besitzen je einen gemeinsamen
Grössenparameter für beide Quadratdiagonalen. Alle Linienbänder sind gerade
und am Rechteck beschnitten.

`summary.json` hält Eingabedatei, SHA-256 des Originalrasters, unveränderte
Beschreibung, Rastergates, Detailfehler und die geprüfte Forminventur fest.
Die rekonstruierten SVGs und PNGs sowie `comparison.png` liegen lokal in diesem
Verzeichnis; die Kreisvorlage ist unter `artifacts/samples/AC0150_L.svg` gespeichert.

Die Raster- und Detailgrenzen wurden nicht gelockert. Die gemeinsame
Geometrieprüfung wurde verschärft und zusätzlich gegen kleine Deformationen,
Knicke und Anhängsel geprüft.

Implementierung und Geltungsbereich:
[Dokumentation](../../../docs/exact_geometric_forms_2026-11-18.md).
