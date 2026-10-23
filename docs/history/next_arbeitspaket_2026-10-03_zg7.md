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
