# Nächstes Arbeitspaket – IDO-10 linker Kreis-Connector Run QC (2026-06-17)

## Ziel

Run QC startet das nächste dokumentierte Arbeitspaket aus
`docs/image_description_only_tasks.md`: **IDO-10 – Linker Kreis-Connector als
erstes vertikales Migrationspaket**. Der erste Schnitt ersetzt keinen weiteren
Legacy-Pfad, sondern legt den katalogfreien Beschreibungspfad für die Topologie
„Kreis mit linkem horizontalem Anschluss“ an und sichert ihn per neutralem
Rename-Test ab.

## Umsetzung

- `buildGeometryIrFromDescriptionImpl(...)` erkennt nun generische
  Beschreibungen wie „Kreis mit waagrechtem Strich links vom Kreis“ ohne
  Bild-/Katalog-ID.
- Der Parser erzeugt dafür getrennte `CircleBackground`- und `HorizontalRule`-
  Elemente mit `target_ref` und `left_of`-Relation.
- Die neuen Tests verwenden neutrale bzw. umbenannte Dateinamen und vergleichen
  die erzeugten Constraints sowie die Geometry-IR direkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m pytest -q tests/detailtests/test_description_contract_helpers.py tests/test_description_perception_fusion.py && python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Exit `0`; `31 passed`; der Hardcoding-Ratchet bleibt auf der
bestehenden Legacy-Baseline (`404` Legacy-Vorkommen) ohne neue Bild-ID.

## 5-Zeilen-Log

- **Getestet:** Beschreibungspfad, Rename-Invarianz und IDO-08/IDO-09-Fusionsregressionen.
- **Ergebnis:** Exit `0`; `31 passed`; keine neue Runtime-Bild-ID oberhalb der Legacy-Baseline.
- **Blocker:** IDO-10 bleibt offen, bis die bestehenden linken Kreis-Connector-ID-Listen vollständig ersetzt und die Qualitätsfixtures gegengeprüft sind.
- **Dokumentation:** Fortschritt ist in `docs/image_description_only_tasks.md` zurückgeführt.
- **Nächster Schritt:** IDO-10 fortsetzen: Perception-/Kontaktmessung und bestehende linke Connector-Familien an den katalogfreien Pfad anbinden, danach Legacy-Baseline reduzieren.
