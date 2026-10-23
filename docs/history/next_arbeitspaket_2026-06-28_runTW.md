# Nächstes Arbeitspaket – DLG0021 generische PolygonPath-Feinpunkt-Probes Run TW (2026-06-28)

Run TW rotiert nach Run TV zurück zum aktiven Plan-B-Spitzenkandidaten
`DLG0021` aus `PLAN_B_KANDIDATEN.md`. Der Fokus bleibt katalogfrei: Die
sequentielle Geometry-IR-Optimierung erhält für `PolygonPath`-Punkte zusätzlich
feine lokale Koordinatenproben.

## Änderungen

- `PolygonPath`-Elemente testen pro Punktkoordinate nun neben den bisherigen
  groben `±0.02`-Verschiebungen auch `±0.01`.
- Die Änderung betrifft nur generische Polygonpfade; andere Primitive behalten
  ihre bisherige lokale Punkt-/BBox-Palette.
- Ein Detailtest sichert, dass der Standard-Provider eine feine Punktprobe
  tatsächlich auswählen kann, wenn nur diese Probe den Renderfehler senkt.

## Perception-Lerneffekt

- `DLG0021` bleibt `nur Sonderfall`: Die reine Bilddetektion liefert weiterhin
  keinen robusten Checkbox-/Haken-Seed. Die neue Feinprobe verbessert aber die
  allgemeine, beschreibungsbasierte `PolygonPath`-Registrierung für Haken,
  Konturen und kleine Diagrammpfade.

## Sicherung

- `pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py` läuft grün
  mit `17 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py`
  läuft grün und meldet weiterhin `0 occurrences`.

## Ergebnis

Run TW erweitert die allgemeine `PolygonPath`-Optimierung um feinere lokale
Punktprobes. Damit kann das nächste Paket entweder weiter in der aktiven
Plan-B-Liste rotieren oder das verbleibende DLG0021-Farb-/Kontur-Feintuning mit
der feineren Punktpalette fortsetzen.
