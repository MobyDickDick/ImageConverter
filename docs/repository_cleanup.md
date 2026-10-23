# Bereinigung und Ablageregeln

Stand: 23. Oktober 2026.

## Ergebnis

Von 28.424 ursprünglich versionierten Dateien wurden 8.040 entbehrliche
Dateien entfernt: 129.092.761 Bytes, ungefähr 123 MiB. Weitere 806 Dateien
wurden umgeordnet. Die Löschungen und Verschiebungen sind als Änderungen
im Arbeitsbaum sichtbar; die Git-Historie wurde nicht umgeschrieben.

| Entfernter Bestand | Dateien | Begründung |
|---|---:|---|
| Konvertierte PNGs und kommentierte Differenzbilder im Katalog-Ausgabeordner | 1.918 | Erzeugte Vorschauen; keine Projekt-Testreferenzen |
| Wiederholte SVG-Ausgaben früherer Erfolgsarchiv-Prüfungen | 2.905 | Historische Laufkopien; das eigentliche Erfolgsarchiv bleibt bestehen |
| Rohdaten der Komponentenversuche | 2.680 | Bereits von Git ignorierte Ausgaben, Telemetrie, Laufberichte und Versuchskopien von Modulen |
| Vorschau- und Differenzbilder in Versuchsläufen | 46 | Erzeugte Diagnoseausgaben |
| Alte Ausgaben unter `src/artifacts` | 488 | Überholte Berichte, Logs und Renderausgaben |
| Erzeugte Annotationsberichte | 2 | Mit dem Annotationsmodus neu erzeugbar |
| Einzelne SVG im Projektstamm | 1 | Ohne Projektverweis und außerhalb der Eingabe-/Testverzeichnisse |

`src/artifacts` wurde vollständig entfernt. Seine 53 noch verwendeten
SVG-Referenzen liegen bytegleich unter
[`artifacts/regression_baseline/legacy_ac08/`](../artifacts/regression_baseline/legacy_ac08/README.md).
Die Qualitätsprüfung und die Regressionsbatterie verwenden diesen Pfad.
Auswertungswerkzeuge lesen aktuelle Laufberichte aus
`artifacts/converted_images/reports`.

## Dokumentation und Verlauf

Die [Dokumentationsübersicht](README.md) führt zu Bedienung, Architektur,
Konzepten und Planung. Der frühere vollständige Index sowie 748 einzelne
Arbeitspaket-, Lauf-, Status- und Merge-Berichte liegen unter
[`docs/history/`](history/README.md). Dokumentationsinhalte wurden nicht
gelöscht. Relative Links und Quellcodeverweise wurden an die neue Ablage
angepasst.

Der frühere Testkonsolenauszug `tests.txt` liegt unter
[`history/logs/tests_undated.log`](history/logs/tests_undated.log), die
Arbeitsnotiz `nextPrompt.txt` unter
[`history/notes/nextPrompt.txt`](history/notes/nextPrompt.txt).
Die Plan-B-Grundsätze sind jetzt [reguläre Dokumentation](plan_b_principles.md).
Das ältere UML-Bild liegt bei den [historischen Abbildungen](history/images/conversion_search_legacy.png).

## Behaltene Daten und Grenzen

- Eingaberaster und Beschreibungen bleiben erhalten.
- `artifacts/satisfactory_conversions/`, Regressions-Baselines und Test-Fixtures
  bleiben erhalten. Sie sind ausdrücklich benötigte Referenzen.
- Die katalogweiten SVGs, Bestlist-Snapshots, Validierungslogs und das
  Differenzbildinventar bleiben erhalten: Qualitätswerkzeuge und Tests
  verwenden diese Bestände auch indirekt über Dateinamen und Verzeichnisse.
- Die übrigen Szenenmanifeste, Eingaben, Referenz-SVGs, Abnahmeberichte und
  versiegelten Szenenbelege bleiben erhalten. Frühere Rohdaten von
  Komponentenversuchen und Archivwiederholungen sind dagegen bereinigt;
  ihre kompakten Berichte dokumentieren historische Ergebnisse und erlauben
  ohne einen neuen Lauf keine vollständige Nachprüfung gelöschter Rohdaten.
- Alle 204 Python-Quelldateien haben Projektverweise. Ein fehlender Import
  allein wäre zudem kein Löschbeweis für ein separat startbares Werkzeug.
  Deshalb wurde kein Programmcode pauschal entfernt.
- Die aktive Python-Umgebung und die verwendete Vendor-Unterstützung bleiben
  erhalten. Die parallel entstandenen Strukturversuche wurden nicht bereinigt.

## Künftige Ablage

- Programmcode: `src/`; keine Laufdaten oder Ausgaben darunter.
- Fachliche Konfiguration: `config/`.
- Benötigte Testdaten: `tests/fixtures/` und `artifacts/regression_baseline/`.
- Abgenommene Paare: `artifacts/satisfactory_conversions/`.
- Bedienung und Architektur: `docs/`.
- Arbeitspakete, Laufberichte und Statusaufnahmen: `docs/history/`.
- Reine Dokumentationslogs: `docs/history/logs/`.
- Neue lokale Versuche: bevorzugt `.tmp/<versuch>/` oder ein ausdrücklich
  gewählter Ausgabeordner. Nur benötigte Eingaben und kompakte Nachweise
  gezielt versionieren.

Die ergänzten `.gitignore`-Regeln verhindern, dass die bereinigten
Vorschauverzeichnisse, Archivkopien und Ausgaben unter `src/` erneut
versehentlich versioniert werden.

## Prüfung der Bereinigung

- `core-green`: 42 Tests bestanden, vor und nach der Bereinigung.
- Qualitätsprüfung, Erfolgsarchiv, Komponenten, Regressionshilfen,
  Abschlussverarbeitung und Gradiententestreferenzen: 114 Tests bestanden,
  ein absichtlich deaktivierter vollständiger Archiv-Konvertierungslauf übersprungen.
- Versiegelte Belege der gemischten, realen Übertragungs- und Restbildszenen:
  29 Tests bestanden.
- Der bestehende Test der Arbeitspaketverweise in `open_tasks.md` besteht
  auch mit den verschobenen Berichten. Insgesamt bestehen 186 unterschiedliche
  gezielte Tests; vier Sparse-Checkout-Tests wurden nach Anpassung ihrer
  Prüfdatei zusätzlich erfolgreich wiederholt.
- Alle 53 verschobenen AC08-SVGs sind bytegleich mit dem vorherigen Git-Stand.
  Das erfolgreiche Paararchiv besteht seine Datei- und Beschreibungsprüfungen.
- Keine neuen fehlenden Ziele relativer Markdown-Links gegenüber dem
  Ausgangszustand. Bereits vorher fehlende historische Ziele wurden nicht
  pauschal rekonstruiert.
- Python-Kompilierung von `src`, `tools` und `tests` sowie CLI-Aufruf mit
  `--help` erfolgreich.

Die vollständige lang laufende Rekonvertierung aller Katalog- und Archivbilder
war nicht Teil dieser Ablagebereinigung. Der erste Teststart im umgeleiteten
Windows-Systemtemp scheiterte an Dateiumbenennungsrechten; mit einem
Testtemp-Verzeichnis im Projekt bestanden die Tests.
