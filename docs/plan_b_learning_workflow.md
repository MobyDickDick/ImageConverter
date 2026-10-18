# Aus gescheiterten Plan-B-Aufgaben lernen

Nach jeder erweiterten, gescheiterten Plan-B-Aufgabe gehört die Nachbearbeitung
zum Arbeitspaket. Ein erneuter identischer Lauf ohne neue Hypothese gilt nicht
als Verbesserung. Die bisherigen Qualitätsgrenzen bleiben unverändert.

## Arbeitsablauf

1. Quelle, eigenständige Beschreibung, Seed, Algorithmusstand, Suchbudget,
   tatsächliches Ausgabe-SVG, Messwerte und Laufdiagnosen sichern. Originalfehler,
   Variantenfehler und technische Ausführungsfehler getrennt erfassen.
2. Den konkreten Fehler mit diesen Eingaben reproduzieren. Mit Vergleichsbild und
   lokalen Objektprüfungen bestimmen, ob die Beschreibung, Erkennung, Anzahl,
   Topologie, Lage, Schrift, Farbe, Suche oder Ausführung verantwortlich ist.
   Eine verfehlte Pixelgrenze allein erklärt die Ursache noch nicht.
3. Bestehende Aufgaben nach nachgewiesener gemeinsamer Ursache bündeln. Mehrere
   Seeds oder Größen sind keine unabhängigen Ursachen. Häufigkeit, betroffene
   Bildfamilien und erwartete allgemeine Wirkung bestimmen die Priorität.
4. Mindestens zwei unterschiedliche, überprüfbare Lösungshypothesen formulieren.
   Beispiele: anderes Szenenmodell, weitere Instanz, andere Objektzuordnung,
   gemeinsamer Textzug gegenüber einzeln gesetzten Zeichen, anderer Startpunkt
   oder gemeinsame statt ausschließlich einzelner Parameteränderungen.
5. Die Hypothesen mit protokolliertem Budget vergleichen. Zwischenstände zeigen
   Modell, Suchweg, Seed, Prüfzahl und besten Fehler. Gleiche Kandidaten nicht
   mehrfach rendern. Stagnation ist ein Grund zum Wechsel des Suchwegs.
6. Eine allgemeine Korrektur umsetzen. Original und alle 16 erweiterten Varianten
   über die echte CLI prüfen; fremde Namen, neue Anordnungen, unabhängige
   Holdouts und Gegenproben gegen falsche Freigaben ergänzen. Laufzeit und
   tatsächliche Renderzahlen gehören zur Bewertung.
7. Erfolgreiche Varianten einschließlich Parameter, Beschreibung, Hashes und
   Prüfstatus erhalten. Einen fachlich sinnvollen Regressionstest ergänzen.
   Eine Aufgabe erst nach nachvollziehbarem Vorher-/Nachher-Nachweis schließen.
   Teilfortschritte und verbleibende Fehler bleiben ausdrücklich sichtbar.

Ein Infrastrukturfehler verlangt zunächst eine technische Reparatur. Ein
Algorithmus wird dadurch nicht automatisch fachlich widerlegt. Umgekehrt ist
ein erfolgreicher Prozessabschluss keine Qualitätsabnahme. Ein kleiner fehlender
Gegenstand kann trotz guter globaler Pixelwerte einen inhaltlichen Fehler bilden.

Die vorhandene Erfassung in `tools/report_plan_b_failures.py` liefert die
reproduzierbaren Aufgaben. Die Analyse und allgemeine Codekorrektur sind weiterhin
Entwicklungsarbeit; ein CI-Fehler schreibt den Algorithmus nicht selbst um.
Der historische Bestand muss noch vollständig inventarisiert und gruppiert
werden. Eine Zahl von ungefähr 20 offenen Fällen ist bisher keine verifizierte
Bestandsaufnahme.

## Umgesetzter erster Suchbaustein

Seit der [adaptiven Suchsteuerung](adaptive_conversion_search_2026-10-18.md)
ist im Portfolio `--search-policy adaptive` voreingestellt: geprüfter früher
Erfolg, Suchwegwechsel bei Stagnation und begrenzte Verlängerung bei spätem
Fortschritt. Der nachfolgend beschriebene erste feste Durchlauf bleibt mit
`--search-policy fixed` als Vergleich verfügbar.

Die CLI verwendet standardmäßig `--search-mode portfolio`. `--search-mode legacy`
schaltet die zusätzlichen Parametersuchen ab. Die neue Kurztextregistrierung
vergleicht in beiden Modi vier fachlich verschiedene Modellvarianten: einen
gemeinsamen Textzug oder einzeln gesetzte Zeichen, jeweils normal oder fett.

Analytische Registrierungen auf Basis von `_register` erhalten bei einem noch
größeren Restfehler (RGB-MSE über 0,0001) und verfehltem lokalem Pixelgate drei zusätzliche Suchwege:
umgekehrte Koordinatenfolge, gemischte Koordinatenfolge und gemeinsame
Parameteränderungen mit Neustart. Das ist eine Auslösebedingung für zusätzliche
Arbeit und **keine veränderte Abnahmegrenze**. Bereits sehr genaue Registrierungen
bleiben unverändert. Der bisherige Fit bleibt der Vergleichskandidat; eine
Alternative muss die Suchverlustfunktion verbessern und darf den gemessenen
Fehler des Aufrufers nicht erhöhen.

Im festen Modus begrenzt `--search-budget` die zusätzlichen Prüfungen **je Modell**,
standardmäßig auf 384, aufgeteilt auf drei Suchwege. Im adaptiven Modus ist dies
die Basis; später Fortschritt erlaubt höchstens das Vierfache, Stagnation
beendet die Suche früher. Die ursprüngliche Registrierung und die
Anzahl aktivierter Modelle zählen zusätzlich. Dies ist kein globales Zeitlimit;
der vorhandene Renderer-/Prozess-Timeout bleibt notwendig. Die Suchstatistik
unterscheidet zusätzliche Vorschläge von tatsächlich gerenderten Fits.

Ohne `--search-seed` wird pro CLI-Aufruf ein frischer Seed erzeugt. Ein expliziter
Seed reproduziert Reihenfolge und Vorschläge bei gleichem Code und gleicher
Konfiguration. `[Search]`-Meldungen und `search/progress.jsonl` zeigen Beginn,
Zwischenstände und Ende. Ein einzelner blockierender Renderer kann dadurch
nicht unterbrochen werden; dafür ist dessen eigener Timeout zuständig.

Unter `AUSGABE/search/` bleiben auch erfolglose Suchtrajektorien erhalten.
`validated/` enthält Varianten, die die lokale Kreis-/Textprüfung bestanden
haben, mit einem getrennten Status des strengen Pixelgates. Die Kombination
ersetzt keine vollständige Katalogabnahme. Parameter und SVGs werden als Belege
gespeichert und später nicht als Vektorvorlagen geladen.

Nur `standard` darf zusätzlich `strategy_memory.json` lesen und schreiben.
Erst nach lokaler semantischer Prüfung **und** strengem Pixelpass wird eine
Modellart darin positiv gezählt. Die Statistik priorisiert beim nächsten Lauf
mit demselben Ausgabeverzeichnis erfolgreiche Modellarten; alle vier Modelle
werden weiterhin geprüft. Es gibt noch keine gelernte neue Topologie oder
übergreifende automatische Codeänderung. `semantic-only` liest diese Statistik
nicht und verändert sie nicht.

```powershell
.venv/Scripts/python.exe -m src.imageCompositeConverter EINGABE --descriptions-path BESCHREIBUNGEN.xml --output-dir AUSGABE --start ERSTES --end LETZTES --search-mode portfolio --search-seed 42 --search-budget 384
```

Die vollständige allgemeine Struktursuche bleibt unter `GENERAL-SCENE-01` offen:
Objekte ergänzen/ersetzen, alternative Szenen zusammensetzen und bislang
unerklärte Rasterbereiche gezielt behandeln. Die jetzige Erweiterung vergleicht
neue Textmodelle und andere Parametersuchwege innerhalb unterstützter Modelle.

Siehe [UML-Ablauf](conversion_search_uml.md) und
[AC0840-Arbeitspaket](next_arbeitspaket_2026-10-17_ac0840_search.md).
