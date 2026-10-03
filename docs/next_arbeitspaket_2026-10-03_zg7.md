# ZG7 Zwischenstand – Determinismus-Scaffold (2026-10-03)

Dieses Paket beginnt nach ZG6 die nächste priorisierte P1-Aufgabe aus
`docs/umsetzungscheck_bild_semantik_2026-05-15.md` um: ein repräsentatives,
reproduzierbares Benchmark-Set, das ausschließlich JPEG und sprachliche
Beschreibung als fachliche Eingaben zulässt.

## Vertrag und Abdeckung

`config/semantic_only_benchmark_v1.json` enthält fünf Fälle und deckt Kreis,
Text, Linie, Rechteck und Pfad ab. Ein Fall darf neben `case_id`, JPEG-Pfad,
Beschreibung und reiner Primitive-Klassifikation keine weiteren Felder
besitzen. Der Runner lehnt insbesondere versteckte Template-, Baseline- oder
bereits konvertierte SVG-Quellen ab. Er liest die Canvasgröße direkt aus dem
JPEG und erzeugt Geometry-IR und SVG aus der Beschreibung.

## Stabilitätsnachweis

`tools/run_semantic_only_benchmark.py` führt den beschreibungsbasierten
Geometry-IR-Render jedes Falls standardmäßig dreimal
aus. SHA-256-Nachweise für JPEG, Beschreibung, normalisierte Geometry-IR und
normalisiertes SVG machen die Eingangs- und Ergebnisidentität prüfbar. Eine
leere Geometry-IR oder voneinander abweichende Wiederholungen lassen den Lauf
fehlschlagen. Der versionierte Bericht liegt unter
`artifacts/evaluation/semantic_only_benchmark_v1/report.json` und bestätigt
fünf von fünf deterministischen Fällen über fünf Primitive-Familien. Der
Report kennzeichnet sich ausdrücklich mit
`assessment_scope=description_render_determinism`, `quality_assessed=false`
und `satisfactory=null`.

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 \
  python tools/run_semantic_only_benchmark.py \
  config/semantic_only_benchmark_v1.json \
  --output artifacts/evaluation/semantic_only_benchmark_v1/report.json
```

## Qualitätsaussage und nächster Schritt

Der Scaffold belegt Reproduzierbarkeit und Quellenreinheit, aber **noch keine
bedeutsame Verbesserung der visuellen Konvertierungsqualität**. Dafür fehlt in
diesem Benchmark bewusst noch ein versionierter Vorher-/Nachher-Vergleich der
Pixel- und Semantikmetriken. Ein belastbarer Zeithorizont lässt sich deshalb
nicht aus Kalenderzeit ableiten. Die nächste P2-Aufgabe sollte die dokumentierte
Metrikhierarchie auf diesen Fällen anwenden und erst nach mindestens zwei
vergleichbaren Läufen eine Qualitätsverbesserung ausweisen. ZG7 bleibt deshalb
offen, bis der echte `semantic-only`-Konverterpfad die Bildpixel verarbeitet
und diese Metriken gegen eine versionierte Baseline ausweist.
=======
# Nächstes Arbeitspaket – ZG7 Benchmark ohne Sonderwissen (2026-10-03)

Dieses Paket setzt nach ZG6 die nächste priorisierte P1-Aufgabe aus
`docs/umsetzungscheck_bild_semantik_2026-05-15.md` um: ein repräsentatives,
wiederholbares Benchmark-Set ohne bildspezifische Hinterlegung.

## Zwei-Quellen-Vertrag und Sample-Set

Das versionierte Manifest `semantic_only_benchmark_v1` enthält sechs JPEGs aus
unterschiedlichen Namens-/Formfamilien und Größenvarianten. Es enthält bewusst
nur Dateinamen: keine Ziel-SVGs, Geometrieparameter, Templates, Checkpoints oder
erwarteten bildspezifischen Rendererpfade.

Der Runner kopiert für jeden Versuch genau ein JPEG in ein frisches,
isoliertes Eingabeverzeichnis und startet die bestehende CLI mit der gemeinsamen
Beschreibungstabelle, `--execution-mode semantic-only` und
`--deterministic-order`. Die absichtlich zufällige, rein präsentative
SVG-Ausgabevariation wird für den Reproduzierbarkeitsnachweis über
`TINY_ICC_OUTPUT_VARIATION=0` abgeschaltet. Damit sind Bild und sprachliche Beschreibung die
einzigen fachlichen Eingaben; frühere Resultate können nicht als Donoren oder
Resume-Quelle in einen Versuch gelangen.

## Stabilitätsnachweis

Jedes Sample wird standardmäßig zweimal in getrennten Arbeitsverzeichnissen
konvertiert. Der Report protokolliert Exit-Code, Ausführungsmodus und SHA-256
des erzeugten SVG je Wiederholung. Nur wenn alle Wiederholungen erfolgreich
sind und byteidentische SVGs liefern, gilt das Sample als stabil. Bereits ein
abweichender Hash oder ein fehlgeschlagener Lauf setzt den Gesamtstatus auf
`passed=false` und den CLI-Exit-Code auf `1`.

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. python \
  tools/run_semantic_only_benchmark.py \
  artifacts/evaluation/semantic_only_benchmark_v1/manifest.json \
  --image-dir artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --work-dir /tmp/image-converter-semantic-benchmark \
  --output /tmp/semantic_only_benchmark_v1.json
```

## Absicherung und nächster Schritt

Helper-Tests sichern die Eingabeisolation, den zwingenden Semantik-only-Modus,
zwei unabhängige Wiederholungen, stabile und instabile SVG-Ergebnisse sowie die
Ablehnung von Pfadtraversal und Nicht-JPEG-Eingaben. Der reale Sechs-Sample-Lauf
wurde ebenfalls mit zwei Wiederholungen ausgeführt und bestätigt für alle
Samples byteidentische SVGs. ZG7 ist damit abgeschlossen. Die nächste
priorisierte Leitaufgabe ist die dokumentierte
Metrik-Hierarchie aus P2.
