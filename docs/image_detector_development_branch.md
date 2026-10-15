# ImageDetector als möglicher Entwicklungszweig (2026-10-14)

## Status und Ziel

Der ImageDetector ist eine mittel- bis langfristige Entwicklungsoption für den
ImageConverter. Diese Notiz hält den Vorschlag fest; sie ist keine Zusage einer
vollständigen Implementierung oder eines Liefertermins. Die Reihenfolge der
[Produkt-Roadmap](product_roadmap.md) bleibt bestehen.

Eine vorgeschaltete Bildanalyse soll geometrische Grundelemente erkennen, ihre
Masse schätzen und dem Konverter strukturierte Ausgangsdaten liefern. Ziel sind
zunächst technische Symbole, Icons und flächige Grafiken. Der erwartete Nutzen
ist ein besserer Startpunkt für die Rekonstruktion und eine breitere Abdeckung
neuer Kombinationen bekannter Grundformen. Eine Qualitätssteigerung muss im
Vergleich mit dem bisherigen Konverter nachgewiesen werden.

## Vorhandene Grundlagen

Der Zweig soll den bestehenden Perception-First-Ansatz weiterführen:

- [Shape-Detection](../tools/shape_detection.py) enthält Bausteine für Kreise und
  Ringe, senkrechte und waagrechte Linien, Farbmerkmale sowie einfache
  Konturklassifikationen. Das sind begrenzte Erkennungsverfahren, keine
  nachgewiesene allgemeine Szenenzerlegung.
- Der [Detection-Contract](../tools/perception_detection_contract.py) beschreibt
  Kandidaten mit Position, Geometrie, Farbe, Konfidenz und Evidenz und enthält
  Hilfen zur Übergabe an die Geometry-IR, die gemeinsame Geometriedarstellung.
- Das [Perception-First-Backlog](perception_first_task_backlog_2026-05-30.md)
  dokumentiert erste Integrationen, Auswertungen und begrenzte Glyphenerkennung.
  Seine historischen Abnahmen belegen nicht den gesamten hier vorgeschlagenen
  Umfang.
- Die [Zielarchitektur Bild + Beschreibung](image_description_only_architecture.md)
  sieht bereits Wahrnehmung, Abgleich mit der Beschreibung und anschließende
  Rekonstruktion vor.

## Vorgesehener Datenfluss

1. Das Rasterbild auf Konturen, Flächen und mögliche Grundelemente untersuchen.
2. Kandidaten mit gemessener Geometrie, Stilmerkmalen und Unsicherheit erzeugen.
3. Kandidaten mit der vorhandenen Bildbeschreibung abgleichen und Beziehungen
   wie Anschluss, Ausrichtung, Einschluss und Überdeckung ableiten.
4. Die ausgewählten Kandidaten in die Geometry-IR des Konverters überführen.
5. Ein SVG rendern, gegen das Eingabebild prüfen und seine Parameter verfeinern.

Der Detector ergänzt die Beschreibung. Erkennungsergebnisse bleiben aus den
Eingaben abgeleitete Daten; gespeicherte Referenz-SVGs, Bild-IDs oder manuell
hinterlegte Koordinaten einzelner Katalogbilder dürfen keine Laufzeitquelle
werden. Bei mehreren plausiblen Deutungen sollen Alternativen und ihre Evidenz
erhalten bleiben. Unzureichende Evidenz führt zu einer Diagnose.

## Umfang und Ausbaustufen

| Stufe | Umfang | Erwartetes Ergebnis |
|---|---|---|
| 1: Grundformen und Masse | Kreise/Ringe, Linien verschiedener Orientierung, Rechtecke und einfache Vielecke | Mittelpunkt, Radius, Endpunkte, Eckpunkte, Winkel, Abstände, Strichbreite und Farben mit Unsicherheitsangaben |
| 2: Zusammengesetzte Szenen | Berührungen, Anschlüsse, Überdeckungen, Ebenen und Symmetrien | Zusammengehörige Elemente und plausible Beziehungen, auch bei teilweise fehlenden Konturen |
| 3: Freie Kurven | Quadratische und kubische Béziersegmente aus Rasterkonturen | Kompakte Kurven mit dokumentiertem Anpassungsfehler |
| 4: Text | Textbereiche, einzelne Zeichen und kurze Beschriftungen | Textinhalt und Position bei ausreichender Evidenz; alternativ rekonstruierte Glyphenkonturen |

Stufe 1 ist der erste begrenzte Prototyp. Die späteren Stufen sind getrennte
Ausbauentscheidungen. Exakte Schriftarterkennung ist eine zusätzliche Option;
optisch passende Buchstabenkonturen können bereits nützlich sein, bleiben aber
Pfade ohne editierbaren Textinhalt.

Die weiteren Details können an die bestehenden Konzepte für
[Bézierkurven](v2_bezier_detection_strategy_2026-05-14.md),
[Überdeckungen und Ebenen](v4_occlusion_zorder_model_2026-05-14.md) sowie
[Objekte, Beziehungen und Bedingungen](v5_semantic_text_representation_2026-05-14.md)
anknüpfen. Diese Konzeptdokumente sind kein Nachweis einer vollständigen
Implementierung.

## Messwerte und Grenzen

Masse entstehen zunächst in Pixeln sowie relativ zur Bildbreite und -höhe.
Millimeter oder Zentimeter benötigen einen bekannten Massstab. Die Genauigkeit
ist durch Auflösung, Kantenglättung und Kompressionsartefakte begrenzt;
Subpixelwerte sind Schätzungen.

Ein durch eine Linie unterbrochener Kreis muss als mögliche Kombination aus
Kreis und Linie erkannt werden. Gleichfarbige, sich berührende Flächen und
verdeckte Konturen machen die Zerlegung mehrdeutig. Bei Bézierkurven lässt sich
eine passende Kurve schätzen, die ursprüngliche Anzahl von Segmenten oder ihre
Kontrollpunkte sind aus dem Raster jedoch nicht eindeutig bestimmbar. Kleine
Textzeichen können geometrischen Formen gleichen; die genaue Schriftart kann
unbestimmbar bleiben. Der vorhandene
[Grenzfallkatalog](v8_non_invertibility_edge_case_catalog_2026-05-14.md) beschreibt
solche Mehrdeutigkeiten ausführlicher.

Eine kompakte, semantisch vollständige Vektorisierung beliebiger Fotografien
gehört nicht zum ersten Zielumfang.

## Erster Prototyp und Qualitätsnachweis

Ein erstes Arbeitspaket soll die vorhandenen Detektoren inventarisieren, Lücken
für Stufe 1 festhalten und ein gemeinsames Kandidatenformat verwenden. Als
prüfbare Ausgabe sind ein maschinenlesbarer Report und ein Kontrollbild mit
eingezeichneten Elementen und Massen vorgesehen. Anschließend werden die
Kandidaten über die bestehende Geometry-IR an den Konverter angebunden.

Die Bewertung soll Erkennung und Konvertierungsnutzen getrennt messen:

- Auf unabhängigen, während der Entwicklung zurückgehaltenen Bildern:
  Precision/Recall je Grundform sowie Fehler von Position, Radius, Winkel und
  Strichbreite anhand bekannter oder unabhängig annotierter Geometrie.
- Für denselben Testsatz: Konvertierung mit und ohne Detector bei gleicher
  Beschreibung, gleichem Optimierungsbudget und unveränderten Qualitätsgrenzen.
  Pixel-, Kanten- und Strukturfehler, SVG-Komplexität und Laufzeit vergleichen.
- Farb-, Größen-, Rotations- und Kompressionsvarianten sowie neue Kombinationen
  bekannter Formen prüfen; Dateiumbenennungen dürfen das Ergebnis nicht ändern.
- Fehlalarme, abgelehnte Kandidaten, alternative Deutungen und den tatsächlich
  verwendeten Ausgangspunkt protokollieren. Konfidenzwerte sind zunächst
  Bewertungsscores; ihre Verlässlichkeit muss separat geprüft werden.
- Bestehende erfolgreiche Konvertierungen gegen Verschlechterungen absichern.

Die erste Stufe gilt erst dann als nützlich belegt, wenn sie auf diesen
unabhängigen Fällen nachvollziehbare Geometriemessungen liefert und die
Konvertierung messbar verbessert, ohne die bestehenden Abnahmen zu schwächen.
Einzelne gelungene Kontrollbilder reichen dafür nicht aus. Numerische
Abnahmeschwellen sind vor der Umsetzung des jeweiligen Arbeitspakets festzulegen.
