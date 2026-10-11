# Katalog-CI: MuPDF-Prozessabsturz (2026-10-11)

Im [fehlgeschlagenen Job von PR #1928](https://github.com/MobyDickDick/ImageConverter/actions/runs/38160644259/job/114532641027?pr=1928)
beendet `AC0836_L` den Konverter während der Textoptimierung in der zweiten
Qualitätsrunde: `MuPDF error: exception stack overflow!`, Rückgabecode `-11`.
222 der 223 Bildprozesse enden erfolgreich. Der getestete PR-Head ist
`2eb3dbd114cf3bc5b06230d6aa3b4e4a6df855c0`, der Merge-Commit
`28eb37d93d9417cbc94a03e8cc3e45681a56a9d1`.

Der Einzelbild-Katalogrunner aktivierte bisher keine Renderisolation. Zudem
versuchte der normale CLI-Pfad nach einem fehlgeschlagenen isolierten Render
MuPDF erneut im Konverterprozess. Python-Ausnahmebehandlung kann einen nativen
Prozessabsturz nicht auffangen. Eine genaue interne MuPDF-Fehlerursache wird
aus dem Log nicht abgeleitet.

## Änderung

- Der Katalogrunner aktiviert Renderisolation und wiederverwendbare
  Renderprozesse standardmäßig. Explizite Umgebungswerte bleiben gültig.
- Jeder Renderprozess besitzt seine eigenen MuPDF-Dokumente und wird nach
  höchstens 64 Anfragen erneuert. So bleiben Optimierungsproben bezahlbar,
  während angesammelter nativer Zustand begrenzt wird. MuPDF läuft im
  Hauptthread des Kindprozesses; nur Pixeldaten gehen zurück.
- Nach einem Prozessabsturz wird die Anfrage innerhalb desselben Zeitbudgets
  einmal in einem frischen Kindprozess wiederholt. Wiederholte Fehler bleiben
  sichtbar und liefern kein Raster. Zeitüberschreitungen beenden den Worker
  und werden als `timeout` erfasst; die nächste Anfrage startet frisch.
- Ein fehlgeschlagener isolierter Render ruft im normalen CLI niemals den
  nativen Renderer im Konverterprozess auf. Der bisherige Einzelprozesspfad
  bleibt für isolierte Aufrufe ohne Worker-Option verfügbar.

Die Prozessgrenze des Katalogrunners, Qualitätsgrenzen, Beschreibungen und
Bildquellen werden durch diese Korrektur nicht angepasst. Kein Bild wird
ausgeschlossen und kein Fehler in `completed` umetikettiert. Renderfehler
werden weiterhin an die vorhandene Optimierungstelemetrie gemeldet.

Die [PyMuPDF-Dokumentation](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html)
beschreibt die Verwendung eigener Renderprozesse. Das ist die Grundlage der
Prozessisolation, kein Beleg für eine bestimmte interne Ursache dieses Absturzes.

## Lokale Abnahme

Mit Windows, CPython 3.10.11 und denselben Bibliotheksversionen wie im CI
(PyMuPDF 1.26.7, NumPy 2.2.6, OpenCV 4.14.0) reproduziert der ungeschützte
Katalogaufruf den MuPDF-Stacküberlauf. Der Konverter endet mit Windows-Code
`3221225512`, der Runner mit Exit 1, nach 7,890 Sekunden.

Mit dem neuen Standard enden zwei frische, vollständige Katalogaufrufe für
dasselbe Bild und denselben Originalkatalog mit Exit 0 nach 17,312 bzw.
18,063 Sekunden. Beide erzeugen dieselbe SVG (SHA-256
`2ad4cb321fc1089cc825e7060f866ce4f7db9efc84f69b4d2ef5e8753dcde0ca`).
Die Optimierungstelemetrie meldet jeweils null Renderfehler und null Timeouts.
Das 180-Sekunden-Budget wird eingehalten. Das resultierende Mean-Delta² von
7198,080078 ist ausdrücklich keine Qualitätsabnahme des Bildes.

Der Vergleich umfasst außerdem `AC0800_M`, `AC0836_M`, `AC0836_S` und
`SE0081` mit ausgeschalteter Ausgabevariation (`TINY_ICC_OUTPUT_VARIATION=0`,
`PYTHONHASHSEED=0`). Die Vorher-/Nachher-Ergebnisse werden im Nachweisordner
festgehalten: alle vier SVGs und sämtliche Bestenlistenmetriken sind identisch.
Zufällige Standardausgaben werden nicht als Bestandsschutz
verwendet. Ein realer Rendervergleich mit Text und Kreis prüft zusätzlich
pixelgenaue Gleichheit über die Worker-Erneuerung hinweg.

Die fokussierte Suite besteht mit 54 Tests. Sie enthält echte Prozessabbrüche,
einmalige Wiederherstellung, wiederholte Fehler, Timeout und nächste Anfrage,
periodische Erneuerung, Pixelgleichheit, CLI-Fallbackschutz, Runner-Konfiguration
und bestehende Verlaufskompatibilität. Syntaxprüfung, CLI-Hilfe,
Runtime-ID-Nullprüfung und Whitespaceprüfung bestehen.
Der zusätzliche AC08-Regressions-Smoke besteht mit expliziter Isolation und
Worker-Wiederverwendung (1 Test, 1,58 Sekunden). Sein erster Aufruf im
Sandbox-Tempverzeichnis scheiterte beim atomaren Dateiersetzen mit
`WinError 5`; derselbe Test mit `--basetemp .tmp/mupdf-smoke` besteht.
Beide Logs bleiben als Nachweis erhalten.

Der vollständige Standardtestlauf besteht mit **2365 Tests, 30 bestehenden
Skips und null Fehlern** in 3900.52 Sekunden. Die Standardprüfung verwendet
wie im bisherigen lokalen Abschlussprofil `IMAGE_CONVERTER_ISOLATE_SVG_RENDER=0`;
die neuen Prozessisolationstests starten ihre Worker trotzdem explizit.
Eine erneute Ubuntu-CI-Abnahme für den korrigierten Commit
steht noch aus. Lokale Einzellaufnachweise ersetzen keinen vollständigen
223-Bilder-Shard oder Archiv-Recheck.

## Verbleibende Qualitätsfehler

`AC0201_L`, `AC0204`, `AC0204_1`, `AC0204_2` und `AR0103` melden semantische
Abweichungen. `DLG0016.JPG`, `GE1302_M.jpg` und `GE9910_W.jpg` werden als
Embedded-Raster-SVG in `batch_failure_summary.csv` als fehlerhaft geführt,
obwohl der CLI-Prozess Exit 0 liefert. Diese drei Fälle sind daher keine
erfolgreichen Bildkonvertierungen. Die Raster-SVG-Sperre bleibt bestehen.
Auch die Beschreibung und Pixelqualität von `AC0836_L` benötigen einen
eigenen Bild-/Textvergleich. Alle Fälle sind unter `CATALOG-SOURCE-REVIEW`
in `docs/open_tasks.md` aufgenommen.

## Reproduktion

Ein temporäres Eingabeverzeichnis mit einer unveränderten Kopie von
`AC0836_L.jpg` verwenden und für jeden Lauf ein neues Ausgabeverzeichnis wählen:

```powershell
# Neuer Runnerstandard: beide Variablen dürfen nicht explizit deaktiviert sein.
.venv/Scripts/python.exe tools/run_catalog_conversion.py --input-dir .tmp/crash-input --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir .tmp/crash-fixed --timeout-seconds 180 --iterations 64 --no-resume
# Negativkontrolle ausschließlich im beaufsichtigten Bildprozess:
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0'
.venv/Scripts/python.exe tools/run_catalog_conversion.py --input-dir .tmp/crash-input --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir .tmp/crash-native --timeout-seconds 180 --iterations 64 --no-resume
.venv/Scripts/python.exe -m pytest -q tests/detailtests/test_render_worker.py tests/detailtests/test_render_dispatch_helpers.py tests/test_run_catalog_conversion.py tests/detailtests/test_svg_render_timeout_defaults.py tests/detailtests/test_rendering_gradient_compatibility.py
```

Quellhashes, CSVs, Logs, Vergleich und Testnachweise liegen unter
`artifacts/evaluation/catalog_render_crash_fix_2026-10-11/`.
