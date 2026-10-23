# Nächstes Arbeitspaket – IDO-17 Valve-Head-SVG-De-ID Run RE (2026-06-20)

Run RE setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und entfernt
die verbliebene katalogspezifische Valve-Head-Wiederherstellung aus dem
Badge-SVG-Renderer.

## 1) Ziel

Valve-Head-Badges sollen weiterhin ihre dedizierte Kopfgeometrie und den
zentrierten vertikalen Connector behalten, auch wenn späte Optimierungs- oder
Fallback-Pfade nur einen dünnen Parametersatz liefern. Diese Entscheidung darf
aber nicht mehr über einen konkreten Katalog-Symbolnamen erfolgen.

## 2) Umsetzung

- `generateBadgeSvgImpl(...)` aktiviert die Valve-Head-Wiederherstellung jetzt
  über neutrales Style-Metadatum `head_style=ac0223_triple_valve`.
- Der bisherige SVG-seitige `variant_name`-/`badge_symbol_name`-/`base_name`-
  Dispatch für diese Wiederherstellung wurde entfernt.
- Die optionale diagonale Quadratgriff-Darstellung hängt nun am expliziten
  Parameter `ac0223_handle_style=square_diagonals` statt an einem Dateisuffix.
- Ein neutraler Detailtest mit `ZZ_NEUTRAL_VALVE_HEAD` sichert, dass
  Valve-Head-Geometrie ohne Katalog-ID aus Style-Metadaten wiederhergestellt
  wird.
- Die Legacy-Baseline wurde auf den neuen Runtime-Bestand aktualisiert.

## 3) Nachweis

- `python -m compileall -q src tests/detailtests/test_semantic_badge_svg_helpers.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py`
  → `6 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (307 legacy occurrences remain).`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py`
  → `diff_renderable_pairs=630`, `successful_renderable_pairs=48`, `selected=GE9002_7S,GE9002_5S,GE9002_3S,GE9002_4M,GE9002_1S`.

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab: Der Badge-SVG-Pfad stellt
Valve-Head-Geometrie nicht mehr anhand einer konkreten Runtime-Katalog-ID wieder
her; der Ratchet sinkt von 308 auf 307 Runtime-ID-Vorkommen.

## 5) Nächster Schritt

IDO-17 fortsetzen und die nächsten verbleibenden katalogspezifischen Runtime-
Tokens in Badge-Parametrisierung, Finalisierung, Fitting oder Diagnosepfaden
durch neutrale Beschreibungssignale, Parameter oder Testdaten ersetzen.
