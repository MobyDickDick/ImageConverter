# SEARCH-STRUCTURE-01: Überdeckung als geordnete Strukturhypothese

Ausgangsstand: `6bd8e2406` (`main`).
Branch: `codex/search-structure-overlap-2026-10-23`.
Ausgewählt aus dem höchsten offenen P0-Paket gemäß
[Aufgabenliste](open_tasks.md) und [verbindlicher Rangfolge](weakness_review_2026-10-23.md).

## Abgeschlossener Teilumfang

Der vorhandene Verlaufskreis-/Restbildweg unterstützt jetzt zwei teilweise
überlappende, verschiedenfarbige, einfarbig gefüllte native Rechtecke.
Jede ihrer vier Seiten muss einen beobachtbaren geraden Abschnitt am
Elternhintergrund besitzen. Vollständig verdeckte Ausdehnungen werden nicht
erfunden. Die beiden möglichen Zeichenreihenfolgen werden als unterschiedliche
Strukturen im vorhandenen begrenzten Edit-Suchweg untersucht.

Der geschlossene Vertrag lautet beispielsweise:

> Ein gefüllter Kreis und zwei gefüllte Rechtecke. Der Kreis hat einen
> horizontalen Farbverlauf. Die Rechtecke liegen innerhalb des Kreises und
> überlappen sich teilweise. Keine Beschriftung.

Vertikaler Verlauf ist ebenfalls unterstützt. Konturen, Rundung, weitere
überlappende Instanzen und sprachlich bezeichnete Vordergrundrollen bleiben
in diesem neuen Teilvertrag ausdrücklich ausgeschlossen. Die bisherigen
getrennten Szenen behalten ihren vorhandenen Umfang.

**SEARCH-STRUCTURE-OVERLAP ist abgeschlossen; SEARCH-STRUCTURE-01 insgesamt
bleibt offen.** Rundung und Konturen zusammen mit Überdeckung, zusätzliche
Schichten und die unabhängige reale Familienabnahme bleiben Folgearbeit.
Alle neuen Fälle sind synthetische Entwicklung. Die vorgeschriebene Sperrung
und unabhängige Markierung anderer realer Prüffamilien bleibt vor realer
Entwicklung erforderlich; GE0018/GE0307 bleiben Entwicklung.

## Ursachen und verglichene Ansätze

Die bisherige Restbildsegmentierung sieht verbundene Farbflächen als eine
Komponente. Außerdem behandelt `scene_key` Kinder als ungeordnet, und die
Add/Replace-Agenda verwirft jede Überdeckung. Zusätzliche Parameteroptimierung
kann diese drei strukturellen Ausschlüsse nicht beseitigen.

1. Der unveränderte Runtime-Stand scheitert an allen zwölf vorher eingefrorenen
   Fällen: **0/12**. Eine gemeinsame Boundingbox für die verbundene Restfläche
   erfüllt das verlangte Inventar nicht.
2. Die gewählte Lösung trennt beobachtete flache Farben und schätzt vier
   Subpixelkanten ausschließlich an freiliegenden Seiten. Anschließend
   untersucht der vorhandene Scheduler die Reihenfolgen. Die erste Umsetzung
   mit ausschließlich den bisherigen lokalen/globalen Rastergates akzeptiert
   noch drei falsche Schichtreihenfolgen in zwölf gezielten Prüfungen: Eine
   kleine andersfarbige Schnittfläche kann in einer größeren Region zu wenig
   Gewicht haben. Die endgültige Geometrieprüfung bindet deshalb die vordere
   Instanz zusätzlich an ihre beobachtete Füllfarbe innerhalb der Schnittfläche.

Eine unabhängige Beschädigungskontrolle vertauscht anschließend nur die beiden
nativen Kinder der zwölf erfolgreichen Ausgaben. Sieben dieser falschen
Reihenfolgen bestehen weiterhin alle bisherigen produktiven Regionsgates;
der unabhängige native Reihenfolgeprüfer weist alle zwölf zurück.
`wrong-order-audit.json` und `wrong_order/` erhalten diesen Gegenbeleg.

Der neue `reorder`-Operator verwendet dieselbe begrenzte Agenda, negative
Evidenz, Registrierung, Rendercache und Bildzeitaufsicht wie Add/Remove/Replace.
Überdeckungsvertrag und geordnete Objektidentität gehören zum Ablehnungsschlüssel:
Eine abgelehnte Reihenfolge sperrt die andere nicht. Doppelte native Instanzen
werden auch bei erlaubter Überdeckung nicht hinzugefügt. Die alten ungeordneten
Schlüssel bleiben für getrennte Kinder erhalten.

Alle bisherigen Objekt-, Containment-, Regions- und Bildgrenzen gelten weiter.
Die vorhandene native Überdeckungsprüfung wird wiederverwendet; insbesondere
ist Verschachtelung kein Ersatz für teilweise Überdeckung. Gleiche Farben,
fehlende Seitenbelege, Textur und unbekannte Aussagen werden zurückgewiesen.

## Nachweise

Alle CLI-Gegenproben verwenden die echte überwachte `semantic-only`-CLI,
**fünf Sekunden je Bild** und **Suchseed 17**. Der unabhängige Nachprüfer
kontrolliert native Instanzen, Formklassen, Boundingboxen, Verlaufsachse,
Elternrelation und jetzt zusätzlich die relative Zeichenreihenfolge der Kinder.
Objektregionen und das vollständige Originalraster werden erneut gerendert;
beide Referenzvektor-Zugriffswächter müssen leer sein.

| Kohorte | Ergebnis |
| --- | --- |
| Zwölf vor Runtime-Änderung eingefrorene Fälle, beide Verlaufsachsen, verschiedene Lagen/Farben und beide Schichtreihenfolgen | vorher 0/12, nachher 12/12 unter neutralen Dateinamen |
| Zwölf zusätzliche synthetische Fälle, Geometrie-/Farbseed 381217 | 12/12 |
| Genau eine gekoppelte Plan-B-Vorlage, Original und 16 Größen-/Lagevarianten | 17/17 |
| Frische lokale Wiederholung des CI-Seeds 391827 | 12/12 |
| Bekannte gerundete Szenen mit hellen Konturen | 12/12 |
| Bekannte gerundete Szenen ohne Konturen | 12/12 |
| Bekannte Split-/Operatorfälle | 20/20 |
| Bekannte Restbildfälle einschließlich zweier kontrastarmer Fehlschläge | 7/9 |

Alle **51 erfolgreichen Bestandsausgaben** dieser vier Kohorten sind bytegleich
zum vorherigen Teilabschluss. Alle **379 gespeicherten Archivpaare** behalten
ihre **758 Bild-/SVG-Prüfsummen**. Dies ist eine Bestandsprüfung, keine erneute
Konvertierung aller Archiveingaben und keine neue Katalogabnahme.

Die **36 neuen gezielten Tests** prüfen außerdem falsche Reihenfolge,
geordnete Deduplizierung, Ablehnungsspeicher, fehlende/zusätzliche Instanzen,
gleiche Farben, verdeckte Seiten, Verschachtelung, Trennung statt Überdeckung,
Textur, falsche Formklasse, Objekte außerhalb des Kreises, nicht unterstützte
Kombinationen und Budgetablauf vor der Registrierung. Die Abschlussresultate
der Bestandstests (**183 bestanden**, einschließlich der 36 neuen Tests) und
der Standardsuite stehen zusammen mit Syntax-, CLI- und Runtime-ID-Prüfung in
`checks.json` und den gespeicherten Protokollen. Die gesamte CLI-Evidenz wurde
aus ausschließlich den für Git vorgesehenen Dateien in einen separaten Ordner
kopiert und dort unabhängig erneut geprüft; alle acht Kohortenzähler bleiben
erhalten (`package-verification.json`).

Die vollständige Standardsuite besteht mit **4.064 bestandenen und 30
übersprungenen Tests**, ohne Fehler. Fünf nach ihrem Start ergänzte
Negativkontrollen bestehen zusätzlich im finalen 36-Testlauf und sind in den
183 gezielten Bestandstests enthalten. Der Gesamtlauf misst 5.520,58 Sekunden
Wandzeit; darin liegt eine beobachtete Ausführungsunterbrechung von rund
50 Minuten (eine angeforderte Wartezeit von 60 Sekunden kehrt erst nach
2.996,986 Sekunden zurück). Diese Dauer wird nicht als aktive Test- oder
Konvertierungszeit ausgegeben. Syntax, CLI-Hilfe, Runtime-ID-Nullprüfung und
Whitespace-Prüfung mit den bestehenden Windows-Zeilenenden bestehen.

Eingaben, tatsächliche SVGs, Laufzeitprüfsummen, Berichte und Zugriffsnachweise:
[`artifacts/evaluation/overlap_composition_v1/`](../artifacts/evaluation/overlap_composition_v1/README.md).
Die CI erzeugt weitere synthetische Szenen und wiederholt die echte CLI samt
unabhängiger Nachprüfung.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_overlap_composition.py
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --prepare .tmp/overlap-inputs --seed 391827
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs .tmp/overlap-inputs --output .tmp/overlap-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs .tmp/overlap-inputs --output .tmp/overlap-cli --verify-only --require-all
```
