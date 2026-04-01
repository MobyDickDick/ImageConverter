# Vorbereitung: Funktionen in einzelne Dateien auslagern

Dieses Repo enthält jetzt ein Vorbereitungs-Tool, das eine strukturierte
Auslagerungsplanung erzeugt.

## Tool

`tools/generate_function_modularization_plan.py`

Das Tool analysiert eine Python-Datei und schreibt ein JSON mit:

- Modul-Imports
- Modul-Konstanten
- allen Top-Level-Funktionen inkl. Quellbereich (Start-/Endzeile)
- direkten Intra-Datei-Abhängigkeiten zwischen Funktionen
- vorgeschlagenem Zielmodul und Ziel-Datei pro Funktion

## Beispiel

```bash
python tools/generate_function_modularization_plan.py \
  src/imageCompositeConverter.py \
  --output-json artifacts/reports/function_modularization_plan_imageCompositeConverter_2026-04-01.json \
  --output-dir src/imageCompositeConverter_functions \
  --module-prefix src.imageCompositeConverter_functions
```

## Ergebnis für `imageCompositeConverter.py`

Es wurde ein Plan mit 133 Funktionen generiert:

- `artifacts/reports/function_modularization_plan_imageCompositeConverter_2026-04-01.json`

## Nächster Schritt (empfohlen)

1. Die generierten `depends_on_functions` als Reihenfolge-Hilfe nutzen
   (zuerst "Leaf"-Funktionen ohne interne Abhängigkeiten auslagern).
2. Für jede ausgelagerte Funktion eine dünne Kompatibilitäts-Weiterleitung im
   Ursprungsmodul lassen, bis alle Aufrufer migriert sind.
3. Nach jedem kleinen Batch Tests ausführen.
