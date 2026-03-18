# Update-Protokoll: Finale_Wurzelformen_V3.ods

- Die Tabelle `Wurzelformen` wurde auf **1.790 Zeilen** gebracht (1 Kopfzeile + 1.789 Bildzeilen).
- Für jede Bilddatei in `artifacts/images_to_convert` wurde eine Tabellenzeile erzeugt.
- Spalte **Bild** enthält den Dateinamen.
- Spalte **Wurzelform** enthält die erkannte Wurzelform (aus Dateinamen-Prefix / Zuordnung).
- Spalte **Beschreibung** wurde automatisch aus den bestehenden Wurzelform-Beschreibungen und Variantenbeziehungen abgeleitet.
- Für nicht sicher zuordenbare Dateien wurde ein klarer manueller Prüfhinweis eingetragen.

## Verifikationsauszug

- Zeilenanzahl in ODS nach Update: `1790`
- Erste Datenzeilen:
  - `AC0010.jpg` → `AC0010`
  - `AC0011.jpg` → `AC0011` (als identische Variante von AC0010 beschrieben)
  - `AC0020_L.jpg` → `AC0020`

## Hinweis

Die Ergänzung erfolgte datengetrieben auf Basis der bestehenden semantischen Beschreibungen in der ODS-Datei. Damit sind alle Bilder tabellarisch erfasst; verbleibende Sonderfälle sind explizit markiert.
