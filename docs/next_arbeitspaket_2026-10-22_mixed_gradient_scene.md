# Gemischte Verlaufsszenen: realer Fehlversuch und anschließende Entwicklung

Begrenzter Entwicklungsschritt **GENERAL-SCENE-MIXED-07** innerhalb der offenen
Aufgabe **GENERAL-SCENE-REAL-05**. Ausgangsstand `26cbde874`, Branch
`codex/concept-audit-real-scenes-2026-10-22`.

## Ergebnis

Der gemeinsame Szeneneinstieg rekonstruiert jetzt eine Kreisfläche mit
horizontalem oder vertikalem Zweipunktverlauf und ein bis zwei getrennte,
einfarbige Rechtecke innerhalb des Kreises. Optionale helle Konturen gehören
zum Modell. Beide Objektzahlen verwenden dieselbe Registrierung; weder eine
Symbolkennung noch eine gespeicherte Familienvorlage bestimmt die Ausgabe.

| Prüfung | Ergebnis |
| --- | ---: |
| Originale GE0026/GE0027, unveränderter Ausgangsstand | 0/2 |
| Erster vorab eingefrorener realer Übertragungsversuch | 0/2 |
| Dieselben Originale nach anschließender Entwicklung | 2/2 |
| Dieselben Originale unter nochmals anderen neutralen Namen | 2/2, SVGs bytegleich |
| Synthetischer Entwicklungssatz, endgültiger Code | 11/12; ein Budgetabbruch |
| Nach letzter Runtime-Änderung erzeugte synthetische Szenen, Seed 983127 | 12/12 |

Die zwei Entwicklungsoriginale bestehen die unabhängigen nativen Objekt- und
Regionsprüfungen, die strengen Pixel-/Komplexitätsgates sowie beide regulären
Zufriedenheitsgates ohne Pflichtmetrikregression. Die Konvertierungsworker
erhalten nur Raster und Beschreibung, mit gesperrten Referenz-SVG-Zugriffen,
Seed 17, 64 angeforderten Iterationen und fünf Sekunden festem Bildbudget.

**Dies schließt GENERAL-SCENE-REAL-05 nicht ab.** Nach dem ersten negativen
Übertragungsversuch wurden beide Originale bewusst zur Entwicklung freigegeben.
Die anschließende Verbesserung ist deshalb keine unabhängige Abnahme zweier
neuer realer Familien. Die Marker wurden vom implementierenden Agenten anhand
vergrößerter Originalraster gesetzt, ohne Detektor-/SVG-Vorgaben; es gab keinen
unabhängigen menschlichen Annotationsaudit. An den eingefrorenen Objektboxen,
Beschreibungen und Qualitätsgrenzen wurde nach den Ergebnissen nichts geändert.

Die 28 echten CLI-Versuche des endgültigen Codes bestehen zusammen mit 27/28:
23/24 synthetisch und 4/4 auf den beiden inzwischen bekannten Realoriginalen
einschließlich Umbenennung. Der Budgetabbruch bleibt im Nenner. Seeds,
Umbenennungen und wiederholte Originale sind keine zusätzlichen Familien.
Die frühere Diagnosephase mit weiteren Fehlschlägen steht getrennt und
vollständig in `trial-summary.json`; sie wird nicht zur finalen Erfolgsquote
umetikettiert. Der bestehende gemeinsame CLI-Verifizierer beendet den
betroffenen Entwicklungslauf zusätzlich mit `Missing or ambiguous runtime row`,
weil der abgefangene Budgetabbruch keine normale Ergebniszeile erzeugt.
Bericht, Zeitspur und `batch_failure_summary.csv` bleiben lokal erhalten.

## Allgemeine Korrekturen

Ein großer zentraler Vordergrund kann den robusten Farbfit des Hintergrunds
stören. Die initiale Verlaufsschätzung verwendet deshalb zunächst das sichtbare
äußere Innenband des Kreises. Abweichende innere Regionen liefern Rechteck-
vorschläge; ihre Hülle dient ausschließlich der Modellhypothese, nicht als
ausgegebener Pfad. Dunkle, durch eine helle Kontur abgetrennte JPEG-Schatten
gehören nicht zur zusammenhängenden einfarbigen Innenfläche. Subpixelkanten
werden aus deren Helligkeitsübergang geschätzt.

Alle vorgeschlagenen Instanzen werden gemeinsam als native SVG-Objekte gerendert
und verfeinert. Die Suchverlustfunktion gewichtet Objektregionen gleich und
berücksichtigt beobachtete Bildableitungen, damit dünne Konturen erhalten bleiben.
Feste Qualitätsgates, tatsächlicher Einschluss, getrennte Rechtecke, Formanzahl,
Verlaufsrichtung, flächige Innenfüllung und gegebenenfalls helle Konturen bleiben
verbindlich. Nicht verbrauchte Beschreibungsaussagen verwerfen das Modell.
Das optionale Netz bleibt ausgeschaltet.

Dies ist ein weiterer begrenzter Szenenvertrag. Neue Formarten, beliebige
Verläufe, freie Sprache oder allgemeine Topologiesuche sind damit nicht belegt.
Ein synthetischer Entwicklungsfall erreicht bei fünf Sekunden weiterhin keine
freigegebene Ausgabe; ein erhöhtes Budget wurde nicht zur Abnahme verwendet.

## Nachweise und Bestand

`artifacts/evaluation/mixed_gradient_scene_v1/` enthält die unveränderten
Original-JPEGs, alle drei realen Phasen als SVGs, ursprüngliche Annotationen,
beide Runtime-Freeze-Manifeste, den erneut berechneten regulären Gate-Bericht
und die zusammengefassten CLI-Versuche. Die Eingaben der neuen Szenen liegen
unter `config/mixed_gradient_scene_families.json`; beide Familien sind dort
jetzt ausdrücklich Entwicklung. Vollständige lokale CLI-Ausgaben stehen unter
`.tmp/concept-audit/`. Ein frischer Checkout muss diese neu erzeugen.

Das Erfolgsarchiv bleibt bei **379 Paaren**. Alle 758 Original-/SVG-Prüfsummen
stimmen mit dem Archivindex überein; der Index und sämtliche bisherigen
Archivdateien wurden nicht geändert. Keine der 379 Archivbeschreibungen
aktiviert den neuen Einstieg. Eine neue vollständige Archiv-Neukonvertierung
war nicht Teil dieses begrenzten Nachweises; ein neuer Kataloggewinn wird
nicht gezählt. Die separate Katalogbeschreibung wird nicht automatisch ersetzt.

Die gezielte lokale Regression besteht mit **256/256 verschiedenen Tests**,
ohne Überspringen oder erwartete Fehler (250 Szenen-/Bestandsprüfungen und
sechs Belegprüfungen). Die vollständige Standardsuite wurde nicht erneut ausgeführt.

Der neue CI-Job `mixed-gradient-scenes` prüft native Geometrie, beschädigte
Gegenproben, sechs eingefrorene synthetische Regressionen und beide bekannten
Originale durch die überwachte CLI. Ein entfernter CI-Lauf wurde nicht gestartet.
Das endgültige lokale Testsignal steht in `checks.json` im Belegordner.

## Reproduktion

Neue Ausgabeordner verwenden. Die Realoriginale gelten bei einer Wiederholung
als bekannte Entwicklungsdaten; eine Wiederholung schafft keinen neuen Holdout.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_gradient_scene --prepare .tmp/mixed-final-new --seed 983127 --count 12
.venv/Scripts/python.exe -m tools.evaluate_mixed_gradient_scene --inputs .tmp/mixed-final-new --output .tmp/mixed-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_gradient_scene --inputs .tmp/mixed-final-new --output .tmp/mixed-cli-new --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_gradient_scene --prepare .tmp/mixed-real-new --real
.venv/Scripts/python.exe -m tools.evaluate_mixed_gradient_scene --inputs .tmp/mixed-real-new --output .tmp/mixed-real-cli-new --require-all
.venv/Scripts/python.exe -m tools.verify_mixed_gradient_scene_evidence artifacts/evaluation/mixed_gradient_scene_v1/manifest.json --output .tmp/mixed-stored-check-new.json
.venv/Scripts/python.exe -m pytest tests/test_mixed_gradient_scene_runtime.py tests/test_mixed_gradient_scene_evidence.py -q
```

Nächste offene Abnahme: mindestens zwei weitere, vorher gesperrte reale
Familien über denselben Szenenweg prüfen, ohne ihn auf diese Ergebnisse
nachzutunen. Der fehlgeschlagene erste reale Übertragungsversuch bleibt als
Beleg erhalten. BENCHMARK-PRACTICAL-01, IDO-19/IDO-21, produktive Netzabnahme
und historische Kompatibilitätsaufsicht behalten ihren offenen Status.

## CI-Korrektur: Archiv-Refresh

Der erweiterte Testprofil-Einstieg scheiterte vor pytest: Der Archivsammler
interpretierte auch das verschachtelte Entwicklungsmanifest als Archivschema
mit `case_id` und einfachem Bildpfad. Die neue Eingrenzung überspringt fremde
Manifest-/Berichtszeilen; gültige Archivfälle, explizite Freigaben und harte
Quell-/SVG-Prüfsummenprüfungen bleiben erhalten. Das tatsächliche neue Manifest
reproduziert den ursprünglichen `KeyError` in einem Regressionstest.

Nach der Korrektur: 24 gezielte Tests bestanden, eine regulär ausgeschaltete
vollständige Archiv-Neukonvertierung übersprungen. Der echte Aufruf
`.venv/Scripts/python.exe -m tools.refresh_satisfactory_archive --output-dir .tmp/archive-refresh-fix/refreshed-archive`
endet mit Exit 0 und denselben 379 Varianten sowie 758 Bild-/SVG-Prüfsummen.
Das bestehende Archiv bleibt unverändert; neue Entwicklungsfälle werden nicht
automatisch aufgenommen. Ein entfernter Workflow-Neulauf wurde nicht ausgelöst.
