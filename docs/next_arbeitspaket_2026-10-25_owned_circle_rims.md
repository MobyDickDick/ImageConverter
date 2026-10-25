# P0: Eigene Kreisfüllung und angrenzende gleiche Farbe

Teilumfang von **SEARCH-STRUCTURE-01**, Rang 1/P0 der verbindlichen
[Prioritätenliste](task_priority_2026-10-24.md). Separater Branch
`codex/search-structure-owned-circle-rims-2026-10-24`, unabhängig vom
[Plan-B-Rahmenfix](https://github.com/MobyDickDick/ImageConverter/pull/2063)
auf Ausgangsstand `da211ee82`.

## Befund und Korrektur

Die Kreisrandsuche erweitert die unabhängig erkannte Füllkomponente, damit
sie den äußeren Rand erreicht. Dabei kann sie die gleiche Füllfarbe eines
benachbarten Rechtecks aufnehmen. Der sichtbare äußere Kreisbogen passt,
aber die anschließende Einschlussprüfung verlangt bislang, dass auch diese
fremden Pixel im Kreis liegen. Kreis vor Rechteck wird deshalb abgelehnt;
die umgekehrte Reihenfolge konnte bereits bestehen.

Die ursprüngliche Randprüfung hat weiterhin Vorrang. Nur wenn sie scheitert
und Pixel einer anderen, getrennt beobachteten Instanz derselben Füllfarbe
in die erweiterte Suchregion ragen,
entsteht ein zusätzlicher Vorschlag: Die Einschlussprüfung bezieht sich dann
auf die eigene Füllkomponente. Die Geometrie stammt weiterhin aus den
parentseitig beobachteten Außenbögen. Innen- und Außenkreis werden unabhängig
gemessen, ihre Zentren müssen übereinstimmen und die gemessene Randbreite muss
passen. Es werden keine Referenzvektoren, Bildnamen oder Sollradien gelesen.

Die frühere, breitere Entwicklungsversion verwendete die eigene Füllung bei
jeder äußeren Kreisprüfung. Der endgültige Code erhält die ursprüngliche
Hypothese und beschränkt die Alternative auf belegte andere gleiche Farbe.
Alle Instanz-, Relations-, lokalen und globalen Rastergates sowie das
gemeinsame Fünf-Sekunden-Bildbudget und die Strukturzustandsgrenze gelten weiter.

## Nachweis

Zwölf vor der Runtime-Änderung gesicherte synthetische Eingaben mit Seed
`731921`, zwei Kindern, Rundung und hellen Konturen verbessern sich von
**6/12 auf 12/12**. Die Eingabebilder und unabhängigen Objektannotationen
bleiben unverändert. Ein weiterer Seed `529713` besteht **12/12**;
eine gekoppelte Vorlage mit Seed `731921` besteht **17/17**.
Alle Varianten werden über die echte CLI konvertiert und anschließend
objektweise, regional und am vollständigen Raster geprüft.

Die erweiterte direkte Gegenprobe enthält 24 gültige Szenen mit und ohne
Rundung. 23 bestehen; eine eckige Szene bleibt ausdrücklich konservativ
abgelehnt: In der dünnen Tiefenbelegregion liegen keine Pixelzentren. Der
Vorschlag für den äußeren Kreis ersetzt nicht die weiterhin geforderten fünf
beobachteten Randsamples der anderen Instanz. Der Fall bleibt im Nenner;
der Test schützt diese Grenze. Weitere Gegenproben verlangen Ablehnung bei
falscher Form, fehlendem/dunklem Rand, Fremdtextur, zusätzlichen oder fehlenden
Objekten und falscher Anzahl. Es gibt kein Abschwächen einer Qualitätsgrenze.

Die abschließenden Befehle, Quellhashes und Exit-Codes stehen in `checks.json`;
kompakte Ergebnisse unter
[`owned_circle_rims_v1`](../artifacts/evaluation/owned_circle_rims_v1/README.md).
Generierte Raster, SVGs und vollständige CLI-Logs bleiben lokale Daten unter
`.tmp/p0-circle-*`. Der Generator bietet jetzt `--same-fill` für reproduzierbare
gemischte Szenen. Regenerierte Raster sind identisch zu den eingefrorenen
Eingaben; XML-Namespacepräfixe können sich durch die Serializer-Registrierung
im selben Python-Prozess unterscheiden.

Die abschließende betroffene Kontur-/Gruppierungsprüfung besteht auf dem
endgültigen Code mit **138/138**, Exit 0 (230,88 Sekunden).
Das Kernprofil besteht mit 42/42. Eine breitere Zwischenprüfung endet mit
165 bestandenen und fünf fehlgeschlagenen Tests; alle fünf betreffen die
bestehende Sechs-/Acht-Instanzen-Kohorte. Die isolierte Wiederholung derselben
fünf Fälle ergibt sowohl mit dem unveränderten Produktionsmodul von `main`
als auch mit dem endgültigen Modul genau zwei bestandene und dieselben drei
fehlgeschlagenen Tests. Die beiden übrigen Fehler sind damit nicht stabil
reproduziert. Diese lokalen Grenzen bleiben beim bestehenden Test-/Budgetpaket
offen; die Zwischenprüfung wird nicht als grün umgedeutet. Auch frühere
unterbrochene beziehungsweise parallel zeitbegrenzte Läufe zählen nicht als
vollständige Regression. Die abschließende betroffene Kontur-/Gruppierungsprüfung
ist in `checks.json` gesondert ausgewiesen; überlappende Testzahlen werden
nicht addiert.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 529713 --children 2 --rounded --outlines --same-fill
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 731921 --children 2 --rounded --outlines --same-fill --variations
.venv/Scripts/python.exe -m pytest -q tests/test_owned_circle_rims.py tests/test_same_paint_overlap.py tests/test_mixed_overlap_outlines.py tests/test_island_group_search.py tests/test_repeated_fill_overlap.py
```

Dies ist ein synthetischer Teilabschluss. Nicht beobachtbare Grenzen,
die beschriebene eckige Tiefenbeleggrenze, beliebige Kompositionen und die
unabhängige reale Gesamt-Abnahme bleiben offen. SEARCH-STRUCTURE-01 wird
deshalb nicht insgesamt geschlossen. Python lokal: 3.10.11. Es wird keine
grüne vollständige Standardsuite oder höhere Katalog-Erfolgszahl behauptet.

## Sitzungslog

- Getestet: kontrollierte CLI-Kohorte, Zusatzseed, gekoppelte Varianten und gezielte Regression.
- Ergebnis: 6/12 → 12/12; zusätzlich 12/12 und 17/17, mit erhaltener konservativer Gegenprobe.
- Blocker: unabhängige reale Abnahme und breitere Komposition bleiben offen.
- Nächster Schritt: weitere reale Familien vor Entwicklung sperren; Tiefenbelege bei dünnen Konturen getrennt untersuchen.
- Startbefehl: oben dokumentierter Variantenlauf mit Seed `731921`.
