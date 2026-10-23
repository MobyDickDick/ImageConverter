# Nächstes Arbeitspaket – ZG7.1 echtes PNG-Zwei-Quellen-Fixture (2026-10-03)

Dieses Paket setzt den ersten Schritt der dokumentierten Folge
`ZG7.1 → ZG7.2 → ZG7.3 → ZG7.4 → ZG7.5 → ZG7.6` aus
`docs/next_arbeitspakete_png_semantic_svg_2026-10-03.md` um.

## Zwei-Quellen-Vertrag

`config/semantic_only_png_benchmark_v1.json` beschreibt drei kleine,
katalogfreie Topologien. Die zugehörigen Rasterdateien werden reproduzierbar
mit `tools/generate_semantic_only_png_fixtures.py` erzeugt und deshalb nicht als
Binärdateien versioniert:

1. Kreis, Kurztext und Anschluss,
2. Rechteck und Diagonale,
3. Polygonpfad und Linie.

Jeder Fall enthält genau den PNG-Pfad, die semantische Beschreibung, eine
neutrale Fallkennung und die dokumentierende Topologie. Zusätzliche Felder
werden bewusst abgelehnt, damit Referenz-/Sample-SVGs, Bestlisten oder
Template-Donoren nicht unbemerkt zu Wissensquellen werden können.

## Ausführung und Nachweis

`tools/run_semantic_only_benchmark.py` erstellt pro Wiederholung eine neue
Sandbox, kopiert genau ein PNG hinein und erzeugt aus der Manifestbeschreibung
die lokale Beschreibungstabelle. Der echte Konverter wird ausschließlich im
Modus `semantic-only` und mit dessen festem `deterministic-order`-Seed `0`
gestartet. Standardmäßig laufen alle Fälle dreimal; die
letzte Wiederholung heißt unabhängig vom ursprünglichen Fall
`renamed_input.png`.

Der JSON-Report protokolliert Eingangs-Hashes, Exitcodes, rohe und normalisierte
SVG-Hashes sowie die Umbenennungsinvarianz. Die XML-Normalisierung entfernt nur
Formatierungsunterschiede; Struktur, Attribute, Texte und Kindreihenfolge
bleiben Teil des Hashes. Ein fehlendes, nicht parsebares oder abweichendes SVG
setzt den Gesamtstatus auf Fehler.

Reproduktionsbefehl:

```bash
python tools/generate_semantic_only_png_fixtures.py
python tools/run_semantic_only_benchmark.py \
  config/semantic_only_png_benchmark_v1.json \
  --work-dir artifacts/semantic_only_png_benchmark/work \
  --output artifacts/semantic_only_png_benchmark/report.json
```

## Ergebnis und Anschluss

Fixture-, Manifest- und Runner-Verträge sind automatisiert abgesichert. ZG7.1
ist damit abgeschlossen. Das nächste dokumentierte Paket ist **ZG7.2
End-SVG-Metrikvertrag**; erst dort werden Qualitätsmetriken eingeführt. Die
aktuelle stabile Ausgabe ist ausdrücklich noch kein Qualitätsurteil.
