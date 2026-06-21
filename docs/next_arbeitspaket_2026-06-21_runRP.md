# Nächstes Arbeitspaket – IDO-17 Semantic-Badge-Kommentar-De-ID Run RP (2026-06-21)

Run RP setzt den in `docs/image_description_only_tasks.md` dokumentierten
IDO-17-Anschluss fort: verbleibende Katalog-ID-Vorkommen in `src/` werden weiter
aus der Runtime herausgelöst beziehungsweise auf neutrale Dokumentation
umgestellt.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** weitere offensichtliche,
  nicht entscheidungsrelevante Katalog-ID-Nennungen in Kommentaren der
  Semantic-Badge-Parametrisierung und -Finalisierung neutralisieren, ohne
  semantische Pfade, Parameterdispatch oder Spezialfälle funktional umzubauen.

## Umsetzung

- VOC- und rF-Kommentare der Badge-Parametrisierung beschreiben die betroffenen
  Topologien nun über neutrale Begriffe wie connector-free, lower vertical,
  top connector und weak-family rotation statt über konkrete Kataloganker.
- Der CO₂-Kommentar in der Style-Finalisierung beschreibt den abgesenkten Index
  über die centered-CO₂-Topologie und die XML-Semantik statt über einen
  konkreten Symbolnamen.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Plan-B-/Sample-Prüfung

Der Sample-Ordner `artifacts/images_to_convert/samples` enthält SVG-Dateien,
die bereits versioniert im Repository liegen. In diesem Paket wurden keine neuen
unversionierten Sample-SVGs gefunden; deshalb wurde keine zusätzliche Plan-B-
Nachzeichnung ausgelöst.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `211` auf `195` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen liegen
  weiterhin überwiegend in aktiven Dispatch-, Metadaten- und
  Kompatibilitätspfaden und müssen in nachgelagerten Paketen semantisch ersetzt
  werden.
