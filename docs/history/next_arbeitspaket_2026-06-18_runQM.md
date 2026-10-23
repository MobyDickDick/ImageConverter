# Nächstes Arbeitspaket – IDO-13 Kreis-/Text-Badges Run QM (2026-06-18)

## Ziel

Run QM startet IDO-13 aus `docs/image_description_only_tasks.md`: Kreis-/Text-Badges
sollen Labelinhalt, zentrierte Textlage und grobe Kreisgeometrie aus der
Beschreibung ableiten, ohne neue Bild-ID-Dispatches einzuführen.

## Umsetzung

- Der beschreibungsgetriebene Geometry-IR-Pfad extrahiert Kreis-Badge-Labels für
  `T`, `M`, `VOC`, `CO₂`, `rF` und `rH` aus generischen Formulierungen wie
  `Text "CO2"`, `Label rF` oder `zentrierter VOC-Glyph`.
- Kreis-Badges werden als `CircleBackground` mit `badge_role="circle_text_badge"`
  und optionalem `TextGlyph` gerendert; Text-Glyphen tragen
  `text_position="center"`, `target_ref="described_circle"` und die Relation
  `centered_in`.
- Kleine und große Kreisformulierungen setzen generische Bounding-Box-Varianten;
  connector-freie textlose Kreise behalten `connector_policy="forbid"` und
  erzeugen keine implizite Text- oder Connector-Relation.

## Sicherung

- `tests/detailtests/test_description_contract_helpers.py` prüft VOC-Badges
  inklusive `centered_in`-Relation, CO₂-/rF-Labelnormalisierung, Kreisgrößen und
  den Negativfall „ohne Buchstabe“.
- Der Runtime-Ratchet gegen neue Bild-ID-Sonderfälle bleibt unverändert grün.

## Ergebnis

IDO-13 hat nun einen ersten katalogfreien Badge-Pfad für die in der Akzeptanz
aufgeführten Label- und Negativfälle. Offen bleibt die spätere Kopplung an echte
Text-/Glyph- und Bildmessungs-Evidenz sowie weitere Textlagen außerhalb der
zentrierten Badge-Position.
