# Testprüfung vom 7. Oktober 2026

## Ergebnis

**2.123 bestanden, 0 fehlgeschlagen, 29 übersprungen** bei insgesamt 2.152 Tests
unter Windows mit Python 3.10.11 und Pytest 8.4.2.

Der abschließende vollständige Lauf umfasst alle drei normalerweise ausgeblendeten
Heavy-Module sowie die zehn reaktivierten Tests. Das zentrale Konverter-Modul
meldet **401/401 bestanden**.
Die 31 gespeicherten zufriedenstellenden Konvertierungen bestehen die Qualitätsbatterie.
Es wurden keine Qualitätsgrenzen abgesenkt und keine fehlgeschlagenen Tests ausgeschlossen.

Die 29 verbleibenden Skips stammen ausschließlich aus
`tests/detailtests/test_local_completion_checks_tool.py`: Diese Integrationstests
benötigen eine POSIX-Shell. Sie wurden auf diesem Windows-Rechner nicht ausgeführt;
ihr Ergebnis ist damit weiterhin unbestätigt.

## Behobene Ursachen

| Bereich | Zuvor rote Fälle | Korrektur |
|---|---:|---|
| Rechteck mit Diagonale und Punkt | 7 | Radius, Punktlage, Rahmen, Diagonale und Verlauf aus dem Raster unabhängig registrieren; mehrere Suchstarts vergleichen. |
| Pfeil-, Diagramm- und Radialkreis-Laufzeitpfad | 5 | Vorhandene, beschreibungsgebundene Rasteranpassungen vor der allgemeinen Ersatzgeometrie aufrufen. |
| Plattformabhängige Testannahmen | 4 | Linux-Reihenfolge ausdrücklich simulieren, tatsächlich erfolgte Importwiederholung prüfen und Pfade als Path-Objekte vergleichen. |

Bei einer parallelen Nachprüfung trat außerdem ein Schreibkonflikt auf:
temporäre Reportordner veränderten die echte Aufgabenliste. Die Zuordnung
akzeptiert jetzt ausschließlich die vorgesehenen Repository-Reportverzeichnisse.
Ein zusätzlicher Test prüft, dass externe Ausgaben vorhandene Aufgaben weder
löschen noch ergänzen und auch ihre ursprünglichen Zeilenenden erhalten.
Der abschließende Gesamtlauf lief allein; Testnebenwirkungen auf die Aufgabenliste
wurden zurückgenommen.

Zusätzlich laufen zehn zuvor übersprungene Tests jetzt tatsächlich:
neun verwenden ihre vorhandenen Bilder auch aus dem Ordner `nonconvertable`,
und ein Schriftbreitentest benötigt den irrtümlich vorausgesetzten Generator nicht.
Seine Testdaten und der ersetzte Methodenname wurden an die aktuelle API angepasst.
Archivierte Bilder werden für Konvertierungstests in ein temporäres Verzeichnis kopiert.

Die ausdrücklich deaktivierte Render-Isolation wird sowohl beim Import als auch
bei der automatischen CLI-Regressionskonfiguration berücksichtigt; neue Tests
sichern dies ab. Die automatische Isolation bleibt ohne ausdrückliche Einstellung aktiv.
Beschriftete Quadrate verwenden ihre spezialisierte Registrierung ohne vorherige
allgemeine Geometriesuche. Doppelte Renderkandidaten der Punktregistrierung werden
innerhalb eines Fits zwischengespeichert.

## Reproduktion

Die vollständige Prüfung wurde mit explizitem direktem Rendering durchgeführt:

```powershell
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m pytest -q -ra
```

Der abschließende Modullauf verwendet dieselben Einstellungen:

```powershell
.venv/Scripts/python.exe -m pytest -q -ra tests/test_image_composite_converter.py
```

Auch `compileall`, CLI-Hilfe und die Image-ID-Hardcoding-Prüfung sind erfolgreich.
Ein normaler Pytest-Aufruf ohne `RUN_HEAVY_CONVERSION_TESTS=1` sammelt nur 1.743 Tests;
er deckt die drei Heavy-Module nicht ab. Die Standardprüfung mit automatischer
Render-Isolation wurde nicht nochmals vollständig ausgeführt.

## Einzelresultate

Die vollständige Liste aller Testnamen, Ergebnisse, Laufzeiten und Skip-Gründe steht
in [test_results.csv](../.tmp/test-audit-2026-10-07/test_results.csv).
Maschinenlesbare Nachweise: [Vollsuite](../.tmp/test-audit-2026-10-07/verified.xml) und
[Zusammenfassung](../.tmp/test-audit-2026-10-07/summary.json).
Die Nachweisdateien liegen im lokalen, von Git ignorierten `.tmp`-Verzeichnis.
