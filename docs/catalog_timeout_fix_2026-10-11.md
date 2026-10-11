# Katalog-CI: Timeout-Budget und Wiederaufnahme (2026-10-11)

## Verifizierter Fehler

Im [Job von PR #1916](https://github.com/MobyDickDick/ImageConverter/actions/runs/38119789330/job/114411968197?pr=1916)
endeten zwei von 218 Konvertierungen mit `process_timeout`, Rückgabecode `124`:
`DLG0001` und `GE0000` nach jeweils 75 Sekunden. Die übrigen 216 Prozesse
beendeten sich erfolgreich. Getesteter Merge-Commit:
`0ffc89717a6a1fe9f709e6627b7180ed3bd91522`, PR-Head:
`e458af3b333bf21f3bd815459ce04fa69e205655`.

Der Workflow übergab 60 Sekunden an `ICC_CONVERSION_TIMEOUT_SEC`. Der
Katalogrunner beendet den gesamten Kindprozess nach Budget plus 15 Sekunden,
also bisher nach 75 Sekunden. Das Konverterbudget gilt je überwachtem
Konvertierungsschritt; die zusätzliche Prozessgrenze begrenzt den gesamten
Aufruf einschließlich Start, Qualitätsrunden und Ausgabe.

## Änderung

- Der Workflow verwendet 180 Sekunden Budget und damit 195 Sekunden als harte
  Prozessgrenze. Das lokale CLI-Default bleibt bei 60 Sekunden.
- Wiederaufnahme überspringt nur CSV-Zeilen mit `status=completed` und
  `returncode=0`. Timeout- und andere Fehler werden erneut versucht. Bisher
  wurden auch diese Fehler als erledigt behandelt.
- `PYTHONUNBUFFERED=1` erhält die bereits geschriebenen Konverterdiagnosen in
  umgeleiteten Logs auch dann, wenn die Prozessgrenze den Aufruf beendet.
- Ein Timeout bleibt ein Fehler mit Code 124; der Shard setzt die Verarbeitung
  mit dem nächsten Bild fort und endet weiterhin mit Code 1 bei Fehlern.

## Lokale Reproduktion und Abnahme

Mit dem bisherigen Runner und explizitem 90-Sekunden-Budget beendeten beide
unveränderten Eingaben den Prozess erfolgreich: `DLG0001` in 83,828 Sekunden,
`GE0000` in 84,719 Sekunden. Die Eingaben und ihre XML-Einträge wurden in ein
temporäres Verzeichnis kopiert; die Katalogquellen bleiben unverändert.

Spätere Windows-Läufe schwanken stark und beenden beide Eingaben mit
Prozess-Timeouts:

| Budget | Prozessgrenze | DLG0001 | GE0000 |
| --- | --- | --- | --- |
| 90 s, ohne parallele Testsuite | 105 s | Timeout, 105,015 s | Timeout, 105,032 s |
| 120 s, ohne parallele Testsuite | 135 s | Timeout, 135,015 s | Timeout, 135,032 s |
| 180 s, mit Stack-Stichproben | 195 s | Timeout, 195,031 s | Timeout, 232,735 s |

Auch parallele Läufe erzeugten Timeouts; ein weiterer Timeout wurde erst nach
1031 Sekunden registriert. Die stark verzögerten lokalen Rückgaben sind kein
verlässlicher Rechenzeitbeleg. Stack-Stichproben zeigen den Fallback in der
Geometrie-IR-Optimierung und wiederholtes PyMuPDF-Rendering von SVG-Verläufen,
einschließlich PNG-Kodierung in `_expand_bezier_linear_gradients_for_fitz`.

Der Konverter verwendet auf POSIX-Systemen `SIGALRM`, während sein
Windows-Watchdog erst nach Rückkehr des überwachten Schritts prüft. Der
Katalogrunner begrenzt zusätzlich den gesamten Prozess. Die entscheidende
Abnahme dieses CI-Fixes erfolgt daher im Ubuntu-Workflow von
[PR #1916](https://github.com/MobyDickDick/ImageConverter/pull/1916/checks).
Die Windows-Timeouts werden ausdrücklich nicht als erfolgreiche Abnahme gezählt.
Laufzeiten hängen von der Rechnerlast ab; ein erfolgreicher lokaler Aufruf
ersetzt keinen erneuten GitHub-Lauf mit dem neuen Commit.

Die fokussierte Runner-/Einzelbildsuite besteht mit 14 Tests. Sie prüft
Budgetweitergabe, Timeout-Fehler und Fortsetzung sowie Wiederaufnahme nach
Timeout, Konverterfehler und widersprüchlicher Status-/Rückgabecode-Kombination.
Syntaxprüfung, CLI-Hilfe und Runtime-ID-Nullprüfung bestehen.

Der vollständige Standardtestlauf besteht mit **2.227 Tests, 30 bestehenden
Profil-/Windows-Skips und null Fehlern**. Die lokal gemessene Gesamtdauer beträgt
3.983,61 Sekunden einschließlich der beobachteten Zeitverzögerungen.

## Qualitätsbefunde

Die im CI-Log gemeldeten semantischen Abweichungen für `AC0201_2.jpg`,
`AR0101.jpg`, `GE1310_S.jpg` und `SE0113.jpg` werden durch das Zeitbudget nicht
behoben. Auch `DLG0001.JPG` und `GE0000.JPG` benötigen eine Quellenprüfung:
Die Rasterbilder sind nahezu leer (1600 × 1200 Pixel, Wertebereich 245–255),
während ihre XML-Texte ein Heizelement mit Plus-/Minuszeichen beschreiben.

`completed` beschreibt einen erfolgreichen Prozessabschluss und ist keine
Qualitätsabnahme. Beschreibungen, Konvertierungslogik und Qualitätsgrenzen
werden mit diesem CI-Fix nicht geändert.

## Reproduktionsbefehle

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_run_catalog_conversion.py tests/test_convert_one_image.py --basetemp .tmp/catalog-timeout-focused
.venv/Scripts/python.exe -m compileall -q src tests tools
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/catalog-timeout-full
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
.venv/Scripts/python.exe -m tools.run_catalog_conversion --input-dir .tmp/catalog-timeout-fixed-inputs --descriptions-path .tmp/catalog-timeout-fixed-inputs/descriptions.xml --output-dir .tmp/catalog-timeout-reproduction --timeout-seconds 180
```

Das temporäre Eingabeverzeichnis enthält ausschließlich Kopien der beiden
JPG-Dateien und eine XML-Datei mit ihren unveränderten Beschreibungseinträgen.
Für eine frische Abnahme ein neues Ausgabeverzeichnis verwenden.

Quellhashes, CSV-Ergebnisse sämtlicher lokaler Versuche und Testnachweise:
[validation.json](../artifacts/evaluation/catalog_timeout_fix_2026-10-11/validation.json).
Der [CI-Logauszug](../artifacts/evaluation/catalog_timeout_fix_2026-10-11/ci_excerpt.log)
enthält die beiden ursprünglichen Prozessfehler und die vier Semantikmeldungen.
