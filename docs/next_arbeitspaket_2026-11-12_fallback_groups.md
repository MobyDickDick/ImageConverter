# FALLBACK-GROUPS-02: Native Pfeile und zusammengesetzte Gelenksymbole

Am 12.11.2026 als begrenztes Entwicklungspaket abgeschlossen. Der tatsächlich
benutzte Fallback prüft jetzt zwei zusätzliche Objektgruppen: Schaft mit
dreieckigem Kopf sowie farbiges Quadrat mit Diagonalen, Anschluss, Gelenk und
schrägem Gestänge. Beide werden aus Originalpixeln vermessen, gemeinsam ersetzt
und in native SVG-Elemente ausgegeben. Keine Bild-ID-Weiche, Referenz-SVG oder
Kontur-Nachzeichnung wird im produktiven Suchweg verwendet.

## Ergebnis bei unveränderten Grenzen

Die vier bekannten Entwicklungsfälle und die bisherigen Fortsetzungsmodule
wurden vor Runtimeänderung gesichert. Verglichen werden der eingefrorene
bisherige kombinierte Fallback, ausschließlich Gruppen und die neue Kombination.
Jeweils Seeds 17/29/43, fünf Sekunden reguläres/maximales Gesamtbildbudget,
Portfolio-Basisbudget 384. Vorschläge, Rendern und Parameterfortsetzung teilen
diese Zeit; es gibt kein zusätzliches Gruppenbudget.

| Bekannter Entwicklungsfall | Bisheriger medianer normierter MSE | Neu kombiniert | Änderung | Vollständige lokale Abnahme, beide Renderer |
| --- | ---: | ---: | ---: | ---: |
| AC0030_S, Pfeilpaar | 0,0060951 | 0,0006186 | −89,9 % | 0/3 → 3/3 |
| AC0303_1_M, Kreis mit Innenlinien | 0,0056703 | 0,0056313 | −0,7 % | 3/3 → 3/3 |
| AC0504_1M_sia, Quadrat mit Gelenk | 0,0083647 | 0,0021849 | −73,9 % | 0/3 → 3/3 |
| GE0362, Werkzeug/Flamme | 0,0279564 | 0,0279564 | 0 % | 0/3 → 0/3 |

MuPDF und unabhängig librsvg bestätigen **3/12 → 9/12** vollständige
Pixel-/Detailabnahmen. Die reine Gruppenablation besteht 6/12 und erhält den
Kreis ohne die bisherige Grundform-/Linienrekonstruktion nicht. Beim Quadrat
erzielt sie einen kleineren MSE als die Kombination; die Kombination ist nicht
für jede Einzelmetrik überlegen.

Acht echte überwachte CLI-Konvertierungen starten ausschließlich aus dekodierten
Originalpixeln und den eingefrorenen Beschreibungen unter neutralen Dateinamen.
Keine historischen Ausgangs-SVGs werden dabei eingelesen. Gleiche 8/10 Sekunden
Bildbudget, fünf Sekunden Mindestaufwand, Seed 17 und 64 Iterationen: Der
bisherige Fallback besteht **1/4**, die neue Kombination **3/4**, jeweils auch
mit dem zweiten Renderer und allen lokalen Detailprüfungen. Die äußeren
CLI-Prozesszeiten liegen bei 7,25–7,93 Sekunden; es gibt keine gesperrten
Referenzzugriffe und keine Modellfreigaben.

## Konstruktionen, lokale Belege und Gegenproben

Der Pfeil besteht aus einer beobachteten, langen Farbspur und einem breiteren
dreieckigen Kopf. Die Öffnung der Farbmaske dient nur zur Detektion; die
Originalpixel bestimmen Kopfgeometrie, Farbe, Schaftbreite und Ausdehnung.
Die Schaftachse begrenzt die Dreiecksachse. Eine Verbindung an Spitze oder
Basismitte ist möglich; kleine Subpixelregistrierungen sind getrennte,
tatsächlich gerenderte Hypothesen. Die Kopf- und Schaftfarben dürfen sich
unterscheiden, etwa bei kräftigen Köpfen an blassen Schäften.

Das zweite Modell verbindet ein beobachtetes farbiges Quadrat mit zwei
Diagonalen, einem seitlichen Anschluss, einer kleinen hellen Ringöffnung und
zwei kollinearen Gestängeteilen. Die Ringöffnung und die schräge Achse benötigen
eigene Rasterbelege. Geometrische Prüfungen verlangen tatsächliche Anschlüsse
zwischen den nativen Teilen; ein Gruppenname allein genügt nicht.

Jeder neue Gruppenentwurf muss die bisherigen Beschreibungszählungen, den
globalen Fehlergewinn und die mindestens 60 Prozent lokal verbesserten
Änderungspixel bestehen. Zusätzlich benötigt jedes Teil einen normierten
lokalen MSE ≤ 0,04 und Kantenbeleg ≥ 0,72. Spätere Linienaddition und
Parameterfortsetzung dürfen bereits gemessene Gruppendetails nicht wieder
verschlechtern. Die Auswahl bleibt auf 32 Vorschläge begrenzt, davon höchstens
acht Gruppenvorschläge; maximal vier Pfeile und 16 beobachtete Ringkandidaten
begrenzen die Detektion. Die bestehenden 512-Pixel- und Elementgrenzen bleiben.

Die unabhängige Nachmessung verwendet feste Regionen der Originalbilder,
zusätzlich zu den mitgereisten Runtime-Teilregionen. Das Kreuz wird im Inneren
des Quadrats geprüft, sein Rand separat: Der erste Diagnoseausschnitt schnitt
den Rand an und vermischte Randkanten mit den Diagonalen. Die Korrektur dieses
Entwicklungsausschnitts ist keine vorab unabhängige Holdout-Abnahme. MSE- und
Kantengrenzen wurden nicht abgesenkt.

33 beschädigte Kontrollen entfernen jeweils ein einzelnes Teil, versetzen es
oder verbinden es falsch. Beide Renderer weisen sämtliche Kontrollen zurück
(66/66). 32 dieser Rendererprüfungen würden bei ausschließlich globalen Gates
noch bestehen. Die lokalen und geometrischen Prüfungen liefern somit eine
zusätzliche, tatsächlich benötigte Unterscheidung.

16 unabhängig erzeugte synthetische Varianten mit vier Farben, vier
Pfeilrichtungen und verschobenen Gelenksymbolen bestehen beide Renderer und
lokale Detailprüfungen: bisher 0/16, Gruppen 16/16, kombiniert 16/16. Das sind
Varianten der beiden Modelle, keine 16 neuen Familien.

## Zeitmessung und Reserven

Ein ursprünglicher Gruppenlauf (AC0030_S, Seed 29) weist eine unerklärte
monotone Beobachtungslücke auf: 9.455,157 Sekunden statt fünf Sekunden. Er ist
mit SVG-Hash und vollständigem Suchbericht separat als unterbrochener Versuch
erhalten und aus den Budgetvergleichen ausgeschlossen. Ein neuer Versuch mit
identischen Eingaben, Seed und Budget unter der vorhandenen Windows-Wachhaltung
endet nach 5,000 Sekunden mit derselben erfolgreichen Gruppenrekonstruktion.
Die 36 vergleichbaren Fortsetzungen benötigen höchstens 5,015 Sekunden;
einzelne native Aufrufe können das Budget weiterhin geringfügig überschreiten.
Aus der Lücke wird weder zusätzliche nützliche Rechenzeit noch eine gesicherte
Standbyursache abgeleitet.

Vor Runtimeänderung wurden zwei zusätzliche reale Kompositionsfamilien
(AC5041-Heizung/Gebläse und AC5050-Ventilator/Gitter) mit Originalbytes,
Beschreibungen, sichtbaren Objektboxen, Relationen und Runtimehashes separat
eingefroren. Alle bekannten Größenvarianten bleiben zusammen reserviert.
Standardvorbereitung und Katalogmessung sperren sie; null Konvertierungsversuche.
Frühere Katalog-/Batchexposition ist möglich, AC5041 erscheint bereits in einer
historischen Qualitätsübersicht. Das sind reservierte Kompositionsfamilien,
keine behaupteten bisher ungesehenen Bilder. Unabhängige vollständige
Kurven-/Teilprüfer und menschlicher Annotationsaudit fehlen weiterhin.
HC0010/Rail bleiben ebenfalls gesperrt und ungetestet.

## Prüfung, Reproduktion und offene Grenze

203 gezielte Regressionen bestehen; eine vollständige Archiv-Neukonvertierung
ist ausdrücklich abgewählt und wird nicht als bestanden gezählt. Das Kernprofil
besteht 42/42. Die vorhandene CI prüft die neuen Gruppen, synthetischen Varianten,
Reservensperre und die drei erfolgreichen echten CLI-Fälle mit librsvg. Ein
GitHub-Lauf ist noch nicht erfolgt.

[Kompakte Messdaten, eingefrorener Vorhercode und Reserven](../artifacts/evaluation/fallback_groups_v1/README.md).

Die Gruppen sind zusätzliche vollständige Konstruktionen im Fallback. Ein
allgemeines Add/Remove/Replace-Portfolio beliebig gemischter Gruppen in einer
vorhandenen Szene fehlt weiterhin. Schwarze/unbunte Pfeile, gekrümmte oder
verdeckte Bauteile, beliebige Panelorientierungen und das Werkzeug-/Flammensymbol
sind offene Grenzen. **Modellfreigaben bleiben 0**, das Erfolgsarchiv wächst
dadurch nicht. SEARCH-STRUCTURE-01, GENERAL-SCENE-REAL-05 und
SEMANTIC-COMPLETENESS-02 bleiben offen.

Das nächste P0-Paket ist **FALLBACK-GROUPS-COMPOSITION-03**: Rastergestützte
Gruppen als wechselbare Add/Remove/Replace-Operationen in vorhandene Szenen
einbauen, mehrere verschiedene Gruppen gemeinsam prüfen und richtige bisherige
Objekte erhalten. Fehlende zusätzliche Objekte und falsche Anschlüsse müssen
unter unveränderten Budgets negative Evidenz liefern. Vor einer ersten
reservierten Familienprüfung ist der vollständige unabhängige Prüfer separat
einzufrieren; Reserven bleiben bis dahin gesperrt.

Sitzungslog: getestet wurden 36 vergleichbare Fortsetzungen, acht CLI-Läufe,
48 synthetische Ablationen, 33 beschädigte Kontrollen sowie Regressionen und
Kernprofil. Ergebnis: 9/12 statt 3/12 sowie 3/4 statt 1/4. Blocker: allgemeine
Komposition, Kurven und vollständige Semantik. Nächster Schritt: gruppenweise
Szenenoperationen. Startbefehl: siehe reproduzierbares Evidenzpaket.
