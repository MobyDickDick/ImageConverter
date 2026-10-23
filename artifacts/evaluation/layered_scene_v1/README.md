# Gefüllte und verschachtelte Grundformszenen

Kompakter Nachweis aus 107 echten CLI-Versuchen: Entwicklung vorher/nachher
je 18, neue finale Prüfszenen vorher/nachher je 18, 18 Umbenennungen und eine
unabhängige erweiterte Plan-B-Vorlage mit 17 Fällen. Elternstand `e533c4307`.

- `manifest.json`: 53 eingefrorene Raster, Beschreibungen und unabhängige
  Referenzobjekte einschließlich Anzahl, Form, Außenbox und Elternbeziehung.
- `sources/`: unveränderte PNG-Eingaben, nur für die unabhängige Nachmessung.
- `vectors/`: tatsächlich gespeicherte CLI-SVGs beider Stände.
- `summary.json`: Einzelentscheidungen, Metriken, Objekt-/Regionsprüfungen,
  Ein-/Ausgabezuordnung, Quellcodeprüfsummen und beobachtete Workerbudgets.
- `comparison.png`: vier Beispiele mit Quelle, Elternausgabe und neuer Ausgabe.
- `checks.json`: Abschlussprüfungen und Archivnachweis.

Die Entwicklungs- und neuen Prüfszenen verbessern sich von jeweils 0/18 auf
18/18; die Umbenennungen liefern bytegleiche SVGs. Die erweiterte Vorlage
besteht 17/17. Die globalen und lokalen Qualitätsgrenzen bleiben unverändert.
Diese synthetischen Szenen sind kein repräsentativer Katalogbenchmark.

Die kompakten Raster-/SVG-Paare können auch in einem frischen Checkout ohne
erneute Konvertierung unabhängig geprüft werden:

```powershell
.venv/Scripts/python.exe -m tools.summarize_layered_scene_evaluation --verify-only
```

Runtime-Metadaten sind aufbewahrte Beobachtungen der ursprünglichen Versuche;
der kompakte Prüfer erzeugt keine neuen Laufzeitmessungen. Vollständige
ursprüngliche CLI-Berichte und -Protokolle liegen lokal unter
`.tmp/general-scene-*`. CI erzeugt einen eigenen Lauf und lädt dessen
vollständige Ausgaben hoch. Siehe [Arbeitspaket](../../../docs/history/next_arbeitspaket_2026-10-20_layered_scene.md)
für reproduzierbare neue CLI-Versuche, Prüftrennung und Grenzen.
