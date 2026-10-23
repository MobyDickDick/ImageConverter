# Nächstes Arbeitspaket – AC0538-Stufenkurvenklassifikation Run ABK (2026-08-01)

Run ABK arbeitet den in Run ABJ dokumentierten Folgepunkt ab und trennt die
AC0538-Stufenkurventopologie katalogfrei von der AC0502-Kreuztopologie.

## 1) Gemeinsamer Anker, getrennte Feldtopologie

`build_diagonal_circle_step_diagram_geometry_ir` verwendet dieselben
normalisierten Relationen für Diagonalverbindung, Horizontalanschluss,
Kreisanker, Farbfeld und Rahmen wie der Kreuzpfad. Im rechten Feld entsteht
jedoch genau ein offener `PolygonPath` mit zwei vertikalen Segmenten und einer
mittleren Verbindung. Weder Bild-ID noch Sample-Datei werden gelesen.

## 2) Rasterklassifikation

`detect_diagonal_circle_step_diagram_geometry_ir` verlangt gemeinsam ein
gesättigtes quadratisches Feld, helle linke/rechte Vertikalspuren, eine helle
Mittelspur und einen plausiblen Kreiskandidaten links. Sind stattdessen beide
vollständigen Diagonalen belegt, wird die Stufenklasse verworfen. Der allgemeine
Perception-Einstieg prüft nach der Kreuzklasse diese zweite Feldtopologie.

## 3) Qualität und Tests

- Das reale Raster `AC0538_1L_sia.jpg` aktiviert den neuen Sechs-Primitive-Seed.
- `AC0502_1L_sia.jpg` wird im Stufendetektor abgelehnt und weiterhin vom
  bestehenden Kreuzdetektor verarbeitet.
- Der direkte Rastervergleich erreicht `mean_delta2=770.669375` statt der in
  Run ABH dokumentierten Roundtrip-Baseline `1629.625242` (52,70 % weniger).
- Der fokussierte Vertrag umfasst zehn grüne Tests einschließlich Builder,
  Realrasterklassifikation, Negativklassifikation und allgemeinem Einstieg.

## 4) Perception-Lerneffekt und nächster Schritt

Die AC0538-Klassifikation ist auf Perception-/Seed-Ebene **generalisiert**. Die
Entscheidung beruht auf der Feldtopologie statt auf dem Katalognamen; der linke
Anker bleibt zwischen beiden Familien wiederverwendbar.

Als nächstes soll die Stufenspur aus ihren tatsächlich erkannten Rasterpunkten
statt den initialen normalisierten Familienrelationen parametrisiert werden.
Dabei sind ihre vier Knickpunkte sowie die Konturbreite innerhalb enger,
qualitätsgesicherter Grenzen zu schätzen.
