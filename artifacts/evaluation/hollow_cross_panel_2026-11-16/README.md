# AC0140_L: Raute und ausgesparte Diagonale

Das Original besitzt zwei lange Diagonalen, eine davon mit hellem Innenstreifen,
und eine ungefüllte Raute im Zentrum. Die gespeicherte Nutzerbeschreibung bleibt
unverändert. „Mitte ausgeschnitten“ bezeichnet hier den Innenstreifen entlang der
Diagonale, keine Unterbrechung am Kreuzungspunkt.

Die bisherige generische Konstruktion konnte nur vollständige Vollbänder und
zusätzliche Korrekturlinien darstellen. Die Raute fehlte. Globale Rastergrenzen
liessen diesen Entwurf trotzdem passieren; beim erneuten Start übernahm die
Sample-Anpassung ihn nach nur einer Prüfung unverändert.

Der neue rastergestützte Aufbau schätzt beide Achsen, Streifenbreiten,
Verlaufsmaximum und vier Rautenkanten aus den Originalpixeln. Er liefert sieben
native Vektorformen. Raute und Diagonalen erhalten zusätzlich lokale Fehlerprüfungen.
Eine Beschreibungsassertion verlangt die sichtbaren vier Kanten und den hellen
Innenstreifen auch bei beliebig kodierten vorhandenen SVGs. Fehlende, gefüllte
oder offene Rauten und fehlende Innenstreifen werden zurückgewiesen. Die
globalen Qualitätsgrenzen bleiben unverändert.

Der Aufbau ist in die reguläre CLI und den GUI-Nachbesserungsweg eingebunden.
Ein als Sample übernommener fehlerhafter Entwurf wird dadurch weiterbearbeitet.
Versionsnummer 6 veranlasst beim nächsten Serverstart die erneute Prüfung alter
grüner Ergebnisse. Der laufende Hintergrunddienst wurde nicht unterbrochen.

## Ergebnis

- [Original / bisher / korrigiert](comparison.png)
- [Korrigiertes SVG](AC0140_L.svg)
- [Kompakte Messdaten](summary.json)
- [Regressionen](tests-final.log): 166 bestanden.
- [Frischer und Sample-GUI-Pfad](gui-tests.log): 2 bestanden.
- [Abschliessende gezielte Wiederholung nach der Vertragsprüfung](verified.log): 12 bestanden.

Das Original wurde mit Seed 34 als neuer Vordergrundauftrag im laufenden lokalen
Server konvertiert: `556decd0ff4e4f0f8f0b1d325e11aec7`. Das geprüfte Ergebnis ist
unter `artifacts/converted_images/converted_svgs/AC0140_L.svg` gespeichert;
das vorherige SVG bleibt in der Projekthistorie und als `before.svg` erhalten.

| Prüfung | Bisher | Korrigiert, MuPDF | Korrigiert, librsvg |
| --- | ---: | ---: | ---: |
| Normalisierter MSE | 0,00299232 | 0,00013746 | 0,00033781 |
| Kantenübereinstimmung | 0,72274 | 0,94307 | 0,94299 |
| Vordergrund-IoU | 0,90523 | 0,96624 | 0,95698 |

Der MSE sinkt mit dem bisherigen Messrenderer um 95,4 %. Beide Renderer bestehen
die unveränderten globalen Prüfungen. Der alte Entwurf scheitert an der neuen
Detailassertion. Regressionen verwenden außerdem unabhängige synthetische
Szenen in drei Größen sowie bewusst beschädigte Gegenproben. Die Unterstützung
ist auf das explizit beschriebene graue Verlaufspanel mit der innen ausgesparten
aufsteigenden Diagonale und der mittigen Raute begrenzt; sie ist kein Nachweis
einer allgemeinen Freiformerkennung oder einer Abnahme anderer Katalogvarianten.
