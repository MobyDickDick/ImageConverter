# Fortschritt zum Ziel einer breiten Bitmap-zu-SVG-Konvertierung

Die belegte Katalogabdeckung liegt bei ungefähr einem Fünftel. Ein Grossteil
der Bilder ist noch nicht erfolgreich abgenommen. Die vielen abgeschlossenen
Entwicklungs- und Prüfpakete dürfen nicht als Prozentwert der Bildabdeckung
interpretiert werden.

## Belastbare Ausgangsbilanz

Die vollständige Inventur vom 07.11.2026 umfasst **1.787** unterschiedliche
Katalogbitmaps, etwas mehr als die ursprünglich geschätzten 1.700.

| Maßstab | Anzahl | Anteil am Katalog |
| --- | ---: | ---: |
| Historisch archivierte Bild-/SVG-Paare | 379 | 21,2 % |
| Mindestens ein gespeichertes SVG besteht die strengen Rastergates beider Renderer | 348 | 19,5 % |
| Historisch archiviert und zugleich strenger aktueller Rasterpass | 288 | 16,1 % |
| Gespeichertes SVG verfehlt die strengen Rastergates | 1.311 | 73,4 % |
| Kein gespeichertes SVG | 124 | 6,9 % |
| Messfehler / damals reserviert | 2 / 2 | 0,1 % / 0,1 % |

Archiv und Rasterpass überlappen und dürfen nicht addiert werden.
Die strengere aktuelle Rasterprüfung bewertet auch Aspekte, die historische
Archivaufnahmen noch nicht vollständig geprüft haben. 379 historische Erfolge
sind deshalb keine Zusage von 379 heute vollständig fachlich neu geprüften
Ausgaben. Umgekehrt ist ein fehlender Rasterpass kein Beweis grundsätzlicher
Nichtkonvertierbarkeit.

Quellen: [vollständige Inventurbilanz](../artifacts/catalog_inventory/summary.json),
[aktueller Archivindex](../artifacts/satisfactory_conversions/index.json).
Der lokale Webserver stellt jetzt eine [vollständige Qualitätsliste mit
abbrechbarer Neumessung](catalog_quality_webserver.md) bereit.
Neue Webberichte bleiben getrennt unter `artifacts/gui/catalog-quality/`;
sie überschreiben den alten Inventursnapshot nicht.

Die Webanzeige berücksichtigt zusätzlich die aktuellen Sperren: sechs Bitmaps
aus vier reservierten Familien, deshalb 1.307 statt damals 1.311 als
`pixel_fail` angezeigte Bilder. Die Rasterpasszahl bleibt 348; die Verschiebung
ist keine Qualitätsverbesserung. Die neu gestartete vollständige Messung wurde
zuletzt abgebrochen. Die letzte vollständige Messung bleibt daher ausdrücklich
der Stand vom 07.11.2026.

## Was die jüngsten Pakete erreicht haben

Der produktive Fallback kann Grundformen wechseln, fehlende Linien ergänzen
und beobachtete Pfeil-/Gelenkgruppen in Szenen hinzufügen oder ersetzen.
An vier bekannten Auditfehlern verbessert sich die echte CLI von einem auf
drei bestandene Fälle. Sechs synthetische Kompositionsprüfungen bestehen
inzwischen ebenfalls. Das sind lokale Entwicklungsnachweise, keine
repräsentative Messung am gesamten Katalog.

CHECKER-04 und das jetzt abgeschlossene [CHECKER-05](next_arbeitspaket_2026-11-13_segment_checker.md)
schaffen eine unabhängige Objekt-/Relationsprüfung einschließlich zulässiger
Linienteilungen. Sie verbessern die Verlässlichkeit der Abnahme und erzeugen
selbst keine neuen erfolgreichen Konvertierungen. Die 18 alten direkten
Kompositionsausgaben bleiben wegen zusätzlicher Striche unvollständig im
annotierten Vertrag; die sichtbare Wirkung dieser Striche ist damit noch
nicht vollständig fachlich klassifiziert.

Die jüngsten echten Katalogstichproben vom 11.11.2026 hatten 13/38 bzw. 11/32
reine Pixelpässe und 10/38 bzw. 3/32 Modellbestätigungen. Wegen kleiner,
verschiedener Zufallsauswahlen sind das keine belastbaren heutigen
Gesamtquoten. Eine frische autonome Gesamtkonvertierung nach den
Fallbackänderungen fehlt. Die Web-Neumessung bewertet vorhandene SVGs und
ersetzt diesen Konvertierungsbenchmark nicht.

## Entfernung zum Ziel

„Grossteil“ ist noch nicht als feste Mindestquote definiert. Als Größenordnung
ergeben sich bei 1.787 Bildern folgende Ziele:

| Zielquote | Benötigte erfolgreiche Bilder | Zusätzlich zum historischen Archiv von 379 |
| --- | ---: | ---: |
| Mehr als die Hälfte | 894 | 515 |
| Mindestens 70 % | 1.251 | 872 |
| Mindestens 80 % | 1.430 | 1.051 |

Diese Differenzen verwenden den historischen, weniger strengen Maßstab.
Bei voller neuer Raster-/Objekt-/Semantikabnahme kann der Abstand größer sein.
Neue Familien, Farb-/Größenvarianten und bereits vorhandene gute Entwürfe
bieten unterschiedliche Hebel; eine gleichbleibende Erfolgszahl pro Paket
ist bisher nicht belegt. Eine seriöse Restdauer oder Zahl verbleibender Pakete
lässt sich daraus noch nicht ableiten.

## Die nächsten wirksamen Schritte

1. **FALLBACK-GROUPS-CLEANUP-06:** Zusätzliche Striche des tatsächlichen
   Fallbacks erklären beziehungsweise vermeiden und vollständige logische
   Inventare unter unveränderten Bild-/Relationsgates erreichen.
2. **Allgemeine Form- und Abnahmeabdeckung:** Kurven, weitere Symbolkompositionen,
   passende Beschreibungen sowie fachliche Prüfung bisheriger guter Entwürfe.
   Keine Freigabe allein aufgrund eines globalen Pixelwerts.
3. **Unabhängige reale Prüfung:** dokumentierte Annotationen samt Unsicherheit,
   menschlicher Audit und geeignete Prüfer vor jedem reservierten Versuch.
   HC0010, Rail, AC5041 und AC5050 bleiben gesperrt.
4. **Breite Wirkung messen:** mindestens 20 vorab abgegrenzte reale Familien
   und anschließend ein vollständiger, wiederaufnehmbarer Kataloglauf mit
   Bildqualität, Fehlversuchen und bestätigten Erfolgen im Nenner.

Das Projekt besitzt inzwischen eine deutlich bessere Such- und Prüfinfrastruktur.
Der verbleibende Hauptaufwand liegt in der breiten Rekonstruktionsqualität
und ihrem realen Nachweis; mehr Suchzeit allein löst die fehlenden Formen nicht.
