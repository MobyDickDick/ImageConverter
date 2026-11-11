# Nächstes P0-Paket: unabhängige Rasterabnahme dünner Rechteckseiten

**SVG-CLIPPED-SIDE-RENDERER-01**, Status **Planned**.
Folge des [angeschnittenen Rechteckpakets](next_arbeitspaket_2026-11-07_clipped_rectangular_parent.md).

## Gesicherter Befund

Die unabhängige Zusatzkohorte `391827` enthält den scharfen Fall
`clipped_rectangle_10`. Sein unverändertes Referenz-SVG besteht die native
Objekt-/Geometrieprüfung und die globale MuPDF-Rasterprüfung. Mit librsvg
bestehen alle sichtbaren Seiten; MuPDF verfehlt zwei Seiten mit
Kantenübereinstimmung ungefähr `0,6924` und `0,4769` bei Mindestwert `0,72`.
Die Abweichung tritt bereits beim exakten Referenz-SVG auf und ist damit
von der rekonstruierten Geometrie zu trennen. Die neue Suche erhält für
diesen Fall keinen stillen Erfolg. Das ist keine reale Familienabnahme.

Der zweite Zusatzfall `clipped_rectangle_02` bleibt ebenfalls nach fünf
Sekunden ohne geprüften Zwischenstand. Seine exakten Referenzkontrollen
bestehen mit beiden Renderern einschließlich Seiten und Ecken. Hier liegt
eine getrennte Registrierungsgrenze vor; sie darf nicht dem Rendererfehler
zugerechnet oder aus dem Zusatznenner entfernt werden. Beide unveränderten
Fälle gehören zur Abnahme des Folgepakets.

## Lieferumfang

1. Originalraster, Referenz-SVG, Beschreibungs-/Objekt-/Relationsmarkierungen,
   Renderer- und Runtimeversionen sowie die vorhandenen Prüfsummen sichern.
   Weitere unabhängige Seitenkontrollen für Subpixellagen, dünne Konturen,
   ähnliche Kontur-/Füllfarben und Verlaufsachsen vor Änderungen einfrieren.
2. Seitenprofile und tatsächliche Canny-Kanten beider Renderer vergleichen.
   Antialiasing, Farbquantisierung, Konturgeometrie und lokale Hysterese
   voneinander unterscheiden. Kein Rückschluss auf Generatorgeometrie im
   Konverter; keine bildnamenabhängige Korrektur.
3. Den allgemeinen Raster-/Registrierungspfad am beobachteten Fehler
   korrigieren. Kanten-, Pixel-, native Objekt-/Relations- und anfängliche
   Fehlergrenzen nicht lockern. Einen Referenzrenderfehler nicht durch
   dauerhaft falsche native Geometrie kompensieren.
   Den separat belegten Registrierungsfehler von `clipped_rectangle_02`
   unter demselben Bildbudget beheben; Hypothesen und lokale Ablehnungsgründe
   getrennt protokollieren.
4. Identische gesicherte Haupt-, Zusatz- und Variantenraster durch die echte
   CLI prüfen. Alle sichtbaren Seiten und Ecken, jedes Objekt und das
   Restbild mit beiden Renderern abnehmen; Ablehnungen im Nenner belassen.
   Fünf Sekunden und 96 Strukturzustände erhalten.
5. Vollständig sichtbare scharfe/gerundete Eltern, angeschnittene Kreise,
   Konturfarben, Tiefenbelege und die negativen Beobachtbarkeitskontrollen
   regressionsprüfen. HC0010 und Rail bleiben `sealed_unrun`.

## Start

```powershell
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --prepare .tmp/clipped-side-controls --seed 391827
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-side-controls --output .tmp/clipped-side-cli
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-side-controls --output .tmp/clipped-side-cli --audit .tmp/clipped-side-audit.json
```

Der [Nachweis des Vorgängerpakets](../artifacts/evaluation/clipped_rectangular_parent_v1/README.md)
enthält den exakten Kontrollvergleich und die vollständigen Fehlversuche.
