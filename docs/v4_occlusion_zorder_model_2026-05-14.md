# V4 – Überdeckungen/Z-Order explizit erkennen (2026-05-14)

## Ziel
Für den Vision-Track V4 wird ein expliziter Layer-Graph mit Occlusion-Relationen definiert, sodass teilverdeckte Griffe/Verbindungen konsistent rekonstruiert werden können.

## Layer-Graph-Modell

Jede Szene wird als gerichteter Multigraph modelliert:

- **Knoten (`nodes`)**: erkannte Primitive/Objekte mit stabiler `id` und Layer-Index `z`.
- **Kanten (`relations`)** mit Typ:
  - `covers`: Objekt A überdeckt sichtbare Teile von Objekt B.
  - `behind`: Objekt A liegt hinter Objekt B (inverse Tiefenbeziehung).
  - `continues_behind`: Objekt A setzt sich geometrisch hinter Objekt B fort, obwohl der Mittelteil unsichtbar ist.

## Maschinenlesbares Deliverable

- Schema: `docs/vision/occlusion_layer_graph_v1.schema.json`
- Beispiel-/Baseline-Artefakt: `artifacts/evaluation/occlusion_layer_graph_v1/baseline_scene_graph.json`

### Kompaktes JSON-Beispiel

```json
{
  "scene_id": "AC0811_L",
  "nodes": [
    {"id": "bowl", "primitive": "ellipse", "z": 3},
    {"id": "handle", "primitive": "line", "z": 2},
    {"id": "label_rf", "primitive": "text", "z": 4}
  ],
  "relations": [
    {"type": "covers", "front": "bowl", "back": "handle", "confidence": 0.89},
    {"type": "continues_behind", "occluder": "bowl", "occluded": "handle", "confidence": 0.83},
    {"type": "behind", "back": "handle", "front": "label_rf", "confidence": 0.76}
  ]
}
```

## Konsistenzregeln

1. `covers(front=A, back=B)` impliziert `z(A) >= z(B)`.
2. `behind(back=A, front=B)` impliziert `z(A) <= z(B)`.
3. `continues_behind` ist nur gültig, wenn zusätzlich eine überdeckende Relation zum gleichen Objektpaar existiert (`covers` oder `behind` konsistent auflösbar).
4. Zyklische harte Tiefenwidersprüche sind unzulässig (z. B. A hinter B und B hinter A mit hoher Confidence).

## Akzeptanzkriterium V4 (messbar)

V4 gilt als erfüllt, wenn auf einem Test-Subset mit teilverdeckten Griff-/Verbindungsformen:

- für jede Szene ein valider Layer-Graph erzeugt wird,
- mindestens eine Occlusion-Relation (`covers` oder `continues_behind`) je verdecktem Objektteil vorliegt,
- und die Rekonstruktion keine Tiefenwidersprüche gemäß Konsistenzregeln enthält.

## Ergebnis

Das V4-Deliverable (expliziter Layer-Graph mit `covers`, `behind`, `continues_behind`) ist damit spezifiziert und maschinenlesbar verankert.
