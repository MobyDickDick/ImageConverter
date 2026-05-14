# V5 – Semantische Textrepräsentation + Bedingungen (v1, 2026-05-14)

## Ziel

Ein deterministischer Zwischenlayer beschreibt eine Szene als **Objekte + Relationen + Constraints**,
so dass aus derselben Beschreibung reproduzierbar dieselbe rekonstruktive SVG-Szene erzeugt werden kann.

## DSL/JSON-Struktur (v1)

Top-Level-Felder:

- `scene_id`: stabile ID der Szene.
- `canvas`: Ausgabegröße (`width`, `height`, `units`).
- `objects`: deklarative Objektliste mit Typ, Geometrie und Stil.
- `relations`: explizite semantische Beziehungen zwischen Objekten.
- `constraints`: harte/weiche Bedingungen für die Rekonstruktion.
- `labels`: optionale Textmarker für Diagnose und Roundtrip-Checks.

### Objektmodell

Jedes Objekt enthält:

- `id`: eindeutige Kennung.
- `type`: z. B. `ladle_bowl`, `ladle_handle`, `text_label`, `connector`.
- `geometry`: typabhängige Parameter (`cx`, `cy`, `r`, `x1`, `y1`, `x2`, `y2`, ...).
- `style`: `stroke`, `stroke_width`, `fill`, optional `gradient_ref`.
- `confidence`: Modellvertrauen `0.0..1.0`.

### Relationsmodell

Vordefinierte Relationstypen:

- `attached_to` (z. B. Griff ist an Schale angebunden)
- `left_of` / `right_of`
- `above` / `below`
- `inside`
- `overlaps`
- `covers` / `behind` / `continues_behind` (kompatibel mit V4)

Jede Relation enthält:

- `subject`, `predicate`, `object`
- optional `tolerance_px`

### Constraint-Modell

Constraint-Felder:

- `kind`: `hard` oder `soft`
- `rule`: regelname (`horizontal_alignment`, `max_gap`, `text_anchor_match`, ...)
- `targets`: betroffene Objekt-IDs
- `params`: regelparameter
- `weight`: nur für `soft` relevant

## Deterministische Rückübersetzung

Minimaler deterministischer Ablauf:

1. `objects` in stabiler Reihenfolge (`id` lexikografisch) instanziieren.
2. `relations` zur Positionierung/Anbindung anwenden.
3. `hard`-Constraints strikt durchsetzen, sonst Fehler.
4. `soft`-Constraints als Optimierungsziel aufnehmen.
5. SVG serialisieren (stabile Attributreihenfolge), Hash bilden.

Akzeptanzkriterium V5 gilt als erfüllt, wenn dieselbe JSON-Beschreibung bei zwei Läufen dieselbe
SVG-Serialisierung (oder denselben kanonischen Hash) erzeugt.

## Artefakte

- Schema: `docs/vision/semantic_scene_description_v1.schema.json`
- Beispielszene: `artifacts/evaluation/semantic_scene_description_v1/example_scene.json`
