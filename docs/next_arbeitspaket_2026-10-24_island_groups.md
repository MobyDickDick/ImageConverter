# P0: gleichfarbige Instanzen mit mehreren Sichtbarkeitsinseln

Ausgewählt aus **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[verbindlichen Rangliste](task_priority_2026-10-24.md). Ausgangscommit
`40c84e83e`; separater Branch
`codex/search-structure-island-groups-2026-10-24`.

Status: **Review des beschriebenen Teilumfangs**; die übergeordnete Aufgabe bleibt offen.

## Ursache und Änderung

Die bisherigen Hypothesen vereinigen alle Flächen einer Füllfarbe oder trennen
jede sichtbare Farbkomponente. Beide scheitern, wenn mehrere gleichfarbige
Instanzen gleichzeitig durch spätere Schichten in mehrere Inseln zerfallen.
Die neue Gegenprobe enthält zwei gleichfarbige Kreise und ein darüberliegendes
Rechteck, das beide Füllungen teilt. Alle Kinder bilden weiterhin eine
zusammenhängende Überdeckungsszene.

Nach den bisherigen Vorschlägen untersucht derselbe Suchweg jetzt auch
Zwischengruppierungen. Ausgehend von einzelnen Farbkomponenten werden nur
Gruppen derselben Farbe vereinigt. Ein Abstandswert priorisiert benachbarte
Gruppen; er entscheidet weder Geometrie noch Abnahme. Jeder vollständige
Vorschlag weist jede berücksichtigte Insel (mindestens zwölf Pixel) genau einer Instanz zu. Kanonische
Gruppierungen und die bestehende Szenendeduplizierung vermeiden Wiederholungen.

Höchstens 16 beobachtete Inseln und acht Kinder werden unterstützt. Die
Gruppierung teilt sich die bestehende Grenze von 96 Strukturzuständen mit
Add/Remove/Replace und nachfolgendem Split plus Edit. Zwischen Zuständen wird
an denselben Scheduler zurückgegeben; das gemeinsame Bildbudget bleibt aktiv.
Die bisherige Vereinigung und Einzelkomponentensuche behalten Vorrang.
`island_partition` protokolliert vorgeschlagene beziehungsweise mangels nativer
Randbelege verworfene Gruppierungen. `group_islands` und `grouping_states` machen
Registrierung und Aufwand sichtbar. Registrierungsablehnungen bleiben an
Raster und Beschreibungsvertrag gebunden.

Jede Gruppe benötigt weiterhin sichtbare Kreisbögen beziehungsweise alle vier
Rechteckseiten. Für schmale Brücken muss die Mindestbreite des gefüllten Kerns
fünf beobachtete Seitensamples ermöglichen. Die Konturbreitengrenze von einem
Viertel bezieht sich jetzt auf die gemessene native Box statt auf den kleineren
ganzzahligen Füllkern. Kantenbänder berücksichtigen Antialiasing; gerundete
Kanten verwenden integrierte Deckung. Auch die Rundungsuntergrenze bezieht
sich auf die native Konturmittellinie; eine messbare innere Eckrundung bleibt
zusätzlich erforderlich. Vollständige Objekt-, Relations-, lokale
und globale Rastergates bleiben unverändert. Referenzvektoren und Bildnamen
liefern weiterhin keine Produktionsgeometrie.

## Kontrollierter Nachweis

Zwölf synthetische Eingaben mit Seed `731529`, Rundung und hellen Konturen
wurden vor jeder Runtime-Änderung gespeichert. Der vollständig abgeschlossene
Ausgangslauf besteht **0/12**. Nachher bestehen dieselben Eingaben **12/12**;
Suchzeitabbrüche bleiben im Nenner. Ein früherer Entwicklungsstand besteht
**6/12**, bevor der Bezug der Konturbreite auf die native Box korrigiert wird.
Diese Fehlversuche bleiben in `summary.json` sichtbar.

Der zusätzliche Seed `418267` verbessert sich nach Korrektur des Radiusbezugs
von **10/12 auf 11/12**. Fall `islands_3_06` bleibt absichtlich abgelehnt:
Die schmale gerundete Brücke liefert nur vier statt der geforderten fünf
beobachteten Seitensamples. Dieser bekannte gültige, aber nicht belegbare Fall
bleibt im Nenner und ist als konservative Negativkontrolle festgehalten.
Der zusätzliche Seed `392841` mit drei gleichfarbigen Kreisen verbessert sich
von **11/12 auf 12/12**. Genau eine gekoppelte Plan-B-Vorlage mit Seed `962731`
besteht auf dem endgültigen Code **17/17**.

Die CLI läuft mit Suchseed 17 und fünf Sekunden je Bild. Der unabhängige
Nachprüfer rendert die gespeicherten nativen SVGs erneut und kontrolliert
Instanzen, Geometrie, Zeichenreihenfolge, lokale Regionen und vollständiges
Raster. Eingabe-/Ausgabehashes, Messungen und Zeitaufsicht stehen unter
[`artifacts/evaluation/island_groups_v1/`](../artifacts/evaluation/island_groups_v1/README.md).
Generierte Raster, Vektoren und vollständige CLI-Bäume bleiben temporär.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_island_groups --seed 731529 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_island_groups --seed 418267 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_island_groups --seed 392841 --children 4 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_island_groups --seed 962731 --rounded --outlines --variations
.venv/Scripts/python.exe -m pytest -q tests/test_island_group_search.py
```

Der Wrapper verlangt vollständige Abnahme. Der Befehl mit Seed `418267`
endet deshalb bei der dokumentierten Grenze 11/12 erwartungsgemäß mit Exit 1.
Die anderen drei CLI-Rezepte bestehen vollständig; CI verwendet die
Drei-Kreise-Prüfung und die Plan-B-Vorlage sowie die gezielte Negativkontrolle.

35 neue Tests prüfen zwei beziehungsweise drei gleichfarbige Kreise, Rundung,
helle Konturen, beide Brückenrichtungen, gleichfarbige Rechtecke und gemischte
Formtypen. Fehlende/zusätzliche Instanzen, falsche Anzahlen, unzureichende
Bögen, Fremdtextur, fehlende/dunkle Konturen und eckige Ersatzformen bleiben
Negativkontrollen. Exakte Inselabdeckung, Zustands-/Kandidatengrenzen,
erschöpfte Budgets, Telemetrie und gebundene negative Evidenz sind abgesichert.
Ein CI-Job wiederholt die neue Suite und zusätzliche CLI-/Plan-B-Fälle.

Die breite Regression vor der abschließenden Radiuskorrektur besteht mit
**591 Tests und einem Skip**, Exit 0 (437,42 Sekunden). Am endgültigen Code
bestehen alle betroffenen Gruppierungs-, Kontur-, Rundungs-, Mehrschicht- und
Reihenfolgeprüfungen mit **352 Tests**, Exit 0 (335,00 Sekunden), sowie das
Kernprofil mit **42/42**, Exit 0. Diese sich überschneidenden Zahlen werden
nicht addiert. Der bestehende Skip betrifft Dateisystemlinks, deren Erstellung
Windows-Berechtigungen voraussetzt. Befehle und Modulhashes stehen in `checks.json`.

Die unkonturierten Entwicklungsfixtures verwenden ausdrücklich `stroke="none"`:
Ein vorhandener Stroke mit Breite null wurde vom Renderer als Haarlinie
sichtbar. Diese Korrektur verändert keine der zwölf vorher gespeicherten
konturierten Vergleichseingaben; deren Referenzhashes wurden erneut verglichen.
Die lokale Python-Version ist **3.10.11**, abweichend von `.python-version`
(`3.10.20`); eine fixierte 3.10.20-Baseline wird nicht beansprucht.

## Grenzen

Dies ist ein synthetischer Teilabschluss. Die begrenzte Zusammenführung muss
nicht jede mögliche Partition finden. Zusammenhängende gleichfarbige Objekte,
nicht beobachtbare Grenzen, weitere Primitive und beliebige Schichten bleiben
offen. Die neue Gruppierung verwendet den Restbildschwellwert 25 und setzt
vollständige beobachtete Inseln voraus. Frühere Editzustände können das
verbleibende Gruppierungsbudget aufbrauchen. Es gibt keine neue unabhängige reale
Familienabnahme und keine erhöhte Katalogzahl. **SEARCH-STRUCTURE-01 bleibt
insgesamt offen.** Keine vollständige Standardsuite wird als grün ausgewiesen.

## Sitzungslog

- Getestet: kontrollierter CLI-Vergleich, Zusatzseeds, 17 Plan-B-Fälle, breite Regression und betroffene Endprüfungen; vollständige Signale in `checks.json`.
- Ergebnis: 0/12 → 12/12; zusätzlich 11/12 mit bekannter konservativer Grenze, 12/12 und 17/17; endgültige Tests 352/352 und Kernprofil 42/42.
- Blocker: unabhängige reale Abnahme und beliebige Strukturkomposition bleiben offen.
- Nächster Schritt: unabhängige reale Familien vor weiterer Entwicklung sperren und vorhandene Operatoren unter demselben vollständigen Vertrag prüfen.
- Startbefehl: `python -m tools.run_seeded_scene_check evaluate_island_groups --seed 418267 --rounded --outlines`.
