# AC0VR2_AB_M: symmetrische Linien auf grauem Verlauf

Die Benutzermeldung vom 29. Oktober 2026 ist mit dem Original-JPEG unter dem
neutralen Namen `UPLOAD` und der unveränderten Beschreibung reproduziert:
Das Suchbudget von 120/240 Sekunden endet nach 1,032 Sekunden mit null
Kandidaten, ohne bestandene Qualität. Der allgemeine Panel-Fallback entfernt
die zwei schrägen Linien und die beiden kurzen rechten Striche.

Der neue Suchweg rekonstruiert diese vier beobachteten Linien, den Rahmen und
einen nativen vertikalen Verlauf mit höchstens neun Farbstopps. Er nutzt weder
Dateinamen noch Sample-SVGs. Fehlende Striche, asymmetrische Linien, zusätzliche
dunkle Objekte und nicht graue Motive werden vor der Registrierung abgelehnt.
Das bestehende adaptive Suchbudget begrenzt die Registrierung; die bestehenden
Qualitätsgrenzen bleiben unverändert.

Die beiden Kataloge beschreiben jetzt die tatsächliche Geometrie. Zusätzlich
verwendet die GUI-Nachprüfung denselben Verlauf-Renderer wie die Konvertierung,
mit anschliessender Rückwandlung von BGR nach RGB. Der bisher direkt verwendete
PyMuPDF-Renderer malte native SVG-Verläufe schwarz und meldete dadurch auch
korrekte SVGs als fehlerhaft. Die Oberfläche bezeichnet die Zeit nun ausdrücklich
als Suchbudget mit Obergrenze und erklärt mögliche frühere Abschlüsse.

Prüfung:

- Original-JPEG mit Benutzerbeschreibung und neutralem Uploadnamen: zwei frische
  CLI-Läufe mit Seeds 273 und 1947; inklusive GUI-Prüfung des gespeicherten SVGs.
- Original-JPEG mit neuer Katalogbeschreibung: bestandene Qualität nach 0,688
  Suchsekunden und einem geprüften Kandidaten.
- Unabhängiges librsvg-Rendering: MSE 0,000710, Vordergrund-IoU 0,9575 und
  Kantendeckung 0,9474; alle bestehenden Grenzen bestanden.
- Synthetische andere Geometrie in drei Auflösungen, Gegenbeispiele,
  abgelaufenes Zeitbudget, Renderfehler und RGB-Farbverlauf sind durch Tests
  abgedeckt. Die kompakte Vorher-/Nachher-Evidenz steht in `summary.json`.

Reproduktion aus dem Projektverzeichnis:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_paired_line_panel_runtime.py tests/test_image_converter_sample.py tests/test_image_converter_gui.py tests/test_adaptive_conversion_search.py tests/test_axial_panel_runtime.py tests/test_chevron_panel_runtime.py tests/test_valley_panel_runtime.py -q
```

Die erzeugten SVGs, PNGs und vollständigen CLI-Verzeichnisse sind lokale
Ausgaben. Die eingebauten Regressionstests rekonstruieren die Prüffälle frisch.
