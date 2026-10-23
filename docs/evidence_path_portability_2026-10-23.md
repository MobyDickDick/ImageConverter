# Plattformunabhängige Pfade in Szenenbelegen

Die neun CI-Fehler in `test_real_scene_transfer_evidence.py` und
`test_residual_scene_evidence.py` entstehen durch gespeicherte Windows-Pfade,
nicht durch fehlende versionierte SVGs. Die alten `output_svg`-Werte enthalten
Backslashes. Unter Linux interpretiert `Path` diese als Zeichen im Dateinamen.

Der SVG-Manipulationstest schrieb dadurch unter Linux eine zusätzliche Datei
mit Backslashes im Namen, statt das versiegelte SVG zu ersetzen. Der Verifier
meldete folgerichtig `Incomplete evidence inventory`; erwartet war die Meldung
`Missing or changed evidence` für das tatsächlich beschädigte Original.

Der gemeinsame Szenenprüfer normalisiert beim Lesen beide Separatoren und
verlangt einen relativen Pfad innerhalb des Belegordners. Absolute Pfade,
Windows-Laufwerke und Pfade außerhalb dieses Ordners werden zurückgewiesen.
Der Manipulationstest verwendet denselben Pfadleser. Neue Plan-B-Berichte
speichern `output_svg` und `reference_svg` mit POSIX-Separatoren.
Historische Berichte, SVGs und versiegelte Prüfsummen bleiben unverändert;
die Inventarprüfung und Qualitätsgrenzen werden nicht abgeschwächt.

## Prüfung

- 74 Tests unter Windows bestehen: beide betroffenen Module,
  `test_mixed_gradient_scene_evidence.py` und
  `tests/detailtests/test_plan_b_variations.py`.
- Neue Regressionen prüfen beide Pfadseparatoren, acht unverändert positive
  bzw. negative gespeicherte SVG-Ausgaben im vollständigen Neun-Fälle-Bericht,
  zurückgewiesene Pfadausbrüche und portable Pfade aus einem echten CLI-Worker.
- Eine gezielte Linux-Gegenprobe in WSL verwendet den unveränderten produktiven
  Pfadhelfer: Der alte Pfadzugriff findet 0/10 historische SVGs aus realem Transfer
  und Restbildprüfung, der korrigierte Zugriff findet 10/10 mit korrekten
  SHA-256-Werten. Das vollständige reale Transferinventar und alle seine
  Dateiprüfsummen stimmen unverändert mit dem Manifest überein.
- Syntax- und Whitespace-Prüfung mit der bestehenden CRLF-Konvention bestehen.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_real_scene_transfer_evidence.py tests/test_residual_scene_evidence.py tests/test_mixed_gradient_scene_evidence.py tests/detailtests/test_plan_b_variations.py -q
```

Die vollständige CI-Suite wurde hier nicht wiederholt. In WSL fehlen pytest
und die Bildbibliotheken; dort wurde der produktive Pfadhelfer mit der
Standardbibliothek gegen die gespeicherten Dateien und Prüfsummen geprüft,
keine Rasterabnahme ausgeführt.
