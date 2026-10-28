# P0: Mehrere getrennte Überdeckungsgruppen

Teilumfang von **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[Prioritätenliste](task_priority_2026-10-24.md). Ausgangscommit `50e4009d1`,
separater Branch `codex/search-structure-composition-2026-10-28`.

## Ursache und Umsetzung

Der gemeinsame Verlaufsszenenweg konnte mehrere Kreis-/Rechteckkinder mit
Rundungen, Konturen und Überdeckungen rekonstruieren. Seine Relationsprüfung
verlangte allerdings einen einzigen zusammenhängenden Überdeckungsgraphen.
Zwei voneinander getrennte überlappende Paare ließen sich dadurch nicht mit
einem vollständigen Beschreibungsvertrag abnehmen.

Der geschlossene Vertrag konsumiert jetzt auch „und bilden zwei getrennte
Gruppen mit teilweisen Überdeckungen“; zwei bis vier Gruppen mit zusammen
höchstens acht Kindern sind erlaubt. Jede Gruppe benötigt mindestens zwei
Instanzen und eine beobachtete Überdeckung. Die tatsächliche Gruppenzahl
wird während der Registrierung am nativen Überdeckungsgraphen geprüft.
Erweiterte native Silhouetten erhalten zwischen den Gruppen einen
konservativen Unsicherheitsabstand einschließlich ihrer Konturen.

Der vorhandene Tiefen-DAG liefert die Reihenfolge der Kinder. Alle
Gruppen teilen sich dieselbe Registrierung, negative Evidenz, das
Fünf-Sekunden-Bildbudget und das bestehende 96-Zustände-Budget. Der
Ablehnungsschlüssel enthält die Gruppenzahl, damit ein abgelehnter
Ein-Gruppen-Vertrag dieselbe Geometrie nicht unter einem passenden
Mehr-Gruppen-Vertrag sperrt. Zusätzliche Beschreibungsaussagen,
Inventar-, Form-, Kontur-, Reihenfolge-, lokale und globale Rastergates
bleiben verbindlich. Keine Familienkennung oder neue Symbolvorlage.

## Vorher/Nachher und Abnahmegrenzen

Zwölf unabhängige synthetische Szenen mit Seed `731429`, zwei Gruppen,
gerundeten Rechtecken und hellen Konturen wurden vor der Runtime-Änderung
erzeugt. Die unveränderte echte CLI besteht **0/12**, die finale Runtime
auf denselben Rasterbytes **12/12**. Zwei weitere Seeds mit drei bzw. vier
Gruppen bestehen jeweils **12/12**. Der neue Generator baut die Referenz
und Objektmarkierungen aus eigener Geometrie, ohne Produktionsdetektor.

Genau eine gekoppelte Plan-B-Prüfung mit Seed `853197` besteht **14/17**.
Die drei Fehlversuche `probe_08`, `probe_12`, `probe_13` bleiben im Nenner:
Die Skalierung/Translation schneidet jeweils den äußeren Verlaufskreis am
Bildrand an. Die bestehende Registrierung verlangt vollständige Formen
innerhalb des Bildes und lehnt die Startgeometrie ab. Diese Grenze wird
weder gelockert noch durch einen anderen Seed versteckt. Es gibt keine
positive vollständige Variantenabnahme dieses Pakets.

Der finale betroffene Regressionsblock besteht **236 Tests**, eine Prüfung
zum Erzeugen einer Windows-Verzeichnisverknüpfung wird regulär übersprungen.
Das Kernprofil besteht **42/42**, beide Aufrufe Exit 0. Gegenproben enthalten
falsche Gruppenzahlen, einen behaupteten einzigen Zusammenhang, isolierte
oder fehlende Kinder, zusätzliche Rasterinhalte, falsche Zeichenreihenfolge,
gleiche Füllfarben und sich berührende Konturen. Ein zunächst fehlerhaft
aufgebauter zusätzlicher Test vermischte RGB- und BGR-Werte; nach Korrektur
der Testdaten besteht auch seine positive Gegenprobe ohne Runtime-Änderung.
Die gesamte Standardsuite und Archiv-Neukonvertierung wurden nicht ausgeführt.
CI enthält die neuen Regressionen und separate Drei-/Vier-Gruppen-CLI-Läufe.

Dies ist eine synthetische Erweiterung der allgemeinen Komposition.
**SEARCH-STRUCTURE-01 bleibt insgesamt offen**; unabhängige reale
Familienabnahme, weitere Komposition und angeschnittene Elternformen sind
nicht erledigt. Die Katalogerfolgszahl wird nicht erhöht. Der zusätzliche
[AC0721-Befund](known_issue_2026-10-28_svg_text_baseline.md) zeigt außerdem
eine unabhängig reproduzierte Grenze der bisherigen Textabnahme.

## Reproduktion

Für jeden Lauf neue, noch nicht vorhandene Zielordner verwenden:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --prepare .tmp/groups-inputs --seed 731429 --groups 2 --rounded --outlines
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/groups-inputs --output .tmp/groups-cli --require-all
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 962713 --groups 3 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 482391 --groups 4 --rounded --outlines
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --prepare .tmp/groups-variants --seed 853197 --groups 2 --rounded --outlines --variations
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/groups-variants --output .tmp/groups-variants-cli
```

Der letzte Aufruf berichtet 14/17; `--require-all` verlangt positive Abnahme
aller Fälle und endet hier mit Exit 1. Der unveränderte Produktionsstand
`50e4009d1` muss für den Vorhervergleich denselben neuen Generator und dieselben
gesicherten Eingaben verwenden. Kompakte Eingabe-/Runtime-Hashes, Entscheidungen
und Prüfbefehle stehen in
[`overlap_groups_v1`](../artifacts/evaluation/overlap_groups_v1/README.md).

## Sitzungslog

- Getestet: gepaarte CLI-Kohorte, drei/vier Gruppen, Plan-B-Varianten, betroffene Regression und Kernprofil.
- Ergebnis: 0/12 → 12/12; Zusatzkohorten 12/12 und 12/12, Varianten 14/17, Regression 236 bestanden/1 übersprungen, Kernprofil 42/42.
- Grenzen: angeschnittene Elternformen, reale Gesamt-Abnahme und unabhängige Textdarstellung bleiben offen.
- Nächster Schritt: reproduzierten SVG-Textbaselinefehler beheben; vor weiterer realer Kompositionsentwicklung neue Familien sperren.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_overlap_groups.py -q`.
