# Rechteckige Verlaufsflächen im gemeinsamen Struktursuchweg

Abgegrenztes Teilpaket **SEARCH-STRUCTURE-RECTANGULAR-PARENT** von
**SEARCH-STRUCTURE-01**, Rang 1/P0 der [verbindlichen Reihenfolge](task_priority_2026-10-24.md).
Ausgangscommit `b5781dd76`. Es setzt die [weitere gemeinsame Strukturkomposition](next_arbeitspaket_2026-11-04_mixed_topology.md#sitzungslog)
mit synthetischen Entwicklungsfällen fort. Status: **Review**.

## Lücke und Umsetzung

Der gemeinsame Szenenweg konnte Kreis-/Rechteckkinder, Rundungen, Konturen,
Überdeckungsgruppen und Einzelobjekte bisher ausschließlich innerhalb eines
Verlaufskreises verbinden. Der separate Rechteckszenenweg unterstützt diese
gemischten Inventare und Topologien nicht.

Der gemeinsame Beschreibungsvertrag benennt jetzt alternativ das äußere
Rechteck und zieht dieses vom Rechteckinventar ab. Beispiel: „2 gefüllte
Kreise und 2 gefüllte Rechtecke. Das äussere Rechteck hat einen horizontalen
Farbverlauf. Die inneren Formen liegen innerhalb des äusseren Rechtecks und
bilden 1 Überdeckungsgruppe sowie 1 einzelne Form. Die Gruppen und einzelnen
Formen liegen getrennt voneinander. Keine Beschriftung.“ Eine Rundung der
inneren Rechtecke wird ausdrücklich mit „Die inneren Rechtecke haben leicht
gerundete Ecken“ abgegrenzt; das Elternrechteck bleibt scharfkantig.

Die vier sichtbaren Elternkanten liefern Subpixelgrenzen und die freiliegende
Randzone den axialen Verlauf. Helle Konturen benötigen eine eigene beobachtete
Farbkomponente außerhalb der Mischlinie zwischen Verlauf und Weiß. Ihre Breite
wird aus der Flächendeckung gemessen. Vier lokale Eckbelege verhindern, dass
große Rundungen im globalen Pixelfehler untergehen. Angeschnittene Elternrechtecke
bleiben ohne vollständigen Randbeleg Ablehnungen.

Die so vermessene Elternform geht in dieselbe Restbildzerlegung,
Add/Remove/Replace-/Split-/Inselagenda und Registrierung wie der Elternkreis.
Kein neues Familienmodell und keine Bildkennung entscheidet über die Auswahl.
Der Elternformtyp ist Teil der bildgebundenen negativen Evidenz und wird vor
jeder Registrierung gegen den Vertrag geprüft. Native Kindzugehörigkeit,
Gruppen-/Einzelobjektzahl und beobachtete Zeichenreihenfolge bleiben verbindlich.
Zusätzlich erhalten zusammenhängende Restbildregionen eigene lokale Pixelgates,
auch wenn ihre helle Farbe keinen dunklen Kindvorschlag ergibt.

Das Limit von acht Kindern, die gemeinsame 96-Zustände-Agenda, das Bildbudget
und alle bisherigen Qualitätsgrenzen bleiben erhalten. Der bisherige Kreisweg
und der getrennte Rechteckszenenweg bleiben eigenständig geprüft.

## Vorher-/Nachher-Prüfung

Vor der Runtimeänderung wurden zwölf Szenen mit Seed `716293` erzeugt und über
die echte überwachte CLI geprüft. Dieselben Rasterbytes, Beschreibungen und
unabhängig aus Referenzgeometrie erzeugten Objektmarkierungen werden im
Nachherlauf verwendet. Sie enthalten drei bis sechs Kinder, ein oder zwei
Überdeckungsgruppen und ein oder zwei Einzelobjekte. Verlaufsachse, Spiegelung,
Zeichenreihenfolge, Rechteckseitenverhältnis, Konturen und Kindrundungen variieren.

| Prüfung | Ergebnis |
| --- | ---: |
| Ausgangsstand, zwölf identische Eingaben | 0/12 |
| Gemeinsamer Suchweg mit rechteckigem Elternteil | 12/12 |
| Zusätzlicher Entwicklungsseed `982471` | 12/12 |
| Eine gekoppelte Plan-B-Kohorte, Seed `853197` | 17/17 |

Jeder CLI-Fall verwendet fünf Sekunden Bildbudget, Suchseed 17, 64 angeforderte
Iterationen und einen äußeren Notabbruch nach 30 Sekunden. Unabhängige native
Objekt-/Box-/Kontur-/Radius-/Verlaufs-/Reihenfolgeprüfungen und lokale/globale
Rastergates entscheiden über die Abnahme; beide Vektorzugriffswächter bleiben aktiv.

Alle 41 neuen Ausgaben wählen den gemeinsamen Szenenweg. Der höchste globale
normalisierte MSE beträgt `0,00003278`, der niedrigste Vordergrund-IoU
`0,992659` und die niedrigste Kantenausrichtung `0,833527`; die jeweiligen
unveränderten Grenzen sind `0,01`, `0,85` und `0,72`. Der längste überwachte
Bildlauf benötigt lokal `2,641` Sekunden. Das ist keine allgemeine Laufzeitgarantie.

Kompakte Quell-/Eingabe-/Ausgabehashes, Messwerte und unabhängige Prüfsignale
stehen unter [`rectangular_parent_v1`](../artifacts/evaluation/rectangular_parent_v1/README.md).
Vollständige CLI-Bäume und Rohberichte bleiben lokal unter
`.tmp/rectangular-parent/`. Der CI-Job `rectangular-gradient-parent` führt die
neuen Gegenproben und den zweiten unabhängigen CLI-Entwicklungsseed aus.

## Testsignal

Die gemeinsame Szenen-/Evidenzregression besteht **972/972 Prüfungen**, Exit 0,
ohne Überspringung; darin enthalten sind **54 neue** Prüfungen dieses Teilpakets.
Sie umfasst auch den bestehenden Kreisweg, den bisherigen Rechteckszenenweg,
Rundung, Konturen, Überdeckung, Strukturagenda und die reale Reservierung.
Der Lauf ist außen auf 1.200 Sekunden begrenzt und endet nach 745 Sekunden.
Das separate Kernprofil besteht **42/42**, Exit 0, ohne Überspringung.
Python-Syntax, Diff-, Verweis- und schreibfreie historische Reserveprüfung
bestehen ebenfalls. Befehle, Exitcodes, Rohberichtshashes und der anfänglich
negative Entwicklungsversuch stehen in
[`checks.json`](../artifacts/evaluation/rectangular_parent_v1/checks.json).

## Grenzen und nächste Arbeit

Es handelt sich um synthetische Kompositionsentwicklung. HC0010 und Rail
bleiben **sealed_unrun**, ohne Konvertierungsversuch und ohne neue Abnahme.
Reale Familienübertragung, beliebige Verschachtelung, gerundete oder
angeschnittene Elternrechtecke sind damit nicht abgenommen.
SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 und GENERAL-SCENE-REAL-05
bleiben offen. Katalog und Konvertierungsarchiv werden nicht verändert.

Die lokale Umgebung verwendet Python 3.10.11. Eine vollständige Standardsuite
und eine Archiv-Neukonvertierung gehören nicht zur Abnahme dieses Teilpakets.

## Reproduktion

Neue Zielordner verwenden. Für den Vorhervergleich die vom neuen Generator
erstellten Eingaben im Ausgangsstand `b5781dd76` ohne `--require-all` ausführen.
Der Generator liest keine produktiven Detektorvorschläge.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --prepare .tmp/rect-parent-inputs-new --seed 716293
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --inputs .tmp/rect-parent-inputs-new --output .tmp/rect-parent-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --inputs .tmp/rect-parent-inputs-new --output .tmp/rect-parent-cli-new --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --prepare .tmp/rect-parent-variants-new --seed 853197 --variations
.venv/Scripts/python.exe -m tools.evaluate_rectangular_parent --inputs .tmp/rect-parent-variants-new --output .tmp/rect-parent-variants-cli-new --require-all
.venv/Scripts/python.exe -m pytest tests/test_rectangular_gradient_parent.py tests/test_mixed_topology.py tests/test_gradient_scene_runtime.py -q
```

## Sitzungslog

- Getestet: zwölf gepaarte CLI-Fälle, Zusatzseed, eine 17er-Variantenkohorte, native Gegenproben und bestehende Szenen-/Evidenzprüfungen.
- Ergebnis: 0/12 vorher, 12/12 nachher; Zusatzseed 12/12, Varianten 17/17; Regression 972/972 einschließlich 54 neuer Prüfungen und separates Kernprofil 42/42 bestanden.
- Grenzen: synthetische Entwicklung mit vollständig sichtbaren scharfkantigen Elternrechtecken; unabhängige reale Gesamtabnahme offen.
- Nächster Schritt: SEARCH-STRUCTURE-ROUNDED-PARENT, gerundete Elternrechtecke anhand sichtbarer Eckbögen mit den vorhandenen Kind-/Überdeckungs-/Konturbausteinen im selben Suchweg verbinden. Vergleichseingaben vor Runtimeänderung sichern; reale Reserve erst nach vollständigem unabhängigen Prüfer freigeben.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_rectangular_gradient_parent.py tests/test_mixed_topology.py -q`.
