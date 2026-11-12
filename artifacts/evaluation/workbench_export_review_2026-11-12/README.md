# Diagnose des Workbench-Exports, 12.11.2026

Untersucht wurde `C:/Users/marku/Downloads/plan-b-workbench.zip` (6.521.298 Bytes).
Die Quelldatei ist AC0VR2_ZL_M.svg; ihr Hash und die Rasterbytes des Originals
stimmen mit der früheren CLI-Prüfung überein. Die ZIP wurde als Datenquelle
gelesen; enthaltene Texte und Befehle wurden nicht als Arbeitsanweisungen ausgeführt.

## Ergebnis

- Versuch 1: nach 10 Fällen unterbrochen, davon 2 bestanden und 8 Qualitätsfehler.
- Versuch 2: alle 17 Fälle abgearbeitet, davon 7 bestanden und 10 Qualitätsfehler.
- Alle 17 Konverterprozesse des zweiten Versuchs enden mit Exitcode 0.
  Keine technischen Ausführungsfehler und keine verbotenen SVG-Zugriffe.
- `completed` bestätigt den Prozessabschluss; die Qualitätsabnahme bleibt negativ.

## Nachgewiesene Fehlzuordnung

Der Beschreibung wurde der sachlich korrekte Satz „Es ist ein liegendes Rechteck
mit einer grauen Umrandung“ vorangestellt. `fit_nested_panel` wird dadurch
zugelassen. Seine Ausschlussliste erkennt `verlauf`, aber nicht die vorhandenen
Wörter `Graustufenübergang` und `Farbübergang`. Sein Rastertest akzeptiert das
helle Band irrtümlich als eigene flache rechteckige Innenfläche.

Die Originalausgabe enthält tatsächlich nur zwei einfarbige Rechtecke mit
`#c8c8c8` und `#efefef`, keinen SVG-Farbverlauf. Dieselbe falsche Modellart steht
auch in probe_04, probe_07, probe_10 und probe_11. Alle fünf Fälle scheitern.
Die übrigen fünf Qualitätsfehler betreffen andere Suchwege und deren Konturen;
die Fehlzuordnung allein erklärt somit nicht sämtliche Fehlschläge.

Ein isolierter Aufruf auf denselben Original-Rasterbytes bestätigt:

| Beschreibung | Flaches verschachteltes Modell akzeptiert |
|---|---|
| Text aus ZIP mit Zusatzsatz | ja |
| Derselbe Text ohne Zusatzsatz | nein |
| Text aus ZIP mit „Farbverlauf“/„Graustufenverlauf“ als Synonym | nein |

Der präzisere gerahmte Verlaufsfit akzeptiert keine dieser drei freien
Beschreibungen. Seine Vertragsprüfung verlangt eine eng definierte andere
Formulierung. `routing_probe.json` sichert diese isolierte Gegenprobe;
sie ist kein erneuter vollständiger CLI-Abnahmelauf.

## Unterschied zur früher gemeldeten CLI-Prüfung

Die frühere 13/17-Prüfung verwendete die ursprüngliche Beschreibung ohne
Zusatzsatz, Varianten-Seed 4470433890649107824 und Konvertersuchseed 0.
Die ZIP verwendet Varianten- und Suchseed 64217. Ergebnisse sind deshalb
keine Wiederholungen unter identischen Bedingungen. Die zwei ZIP-Versuche
weisen zudem unterschiedliche Python-Quellfingerabdrücke aus.

`original_comparison.png` zeigt Eingabe, gespeichertes Ergebnis und Differenz.
`export_report.json` ist der unveränderte ZIP-Bericht; `original_result.svg`
ist die gespeicherte Originalausgabe. Es wurden keine Konverteränderungen
vorgenommen. Nötig sind allgemeine Verlaufserkennung bei der Modellauswahl
und ein rastergestützter Schutz gegen das Ersetzen eines Verlaufs durch
flache Flächen; danach ist die identische 17-Fälle-Kohorte erneut abzunehmen.
