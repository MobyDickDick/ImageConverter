# Linux-CI: Glyphenlage korrekt, Textdeckung zu gering

PR #2073, fehlgeschlagener Job:
[svg-text-baseline](https://github.com/MobyDickDick/ImageConverter/actions/runs/40750577862/job/123035867289).
Der Fehler liegt im Foreground-IoU-Pixelgate nach zwei bestandenen Glyphengrenzenprüfungen.
Unter Ubuntu 26.04 reproduziert; explizites Liberation Sans reproduziert ihn
auch unter Windows: AC0721_M erreicht 0,814516 statt mindestens 0,85.

Die allgemeine Quadratbeschriftungsregistrierung prüft fünf dünne Konturen
aus der Originalpixelevidenz. AC0721_M erreicht damit 0,911290. Drei Archivpaare
erhalten die geprüfte Kontur von 0,125 Pixeln einschließlich Messwerten und Hashes.
Geometrie, Baseline, Katalogzahl und Abnahmegrenzen bleiben erhalten.
Die neue Regression prüft Systemschriften und Liberation getrennt; der
ursprüngliche negative Fall bleibt als Gegenprobe erhalten.

`checks.json` enthält kompakte Fälle, Grenzwerte, Prüfbefehle und Ergebnisse.
Alle ausführlichen CLI-/Rendering-Rohdaten bleiben unter `.tmp/svg-text-*`.
Die ursprünglichen Baseline-Berichte werden nicht mit einem neuen Erfolg überschrieben.

Abnahme unter Ubuntu 26.04 mit Python 3.10.22 wie im CI: 40 Tests bestanden,
eine vollständige Archiv-Neukonvertierung regulär übersprungen. Beide regulären
CLI-Gates und die unabhängige librsvg-Abnahme bestehen jeweils 6/6.
Unter Windows bestehen die betroffenen SVG-/Archivfälle (201), die GUI-Prüfung
(18) sowie das Kernprofil (42). Die separate interne Plan-B-Prüfung bleibt
wegen AC0721_L unverändert 5/6. Die neue Remote-CI wurde noch nicht ausgeführt.

Zusätzlich blockierte eine Bild-ID in einem GUI-Kommentar die Jobs
`image-id-hardcoding-ratchet`, `completion-profile` und `batch-artifact-drift-gate`.
Der Kommentar ist verallgemeinert, der Scanner unverändert und lokal grün.

[Umsetzung und historische Abnahmegrenzen](../../../docs/next_arbeitspaket_2026-10-28_svg_text_baseline.md#ci-nachtrag-linux-schriftrückfall-und-buchstabendeckung).
