# Schwach, aber noch machbar konvertierbare Formfamilien (2026-05-31)

## Ziel

Diese Notiz dokumentiert die Einschätzung, welche Formfamilien aktuell schlechter
konvertieren, aber noch als realistische Plan-B-/Nachzeichnungsaufgaben gelten.
Sie dient als Vorprüfung, bevor neue manuelle Referenzbilder nachgezeichnet und
anschliessend als Plan-B-Aufgaben abgearbeitet werden.

Nicht gemeint sind hoffnungslos komplexe oder vollständig fehlgeschlagene Fälle.
Gesucht sind Familien, bei denen die Semantik bereits teilweise stimmt, der
Pixel-/Delta-Fehler aber noch deutlich auffällig ist.

## Prüfkriterien

Eine Familie wird hier als **schlecht, aber machbar** eingestuft, wenn mehrere
der folgenden Punkte erfüllt sind:

1. **Vorhandene Artefakte/Snapshots:** Es gibt bereits `conversion_bestlist`-
   Snapshots mit `variant`, `mean_delta2`, `error_per_pixel` und semantischen
   Parametern.
2. **Erhöhte Fehlerwerte:** `mean_delta2` ist im Vergleich zu einfachen
   Kontrollfamilien hoch oder `error_per_pixel` liegt nahe/über dem aktuellen
   Qualitätsgrenzwert `allowed_error_per_pixel = 0.045945679012345676`.
3. **Semantik vorhanden:** Die Snapshot-Parameter enthalten erkennbare Elemente
   wie Kreis, Text, Griff/Linie oder Richtung; die Konversion ist also nicht
   einfach leer oder semantisch unbrauchbar.
4. **Parametrisierbare Geometrie:** Die Familie lässt sich mit wenigen Plan-B-
   Parametern beschreiben, z. B. Kreisradius, Randbreite, Textposition,
   Schriftgrösse, Grifflänge, Griffbreite und Dreh-/Orientierungsregel.
5. **Plan-B-kompatibel:** Die Verbesserung passt zu den Plan-B-Grundsätzen:
   Parameter werden aus Bildsignal und Beschreibung iterativ bestimmt und der
   beste Kandidat wird über den Pixel-Fehler ausgewählt.

## Evidenz aus den aktuellen Snapshots

Die folgende Tabelle fasst die wichtigsten Familien zusammen. Die Werte wurden
aus `src/artifacts/converted_images/reports/conversion_bestlist_snapshots/*.json`
aggregiert.

| Priorität | Familie | Varianten im Snapshot | Ø `mean_delta2` | Max. `mean_delta2` | Ø `error_per_pixel` | Max. `error_per_pixel` | Einschätzung |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| A | `AC0835` | `AC0835_S/M/L` | 8638.33 | 11170.07 | 0.1004 | 0.1701 | Rundes `VOC`-Badge ohne Griff; geometrisch einfach, aber Text/Grauwerte sind aktuell schwach. |
| A | `AC0820` | `AC0820_S/M/L` | 8244.80 | 9983.60 | 0.0924 | 0.1727 | Rundes `CO₂`-Badge; Superscript/kleine Glyphen machen die Konversion schlecht, aber beschreibbar. |
| A | `AC0870` | `AC0870_S/M/L` | 6601.34 | 6839.05 | 0.0863 | 0.1513 | Rundes `T`-Badge; einfache Grundform, aber Textgrösse/-zentrierung und Antialiasing sind kritisch. |
| B | `AC0838` | `AC0838_S/M/L` | 7969.79 | 9225.63 | 0.0471 | 0.0768 | `VOC`-Badge mit waagrechtem Griff; Text bleibt horizontal, Form-/Textrotation sind entkoppelt. |
| B | `AC0837` | `AC0837_S/M` | 6236.22 | 7265.97 | 0.0521 | 0.0765 | `VOC`-Badge mit Griff links; Richtung wird erkannt, exakte Lage/Überdeckung bleiben schwach. |
| B | `AC0839` | `AC0839_S/M/L` | 5118.40 | 5968.19 | 0.0336 | 0.0499 | `VOC`-Badge mit Griff rechts; meist knapp machbar, aber einzelne Varianten überschreiten die Grenze. |
| B | `AC0836` | `AC0836_S/M/L` | 4757.94 | 5446.60 | 0.0337 | 0.0497 | `VOC`-Badge mit senkrechtem Griff; gute Plan-B-Familie für Kreis+Griff+Text. |
| B | `AC0882` | `AC0882_S/M/L` | 4145.59 | 6716.56 | 0.0302 | 0.0438 | `T`-Badge mit Griff/Drehung; unter Grenzwert, aber hoher Delta-Fehler bei mindestens einer Variante. |
| C | `AC0831` | `AC0831_S/M/L` | 4653.89 | 5450.81 | 0.0345 | 0.0525 | Kelle mit Buchstabe/`T` und Griff unten; semantisch verstanden, geometrisch noch ungenau. |
| C | `AC0832` | `AC0832_S/M/L` | 4587.04 | 5184.14 | 0.0333 | 0.0572 | Gedrehte Buchstaben-Kelle mit Griff links; gute mittlere Plan-B-Aufgabe. |
| C | `AC0833` | `AC0833_S/M/L` | 4396.71 | 4657.08 | 0.0315 | 0.0527 | Verwandte Buchstaben-Kellenfamilie; ähnlich wie `AC0831`/`AC0832`. |
| C | `AC0834` | `AC0834_S/M/L` | 4332.44 | 5650.15 | 0.0311 | 0.0483 | Gedrehte Buchstaben-Kelle mit Griff rechts; knapp oberhalb der Grenze bei einzelnen Varianten. |
| Kontrolle | `AC0811` | `AC0811_S/M/L` | 1021.41 | 1455.94 | 0.0140 | 0.0248 | Einfache Kelle ohne Text; deutlich besser und deshalb keine erste Nachzeichnungspriorität. |

## Empfohlene Nachzeichnungsreihenfolge

### Priorität A: runde Badges mit Text/Glyphen

Zuerst nachzeichnen:

1. `AC0835_S`, `AC0835_M`, `AC0835_L`
2. `AC0820_S`, `AC0820_M`, `AC0820_L`
3. `AC0870_S`, `AC0870_M`, `AC0870_L`

Begründung: Diese Familien sind visuell relativ einfach und stark
parametrisierbar. Der Fehler entsteht sehr wahrscheinlich aus Text/Glyphen,
Graustufen, Randbreite, Zentrierung und Antialiasing. Ein sauberes Nachzeichnen
liefert daher einen hohen Lerneffekt für Text- und Label-Badges.

### Priorität B: Kreis + Griff + horizontal bleibender Text

Danach nachzeichnen:

1. `AC0836_S`, `AC0836_M`, `AC0836_L`
2. `AC0837_S`, `AC0837_M`
3. `AC0838_S`, `AC0838_M`, `AC0838_L`
4. `AC0839_S`, `AC0839_M`, `AC0839_L`
5. `AC0882_S`, `AC0882_M`, `AC0882_L`

Begründung: Diese Familien testen eine wichtige Plan-B-Fähigkeit: Der Griff ist
rotiert oder seitlich, der Text soll aber horizontal lesbar bleiben. Dadurch
müssen Kreis-/Griffgeometrie und Textorientierung getrennt modelliert werden.

### Priorität C: Buchstaben-/`T`-Kellen

Anschliessend nachzeichnen:

1. `AC0831_S`, `AC0831_M`, `AC0831_L`
2. `AC0832_S`, `AC0832_M`, `AC0832_L`
3. `AC0833_S`, `AC0833_M`, `AC0833_L`
4. `AC0834_S`, `AC0834_M`, `AC0834_L`

Begründung: Diese Familien sind gute Folgeaufgaben, wenn die Badge- und
Grifflogik stabiler ist. Sie sind weniger dringend als Priorität A, aber immer
noch deutlich schwächer als einfache Kontrollfamilien.

## Was vorerst nicht priorisiert werden sollte

`AC0811` dient hier als Kontrollfamilie für einfache Kellen ohne Text. Die
Fehlerwerte sind deutlich niedriger als bei den Text-/VOC-/CO₂-Familien. Diese
Familie kann später weiter verbessert werden, ist aber keine gute erste Wahl,
wenn gezielt schwache und dennoch machbare Plan-B-Kandidaten gesucht werden.

## Allgemeine primitive Risikoklassen

Die Primitive-Inventar-Metriken stützen die Priorisierung:

- `text` hat nur `recall = 0.5`; kleine Labels und kurze Glyphen bleiben daher
  ein zentrales Risiko.
- `rect` hat `precision = 0.0` und `recall = 0.0`; Rechteck-/Box-Elemente sollten
  bei passenden Kandidaten separat geprüft werden.
- `ellipse` hat `precision = 0.5`; ovale oder elliptisch erkannte Kreisformen
  können Fehlpositive erzeugen.

Für die aktuelle Nachzeichnungsfrage sind deshalb vor allem Text-/Glyph-Badges
und Badge+Griff-Kombinationen relevant.

## Konkreter Vorprüfablauf für künftige Kandidaten

Vor dem Nachzeichnen einer neuen Familie sollte jeweils folgender kurzer Check
laufen:

1. Snapshot-Dateien für die Familie suchen.
2. `mean_delta2`, `std_delta2` und `error_per_pixel` pro Variante aggregieren.
3. Gegen den aktuellen `allowed_error_per_pixel` vergleichen.
4. Prüfen, ob `params.elements` sinnvolle Semantik enthält.
5. Prüfen, ob die Geometrie mit wenigen Plan-B-Parametern modellierbar ist.
6. Familie nur dann in die Nachzeichnungsrotation aufnehmen, wenn sie weder
   bereits gut genug noch vollständig semantisch verloren ist.

Das vorhandene Hilfsskript `src/weak_family_pipeline.py` kann dafür als Basis
dienen, weil es Ranking-Zeilen lädt, nach `mean_delta2` sortiert, Top-Varianten
nach Präfix auswählt und Vorher/Nachher-Vergleiche schreiben kann.
