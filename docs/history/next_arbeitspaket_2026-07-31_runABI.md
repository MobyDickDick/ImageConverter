# Nächstes Arbeitspaket – gemeinsamer AC0502-L/M-Seed Run ABI (2026-07-31)

Run ABI arbeitet den in Run ABH dokumentierten nächsten Schritt ab: Ein
gemeinsamer Geometry-IR-Seed beschreibt die Topologie der beiden AC0502-Samples,
ohne eine Bild-ID, einen Dateinamen oder zwei getrennte Grössenmodelle zu
verwenden.

## 1) Implementierung

`build_diagonal_circle_cross_diagram_geometry_ir` erhält ausschliesslich die
normalisierte Bounding-Box des erkannten roten Diagrammfelds. Von diesem Anker
leitet der Builder sieben getrennte Primitive ab:

- graue Diagonal- und Horizontalverbindung als offene `PolygonPath`s,
- rotes Feld als `ColorPatch`,
- zwei weisse Diagonalen als offene `PolygonPath`s,
- grauer Feldrand als `RectBorder`,
- grauer Kreisanker als `CircleBackground`.

Alle Punkte, Konturbreiten und die Kreis-Bounding-Box sind Relationen des
Diagrammfelds. Der Seed enthält weder `AC0502` noch `L`, `M` oder absolute
Viewport-Koordinaten. Seine Telemetrie kennzeichnet die Herkunft mit
`normalized_primitive_relations` und dem Schema `perception_family_seed_v1`.

## 2) Grössengeneralisierung und Tests

Ein parametrisierter Helper-Test speist die aus den Referenzen ermittelten
Feld-Bounding-Boxen für 80×40 und 60×30 in denselben Builder ein. Er prüft die
identische Primitive-Reihenfolge, die allgemeine Perception-Metadatenstruktur
und die Renderbarkeit beider Viewports. Ein Negativtest sperrt leere
Feldgeometrien, bevor ungültige Seeds in den Optimierer gelangen.

## 3) Qualitäts- und Laufzeitbericht

Die erzeugten SVGs wurden mit derselben `_delta2`-Metrik wie der dokumentierte
Roundtrip in `tools/plan_b_roundtrip.py` direkt gegen die Samples verglichen:

| Sample | Run-ABH-Baseline | gemeinsamer Seed | Verbesserung |
| --- | ---: | ---: | ---: |
| `AC0502_1L_sia` | 497.845640 | 49.279257 | 90.10 % |
| `AC0502_1M_sia` | 465.142682 | 66.420423 | 85.72 % |

Der gemeinsame Qualitätslauf benötigte etwa 2.0 Sekunden für beide
Render-/Vergleichspaare. Der fokussierte Testlauf mit sechs Tests benötigte
2.17 Sekunden (`6 passed`).

## 4) Plan-B-/Perception-Lerneffekt und nächster Schritt

Der AC0502-L/M-Familienpfad ist auf Seed-Ebene **generalisiert**: Eine erkannte
Rechteckgeometrie reicht aus, um dieselben topologischen Relationen in beiden
Grössen zu erzeugen. Das ist keine Sample-Kopie; das Referenz-SVG wird weder
eingebettet noch zur Laufzeit gelesen.

Als nächstes soll der generische Feld-/Topologie-Detektor den Builder aus realen
Rasterkandidaten aufrufen. Danach folgt die in Run ABH abgegrenzte
AC0538-Klassifikation: gemeinsamer linker Diagonal-/Kreisanker, aber Stufenkurve
statt Kreuz und ein fachlich anderes rechtes Feld.
