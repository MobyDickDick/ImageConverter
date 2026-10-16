# Formenfamilien gemeinsam bearbeiten

Mehrere verwandte Vorlagen können in einer Aufgabe gemeinsam bearbeitet und
als Batch konvertiert werden. Gleiche Farben oder gleiche Bildgrößen sind
dafür nicht erforderlich. Entscheidend sind die gemeinsame Formstruktur und
ein ähnlicher Aufbau der Farbverläufe, etwa eine helle Mitte mit dunkleren
Rändern. Eine Verbesserung des gemeinsamen Algorithmus soll möglichst alle
passenden Varianten erschließen.

## Was der Converter bereits unterstützt

Der Converter nimmt einen Eingabeordner mit mehreren Rasterbildern entgegen.
Für unterstützte Formstrukturen bestimmt er Geometrie, Maße, Farben und
Verlaufsprofile aus dem jeweiligen Rasterbild und seiner eigenständigen
Beschreibung. Die Parameter werden für jedes Bild einzeln ermittelt und
geprüft. Ein gemeinsamer Batch bedeutet keine zwingend parallele Berechnung.

Im voreingestellten Modus `semantic-only` verwendet eine Konvertierung
ausschließlich das betreffende Rasterbild und seine Beschreibung. Sie lernt
während des Batches nicht aus anderen Bildern und übernimmt keine bereits
erzeugte SVG als Vorlage. Nur der ausdrücklich gewählte Kompatibilitätsmodus
`standard` erlaubt die dokumentierte Wiederverwendung vorhandener Ergebnisse
und Template-Transfers; diese sind keine Voraussetzung für Familienaufgaben.

Die Batchfähigkeit ist vorhanden, die Motivabdeckung bleibt begrenzt. Eine
neue Formstruktur kann weiterhin Entwicklungsarbeit erfordern. Eine beliebige
Sammlung ähnlicher Bilder wird noch nicht automatisch als neue Familie erkannt
und unterstützt. Ähnliche Farben allein belegen keine gemeinsame Formstruktur.

## Vorgehen für eine Familienaufgabe

1. Zu Beginn die verwandten Vorlagen zusammenstellen und ihren gemeinsamen
   Aufbau festhalten. Unterschiede in Farbe, Auflösung, Proportionen und
   Verlaufsrichtung ausdrücklich aufnehmen. Weitere verwandte Motive können
   dazugehören, wenn der gemeinsame Algorithmus sie tatsächlich abdeckt.
2. Für jedes Bild eine eigenständige, zutreffende Beschreibung sicherstellen.
   Maße und Farben aus dem jeweiligen Bild bestimmen; keine festen
   Katalogkoordinaten, Bildkennungen oder Referenz-SVGs in die Runtime einbauen.
3. Den Ausgangszustand der ausgewählten Varianten mit frischen CLI-Läufen
   messen. Die gemeinsame Verarbeitung anhand repräsentativer Fälle
   verbessern und weitere Farb-, Größen- und Geometrievarianten zurückhalten,
   um die Übertragbarkeit unabhängig zu prüfen.
4. Alle ausgewählten Varianten einzeln durch die unveränderten Qualitätsgates
   prüfen. Unabhängige Variationen und den Bestandsschutz gemäß dem regulären
   Abnahmeverfahren ergänzen. Ein gutes Ergebnis für eine Vorlage ersetzt
   keine Abnahme der übrigen Familienmitglieder.
5. Bestandene, fehlgeschlagene und noch ungeprüfte Varianten im Familienbericht
   getrennt ausweisen. Erfolgreiche Original-/SVG-Paare samt Beschreibungen und
   Messwerten in die Erfolgsübersicht übernehmen; offene Fälle sichtbar halten.

Eine zusammengehörige Familienaufgabe kann auf einem Branch umgesetzt werden.
Für jede Farb- oder Größenvariante ist kein eigener Branch erforderlich.
Falls unabhängige Aufgaben gleichzeitig auf verschiedenen Branches bearbeitet
werden, benötigen sie getrennte Arbeitsverzeichnisse, beispielsweise Git
Worktrees. Ein Branchwechsel im selben Arbeitsverzeichnis tauscht dessen
Dateistand aus und eignet sich deshalb nicht für gleichzeitig laufende Arbeiten.

## Nachgewiesenes Beispiel

Die [seitliche T-Verzweigung GE9034](next_arbeitspaket_2026-10-16_ge9034_6m.md)
wurde als Familie mit 14 Farb-/Größenvarianten abgenommen. Die gemeinsame
Verarbeitung bestimmt Arme, Verlaufsprofile und Übergänge aus jedem Raster
neu. Alle 14 Varianten bestehen laut dokumentierter Abnahme die regulären
Gates und die strengeren Plan-B-Pixelgrenzen. Eine unabhängig konstruierte
grüne Vorlage mit veränderter Zeichenfläche, Lage, Proportionen und Palette
ergänzt den Nachweis.

Die ausführbaren Batchbefehle stehen in der [CLI-Referenz](image_converter_cli.md),
die allgemeinen Abschlussprüfungen im [Workflow](image_converter_workflow.md).
