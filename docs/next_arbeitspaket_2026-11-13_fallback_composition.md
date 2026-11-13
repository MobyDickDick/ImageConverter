# FALLBACK-GROUPS-COMPOSITION-03: Gruppen in vorhandenen Szenen wechseln

Am 13.11.2026 als begrenztes synthetisches Entwicklungspaket abgeschlossen.
Der tatsächliche Fallback kann beobachtete Schaft-/Dreiecks- und
Quadrat-/Diagonalen-/Gelenkgruppen hinzufügen, atomar ersetzen und unbelegte
vorhandene Objekte entfernen. Verschiedene Gruppen sammeln sich in derselben
Szene. Richtige vorhandene Objekte bleiben erhalten. Das ist keine allgemeine
reale Familienabnahme oder Modellfreigabe.

## Vergleich und Budget

Sechs synthetische Szenen mit jeweils beiden Gruppen, einem zusätzlichen Kreis
und einer kurzen Linie wurden mit dem bisherigen Runtimecode vor dessen
Änderung eingefroren. Die Ausgangs-SVGs enthalten unterschiedliche fehlende
Gruppen, falsche Schaftrechtecke, unvollständige Quadrate und zusätzliche
Fehlobjekte. Die richtigen Kreis-/Linienobjekte tragen überprüfbare Identitäten.
Alle sechs Bilder verwenden dieselbe grundlegende Anordnung mit drei Farben;
das sind zwei bekannte Konstruktionsfamilien, keine sechs unabhängigen Familien.

| Prüfung | Bisher | Komposition |
| --- | ---: | ---: |
| Direkte Struktursuche, sechs Szenen × drei Wiederholungen | 0/18 | 18/18 |
| Vollständige lokale Szenenabnahme mit MuPDF und librsvg | 0/36 | 36/36 |
| Überwachte echte CLI mit unveränderten Originalrastern/Beschreibungen | 0/6 | 6/6 |

Die direkte Studie begrenzt jeden Aufruf auf fünf Sekunden und 32 Vorschläge.
Seeds 17/29/43 konfigurieren das Portfolio; die analytischen Strukturvorschläge
sind selbst deterministisch. Die Wiederholungen sind keine zusätzliche
unabhängige Kohorte. Die aktuellen direkten Aufrufe enden spätestens nach
0,593 Sekunden. Es handelt sich um Struktursuche ohne anschließende vollständige
Parameterfortsetzung; ungenutzte Zeit wird nicht als Sucharbeit gezählt.

Die CLI startet ausschließlich aus neutral benannten PNGs und den eingefrorenen
Beschreibungen, ohne Ausgangs- oder Referenz-SVG. Die drei Ziel-Farbvarianten
kommen jeweils zweimal vor; unterschiedliche Ausgangs-SVGs betreffen nur die
direkte Studie. Deshalb werden die sechs CLI-Fälle als wiederholte
Integrationsprüfung dreier Farbvarianten derselben Anordnung ausgewiesen.
Jeweils acht Sekunden reguläres, zehn Sekunden maximales Bildbudget,
fünf Sekunden Mindestaufwand, Seed 17 und 64 Iterationen. Die äußeren überwachten
Prozesszeiten liegen bei 8,859–9,828 Sekunden. Keine gesperrten SVG-Zugriffe,
keine Modellfreigaben. Die Windows-Wachhalteanforderung meldete in dieser
Umgebung `Zugriff verweigert`; die überwachten Zeitgrenzen blieben aktiv.

## Verhalten und Abnahme

Bis zu acht bisherige vollständige Gruppenalternativen bleiben verfügbar.
Gruppenkomposition einschließlich dieser Alternativen belegt höchstens 24 der
32 Vorschläge. Primitive Ergänzungen und Restbildlinien teilen sich den Rest;
sechs Versuche bleiben für Linien reserviert. Rendern, Detektion und sämtliche
Operationen verwenden dieselbe aktive Bilddeadline. 512 Pixel Seitenlänge und
48 native Elemente bleiben verbindliche Grenzen.

Ersetzungen erfolgen am bisherigen Zeichenplatz; Definitionen und andere
Objekte bleiben erhalten. Für das geometrische Zuordnen werden nur native
Objekte ohne Transformationen oder Effekte verwendet. Entfernen funktioniert
auch innerhalb verschachtelter Gruppen. Jede weitere Entfernung baut auf dem
aktuellen Zwischenstand auf und führt bereits entfernte Objekte nicht wieder
ein. Fehlende native Kreis-/Rechteckobjekte können zusätzlich in eine bereits
gruppierte Szene übernommen werden. Bestehende Gruppenbereiche werden dabei
nicht mit weiteren primitiven Kopien übermalt.

Jeder Kandidat benötigt weiterhin Beschreibungszählungen, globalen Fehlergewinn,
lokalen Gewinn und mindestens 60 Prozent verbesserte Änderungspixel. Neue
Gruppenteile und Anschlüsse behalten ihre bisherigen MSE-/Kantengrenzen und
geometrischen Prüfungen. Bereits bestandene Gruppendetails dürfen nicht
verschlechtert werden. Zusätzlich schützen vor der Änderung vollständig passende
zusammenhängende Objekte ihre lokalen Bildregionen; das verhindert beispielsweise
das Löschen einer kleinen richtigen Linie zugunsten größerer Flächen. Derselbe
Schutz gilt bei späterer Parameterfortsetzung. Dies ersetzt keinen vollständigen
semantischen Prüfer für verdeckte oder nur näherungsweise passende Objekte.

Die erste CLI-Prüfung scheiterte vor dem Fallback: Richtungswörter und ein Kreis
in einer mehrteiligen Beschreibung aktivierten die Einzelzeichenheuristik.
Explizit nebeneinander/getrennt beschriebene unterschiedliche Formen werden jetzt
dem allgemeinen Suchweg überlassen. Einzelkreis-Beschreibungen behalten ihre
Zuordnung; bestehende semantische Gates bleiben aktiv. Anschließend fehlten im
CLI noch der zusätzliche Kreis und die Linie. Primitive Ergänzungen und die
Priorisierung der Liniennachsuche am besten gruppierten Zwischenstand beheben
beide Fehler. Die frühen fehlgeschlagenen CLI-Versuche bleiben lokal erhalten;
der ursprüngliche Fehlvergleich ist zusätzlich in der kompakten Evidenz enthalten.

30 beschädigte Kontrollen entfernen eine vollständige zusätzliche Gruppe, den
richtigen Kontextkreis oder einen Pfeilkopf, verkürzen einen Anschluss oder
fügen ein fremdes Objekt hinzu. Beide Renderer weisen alle 60 Kontrollen zurück.
Die festen Rasterregionen stammen aus dem eingefrorenen Entwicklungsmanifest.
Verbindungen werden zusätzlich mit dem vorhandenen Runtime-Geometrieprüfer
kontrolliert: Die breite Rasterregion allein erkennt nicht jede Anschlusslücke.
Es wird daher kein vollständig unabhängiger Semantikprüfer behauptet.

## Reproduktion und nächste Grenze

[Messdaten, eingefrorener Runtimecode und Replay](../artifacts/evaluation/fallback_composition_v1/README.md).
Die Regressionen prüfen außerdem verschachtelte Ersetzungen, unveränderte
Definitionen, zwei aufeinanderfolgende Entfernungen, Beschreibungszählungen,
Deadline und Vorschlagslimit. 260 gezielte Regressionen und das Kernprofil
42/42 bestehen ohne Überspringungen; eine vollständige Archiv-Neukonvertierung
wurde ausdrücklich abgewählt. Vier zusätzliche überwachte bekannte CLI-Fälle
bestätigen die bisherigen drei Erfolge; Werkzeug/Flamme bleibt negativ.
Die CI wurde um die
neuen Regressionen und sechs CLI-Prüfungen mit beiden Renderern erweitert; ein
GitHub-Lauf wurde nicht gestartet. Eine vollständige historische
Archiv-Neukonvertierung gehört nicht zu diesem Paket.

Alle realen Reserven, einschließlich HC0010/Rail und AC5041/AC5050, bleiben
`sealed_unrun`. Null reservierte Versuche, null Modellfreigaben, keine
Archivpromotion. Beliebige Kurven, schwarze Pfeile, verdeckte Verbindungen,
allgemeine Transformationen und unabhängige reale Vollständigkeit bleiben offen.

Nächstes P0-Paket ist **FALLBACK-GROUPS-CHECKER-04**: Einen von den
Runtime-Gruppenmarkierungen und Runtime-Verbindungsprüfungen unabhängigen
vollständigen Objekt-/Relationsprüfer entwickeln. Fehlende zusätzliche Objekte,
falsche Anschlüsse, verdeckte Teile und Transformationen getrennt prüfen, seine
Negativkontrollen und Grenzen dokumentieren und den Prüfer vor jeder ersten
reservierten Familienprüfung separat einfrieren. Fehlende Kurvenabdeckung und
der menschliche Annotationsaudit bleiben Voraussetzungen für eine spätere reale
Abnahme. Bis dahin bleiben die Reserven gesperrt. SEARCH-STRUCTURE-01,
GENERAL-SCENE-REAL-05 und SEMANTIC-COMPLETENESS-02 bleiben offen.

Fortschreibung vom 13.11.2026: [CHECKER-04 ist als begrenzter nativer
Einzelprimitivprüfer umgesetzt und separat eingefroren](next_arbeitspaket_2026-11-13_fallback_checker.md).
Seine vollständige Inventarprüfung zertifiziert die damaligen 18 Ausgaben wegen
geteilter Gestängelinien und zusätzlicher Restbildstriche nicht. Das verändert
die obigen Pixel-/Runtime-Detailmessungen nicht und ist kein allgemeiner
fachlicher Fehlernachweis. Segmentäquivalenz ist das nächste P0-Prüferpaket;
reale Reserven bleiben gesperrt.
