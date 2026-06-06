# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-06, nach AC0864-S-Run)

Die dokumentierte AC08-Weak-Family-Rotation ist vollständig abgearbeitet. Aktuell
gibt es keinen aktiv freigegebenen Plan-B-Kandidaten. Vor einer neuen Rotation
muss die Qualitätsauswertung erneut erzeugt und daraus ein noch nicht erledigter,
visuell einfacher bis mittlerer Kandidat ausgewählt werden.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktive PF8-Linkage-Report ist nach Abschluss von `AC0864_S.jpg` leer. Der
Lerneffekt dieses letzten Kandidaten ist abgeschlossen: Kreis und Linie wurden
`generalisiert` erkannt, und die semantische Ausgabe nutzt die allgemeine
AC08-Geometrie für ein horizontal gespiegeltes `rF`-Badge.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
