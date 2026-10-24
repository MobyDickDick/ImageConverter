# P0: gleichfarbige überlappende Instanzen

Ausgewählt aus **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[verbindlichen Rangliste](task_priority_2026-10-24.md). Ausgangscommit
`5846dcb1d`. Status: abgeschlossener begrenzter Entwicklungsschritt;
die übergeordnete Aufgabe bleibt offen.

## Ursache und Änderung

Der Überdeckungsdetektor verlangte mindestens zwei verschiedene Füllfarben.
Zwei teilweise überlappende gleichfarbige Rechtecke mit sichtbaren hellen
Konturen wurden dadurch schon vor der bestehenden Instanzzerlegung verworfen.
Mit beobachteten Konturen genügt jetzt eine Füllfarbe. Die vorhandene
Komponententrennung liefert weiterhin die Instanzen; jede braucht ihre
eigenen beobachteten Seiten beziehungsweise Kreisbögen. Ohne Konturen bleibt
die einfarbige Vereinigung unzureichender Beleg für mehrere Objekte.

Gleiche Füllfarben bestimmen keine Zeichenreihenfolge. Der gemeinsame
Reihenfolgenvorschlag prüft deshalb die eigene Kontur jeder Instanz im Inneren
der anderen. Fremdobjekte werden aus den Belegregionen ausgeschlossen.
Mindestens fünf abseits der Kantenglättung abgetastete Randpixel je Richtung
und eine eindeutige Verteilung sichtbarer/überdeckter Konturen sind nötig.
Fehlende oder widersprüchliche Evidenz liefert keinen Tiefenvorschlag.
Auch die produktive Registrierung muss dieselbe Konturreihenfolge auf der
jeweils angepassten Geometrie bestätigen. Ein vertauschter Kandidat scheitert
damit unabhängig davon, dass beide flachen Füllungen identisch aussehen.

Die bestehenden nativen Instanz-, Relations-, lokalen und globalen Rastergates
bleiben erhalten. Höchstens acht Kinder, die gemeinsame 96-Zustände-Grenze,
der bestehende Scheduler und das gemeinsame Bildbudget gelten weiter.
Es gibt keine Symbolkennung, Vorlage oder Referenzgeometrie im Runtime-Code.

## Kontrollierter Nachweis

Zwölf synthetische gerundete und hell konturierte Rechteckpaare wurden mit Seed
`648217` vor der Runtime-Änderung gespeichert. Der abgeschlossene Vorlauf
besteht **0/12**, der Nachherlauf auf denselben unveränderten Eingaben
**12/12**. Suchseed 17, fünf Sekunden je Bild, 64 angeforderte Iterationen
und die unabhängigen nativen Objekt-, Regions- und Pixelprüfungen bleiben gleich.
Ein weiterer Seed `915463` besteht **12/12**.

Genau eine gekoppelte Vorlage mit Seed `372851` durchläuft Original und
16 Größen-/Farb-/Lagevarianten: **16/17**, keine vollständige Plan-B-Abnahme.
`probe_04` bleibt im Nenner und wird nicht nachgestimmt: Der vorhandene
Rundungsdetektor findet keine zwei von Fremd-/Rekonstruktionsfehlern freien
Eckfenster. Ein gezielter Test erhält diese konservative Grenze.

Die gemischte Kreis-/Rechteckkontrolle umfasst acht synthetische Fälle:
**4/8** bestehen, wenn das Rechteck vor dem Kreis liegt. Bei den übrigen vier
verhindern gleichfarbige angrenzende Flächen die bisherige äußere
Kreisrandrekonstruktion; sie bleiben ausdrücklich Ablehnungen.
Die frühere `same_color`-Negativkontrolle der Kreisrandsuite ist nun eine
positive Kontrolle mit vollständigen Objekt-/Regions-/Pixelgates.
Alle Kontrollen für fehlende Konturen, Fremdtextur und unpassende Formen bleiben.

Kompakte Eingabe-/Ausgabehashes, Messwerte, Quellenstände und Entscheidungen:
[`artifacts/evaluation/same_paint_overlap_v1/`](../artifacts/evaluation/same_paint_overlap_v1/README.md).
Generierte Raster, SVGs und vollständige CLI-Bäume sind lokale Arbeitsdaten
unter `.tmp/`; die versionierte Zusammenfassung ist kein vollständiges Roharchiv.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 648217 --rounded --outlines --same-fill
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 915463 --rounded --outlines --same-fill
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 372851 --rounded --outlines --same-fill --variations
.venv/Scripts/python.exe -m pytest -q tests/test_same_paint_overlap.py
```

Der Variantenbefehl verlangt vollständige Abnahme und endet bei 16/17
erwartungsgemäß mit Exit 1. CI prüft den zweiten Rechteckseed sowie die
positiven und konservativen Gegenproben der gezielten Suite.
Die genaue Regression und ihre Exit-Codes stehen in `checks.json`.
Die lokale Python-Version ist 3.10.11, abweichend von der konfigurierten 3.10.20.

Der breite Lauf besteht mit **620 Tests und einem Skip**, enthält aber noch
zwei fehlgeschlagene ältere `same_color`-Negativerwartungen bei konturierten
Rechtecken. Diese beiden bisherigen Einschränkungen sind mit diesem Paket
behoben: Die unveränderten Szenen werden jetzt als Positivkontrollen mit
vollständiger nativer Objekt-/Reihenfolge-/Regions-/Pixelabnahme geprüft.
Auf demselben unveränderten Produktionsmodul bestehen danach die vollständige
betroffene Kontursuite und alle neuen Gegenproben mit **94/94**, Exit 0
(23,45 Sekunden). Das Kernprofil besteht **42/42**, Exit 0. Diese Zahlen
überschneiden sich mit dem breiten Lauf und werden nicht addiert.
Der eine Skip betrifft Dateisystemlinks mit fehlenden Windows-Berechtigungen.
Eine erneute vollständige Standardsuite wird nicht als grün ausgewiesen.

## Restumfang und nachrangiger Wunsch

Dies ist ein synthetischer Teilabschluss, keine unabhängige reale
Familienabnahme. Nicht sichtbare Instanzgrenzen, die beschriebenen Rundungs-
und Kreisrandgrenzen, beliebige Schichten sowie der vollständige P0-Suchraum
bleiben offen. Es wird keine erhöhte Katalogzahl oder grüne Gesamtsuite behauptet.
Vor einer weiteren realen Entwicklung sind andere reale Prüffamilien zu sperren.

**CONVERSION-FILM-01** hält den Nutzerwunsch vom 24.10.2026 fest: Ein optionaler
Film soll die einzelnen Konvertierungsschritte besser beurteilbar machen.
Er bleibt als P3 hinter Konvertierungsqualität und den höher priorisierten
Abnahmen; seine Implementierung gehört nicht zu diesem P0-Schritt.

## Sitzungslog

- Getestet: kontrollierter CLI-Vergleich, Zusatzseed, gekoppelte Varianten und gezielte/breite Regression; Signale in `checks.json`.
- Ergebnis: 0/12 → 12/12; zusätzlich 12/12, Varianten 16/17, gemischte Entwicklungskontrollen 4/8.
- Blocker: konservative Rundungs-/Kreisrandgrenzen und unabhängige reale Gesamt-Abnahme bleiben offen.
- Nächster Schritt: reale Prüffamilien vor Entwicklung sperren; verbleibende Randbelege ohne schwächere Gates kombinieren.
- Startbefehl: `python -m tools.run_seeded_scene_check evaluate_overlap_composition --seed 372851 --rounded --outlines --same-fill --variations`.
