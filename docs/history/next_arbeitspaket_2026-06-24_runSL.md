# Nächstes Arbeitspaket – IDO-P2 Abschluss Run SL (2026-06-24)

Run SL arbeitet nach Abschluss von IDO-21 das nächste noch offene dokumentierte
Arbeitspaket aus `docs/open_tasks.md` und `docs/image_description_only_tasks.md`
ab: **IDO-P2 – ID-spezifische Runtime-Pfade ablösen**.

## Änderungen

- IDO-10 bis IDO-15 sind als abgeschlossen dokumentiert, nachdem die spätere
  IDO-17-/IDO-18-Nullprüfung bestätigt, dass im Runtime-Quellbaum keine
  Katalog-ID-Vorkommen mehr verbleiben.
- Der Abschluss verweist die einzelnen Migrationspakete auf ihre neutralen
  Steuergrößen: Connector-Richtung und Relationen für linke/rechte/vertikale
  Kreis-Connectoren, `connector_policy`/Z-Order für connector-freie und
  verdeckte Fälle, Text-/Glyph- und Kreisparameter für Badges,
  Primitive-Zerlegungen plus generische Transformationen für Ventil-/Kellenpfade
  sowie Profilmetadaten für Adaptive Locks und Optimierungsgrenzen.
- `docs/open_tasks.md` markiert IDO-P2 als erledigt und aktualisiert den
  Aufgaben-Gesamtzähler für diese Datei.

## Sicherung

- `python tools/check_no_new_image_id_hardcoding.py` meldet weiterhin `0`
  Runtime-ID-Vorkommen.

## Ergebnis

IDO-P2 ist abgeschlossen: Die vormals offenen IDO-10- bis IDO-15-Pakete sind
auf messbare Merkmale und neutrale Verträge zurückgeführt und die Runtime bleibt
unter der absoluten Nullregel frei von Bild-/Katalog-IDs.
