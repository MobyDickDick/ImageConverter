# Überdeckungsgruppen und einzelne Formen gemeinsam komponieren

Abgegrenzter Entwicklungsschritt **SEARCH-STRUCTURE-MIXED-TOPOLOGY**, Teil von
**SEARCH-STRUCTURE-01**, Rang 1/P0 der [verbindlichen Reihenfolge](task_priority_2026-10-24.md).
Ausgangscommit `88d062c00`. Er setzt den [dokumentierten nächsten Schritt](next_arbeitspaket_2026-11-03_real_family_freeze.md#sitzungslog)
mit synthetischen Entwicklungsfällen fort. Status: **Review**.

## Lücke und Umsetzung

Die bisherige gemeinsame Verlaufssuche unterstützte entweder getrennte Kinder
oder Gruppen, in denen jedes Kind an einer Überdeckung beteiligt ist. Eine
Mischung aus Überdeckungsgruppen und einzelnen Formen wurde vom vollständigen
Beschreibungsvertrag zurückgewiesen. Zusätzliche Parameteroptimierung konnte
diese Struktur nicht herstellen.

Der gemeinsame Vertrag enthält jetzt die Anzahl der Überdeckungsgruppen und
der einzeln stehenden Formen. Beispiel: „Die inneren Formen liegen innerhalb
des äusseren Kreises und bilden 2 Überdeckungsgruppen sowie 1 einzelne Form.
Die Gruppen und einzelnen Formen liegen getrennt voneinander.“ Der vorhandene
Primitive-/Rundungs-/Konturdetektor erzeugt die Instanzen aus Originalpixeln;
keine neue Symbolvorlage oder Katalogkennung wird verwendet.

Während jeder Registrierung wird der Graph der nativen Überdeckungen geprüft:
genau die verlangten Komponenten mit mindestens zwei Kindern, genau die
verlangten Einzelobjekte und getrennte native Konturen zwischen allen
Komponenten. Boxüberschneidungen allein liefern keinen Tiefenbeleg. Beobachtete
Füllungen beziehungsweise Konturen begründen die Zeichenreihenfolge; eine
vertauschte Reihenfolge bleibt eine Ablehnung. Die bildgebundene negative
Evidenz enthält auch die Anzahl der Einzelobjekte, sodass ein falscher
Vertrag keinen späteren richtigen Vertrag sperrt.

Das bestehende Limit von acht Kindern, das gemeinsame Bildbudget und die
96-Zustände-Agenda bleiben erhalten. Alle Beschreibungsaussagen müssen
verbraucht sein. Vollständiges Inventar, Rundung, Konturen, Elternzugehörigkeit,
lokale und globale Rasterqualität bleiben verbindlich.

## Vorher-/Nachher-Vergleich

Vor der Runtimeänderung wurden zwölf synthetische Szenen mit Seed `641927`
gesichert und über die echte überwachte CLI geprüft. Sie kombinieren ein oder
zwei Überdeckungsgruppen mit ein oder zwei einzeln stehenden Formen, insgesamt
drei bis sechs Kreis-/Rechteckkinder. Spiegelung, Zeichenreihenfolge und
Verlaufsachse variieren; Rechtecke sind gerundet und alle Formen hell konturiert.
Der Nachherlauf verwendet dieselben Rasterbytes, Beschreibungen und unabhängig
generierten Objektmarkierungen.

| Prüfung | Ergebnis |
| --- | ---: |
| Ausgangsstand auf zwölf Vergleichseingaben | 0/12 |
| Erweiterter Szenenweg auf denselben Eingaben | 12/12 |
| Zusätzlicher Entwicklungsseed `972431` | 12/12 |
| Eine gekoppelte Plan-B-Kohorte, Seed `853197` | 17/17 |

Jeder CLI-Fall erhält unverändert fünf Sekunden Bildbudget, Seed 17,
64 angeforderte Iterationen und einen äußeren Notabbruch nach 30 Sekunden.
Die unabhängige Nachprüfung kontrolliert native Objektzahl/-art, Boxen,
Konturbreiten, Radien, Verlaufsausrichtung, Zeichenreihenfolge und lokale/globale
Pixelgates. Beide Vektorzugriffswächter bleiben erforderlich.

Bei der Vorbereitung ergänzte der Referenzgenerator explizite SVG-Standardwerte
für Verlauf und Stopposition, damit der native Prüfer auch die Referenz selbst
prüfen kann. Alle zwölf Rasterprüfsummen, Beschreibungen und Objektmarkierungen
blieben dabei identisch; die Vergleichseingaben wurden nicht nachgestimmt.

## Nachweise und Grenzen

Der Szenenregressionsblock besteht **658/658 Prüfungen**, darunter **59 neue**
Prüfungen dieses Teilpakets; keine Überspringung. Der kombinierte
Entwicklungsdurchlauf mit zusätzlichen 55 Evidenzprüfungen endete zunächst
mit 712 bestandenen Prüfungen und genau dem alten Freeze-Test als Fehler.
Nach dessen unten beschriebener Korrektur bestehen die betroffenen
Evidenzprüfungen separat **55/55**, Exit 0. Zwischen diesen Läufen wurde
ausschließlich der Freeze-Test geändert; die produktive Runtime blieb
identisch. Das separate Kernprofil besteht **42/42**, Exit 0.
Syntax-, Diff-, Verweis- und schreibfreie Reserveprüfung bestehen ebenfalls.
Es wird kein einzelner grüner kombinierter 713er-Lauf behauptet.

Kompakte Eingabe-/Ausgabe-/Runtimehashes und Prüfsignale stehen unter
[`mixed_topology_v1`](../artifacts/evaluation/mixed_topology_v1/README.md).
Die vollständigen CLI-Bäume und Rohberichte bleiben lokal unter
`.tmp/mixed-topology/`. Der bestehende CI-Job `disconnected-overlap-groups`
führt die neuen Gegenproben und einen unabhängigen CLI-Entwicklungsseed mit aus.

HC0010 und Rail bleiben unverändert **sealed_unrun**; sie wurden weder
konvertiert noch zur Entwicklung herangezogen. Die Vorprüfung bestätigte den
damals unveränderten Runtime-Stand. Nach der Entwicklung prüft der schreibfreie
Nachprüfer die historische Versiegelung ohne aktuellen Runtimevergleich.
Das Paket belegt synthetische Komposition, keine neue reale Familienabnahme.
SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 und GENERAL-SCENE-REAL-05
bleiben offen. Es gibt keinen Kataloggewinn und keine Archivänderung.

Der bisherige Freeze-Regressionstest setzte dauerhaft Gleichheit zwischen
historischer und aktueller Runtime voraus. Er prüft jetzt die unveränderliche
historische Versiegelung. Die frische Testversiegelung verlangt weiterhin
aktuellen Runtimevergleich; eine zusätzlich simulierte Quelländerung muss
beim expliziten Vergleich scheitern, während die historischen Prüfsummen
unverändert gültig bleiben. Die produktive Sperr-/Prüflogik wurde nicht geändert.

Die lokale Umgebung ist Python 3.10.11. Eine vollständige Standardsuite und
eine Archiv-Neukonvertierung gehören nicht zur Abnahme dieses Teilpakets.

## Reproduktion

Neue Zielordner verwenden. Für einen neuen Vorhervergleich denselben
Eingabebestand im Ausgangscheckout `88d062c00` ausführen; der neue Generator
importiert keinen produktiven Detektor.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --prepare .tmp/topology-inputs --seed 641927
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --inputs .tmp/topology-inputs --output .tmp/topology-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --inputs .tmp/topology-inputs --output .tmp/topology-cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --prepare .tmp/topology-variants --seed 853197 --variations
.venv/Scripts/python.exe -m tools.evaluate_mixed_topology --inputs .tmp/topology-variants --output .tmp/topology-variants-cli --require-all
.venv/Scripts/python.exe -m pytest tests/test_mixed_topology.py tests/test_overlap_groups.py tests/test_overlap_proposal_reuse.py -q
```

## Sitzungslog

- Getestet: zwölf gepaarte echte CLI-Fälle, Zusatzseed, eine 17er-Variantenkohorte, Szenen-/Evidenzregressionen und Kernprofil.
- Ergebnis: 0/12 vorher, 12/12 nachher; Zusatzseed 12/12, Varianten 17/17; Szenen 658/658, Evidenz nach Testkorrektur 55/55 und Kernprofil 42/42.
- Grenzen: synthetischer Kreis-/Rechteckumfang; unabhängige reale Gesamtabnahme offen.
- Nächster Schritt: weitere gemeinsame Strukturkomposition; reale Reserve erst nach vollständigem unabhängigen Prüfer freigeben.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_mixed_topology.py tests/test_overlap_groups.py -q`.
