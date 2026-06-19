# Nächstes Arbeitspaket – IDO-17 Generische Semantic-Debug-Ausgabe Run QS (2026-06-19)

Run QS setzt nach IDO-16 das nächste dokumentierte Arbeitspaket aus
`docs/image_description_only_tasks.md` fort: IDO-17 entfernt weitere
Runtime-Katalog-ID-Kopplung aus `src/`, ohne neue Bild-/Katalog-ID in der
Runtime einzuführen.

## Umsetzung

- Die Conversion-Debug-Ausgabe unter `debug_ac0811_dir` ist nicht mehr auf die
  konkrete AC0811-Basis eingeschränkt. Wenn ein Debug-Verzeichnis gesetzt ist,
  schreibt `_emitVariantDebugDump(...)` den maschinenlesbaren Dump nun für jede
  Variante unter dem neutralen Variantennamen.
- Der Semantic-Validation-Debug-Fallback ist ebenfalls katalogfrei: Ein
  gesetztes Debug-Verzeichnis erzeugt den Varianten-Unterordner unabhängig vom
  Dateistamm beziehungsweise der Bild-ID.
- Die zugehörigen Regressionstests verwenden neutrale Dateinamen und sichern,
  dass der Debug-Fallback sowie der Conversion-Dump ohne AC0811-Sonderfall
  funktionieren.

## Qualität / Ratchet

- `tools/check_no_new_image_id_hardcoding.py --update` verkleinert die Legacy-
  Baseline um die entfernten Runtime-ID-Vorkommen aus Conversion-Debug,
  Semantic-Validation-Debug und dem bereits katalogfrei gewordenen
  Optimierungsprofil-Alias.
- Der Ratchet meldet anschließend `365 legacy occurrences remain` und bleibt
  grün.

## Abschluss

- **Fortschritt:** IDO-17 ist weiter reduziert: Debug-Instrumentierung für
  Semantic-/Conversion-Dumps entscheidet nicht mehr über `AC0811`, sondern über
  das Vorhandensein eines explizit gesetzten Debug-Verzeichnisses.
- **Blocker:** Kein neuer technischer Blocker; die verbleibenden Runtime-IDs
  liegen weiterhin in älteren Qualitäts-, Reporting- und Semantikpfaden und
  müssen paketweise in generische Merkmale überführt werden.
- **Nächster sinnvoller Schritt:** IDO-17 fortsetzen und den nächsten kleinen
  Runtime-ID-Cluster aus `src/` in einen parameter- oder metrikbasierten Pfad
  verschieben.
