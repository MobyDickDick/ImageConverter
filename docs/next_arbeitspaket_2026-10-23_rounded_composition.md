# SEARCH-STRUCTURE-01: Rundung mit Restbildinstanzen kombinieren

Basis: `985ee019cde2332d646e0e8f68a9f247728d7c5a` (`main`).
Branch: `codex/search-structure-rounded-composition-2026-10-23`.
Auswahl: höchstes offenes P0-Paket gemäß `open_tasks.md` und
[Schwächenprüfung](weakness_review_2026-10-23.md).

## Verhalten und Ursachenvergleich

Der gemeinsame Verlaufskreis-/Restbildweg unterstützt jetzt einfarbige
Rechteckkinder mit leicht gerundeten Ecken. Diese verwenden denselben
Instanzvorrat, die alternative Segmentierung, die begrenzte Edit-Agenda,
den Rendercache und das überwachte Bildbudget wie die bisherigen Kinder.
Die Rundung ist ein nativer SVG-Parameter `rect rx`; es entsteht kein
zusätzlicher Symbol- oder Familienpfad. Native Kreiskinder können daneben
weiterhin Bestandteil derselben Szene sein.

Zwei Lösungsansätze wurden mit echten Rasteranpassungen geprüft:

1. Die bestehenden gerundeten Rechteckszenen lediglich anhand des Wortes
   „gerundet“ aufzurufen wäre unpassend: Deren Vertrag enthält keinen
   Verlaufskreis und keine frei angeordneten Restbildkinder. Der eingefrorene
   CLI-Ausgangsstand erreicht bei diesen Kompositionen **0/12**.
2. Rundung als zusätzliche Geometrie an die vorhandenen Instanzen anzuschließen
   erhält deren vollständigen Vertrag. Die erste Schätzung aus interpolierten
   Kanten und fehlender Eckfläche war noch ungenau: Drei von 30 gezielten Tests
   scheiterten, darunter eine falsche Rundungsbehauptung bei eckigem Raster.
   Die endgültige Schätzung integriert stattdessen die beobachtete
   Antialiasdeckung der geraden Kanten. Die gegenüber einem Rechteck fehlende
   Fläche liefert über `(4-pi)*r²` einen Startwert; die gemeinsame Registrierung
   kann ihn zusammen mit Position, Größe und Farben anpassen.

Eine Rundungsbehauptung braucht sichtbare fehlende Eckfläche. Ein beliebig
kleines positives `rx` bei tatsächlich eckigem Raster genügt nicht. Die
Vorschlagsschwelle ist keine gelockerte Qualitätsgrenze. Der geschlossene
Parser bindet den Zusatz an genau die quantifizierte Rechteckgruppe; sämtliche
übrigen Aussagen, Anzahl, Formklassen, Containment, Trennung, Reihen-/Spaltenlage
und lokale sowie vollständige Rastergates bleiben verbindlich.

Der Eckradius gehört jetzt auch zur Identität eines Strukturvorschlags.
Unterschiedliche Rundungshypothesen dürfen weder als identisch dedupliziert
noch durch negative Evidenz einer anderen Hypothese gesperrt werden.
Die negative Evidenz unterscheidet zudem den gerundeten vom eckigen Vertrag.

## Nachweis

Alle Vergleiche verwenden die echte überwachte `semantic-only`-CLI mit
**fünf Sekunden je Bild** und **Suchseed 17**. Der unabhängige Nachprüfer
liest die tatsächlich erzeugten nativen SVG-Objekte, prüft Anzahl, Form,
Bounds, Eckradius, Verlaufsachse, Zeichenreihenfolge, Objektregionen und das
gesamte Originalraster. Beide Referenzvektor-Zugriffswächter bleiben leer.

| Kohorte | Ergebnis |
| --- | --- |
| Zwölf vor Runtime-Änderung gespeicherte Szenen, ein/zwei/vier/sechs Rechteckkinder, beide Verlaufsachsen | vorher 0/12, nachher 12/12 |
| Dieselben Eingaben unter neutralen Dateinamen, endgültiger Runtime-Stand | 12/12 |
| Zwölf zusätzliche synthetische Szenen mit anderem Geometrie-/Farbseed | 12/12 |
| Genau eine gekoppelte Plan-B-Vorlage, Original plus 16 Größen-/Lagevarianten | 17/17 |
| Zwanzig bekannte Split-/Operatorfälle, echte CLI-Wiederholung | unverändert 20/20 |
| Neun bekannte Restbildfälle, echte CLI-Wiederholung | unverändert 7/9 |

Alle 27 bisher erfolgreichen Ausgaben dieser beiden Regressionskohorten
sind bytegleich zum vorherigen Teilabschluss. Die beiden kontrastarmen
Restbildfehler bleiben ausdrücklich im Nenner.

Die gezielten Regressionen prüfen zusätzlich fehlende/zusätzliche Objekte,
falsche Anzahl und Anordnung, eckige Ersatzformen, Textur, Kinder außerhalb
des Kreises, unbekannte Aussagen, gemischte Kreis-/Rechteckinventare, Rundung
plus Remove sowie Ablauf des gemeinsamen Budgets vor der Registrierung.
`checks.json` und die gespeicherten Protokolle enthalten die Abschlussprüfungen.
Die vollständige Standardsuite besteht mit **3.999 bestandenen und 30
übersprungenen Tests**, ohne Fehler (46 Minuten 23 Sekunden). Alle **34 neuen
gezielten Tests** bestehen ebenfalls; sie sind in der Gesamtzahl enthalten.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung und Whitespace-Prüfung unter
Berücksichtigung der bestehenden Windows-Zeilenenden bestehen. Die komplette
CLI-Evidenz wurde ausschließlich aus den für Git ausgewählten Dateien in
einen separaten Ordner kopiert und dort unabhängig erneut geprüft.
Alle **379** gespeicherten Archivpaare bestehen ihre bisherige absolute
Pixelprüfung; **758** Bild-/SVG-Prüfsummen sind unverändert. Diese Prüfung
ist keine erneute Konvertierung aller Archiveingaben.

Eingaben, Berichte, tatsächliche SVGs und Zugriffsnachweise liegen unter
[`artifacts/evaluation/rounded_composition_v1/`](../artifacts/evaluation/rounded_composition_v1/README.md).
Die CI wiederholt die gezielten Tests und zwölf neu erzeugte Szenen durch
die überwachte CLI samt unabhängiger Nachprüfung.

## Restumfang

Dieser Rundungsbaustein ist ein weiterer technischer Teilabschluss des P0-Pakets.
**SEARCH-STRUCTURE-01 bleibt insgesamt offen.** Überdeckung, zusätzliche
Schichtbeziehungen und Rundung zusammen mit Konturen sind in diesem
Verlaufskreisvertrag noch nicht abgenommen. Der Parser weist die Kombination
mit hellen Konturen deshalb ausdrücklich zurück. Der bisherige separate
Rechteck-Verlaufsszenenweg behält seinen eigenen geprüften Umfang.

Alle neuen Fälle sind synthetische Entwicklung, keine neue reale Familie.
Vor realer Entwicklung für GENERAL-SCENE-COMPOSITION-09 müssen weiterhin zwei
andere reale Prüffamilien unabhängig markiert und gesperrt werden.
GE0018/GE0307 bleiben Entwicklung. Die Grenzen für Rundungsbeobachtung und
leichte Rundung werden ausdrücklich beibehalten; beliebige Kurven, sehr kleine
unbeobachtbare Radien oder freie Formen sind nicht nachgewiesen.
