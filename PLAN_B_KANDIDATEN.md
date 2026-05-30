# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-30, nach Qualitätsreview bisheriger Konvertierungen)

1. `AC0224_S.jpg` – AC0221-verwandter Kellenkandidat ohne `M`, 90° nach rechts gedreht und mit vorhandenem Diff-Artefakt.
2. `AC0231_S.jpg` – AC0221-verwandtes 3-Wege-Ventil mit oberer `M`-Kelle und vorhandenem Diff-Artefakt.
3. `AC0838_M.jpg` – Qualitätsreview-Befund: vorhandenes SVG-Paar rendert, überschreitet aber die Review-Grenze (`normalized_mse=0.04729276`).
4. `AC0881_M.jpg` – Qualitätsreview-Befund: Originalbild vorhanden, aber kein passendes SVG-Artefakt in den geprüften Konvertierungs-/Baseline-Pfaden.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
