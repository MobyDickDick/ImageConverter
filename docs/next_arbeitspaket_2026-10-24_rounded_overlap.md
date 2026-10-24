# SEARCH-STRUCTURE-01: Rundung und Überdeckung kombinieren

Ausgangsstand: `414da01c0` (`main`). Ausgewählt aus dem höchsten offenen
P0-Paket der [verbindlichen Rangfolge](weakness_review_2026-10-23.md).

## Abgeschlossener Teilumfang

Zwei verschiedenfarbige, teilweise überlappende gerundete Rechteckkinder
werden im vorhandenen Verlaufskreis-/Struktursuchweg rekonstruiert. Der
Vertrag kombiniert den vorhandenen Rundungszusatz mit der bestehenden
Überdeckungsrelation, beispielsweise:

> Ein gefüllter Kreis und zwei gefüllte Rechtecke mit leicht gerundeten Ecken.
> Der Kreis hat einen horizontalen Farbverlauf. Die Rechtecke liegen innerhalb
> des Kreises und überlappen sich teilweise. Keine Beschriftung.

Beide Verlaufsachsen und beide Zeichenreihenfolgen sind geprüft. Die native
SVG-Ausgabe enthält weiterhin einen Kreis und zwei Rechtecke mit `rx`.
Es gibt keine zusätzliche Symbolvorlage oder bildspezifische Registrierung.

**SEARCH-STRUCTURE-ROUNDED-OVERLAP ist abgeschlossen; SEARCH-STRUCTURE-01
insgesamt bleibt offen.** Konturen zusammen mit Überdeckung, mehr als zwei
überlappende Kinder, zusätzliche Schichten und die unabhängige reale
Familienabnahme sind nicht durch dieses Teilpaket abgenommen. Alle neuen
Fälle sind synthetische Entwicklung. Vor weiterer realer Entwicklung müssen
andere reale Prüffamilien gesperrt und unabhängig annotiert werden;
GE0018/GE0307 bleiben bekannte Entwicklungsdaten.

## Ursache und Umsetzung

Der vorherige Szenenvertrag schließt Rundung bei Überdeckung ausdrücklich
aus. Außerdem liefert der Überdeckungsdetektor nur eckige Instanzen.
Parameteroptimierung kann diesen strukturellen Ausschluss nicht reparieren.
Die zwölf vor der Runtime-Änderung gespeicherten CLI-Eingaben scheitern
unverändert **0/12**.

Eine Radiusmessung aus dem gesamten Restflächenverlust wäre hier ungeeignet:
Verdeckte Füllung würde als fehlende Eckfläche gezählt. Stattdessen werden
die vorhandenen, aus freiliegenden geraden Seiten geschätzten Boundingboxen
mit einer lokalen Eckmessung kombiniert. Die rekonstruierte Mischung aus
Elternverlauf und eigener Füllfarbe muss die beobachteten Pixel erklären;
Fenster mit fremder Farbe werden für die Radiusmessung ausgeschlossen.
Mindestens zwei sichtbare Ecken je Kind müssen konsistente Radien tragen.
Der integrierte Flächenverlust einer Ecke beträgt `(1 - pi/4) * rx**2`.
Eckige Silhouetten erhalten dadurch keinen beliebig kleinen Ersatzradius.

Die bestehenden Begrenzungen bleiben erhalten: Alle vier Seiten benötigen
beobachtbare gerade Abschnitte; gleiche Farben, vollständig verdeckte Seiten
und zusätzliche Textur rechtfertigen keine Instanz. Konturen bleiben in
diesem Überdeckungsvertrag ausdrücklich nicht unterstützt. Die vorhandene
geordnete Strukturagenda übernimmt Radien in Identität, Deduplizierung und
Ablehnungsspeicher. Eine kontrolliert falsche erste Reihenfolge wird
zurückgewiesen und anschließend durch `reorder` repariert. Native Inventar-,
Containment-, Schnittflächenfarb-, Regions- und Vollbildgates gelten weiter.

## Nachweise

Alle produktiven Vergleiche verwenden die echte überwachte `semantic-only`-CLI,
fünf Sekunden Bildbudget und Suchseed 17. Die unabhängige Nachprüfung prüft
die gespeicherten SVGs erneut auf native Formklassen, Anzahl, Boundingboxen,
Radien, Verlaufsachse, Eltern- und Hinter-/Vordergrundrelation sowie lokale
und globale Rasterqualität. Beide Referenzvektorwächter müssen leer bleiben.

| Kohorte | Ergebnis |
| --- | --- |
| Zwölf vor Runtime-Änderung gespeicherte Eingaben; beide Achsen, gespiegelte Lagen, verschiedene Farben/Radien und beide Reihenfolgen | vorher 0/12, nachher 12/12 mit neutralen Namen |
| Zwölf zusätzliche synthetische Szenen, Seed 381217 | 12/12 |
| Genau eine gekoppelte Plan-B-Vorlage und 16 Größen-/Lagevarianten | 17/17 |
| Frische lokale CLI-Probe des CI-Seeds 391827 | 12/12 |
| Bestehende eckige Überdeckung | 12/12 |
| Bestehende Rundung mit hellen Konturen | 12/12 |
| Bestehende Rundung ohne Konturen | 12/12 |
| Bestehende Split-/Operatorfälle | 20/20 |
| Bestehende Restbildfälle, einschließlich zweier kontrastarmer Fehlschläge | 7/9 |

Alle **63 erfolgreichen Bestandsausgaben** sind bytegleich zum vorherigen
Teilabschluss. Die **379 gespeicherten Archivpaare** behalten ihre **758
Prüfsummen**. Dies ist keine neue Archivkonvertierung oder Katalogabnahme.

**372 gezielte Tests bestehen**: 176 Struktur-/Kompositionsprüfungen und
196 weitere Szenen-/Scheduler-/Evidenzprüfungen in getrennten Modulen.
Darunter sind 26 neue Prüfungen für die Rundungs-/Überdeckungskombination,
einschließlich eckiger Ersatzformen, eines einzelnen eckigen Kindes,
fehlender/zusätzlicher Objekte, verdeckter Seiten, Textur, unbekannter
Aussagen, beschädigter Radien und Reihenfolgen sowie Budgetablauf vor
Registrierung. Syntaxprüfung, CLI-Hilfe und Whitespaceprüfung mit den
bestehenden Windows-Zeilenenden bestehen. Eine vollständige Standardsuite
wurde in diesem Paket nicht ausgeführt.

Die CLI-Nachweise sind zusätzlich aus ausschließlich Git-sichtbaren neuen
Dateien und versionierten bestehenden Eingaben in einem separaten Ordner
erneut unabhängig geprüft. Alle neun Kohortenzähler bleiben erhalten.
Die erste Bestandsvergleichsautomation hatte einen falsch geschriebenen
Evidenzordnernamen; nach dessen Korrektur wurden vorhandene Läufe nachgeprüft
und die verbleibenden Kohorten fortgesetzt. Der technische Fehler und die
Fortsetzung stehen getrennt in `regression.log` und `regression-resume.log`.

Eingaben, tatsächliche Ausgaben, Quellprüfsummen und Ergebnisse:
[Evidenzordner](../artifacts/evaluation/rounded_overlap_v1/README.md).
Die CI prüft zusätzlich generierte Szenen durch dieselbe echte CLI und
unabhängige Nachprüfung. Neue reale Übertragung wird dadurch nicht behauptet.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_rounded_overlap_composition.py tests/test_overlap_composition.py tests/test_rounded_outlines.py tests/test_rounded_composition.py tests/test_structure_search_operators.py tests/test_residual_scene_search.py
.venv/Scripts/python.exe artifacts/evaluation/rounded_overlap_v1/verify.py
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --prepare .tmp/new-rounded-overlap --rounded --seed 391827
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs .tmp/new-rounded-overlap --output .tmp/new-rounded-overlap-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs .tmp/new-rounded-overlap --output .tmp/new-rounded-overlap-cli --verify-only --require-all
```
