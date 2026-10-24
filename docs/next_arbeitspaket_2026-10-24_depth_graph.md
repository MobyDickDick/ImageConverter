# P0: beobachtete Überdeckungsreihenfolge für größere Inventare

Ausgewählt aus **SEARCH-STRUCTURE-01**, Rang 1/P0 der verbindlichen
[Schwächenprüfung](weakness_review_2026-10-23.md). Die offenen GitHub-Aufgaben
betreffen vorwiegend Plan-B-Einzelfälle und ersetzen diese dokumentierte
Reihenfolge nicht. Neue Regressionen wurden zuerst repariert, danach dieses
abgegrenzte Strukturpaket umgesetzt.

Reparaturbasis: `72e0a5113`, Branch
`codex/fix-cleanup-inventory-ignore-2026-10-24`. Separater P0-Branch:
`codex/search-structure-depth-graph-2026-10-24`.

## Änderung

Der bestehende Verlaufskreisweg kann jetzt fünf bis acht verschiedenfarbige,
teilweise überlappende Rechteckkinder vorschlagen. Statt bis zu `8!`
Zeichenreihenfolgen zu enumerieren, liefert das Bild gerichtete Kanten zwischen
beobachteten Vorder- und Hintergrundrollen. Eine topologische Sortierung
ergibt einen Startvorschlag für dieselbe native Registrierung. Fehlende
Paarbelege erzeugen keine behauptete Tiefenbeziehung; ausgeglichene
widersprüchliche Belege oder ein Zyklus liefern keinen Graphvorschlag.
Die begrenzte Agenda mit 96 Zuständen und das gemeinsame Bildbudget bleiben
erhalten. Die vorhandenen Zwei- bis Vier-Kinder-Wege behalten ihre Reihenfolge.

Sehr schmale Schnittflächen enthalten ebenfalls Tiefeninformation. Die
Analyse berücksichtigt reine Füllpixel mindestens einen halben Pixel innerhalb
der vorgeschlagenen Füllgrenze. Überwiegt eine beobachtete Farbe mindestens
4:1, darf sie trotz weniger Randpixel der anderen Farbe eine Reihenfolge
vorschlagen. Das ist keine Abnahmegrenze: native Geometrie, vollständiges
Inventar, Konturen, Rundung, Zusammenhang des Überdeckungsgraphen, lokale und
globale Rastergates sowie die vorhandene Tiefenprüfung bleiben erforderlich.

Bei mehr als vier Farben kann ein Mischpixel zufällig einer anderen Füllfarbe
entsprechen und deren sichtbare Komponente um einen Pixel vergrößern.
Der Detektor sucht deshalb höchstens zwei Pixel innerhalb dieses Randes nach
denselben mindestens fünf geraden, gegen das Elternbild freiliegenden
Kantenbelegen. Es werden weiterhin keine vollständig verdeckten Seiten ergänzt.

Der unabhängige Objektprüfer löst seine Zuordnung jetzt exakt mit
Branch-and-Bound statt alle Permutationen zu durchlaufen. Form, Anzahl,
Eckradius, Kontur, Eltern-/Tiefenrelationen und minimaler maximaler Boxfehler
werden unverändert geprüft. Der Prüfer verwendet keine Runtime-Erkennung.
24 Gegenprüfungen erfolgreicher und in ihrer Zeichenreihenfolge veränderter
Ausgaben stimmen exakt mit dem bisherigen erschöpfenden Prüfer überein.

## Vergleich und Lernschritte

Zwölf Sechs-Kinder-Fälle, Generatorseed **814295**, wurden vor der Runtime-
Änderung erzeugt und über die echte überwachte CLI mit fünf Sekunden pro Bild
und Suchseed 17 geprüft: **0/12** auf der Reparaturbasis. Die unveränderten
Raster und Referenzen bestehen nach der Änderung **12/12**, einschließlich
unabhängiger Rasterung, Objekt-, Relations- und lokaler/globaler Pixelprüfung.
Kompakte Prüfsummen stehen in
[`artifacts/evaluation/depth_order_v1/summary.json`](../artifacts/evaluation/depth_order_v1/summary.json).

Die erste Graphhypothese ignorierte sehr schmale Schnittflächen und erreichte
10/12. Die Vermutung, die zwei übrigen Tiefenrelationen seien vollständig
verdeckt, wurde an den Referenzsilhouetten widerlegt; die ursprünglichen
Objekt-/Relationsmarkierungen bleiben unverändert. Erst die Einbeziehung der
sichtbaren schmalen Schnittflächen erreicht 12/12.

Die zusätzliche Acht-Kinder-Kohorte, Seed **962431**, erreichte zunächst 9/12,
auch bei serieller Ausführung. Zwei Fälle fehlten wegen der um einen Pixel
verschobenen Farbkomponentengrenze, einer wegen zu empfindlicher Behandlung
weniger widersprechender Randpixel. Die gekoppelte Sechs-Kinder-Plan-B-Aufgabe,
Seed **713849**, erreichte zunächst 8/17. Dominante Paarbelege statt eines
Vetos durch einzelne Randpixel verbessern sie auf **17/17**. Diese
Fehlversuche werden nicht aus den Nennern entfernt und sind keine Holdouts.

Die abschließende serielle Acht-Kinder-Wiederholung besteht nach beiden
Korrekturen **12/12**; die gekoppelte Plan-B-Aufgabe erneut **17/17**.

## Grenzen und Datenlebenszyklus

Die zusätzliche direkte Matrix enthält 36 erfolgreiche Szenen sowie drei
bewusst erhaltene Ablehnungen bei fehlenden unabhängigen Eckradiusmessungen.
Fehlende Kinder, gleiche Farben, falsche Anzahl, verdeckte Seiten,
Außenpositionen, Fremdtextur und zyklische Tiefenbelege bleiben Gegenproben.
Mehr als acht Kinder, gleiche/mehrdeutige Füllfarben, weitere Primitive und
eine unabhängige reale Familienabnahme sind nicht abgeschlossen.
**SEARCH-STRUCTURE-01 bleibt deshalb insgesamt offen.**

Abschließende Prüfung: betroffene CI-Testgruppe **288 bestanden, ein Skip**;
angrenzende Szenen-, Such-, Evidenz- und Archivprüfungen **181 bestanden, ein
Skip**; schnelles Kernprofil **42 bestanden**. Alle 379 archivierten Paare
und deren 758 Datei-Prüfsummen sind unverändert. Keine vollständige
Standardsuite oder neue reale Familienabnahme.

Neue wiederholbare Läufe verwenden `tools.run_seeded_scene_check`: Seeds und
Optionen werden zuerst gespeichert; Rohdaten werden auch nach Fehlern
entfernt. Das eingefrorene Vorher-/Nachher-Arbeitsverzeichnis wird nach
Sicherung der kompakten Ergebnisse ebenfalls entfernt. Die zentrale
Ignore-Regel erfasst auch dieses neue Evidenzpaket. Keine Änderung am
akzeptierten Archiv und keine Historienumschreibung.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 814295 --children 6
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 962431 --children 8
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 713849 --children 6 --variations
.venv/Scripts/python.exe -m pytest -q tests/test_observed_depth_order.py tests/test_test_data_lifecycle.py
```
