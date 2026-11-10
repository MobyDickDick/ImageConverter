# Mindestaufwand bei ungenügenden Konvertierungen (2026-11-07)

Anlass: Der Konverter konnte nach wenigen Sekunden mit einem sichtbar
ungenügenden Entwurf enden, obwohl 60 Sekunden reguläre Suchzeit bereitstanden.
Bot-Stagnation und Vorschlagsgrenzen beendeten die endliche Parametersuche;
mehrere ältere Ausgabepfade führten überhaupt keine zusätzliche Modellsuche aus.
Zudem konnte die GUI einen Pixelpass als vollständige Qualitätsfreigabe anzeigen,
obwohl die Modellsuche das tatsächlich gespeicherte SVG nicht bestätigt hatte.

## Verhalten

- Die adaptive Standard-CLI reserviert `--search-min-seconds 30` Sekunden aktive
  Bildzeit für ungenügende Fits. Ein ausdrücklich kürzeres `--search-seconds`
  begrenzt auch den Mindestaufwand; `--search-min-seconds 0` erlaubt das frühere
  Abbruchverhalten. Direkte Bibliotheksaufrufe bleiben ohne explizite Mindestzeit
  kompatibel. Feste und Legacy-Suchen behalten ihr Verhalten.
- Stagnations- und Vorschlagsgrenzen dürfen die Mindestzeit nicht abkürzen.
  Erschöpfte Bots starten mit neuen, deterministisch gesäten Suchregionen neu:
  verschiedene Schrittweiten, gekoppelte Form-/Farbänderungen und unabhängige
  Ausgangspunkte. Bereits gemessene Parameter bleiben bekannt. Es gibt keine
  Warteschleife, die bloss die Laufzeit verlängert.
- Der reguläre Vorschlagsdeckel und sein Vierfaches gelten nach der geschützten
  Mindestphase wieder. `proposals_beyond_budget` macht die zusätzliche Arbeit
  sichtbar. Harte Zeitgrenzen, Abbruch und Prozessaufsicht bleiben verbindlich.
- Ein früher Erfolg verlangt während der Mindestphase zusätzlich zu den
  bestehenden Modellprüfungen ein genaueres Suchziel: normalisierter MSE
  höchstens 0,0005, Vordergrund-MSE höchstens 0,005, IoU mindestens 0,97 und
  Kantenausrichtung mindestens 0,90. Die bisherigen Abnahmegrenzen bleiben
  unverändert. Ein niedriger globaler MSE unterdrückt die Suche bei fehlenden
  kleinen Details nicht mehr.
- Bereits semantisch gültige Kandidaten bleiben als Rückfall erhalten, wenn
  weitere Pixelverbesserungen die Modellprüfung verletzen. Bei Kurztexten werden
  nach Erreichen des Mindestaufwands alle bereits laufenden Schriftmodelle
  abgeschlossen und verglichen; ihre Fertigstellungsreihenfolge entscheidet
  nicht mehr über die Auswahl.
- Schnelle ältere SVG-Ausgaben werden am Original nachoptimiert: gemeinsame
  Platzierung und gleichmässige Skalierung, gemeinsame Strichbreiten und Farben,
  geordnete Verlaufsstopps. Formen, Texte, Objektanzahl und Reihenfolge bleiben
  erhalten. Es werden weder Referenz-SVGs gelesen noch Konturen abgepaust.
  Bestehende explizite Beschreibungsprüfungen gelten auch für den Entwurf.
  Nach einer endlichen Sample-Koordinatensuche ist diese Fortsetzung ebenfalls
  angeschlossen, sofern das Sample noch keinen Pixelpass hat.
- Die GUI zeigt bei Pixelpass ohne vollständige Modellbestätigung einen Entwurf
  mit ausdrücklichem Hinweis. Sie zeigt weiterhin die Zahl der geprüften
  Kandidaten. Profile: Schnell 35–45, Normal 60–120, Gründlich 120–240 Sekunden,
  zuzüglich Start und Abschluss. Das schnelle Profil lässt nach dem 30-Sekunden-
  Mindestaufwand fünf Sekunden für Auswahl und Abschlussprüfung frei.

Ein unbekanntes Motiv, eine widersprüchliche Beschreibung oder ein fehlender
Formtyp wird durch längere Parametersuche nicht automatisch lösbar. Ohne
bearbeitbares, eigenständiges SVG gibt es keine künstliche 30-Sekunden-Pause.
Die allgemeine Nachoptimierung erteilt keine neue lokale Modellfreigabe für ein
verändertes SVG; diese bleibt an das tatsächlich modellgeprüfte SVG gebunden.

## Gemessene Beispiele

Vier vorhandene GUI-Eingaben wurden mit ihren gespeicherten Beschreibungen und
demselben Seed erneut per isolierter `semantic-only`-CLI konvertiert. Vergleich:
Mindestzeit 0 gegen 30, regulär 35 Sekunden, harte Suchgrenze 45 Sekunden,
keine zusätzlichen Qualitätsrunden. Die Zahlen bezeichnen aktive Bildzeit;
Start/Abschluss kommen zur Gesamtlaufzeit hinzu. Kleine Laufzeitunterschiede
zwischen Wiederholungen sind möglich.

| Eingabe | Zeit vorher → nachher | Kandidaten vorher → nachher | Normalisierter MSE vorher → nachher | Ergebnis |
|---|---:|---:|---:|---|
| AC0VR2_M, genauer Verlauf | 3,984 → 4,328 s | 178 → 178 | 0,00003062 → 0,00003062 | Identisches sehr gutes SVG, früher Abschluss |
| AC0VR2_AB_M, schräge Linien im Rechteck | 1,469 → 30,608 s | 1 → 1546 | 0,00070345 → 0,00048091 | Rund 31,6 % weniger MSE; Vordergrundfehler und IoU ebenfalls verbessert |
| AC0835_L, VOC-Kreissymbol | 14,031 → 31,000 s | 778 → 1776 | 0,00272021 → 0,00266988 | Rund 1,9 % weniger MSE; begrenzter Gewinn |
| AC0501_S_sia, alte unpassende Beschreibung | 5,405 → 30,360 s | 0 → 1409 | 0,00998501 → 0,00977265 | Etwas besser, aber weiterhin ungenügend; keine Freigabe |

Die Kantenmetrik des Linienrechtecks sinkt dabei leicht von 0,95765 auf 0,94786;
alle unveränderten Pixelgrenzen bleiben erfüllt. Die Suche optimiert ihren
Fehlerwert unter Qualitätsgrenzen, nicht jede Metrik gleichzeitig. Ein früherer
Vergleich desselben Beispiels ergab 35,6 % weniger MSE; die Tabelle dokumentiert
den anschliessenden Lauf mit der abschliessenden Auswahlkorrektur. Unterschiedliche
Rechenzeiten beeinflussen die Verteilung des gemeinsamen Zeitbudgets.

Der letzte Fall prüft ausdrücklich den zuvor nicht angeschlossenen nativen
Ausgabepfad und eine negative Grenze. Mehr Suchzeit ersetzt hier keine richtige
Beschreibung der quadratischen Kelle. Die Angaben sind Entwicklungsbeispiele,
keine erneute Abnahme aller 1787 Katalogbitmaps. Reservierte reale Prüffamilien
wurden nicht verwendet.

Maschinenlesbare Messergebnisse:
`artifacts/evaluation/search_minimum_effort_v1/summary.json`.
Rohläufe liegen lokal unter `.tmp/search_effort/` und verändern keine gespeicherten
GUI-Aufträge oder Katalogausgaben.

## Prüfungen

`tests/test_search_minimum_effort.py` prüft mit injizierter Uhr echte, eindeutige
Kandidaten bis 30 Sekunden, gekoppelte Sprünge über das ursprüngliche Suchraster,
kurze harte Grenzen, frühe bestätigte Erfolge, ungültige Einstellungen, kleine
fehlende Details und die Verbesserung einer nativen Form ohne Objektänderung.
Die vorhandenen Tests für kooperative Bots, Scheduler, Suchportfolio, Sample,
GUI und Prozessaufsicht werden ebenfalls ausgeführt.
Die GUI-/CLI-Integrationstests verwenden wie die GUI den überwachten,
wiederverwendeten Renderprozess (`IMAGE_CONVERTER_REUSE_RENDER_WORKER=1`), damit
der Test das Suchbudget statt tausendfachen Interpreterstarts prüft.

Abschliessend bestanden: 146 Such-/CLI-/GUI-/Sampleprüfungen, 117 Modell-/
Komponenten-/Sprachprüfungen und das 42 Tests umfassende `core-green`-Profil.
Zwei echte GUI-Prozess-/HTTP-Prüfungen liefen mit Hostberechtigungen erfolgreich;
drei gezielte CLI-/Prozessprüfungen bestanden ebenfalls (zwei davon sind bereits
in der Modellgruppe enthalten). Einzelheiten stehen in
`artifacts/evaluation/search_minimum_effort_v1/checks.json`.
