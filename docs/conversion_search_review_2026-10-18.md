# Prüfung des Konvertierungsverfahrens (2026-10-18)

Ausgangsstand: `05de58ff1`. Die Formulierung „drei begrenzte Suchwege“ im
Sequenzdiagramm beschreibt einen implementierten ersten Baustein, keine
ausreichende Zielarchitektur für allgemeine Rekonstruktion. Die Zahl drei ist
nicht an sich schlecht. Problematisch sind der kleine Hypothesenraum, die frühe
Festlegung auf eine Struktur und voneinander unabhängige Budgets.

**Fortschreibung nach der Nutzerpräzisierung:** 60 Sekunden sind nun das
normale Suchbudget. Später messbarer Fortschritt darf es begrenzt verlängern;
früher Erfolg und echte Stagnation verkürzen es. Die inzwischen angeschlossene
Steuerung, konkrete Grenzen und Nachweise stehen unter
[Adaptive Konvertierungssuche](adaptive_conversion_search_2026-10-18.md).
Die folgende Bestandsaufnahme beschreibt den Ausgangsstand.

## Was der Code tatsächlich tut

- `SearchPortfolio.explore_parameters` versucht einmal rückwärts geordnete
  Koordinaten, einmal gemischte Koordinaten und gemeinsame Parameterneustarts.
  Alle drei bleiben innerhalb derselben Parameterliste und Gültigkeitsregeln.
  Auch ein höheres Budget erzeugt keine vierte Dreiecksinstanz oder einen
  fehlenden Anschluss. Der endliche Vorschlagsplan kann sein Budget sogar
  unterschreiten. Es handelt sich nicht um eine allgemeine Modellsuche.
- `--search-budget 384` gilt **je analytischem Modell**, zusätzlich zum
  ursprünglichen Fit. Vier Modellhypothesen können entsprechend mehr Arbeit
  auslösen. Weder dieses Argument noch der Seed begrenzen die gesamte Bildzeit.
- `FilledSymbols._register` ruft das Portfolio erst bei Restfehler und einem
  verfehlten lokalen Pixelgate auf. Die semantische Prüfung des jeweiligen
  Aufrufers folgt später. Ein lokaler Pixelpass ist deshalb kein vollständiger
  Nachweis, dass die Bildkonvertierung zufriedenstellend ist.
- `NonCompositeRuntime` beendet den ersten passenden Spezialpfad früh.
  `SemanticBadgeRuntime` kann vorher bereits Kreis/Text wählen. Beim nächsten
  Paket AC0232 ließ sich genau dieser Verlust von Ventildreiecken im echten
  CLI-Lauf reproduzieren. Der neue zusammengesetzte Fit ist jetzt an beide
  Einstiege angeschlossen; eine allgemeine gemeinsame Szenenauswahl fehlt weiter.
- `_wallClockTimeout` unterbricht auf Unix über ein Signal. Unter Windows prüft
  er erst nach Rückkehr die verstrichene Zeit. Das ist dort keine harte
  Unterbrechung. Der Katalogrunner hat einen separaten Prozess-Timeout, aber
  dessen Abbruch bedeutet noch keine Ausgabe des besten Zwischenstands.

Gut und erhaltenswert sind die messbare Render-Rückkopplung, native SVG-Formen,
Gültigkeitsbedingungen, Dublettenvermeidung, Seeds, nachvollziehbare Artefakte,
getrennte Semantik-/Pixel-/Komplexitätsgates und echte CLI-Gegenproben mit
gesperrten Referenz-SVG-Zugriffen. Die bisherigen Familienabnahmen belegen ihre
Fälle, keine allgemeine Szenenrekonstruktion.

Schlecht für das Projektziel sind verteilte sprachliche Schalter auf ganze
Symbolmodelle, ein früher Erfolg ohne Vergleich vollständiger Alternativen,
globale Pixelmittel als alleiniger Stellvertreter kleiner Objekte und
wiederholte identische Fits mit höheren Iterationszahlen, obwohl der Spezialfit
diese gar nicht nutzt. Immer neue Symbolfamilien lösen einzelne Fälle, ersetzen
jedoch keinen gemeinsamen Szenenweg.

## Forschungsstand und praktische Folgerung

Es gibt keinen universellen „besten“ Konverter unabhängig von Bildart,
Editierbarkeit, Laufzeit und Semantik. Für exakte technische Symbole ist ein
hybrides Verfahren aus gemessenen Grundformen, expliziten Beziehungen und
Renderoptimierung eine begründete technische Wahl; das ist unsere Ableitung,
keine veröffentlichte Rangliste für diesen Katalog.

**Anytime-Verfahren** halten einen gültigen besten Zwischenstand und verbessern
ihn mit zusätzlicher Rechenzeit. Zeitbudget und Fortschrittssteuerung sind
etablierte Informatik, keine neue Heuristik. Quelle:
[Zilberstein, Berkeley, 1993](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/6276.html).

**Differenzierbares Rendern** ermöglicht die gemeinsame Optimierung von
Geometrie und Farben gegen das Raster. DiffVG zeigt dieses Prinzip für
Vektorgrafik; daraus folgt noch keine automatische Wahl fehlender Objekte.
Quelle: [DiffVG, SIGGRAPH Asia 2020](https://people.csail.mit.edu/tzumao/diffvg/).

**Struktureller Ausbau** behandelt Zahl, Schichten und Komplexität der Formen
zusätzlich zu ihren Koordinaten. LIVE rekonstruiert schichtweise Topologien.
AdaVec passt Pfade und Kontrollpunkte an die Bildkomplexität an und optimiert
sie durch differenzierbares Rendern. Diese Arbeiten stützen die Richtung,
Struktur und Parameter gemeinsam weiterzuentwickeln. Quellen:
[LIVE, CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Ma_Towards_Layer-Wise_Image_Vectorization_CVPR_2022_paper.html),
[AdaVec, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Zhao_Less_is_More_Efficient_Image_Vectorization_with_Adaptive_Parameterization_CVPR_2025_paper.html).

**Bild-/Sprachmodelle** können SVG-Programme vorschlagen. StarVector ist ein
aktuelles Beispiel für Bild-/Text-Eingaben und verschiedene SVG-Aufgaben.
Für diesen Katalog wären solche Modelle zusätzliche Hypothesenlieferanten;
eine erzeugte Beschriftung oder Anschlussstruktur müsste weiterhin am
Original geprüft werden. Quelle:
[StarVector, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Rodriguez_StarVector_Generating_Scalable_Vector_Graphics_Code_from_Images_and_Text_CVPR_2025_paper.html).

Ein großes neuronales Modell oder Bayesian Optimization ist daher kein
automatisch besserer nächster Schritt. Zuerst müssen korrekte Instanzen,
Strukturänderungen, einheitliche Bewertung und globale Ressourcensteuerung
vorhanden sein. Die vorhandenen analytischen Starts bleiben dabei wertvoll.

## Vorgeschlagener Vertrag: zufriedenstellend oder spätestens 60 Sekunden

Die gewünschte Minute wird als **Obergrenze je Bild**, nicht als auszuschöpfende
Mindestlaufzeit, übernommen. Dieser Vertrag ist ein dokumentiertes Folgepaket;
er ist mit dieser Prüfung noch nicht überall implementiert.

1. Eine monotone Deadline startet vor Bildanalyse und Modellbildung. Alle
   Suchwege teilen die verbleibende Zeit; ein Modell darf das Budget nicht
   neu starten. Laden, Optimieren und abschließende Prüfung zählen dazu;
   Prozessstart und Dateiausgabe erhalten eine klar ausgewiesene Reserve.
2. Raster und Beschreibung liefern Objekte, Anzahl, Negationen und Beziehungen.
   Ein schneller analytischer Start erzeugt die erste vollständige Hypothese.
3. Nur ein **vollständiger** Kandidat mit erfüllter Objekt-/Anschluss-/Textprüfung
   und unveränderten Pixel-/Komplexitätsgates beendet die Suche erfolgreich.
4. Bei Stagnation wechselt die Suche Startpunkt, gekoppelte Parameter oder
   Optimierer. Bleiben zusammenhängende Rasterbereiche unerklärt, wird die
   Szene erweitert oder eine Form ersetzt. Leere Hintergrundflächen dürfen
   zusätzliche Objekte nicht durch gute Durchschnittswerte verdecken.
5. Kandidaten werden in kleinen Zeitscheiben verglichen. Günstige analytische
   Verfahren beginnen; weiterführende Verfahren bekommen Zeit anhand ihres
   bisherigen Fortschritts, bei reservierter Exploration neuer Hypothesen.
   Wiederholte identische Vorschläge werden nicht erneut gerendert.
6. Der beste gültige Zwischenstand wird nach Verbesserungen gesichert.
   Ein isolierter Prozess samt begrenzten Renderaufrufen erzwingt das Limit
   auch unter Windows. Eine Prüfreserve verhindert, dass ein ungeprüfter letzter
   Kandidat beim Timeout als Erfolg erscheint.
7. Ergebnisstatus unterscheidet `satisfactory`, `timeout_unsatisfactory`,
   `unsupported_structure`, `search_exhausted` und `execution_error`.
   Eine vollständig erschöpfte Menge zulässiger Alternativen darf früher enden;
   nutzloses Warten bis Sekunde 60 schafft keine neue Konvertierungsart.

Die Suche kann vorhandene **Operatoren** kombinieren und damit mehr Szenen
erzeugen. Sie kann nicht während eines einzelnen Laufs beliebige neue
Konvertierungsalgorithmen erfinden. Neue Formklassen benötigen implementierte
Operatoren oder einen dafür validierten Modellgenerator.

## Priorisierte Folgepakete und Abnahme

1. **SEARCH-DEADLINE-01:** gemeinsamer per-Bild-Kontext, monotone Deadline,
   überprüfter bester Zwischenstand, plattformübergreifender Prozessabbruch.
   Abnahme: Fake-Clock-Tests über mehrere Modelle, echte blockierte Worker,
   Erfolg vor Deadline, Timeout mit/ohne gültigem Zwischenstand sowie Batchfälle
   mit jeweils neuem Bildbudget. Ein bloßer Zeitcheck nach Rückkehr reicht nicht.
2. **GENERAL-SCENE-01 fortsetzen:** erkannte Instanzen erhalten, Beziehungen
   prüfen, Alternativen aus einem gemeinsamen Szenenmodell erzeugen;
   Add/Remove/Replace statt ausschließlich Koordinatenmutation. Beginn mit den
   bereits dokumentierten getrennten Kreisen/Rechtecken, danach Anschlüsse.
3. **SEARCH-SCHEDULER-02:** gemeinsame Zeitscheiben, lokale/gekoppelte/globalere
   Suche mit Fortschritt pro Rendersekunde. Neue Optimierer nur übernehmen,
   wenn sie im gleichen Zeitbudget auf unbekannten Familien besser abschneiden.
4. **BENCHMARK-ANYTIME-01:** eingefrorene bekannte und unbekannte Familien,
   Größen/Farben/Beschreibungsumformulierungen; Qualitätskurven nach 1/5/15/60 s,
   Objektfehler, Median/p95-Laufzeit, Renderzahlen und mehrere Seeds messen.
   Vergleich gegen den Elternstand; unveränderte Gates und Archivschutz.

Diese Architekturarbeiten sind von der regulären Rotation getrennt. Das auf
diese Prüfung folgende konkrete Arbeitspaket ist AC0232 L/M/S. Seine lokale
Erweiterung wird nicht als bereits gelöste allgemeine Struktursuche ausgegeben.
