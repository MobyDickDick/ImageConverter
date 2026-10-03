# PNG + Bildbeschreibung → zufriedenstellendes SVG: Implementierungsplan

## Kurzantwort

Ja. Das Problem ist als **beschränkte inverse Grafik** lösbar: Die Beschreibung
liefert erlaubte Objekte und Beziehungen, das PNG liefert deren messbare
Geometrie, Farbe und Konturen. Anschließend wird ausschließlich ein
parametrisches SVG gerendert und gegen das PNG optimiert. Weder ein früheres
SVG noch eine Bild-ID darf als Eingabe dienen.

Ein reiner Beschreibung→SVG-Render reicht nicht. Ebenso reicht eine blinde
Pixelvektorisierung nicht, weil sie zwar Konturen kopieren, aber Text,
Überdeckung und Objektbeziehungen semantisch falsch rekonstruieren kann.

## Verbindliche Pipeline

### 1. Zwei Eingaben normalisieren

- PNG dekodieren, Alpha auf einen festgelegten Hintergrund komponieren und
  Canvasbreite/-höhe unverändert übernehmen.
- Beschreibung in einen Constraint-Graphen übersetzen: Primitive, Anzahl,
  Farbe, relative Lage, Verbindungen, Text und Z-Reihenfolge.
- Unbekannte oder widersprüchliche Angaben als Unsicherheit erhalten; nicht
  durch katalogspezifische Defaults ersetzen.

### 2. Primitive aus beiden Quellen fusionieren

- Aus dem PNG allgemeine Kandidaten für Linien, Kreise/Ringe, Rechtecke,
  Polygonpfade, Farbflächen und Textregionen ermitteln.
- Beschreibungsknoten und Bildkandidaten per gewichteter Zuordnung verbinden.
  Harte Bedingungen sind beispielsweise Primitive-Anzahl, Textinhalt und
  Anschlussrichtung; weiche Evidenz sind Pixelposition, Farbe und Confidence.
- Mehrere plausible Zuordnungen als Beam von Geometry-IR-Hypothesen behalten,
  statt den ersten Treffer festzuschreiben.

### 3. SVG parametrisch rekonstruieren

- Nur echte SVG-Primitive (`path`, `rect`, `circle`/`ellipse`, `line`, `text`,
  Gradients) erzeugen; kein eingebettetes PNG.
- Alle Koordinaten auf den Canvas normieren. Stilparameter, Geometrie und
  Z-Reihenfolge bleiben getrennt optimierbar.
- Für Schrift zunächst verfügbare Fonts vermessen; wenn metrische
  Reproduzierbarkeit nicht erreichbar ist, die erkannte Glyphe in einen
  generalisierten Pfad umwandeln und diese Entscheidung reporten.

### 4. Differenz getrieben optimieren

Jede Hypothese wird zu Raster gerendert. Die Zielfunktion darf nicht nur aus
globalem MSE bestehen, sondern kombiniert:

`L = 0.35·L_pixel + 0.25·L_edge + 0.20·L_structure + 0.20·L_semantic`

- `L_pixel`: linearisierter Farbfehler, ergänzt um DeltaE;
- `L_edge`: Distanz der gerenderten und beobachteten Konturen;
- `L_structure`: maskenbasierte IoU je Objekt und Anschlusskontinuität;
- `L_semantic`: fehlende/falsche Primitive, Relationen, Text und Z-Reihenfolge.

Zuerst werden diskrete Entscheidungen (Primitive-Typ, Zuordnung, Z-Order),
danach kontinuierliche Parameter (Position, Größe, Stroke, Farbe,
Gradientenstopps) optimiert. Grob-zu-feine Suche, Trust-Region und Pareto-Filter
verhindern, dass ein kleiner Pixelgewinn eine semantisch falsche Lösung
verdrängt.

### 5. „Zufriedenstellend“ hart entscheiden

Ein Ergebnis ist nur dann `good`, wenn **alle** Bedingungen erfüllt sind:

- Dimension und Seitenverhältnis stimmen mindestens zu `0.99` überein;
- Semantikscore ist mindestens `0.85`;
- `error_per_pixel` ist höchstens `0.05`;
- es gibt kein eingebettetes Raster und keinen unerlaubten Wissenskanal;
- ein erneuter Render des gespeicherten SVGs reproduziert die Messwerte.

Andernfalls lautet der Status `suboptimal` oder mit kanonischem Grund
`not_reachable`. Ein grüner Prozess-Exit ist ausdrücklich kein Qualitäts-Pass.

## Anschluss an den vorhandenen Code

Der Bestand enthält bereits wichtige Bausteine: PNG wird als Eingabeformat
akzeptiert, Perception-Seeds können mit Description-Geometry-IR konkurrieren,
der Geometry-IR-Optimizer variiert Registrierung und Stroke, und das
Good-Solution-Gate besitzt die drei Kernschwellen. Die entscheidende Lücke ist
ein End-to-End-Runner, der diese Teile pro Benchmarkfall zwingend verbindet
und die Metriken des **gespeicherten End-SVGs** ausgibt.

## Nächstes ausführbares Paket

1. Den ZG7-Runner auf den echten `semantic-only`-Konverterpfad umstellen.
2. Pro Fall Quell-PNG, Beschreibung, End-SVG und Re-Render erfassen.
3. Pixel-, Edge-, Struktur-, Semantik- und Dimensionsmetriken schreiben.
4. Eine unveränderliche Baseline anlegen und nachfolgende Läufe dagegen
   vergleichen.
5. Erst bei bestandenem Gate `satisfactory=true` ausgeben; andernfalls Gründe
   und beste noch offene Fehlerregionen protokollieren.

Die Umsetzung ist in sechs voneinander abnehmbaren Paketen von echtem
Zwei-Quellen-Runner bis zum Plan-B-Piloten geplant:
`docs/next_arbeitspakete_png_semantic_svg_2026-10-03.md`.

Damit ist der Weg technisch klar. Ob die aktuelle Implementierung ein
konkretes PNG zufriedenstellend konvertiert, bleibt dennoch eine Messfrage und
darf nicht aus dem Vorhandensein dieser Architektur abgeleitet werden.
