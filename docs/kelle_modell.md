# Kelle-Modell (Kreis + Griff)

Dieses Dokument beschreibt das neu ergänzte, streng typisierte Kellen-Modell im Projekt.
Die atomaren Werte bleiben Zahlen und Zeichenketten; die Python-API setzt das mit
Datentypen und Constraints um.

## Kerntypen

- `RGBWert(r, g, b)` mit `0 <= Kanal < 256`.
- `Punkt(x, y)`.
- `Abstand(punkt1, punkt2)` als euklidische Distanz.
- `Kreis(mittelpunkt, radius, randbreite, rand_farbe, hintergrundfarbe)` mit Constraint `randbreite <= radius`.
- `Griff(anfang, ende)` mit abgeleiteter `laenge`.
- `Kelle(griff, kreis)` mit Constraints:
  - `griff.anfang == kreis.mittelpunkt`
  - `griff.laenge > kreis.radius`

## Rendering-Regeln

- Zeichnungsreihenfolge: **erst Griff, dann Kreis** (`draw(Griff) < draw(Kelle)`).
- Objekte dürfen rechnerisch über den Rand hinausgehen.
- Finale Ausgabe wird auf die Zeichenfläche geclippt.

## Orientierungen

`build_oriented_kelle(...)` unterstützt:
- `left` / `links`
- `top` / `up` / `oben`
- `right` / `rechts`
- `bottom` / `down` / `unten`

Damit lassen sich Kellen mit Griff nach links, oben, rechts und unten direkt erzeugen und als SVG rendern.
