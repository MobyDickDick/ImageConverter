# FALLBACK-GROUPS-CHECKER-04: unabhängige native Objekt- und Relationsprüfung

Am 13.11.2026 als **begrenztes synthetisches Prüferpaket abgeschlossen**.
Der Prüfer benötigt keine Runtime-Gruppenmarkierungen, Runtime-Verbindungsprüfung,
Detektoren oder Konvertierung. Eine vollständige unabhängige reale Familienabnahme
ist damit weiterhin nicht möglich; alle vier reservierten Familien bleiben
`sealed_unrun`, ohne Konvertierungsversuch oder Modellfreigabe.

## Vertrag und unabhängige Grenze

`tools.check_native_scene.check_scene(svg, annotation)` verlangt eine separate,
vollständige Annotation (`independent_native_scene_v1`): sämtliche nativen Objekte
einschließlich Hintergrund und bekannter verdeckter Teile, Geometrie, Farben,
Strichbreiten, lokale Toleranzen und ausdrücklich angegebene Relationen.
Die Annotationen werden nicht aus dem Kandidaten oder seinen Markierungen gewonnen.
SVG-IDs, `data-part` und `data-fallback-group` haben keinen Einfluss auf die Prüfung.
Der Prüfer importiert keinen produktiven Projektcode. Die Rasterdiagnostik des
separaten Evaluators verwendet MuPDF und librsvg und beeinflusst den geometrischen
Prüferentscheid nicht.

Eine injektive Zuordnung verhindert, dass dasselbe SVG-Element mehrere erwartete
Teile belegt. Fehlende und zusätzliche native Elemente, auch vollständig verdeckte,
scheitern. Nach der Geometrie-/Farbzuordnung folgen eigenständige Punkt-/Segment-
und Kreis-/Polygonrandabstände für Anschlüsse, echte Linienkreuzungen und die
annotierte Zeichenreihenfolge. Anschlussfehler innerhalb der zugelassenen
Objektpositionstoleranz werden separat erkannt. Der vollständige Prüfentscheid
verlangt alle annotierten Objekte und Relationen, nicht nur einen globalen Score.

Unterstützt werden scharfe Rechtecke, Kreise, Linien und Polygone mit einfarbiger
Füllung/Kontur sowie verschachtelte Gruppen, geerbte Zeichenattribute,
Translation, Drehung, Spiegelung und gleichmäßige Skalierung. SVG-Transformations-
reihenfolge und transformierte Strichbreiten werden berücksichtigt. Grenzen:
512 Pixel je Seite, 48 native Objekte, 24 Verschachtelungen, 4.096 Zuordnungsschritte.
Nicht unterstützte Elemente/Attribute, fehlerhafte Zahlen, fremde Namensräume,
CSS, Transparenz, Effekte, Referenzen, andere ViewBoxes, Scherung und ungleichmäßige
Skalierung erhalten ausdrücklich keine positive Abnahme.

## Eingefrorene Entwicklung und Gegenproben

Fünf synthetische Szenen enthalten dieselben 14 explizit konstruierten Teile:
beide bekannten Gruppen, zwei zusätzliche Kontextobjekte und einen eigenen
Verdeckungsbereich. Die Varianten prüfen Identität, Viertel-/Halbdrehung,
gleichmäßige Skalierung und Spiegelung. Sie sind **eine Konstruktion mit
Transformationsvarianten, keine fünf unabhängigen realen Familien**. Die
Annotationen wurden separat zum XML formuliert; diese Entwicklungskontrollen
ersetzen keinen menschlichen Annotationsaudit.

| Prüfung | Ergebnis |
| --- | ---: |
| Vollständige synthetische Positivszenen | 5/5 |
| Fehlende Kontextobjekte, Köpfe, Diagonalen und verdeckte Teile | 20/20 zurückgewiesen |
| Falsche verdeckte Geometrie und zusätzliche verdeckte Objekte | 10/10 zurückgewiesen |
| Falsche Anschlüsse, Farbe, Strichbreite, Transformation und Zeichenreihenfolge sowie sichtbare Zusatzobjekte | 30/30 zurückgewiesen |
| Davon rasteridentische Gegenproben mit beiden Renderern | 15/15 trotzdem zurückgewiesen |
| Originale synthetische Zielkonstruktionen des Vorgängerpakets | 6/6 |
| Bereits gespeicherte direkte Entwicklungsausgaben des Vorgängerpakets | 0/18 zertifiziert |

Die letzten 18 Ausgaben enthalten 15 bis 18 native Elemente statt der elf
annotierten Zielbestandteile. Unter anderem ist das durchgehend konstruierte
Gestänge in zwei sichtbare Segmente zerlegt, zusätzlich existieren nachgezeichnete
Restbildlinien. Die sechs verschiedenen Ausgaben wurden je dreimal mit
verschiedenen Seeds erzeugt; das sind keine 18 unabhängigen Fälle. Ihre damaligen
Pixel-/Runtime-Detailpässe bleiben unverändert, belegen jedoch keine vollständige
unabhängige Objektabnahme.

Diese Ablehnung ist **keine vollständige fachliche Fehlerklassifikation**:
Ein unter einem Gelenk geteilter Strich kann dieselben sichtbaren Inhalte wie ein
durchgehender Strich darstellen. Der neue Prüfer verlangt bewusst eine
Eins-zu-eins-Zuordnung nativer Einzelprimitive und beweist noch keine Äquivalenz
solcher Zerlegungen. Ob zusätzliche Striche legitime Konturdarstellung oder
unbelegter Überzeichnungsrest sind, benötigt ein eigenes, vorab festgelegtes
Objektmodell. Die Toleranzen wurden nicht erhöht, um historische Ausgaben
nachträglich zu akzeptieren. Der produktive Converter wurde nicht verändert.

## Separater Freeze und Reproduktion

[Evidenz und Befehle](../artifacts/evaluation/fallback_checker_v1/README.md).
`checker.py`, `evaluator.py` und `manifest.json` sind separat mit SHA-256 gebunden;
der Replay prüft die eingefrorenen Kopien gegen den ausgeführten Code und
verweigert Änderungen. Die Vorbereitung überschreibt keine vorhandenen Ordner.
Die 18 historischen Kandidaten sind gespeichert und in der Ergebnisdatei
einzeln hashgebunden. Keine reservierte Eingabe ist Teil dieser Studie.

101 neue Prüferregressionen und 87 bestehende Struktur-/Kompositions-/Reserve-
regressionen bestehen gemeinsam: **188/188**, ohne Überspringungen. Separates
Kernprofil: **42/42**. Replay: fünf Positivszenen, 60 Negativkontrollen und 18
historische Nachprüfungen. Lokale Python-Version 3.10.11. CI ist um die
Prüferregressionen und den separat versiegelten Replay erweitert; kein GitHub-Lauf
wurde gestartet. Keine neue CLI-Konvertierung und keine Archiv-Neukonvertierung,
da dieses Paket ausschließlich die unabhängige Prüfung verändert.

## Nächstes Paket und reale Sperre

Nächstes P0-Paket ist **FALLBACK-GROUPS-CHECKER-05**: vollständige logische Objekte
aus sichtbaren Segmenten unabhängig zuordnen, zulässige Teilung unter einem
Gelenk von falschen Anschlüssen unterscheiden und zusätzliche Restbildstriche
mit eigenen negativen Überzeichnungskontrollen bewerten. Den erweiterten
Prüfervertrag wieder vor einer Reserveprüfung einfrieren; der jetzige strikte
Prüferstand bleibt als Entwicklungsevidenz erhalten.

Beliebige Kurven, Rundungs-/Schattierungsgeometrie und die übrigen dokumentierten
realen Prüflücken sind noch nicht abgedeckt. Vollständig verdeckte reale Geometrie
kann aus Pixeln allein nicht rekonstruiert werden: Solche Annotationen benötigen
eine dokumentierte Quelle und Unsicherheit statt erfundener Vollständigkeit.
Ein unabhängiger menschlicher Annotationsaudit fehlt weiterhin. Der neue Freeze
erteilt keine Reservefreigabe und schließt diese Voraussetzungen nicht.
HC0010, Rail, AC5041 und AC5050 bleiben gesperrt und ungetestet.
SEARCH-STRUCTURE-01, GENERAL-SCENE-REAL-05 und SEMANTIC-COMPLETENESS-02 bleiben offen.
