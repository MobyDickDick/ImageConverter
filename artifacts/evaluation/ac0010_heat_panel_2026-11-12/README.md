# AC0010: Heizelement und wiederholte Fehlversuche

Die drei GUI-Versuche vom 12.11.2026 sind in `summary.json` mit Job-ID,
Suchseed, SVG-Hash, Kandidatenzahl und ursprünglichen Qualitätswerten erfasst.
Sie prüften 1917, 1833 und 1832 Kandidaten mit verschiedenen Seeds. Die SVGs
waren verschieden, unterschieden sich gerastert aber im Mittel um weniger als
einen Grauwert pro Kanal. Alle drei endeten mit `supported_models_exhausted`.
Die Vordergrund-IoU blieb bei rund 0,745 statt der geforderten 0,85.

Der bisherige elementweise Fit suchte das Plus anhand heller Bildbereiche,
erzwang wegen „Plus-Minus-Zeichen“ einen zusätzlichen Minusstrich und verfeinerte
danach den falschen Aufbau. Eine andere Suchreihenfolge konnte das fehlende
Modell nicht ersetzen. Das Original zeigt nur ein dunkles Plus.

Der neue allgemeine Raster-Fit vermisst Rahmen, Diagonale, beide Plusarme und
gegebenenfalls einen tatsächlich sichtbaren Minusstrich als getrennte Komponenten.
Rahmendicke, Positionen, Strichbreiten und fünf kontinuierliche Verlaufsstopps
werden am Raster registriert. Es werden keine Bild-IDs oder Referenz-SVGs im
Laufzeitpfad verwendet. Fehlende Plusarme, zusätzliche Objekte, falsche Diagonale
und unpassende Farben werden abgewiesen. Ein ausdrücklich beschriebenes
„Plus und Minus“ benötigt beide beobachteten Zeichen; der alte zusammengesetzte
Familienbegriff bleibt für bestehende Uploads verwendbar.

Beide Kataloge beschreiben AC0010 jetzt ausdrücklich mit Plus und ohne separates
Minus. Andere Katalogeinträge und bestehende Sample-SVGs wurden nicht verändert.
Die GUI erläutert bei ausgeschöpften Modellen, weshalb ein weiterer Versuch
wieder denselben fehlerhaften Aufbau liefern kann.

## Abnahme

Zwei echte `semantic-only`-CLI-Läufe mit der bisherigen Beschreibung, neutralem
Eingabenamen `UPLOAD.jpg`, Seeds 42 und 314159 und dem normalen GUI-Zeitbudget
bestehen die Prüfung des gespeicherten SVGs. Die festen Grenzen bleiben erhalten.

| Seed | Kandidaten | IoU MuPDF | IoU librsvg | Kantendeckung librsvg |
|---|---:|---:|---:|---:|
| 42 | 1776 | 0,9304 | 0,9212 | 0,8908 |
| 314159 | 1876 | 0,9316 | 0,9218 | 0,8943 |

Beide Renderer bestehen sämtliche Pixelgrenzen. `AC0010.svg` ist die Ausgabe
des ersten Laufs; die Seed-Unterordner enthalten beide Ergebnisse, Raster und
Suchprotokolle. Das native SVG enthält einen Rahmen, eine Diagonale, ein Plus
und einen Verlauf, keine eingebetteten Raster oder nachgezeichneten Pixelkonturen.

206 gezielte Tests bestehen: 16 neue Heizelementprüfungen, 26 bestehende GUI-Tests
und 164 Tests für bisherige Symbolpfade, Geometrie, neutrale Laufzeitnamen und
das benachbarte Panelmodell. Zwei GUI-Systemtests benötigten eine Wiederholung
außerhalb der Sandbox, da diese lokale Sockets und das Beenden eigener
Testprozesse blockiert. Diese Wiederholung besteht ebenfalls.

Die sechs unabhängigen synthetischen Fälle variieren die Auflösung und das
Vorhandensein eines Minuszeichens. Das ist keine allgemeine Abnahme beliebiger
Heizelemente oder aller Katalogmotive. Der neue Fit unterstützt dunkle,
getrennte Zeichen auf einem grauen horizontalen Verlauf; andere Strukturen
behalten die bestehenden Suchwege.
