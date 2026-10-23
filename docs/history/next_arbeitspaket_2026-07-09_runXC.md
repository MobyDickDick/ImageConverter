# Nächstes Arbeitspaket – DLG0021 Half-Yoctofine-Gradient-Probes Run XC (2026-07-09)

Run XC rotiert nach dem Checkpoint-Resume-Audit aus Run XB zurück in die aktive
Plan-B-Liste zu `DLG0021`. Der Fokus bleibt katalogfrei: Die allgemeinen
`PolygonPath`-Stroke-Gradient-Offset-Probes werden um eine halbyoctofeine
Zwischenstufe ergänzt, damit sehr kleine Positionsunterschiede in beschriebenen
Haken-/Konturgradienten ohne Bild-ID-Sonderfall bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-
  `stroke_gradient`-Stops nun zusätzlich `±0.0000244140625` im normalisierten
  Offset-Raum, also `±0.00244140625` Prozentpunkte.
- Ein neuer Helper-Test sichert, dass ein Stop bei `50.00244140625%` durch die
  neue Probe deterministisch auf `50%` registriert werden kann.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `DLG0021` noch an eine andere Runtime-Bild-ID.

## 2) Perception-Lerneffekt

`DLG0021` bleibt ein beschreibungsbasierter Checkbox-/Haken-Contract mit
`PolygonPath`-Kontur und grün-grauem Stroke-Gradienten. Run XC erweitert nicht
die Detektion, sondern den allgemeinen Optimierungsraum für bereits vorhandene
Gradienten-Stops. Der Lerneffekt bleibt daher: Primitive und Gradient sind als
Geometry-IR-Struktur nutzbar, die reine Bilddetektion allein reicht aber weiter
nicht für eine zufriedenstellende Konvertierung.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_half_yoctofine_probe` läuft grün mit `1 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-dlg0021-runXC --start DLG0021 --end DLG0021 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte DLG0021-Einzellauf bleibt stabil bei `Mean-Delta²=17056.199219` und `Fehler/Pixel=0.077702`.

## 4) Ergebnis / nächster Schritt

Run XC schließt den dokumentierten DLG0021-Feinschritt ab. Die zusätzlichen
Gradient-Offset-Probes sind allgemein verfügbar, verbessern den isolierten
DLG0021-Wert aber noch nicht. Das nächste Arbeitspaket kann in der aktiven
Plan-B-Rotation zu `GE1410_L` wechseln oder einen anderen Hebel für den
konzentrierten DLG0021-Restfehler prüfen.

## 5) Zwischenfazit zur Katalogqualität

Der aktuell im Repository dokumentierte Positivbestand umfasst `48` Varianten in
`successed_conversions.txt`. Bei einem Zielkatalog von circa `1700` Bildern sind
damit derzeit nur etwa `2,8 %` der Bilder explizit als qualitativ
zufriedenstellend nachgewiesen. Für eine belastbare Gesamtquote fehlen in diesem
Snapshot die vollständigen Batch-Reports für alle circa `1700` Bilder; die Zahl
`48` ist daher der dokumentierte Mindeststand, nicht zwingend eine endgültige
Vollkatalog-Auswertung.
