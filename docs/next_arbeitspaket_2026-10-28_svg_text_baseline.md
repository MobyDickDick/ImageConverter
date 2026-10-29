# SVG-TEXT-BASELINE-01: explizite alphabetische Baseline und echte Glyphenprüfung

Der [reproduzierte AC0721-Fehler](known_issue_2026-10-28_svg_text_baseline.md)
ist für neue Ausgaben und die sechs AC0721-Archivpaare behoben.
Die bestehende alphabetische Koordinatenkonvention wird in allen sieben
nativen Textausgaben explizit als `dominant-baseline="alphabetic"` ausgegeben:
Quadratbeschriftungen, Ventilbeschriftungen, allgemeine `TextGlyph`-Elemente
sowie CO, die tiefgestellte 2, VOC und rF im Badge-Emitter.
Die Registrierung, Schriftgrößen und Textkoordinaten bleiben erhalten.

## CI-Nachtrag: Linux-Schriftrückfall und Buchstabendeckung

Der erste Linux-CI-Lauf von PR #2073 widerlegt eine plattformübergreifende
Abnahme der ursprünglichen Ausgabe: Bei AC0721_M bestehen beide
Glyphengrenzenprüfungen, aber das globale Foreground-IoU-Gate scheitert.
Arial wird unter Ubuntu durch Liberation Sans ersetzt. Der Fehler ist mit
unveränderten Originalpixeln lokal unter Ubuntu 26.04 reproduziert.
Ein expliziter Liberation-Vergleich unter Windows ergibt ebenfalls
0,814516 IoU bei unveränderter Mindestgrenze 0,85.

Die allgemeine Quadratbeschriftungsregistrierung prüft jetzt zusätzlich
fünf dünne Textkonturen von 1/32 bis 1/4 Originalpixel. Eine Kontur in der
Textfarbe wird nur übernommen, wenn der bisherige Registrierungsfehler und
der quadratische Pixelfehler sinken, die globale Vordergrunddeckung nicht
abnimmt, die lokale Buchstabendeckung steigt und das Kantengate 0,72 besteht.
Das erhält die beobachtete Geometrie und verfeinert die diskrete Normal-/Fett-
Wahl kontinuierlich. Kein unabhängiger Renderer im Runtime-Fit, keine
Bildkennung und keine gelockerte Abnahmegrenze. Die Kantenausrichtung kann
dabei gegenüber der unmittelbar vorherigen Ausgabe leicht sinken; sie wird
nicht als durchgehend monotone Verbesserung aller Einzelmetriken dargestellt.

AC0721_M erreicht mit einer aus dem Raster gewählten Kontur von 0,125 Pixeln
im expliziten Liberation-Vergleich 0,911290 IoU. Drei AC0721-Archiv-SVGs
erhalten die geprüfte Verfeinerung samt aktuellen Messwerten und Hashes.
Die Migration bleibt hashgebunden; historische Quellen und Berichte bleiben
erhalten. Die nachfolgenden Angaben zur Pixelgleichheit dokumentieren die
ursprüngliche reine Baselineänderung, nicht diese spätere Deckungskorrektur.

Die Regression prüft Systemschriften und Liberation getrennt sowie den
reproduzierten negativen Ausgangsfall. Vergleiche mit historischen Vektoren
erhalten die gesamte bisherige Geometrie; nur die zusätzliche dünne
Textkontur ist erlaubt und muss Pixelabweichung und Vordergrunddeckung
verbessern. Zusätzlich wurde die Bildkennung aus einem GUI-Kommentar
entfernt, an der drei andere CI-Jobs scheiterten. Die Scannerregeln bleiben
unverändert. [Kompakte Folgeevidenz](../artifacts/evaluation/svg_text_coverage_v1/README.md).

## Tatsächliche Position statt Textanker

Der Beschriftungsprüfer ermittelt die sichtbaren Glyphengrenzen durch
Differenz zum selben SVG mit unsichtbarem Textelement, bei achtfacher
Auflösung. Die Glyphen müssen innerhalb der inneren Quadratkontur liegen.
Zusätzlich vergleicht `measure()` die Grenzen mit der beobachteten
Kontrastkomponente im ursprünglichen Raster. Maximal 1,5 Originalpixel
Unsicherheit sind zulässig; vorhandene globale Qualitätsgrenzen bleiben
unverändert. Ein Kleinbuchstabe mit Unterlänge muss nicht geometrisch
zentriert sein. Seine tatsächliche Position ergibt sich aus dem Original.

Die unabhängige Prüfung verwendet das installierte `rsvg-convert`, lokal
librsvg 2.62.3. Sie verwendet dieselben unveränderten Plan-B-Grenzen wie
die bisherige Pixelprüfung und zusätzlich die Glyphengrenzen. Ein fehlender
Renderer ersetzt diese Prüfung nicht durch MuPDF. Die eigene CI-Aufgabe
installiert librsvg und eine serifenlose Schrift und verlangt den Renderer
vor den Tests. CI selbst wurde in dieser Sitzung nicht ausgeführt.

## Reale CLI-Abnahme und offene Bestandsgrenzen

Die sechs unveränderten Originalraster von AC0721 (rosa und grau, L/M/S)
wurden über `tools.run_labeled_description_recheck` mit neutralen Namen
neu konvertiert. Beide regulären Gates bestehen **6/6**; die unabhängige
librsvg-Pixelprüfung samt Glyphenprüfung besteht ebenfalls **6/6**.
Die obere T-Kante bei AC0721_1_L liegt in MuPDF bei 9,75 und in librsvg bei
10,0; zuvor lag sie in librsvg bei 15,5 Originalpixeln. Negativkontrollen
verwerfen den alten Baselineversatz sowie ein zusätzlich verschobenes T
mit weiterhin gültigem Anker und unverändertem Buchstaben.

Die separate strengere **MuPDF-Plan-B-Prüfung bleibt 5/6**: AC0721_L
unterschreitet unverändert ihre Foreground-IoU-Grenze. Das ist die bereits
offene Aufgabe AC0721-PB-GREY. Die Baselinekorrektur ändert keines der
Produktionspixel und beansprucht keine Lösung dieses anderen Fehlers.

Vor der Archivänderung wurden alle **60** archivierten Text-SVGs untersucht.
**39** enthielten die problematische `middle`-Angabe; die Baselinekorrektur
erzeugt bei allen 60 bytegleiche MuPDF-Raster. Unter den unabhängigen
strengen Pixelgates bestehen zuvor **17/60**, mit Baselinekorrektur **34/60**.
Eine Baselineänderung allein ist somit keine allgemeine Archivabnahme.
Bei neun bereits zuvor gescheiterten AC08-Ausgaben steigt der unabhängige
MSE sogar; die vollständigen Fehler bleiben im Inventar sichtbar.

Nur die unabhängig abgenommenen **sechs AC0721-Archiv-SVGs** wurden geändert,
einschließlich ihrer Hashes im Archivindex. Die übrigen 373 Paare und alle
Originalbilder bleiben unverändert; die Katalogzahl bleibt 379. Historische
CLI-SVGs und Abnahmeberichte behalten ihre ursprünglichen Bytes.
`refresh_satisfactory_archive` spielt genau die sechs hashgebundenen,
geprüften Korrekturen erneut ein. Andere SVGs mit absichtlich gesetzter
`middle`-Baseline werden nicht verändert. Die verbleibenden 33 historischen
Baselineangaben und 26 negativen unabhängigen Kandidatenprüfungen stehen
unter ARCHIVE-TEXT-REVALIDATION; diese Mengen überschneiden sich.

## Reproduktion

Der abschließende betroffene Regressionsblock besteht **341 Tests**, eine
regulär abgeschaltete vollständige Archiv-Neukonvertierung wird übersprungen,
Exit 0. Enthalten sind die neue Baseline-/Archivprüfung, T/P-/Links-/Rechts-
Quadrate, beschriftete Kreise, Kurzlabels, Badge-Emitter/-Runtime sowie
Geometry-IR-Helfer und Wahrnehmungs-Roundtrip. Das Kernprofil besteht 42/42,
Exit 0. Die exakten Befehle stehen in `checks.json`.

Neue Zielverzeichnisse verwenden:

```powershell
.venv/Scripts/python.exe -m tools.run_labeled_description_recheck artifacts/evaluation/labeled_t_square_recheck_v1/manifest.json --output-dir .tmp/svg-text-replay
.venv/Scripts/python.exe -m tools.evaluate_svg_text_baseline --manifest .tmp/svg-text-replay/manifest.json --output-dir .tmp/svg-text-independent-replay
.venv/Scripts/python.exe -m pytest tests/test_svg_text_baseline.py tests/test_satisfactory_archive.py -q
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Der erste Aufruf besteht die beiden regulären Gates, der zweite verlangt
6/6 unabhängige Abnahmen und berichtet die separate interne Plan-B-Zahl.
`--rsvg-convert PFAD` wählt bei Bedarf das ausführbare Prüfprogramm.
Ohne `--manifest` inventarisiert das Werkzeug das gegenwärtige Archiv;
nach der Migration sind darin sechs der ursprünglichen 39 Angaben bereits
korrigiert. Zur exakten Wiederholung des ursprünglichen 60er-Vergleichs
die Archivdateien des Ausgangsstands verwenden. Originalhashes, beide
Messungen und Glyphengrenzen sind in der
[kompakten Evidenz](../artifacts/evaluation/svg_text_baseline_v1/README.md) gespeichert.

## Sitzungslog

- Getestet: reale CLI, unabhängiges Rendering, Archivintegrität/-Wiederholung, Text-/Geometrie-/Badge-Regression und Kernprofil.
- Ergebnis: reguläre CLI 6/6, unabhängige CLI 6/6, interne Plan-B-Prüfung unverändert 5/6; Regression 341 bestanden/1 übersprungen und Kernprofil 42/42, Exit 0.
- Grenzen: weitere historische Text-SVGs benötigen individuelle Prüfung; keine vollständige Archiv-Neukonvertierung oder Standardsuite.
- Nächster Schritt: übergeordnetes SEARCH-STRUCTURE-01 gemäß Prioritätenliste; dokumentierte Archiv- und IoU-Restaufgaben bleiben offen.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_svg_text_baseline.py -q`.
