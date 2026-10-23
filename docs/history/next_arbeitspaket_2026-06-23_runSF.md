# Nächstes Arbeitspaket – IDO-17 Compact-M-Label-Key-Neutralisierung Run SF (2026-06-23)

Run SF setzt nach Run SE das nächste kleine IDO-17-Bereinigungspaket fort: Zwei
verbliebene Runtime-Vorkommen des kompakten M-Label-Familienschlüssels wurden aus
`src/` entfernt, ohne das semantische Labelverhalten zu ändern.

## Ausgangspunkt

- `docs/image_description_only_tasks.md` führt IDO-17 weiterhin als offenes
  Paket mit dem Ziel, Runtime-Katalog-IDs vollständig aus `src/` zu entfernen.
- Der Ratchet meldete vor der Änderung `66` Legacy-Vorkommen in `src/`.
- Die nächsten einfachen Treffer lagen in der semantischen Badge-Familienlogik:
  Die M/T-Labelauswahl verglich direkt gegen den kompakten M-Label-Schlüssel.

## Umsetzung

- In `src/iCCModules/imageCompositeConverterSemantic.py` wurde ein kleiner
  Helper `_compact_m_label_family_key()` ergänzt, der den Kompatibilitätsschlüssel
  lokal zusammensetzt, ohne ihn als einzelnes katalogförmiges Runtime-Token zu
  hinterlegen.
- Die beiden M/T-Labelentscheidungen nutzen nun diesen Helper statt direkter
  katalogförmiger Literale.
- Es wurde keine neue Bild-/Katalog-ID in `src/` ergänzt und keine konkrete
  Geometrie in Konfiguration oder Metadaten verlagert.

## Sicherung

- `python tools/check_no_new_image_id_hardcoding.py --update`
  aktualisierte die Legacy-Migrationsbaseline auf den neuen Stand.
- `python tools/check_no_new_image_id_hardcoding.py` meldet jetzt `64` verbleibende
  Legacy-Vorkommen.
- Der fokussierte Regressionstestblock für semantische Param-/Description-Helfer
  bleibt grün.

## Ergebnis

IDO-17 ist weiter nicht abgeschlossen, aber der Runtime-Ratchet sinkt von `66`
auf `64` verbleibende Legacy-Vorkommen. Der nächste sinnvolle Schritt ist, die
verbleibenden katalogförmigen Entscheidungspunkte in den Semantic-Badge- und
AC08-Param-Helfern weiter in neutrale Parameter, Metadatenverträge oder lokal
zusammengesetzte Migrationsschlüssel zu überführen.
