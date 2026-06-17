# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-17, Review-Refresh Run PII)

`AC0845_S` wurde als anschlussfreies Kreis-/Text-Badge aus der Beschreibung
rekonstruiert. Kreisgrundkörper und zentrierter `rH`-Glyph bleiben getrennte,
größenrelative Geometry-IR-Elemente; die allgemeine Rasterregistrierung passt
die gemeinsame Geometrie an die kleine Rastervariante an.

Der reproduzierbare Review findet auch nach der erneuten Inventur mit `132`
Diff-Varianten, `123` renderbaren Diff-Paaren und `48` renderbaren erfolgreichen
Konvertierungen **keinen** qualifizierten Diff-Fall oberhalb der Review-Grenze. Die reguläre Rotation ist daher leer und wird erst
bei einem neu qualifizierten Kandidaten fortgesetzt.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Der abgeschlossene Kandidat bestätigte den allgemeinen `CircleBackground`-Seed.
Die `rH`-Glyph wird derzeit zuverlässig aus der expliziten Bildbeschreibung als
`TextGlyph` ergänzt; ein bild- oder variantenspezifisches Sample-SVG ist nicht
erforderlich. Der maschinenlesbare PF8-Linkage-Report ist nach Abschluss der
Rotation leer. Der Review-Refresh vom 2026-06-17 bestätigt außerdem `0`
ausgewählte Plan-B-Kandidaten; die Kandidatenrotation bleibt deshalb bewusst
leer, bis neue qualifizierte Diff-Fälle entstehen.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
