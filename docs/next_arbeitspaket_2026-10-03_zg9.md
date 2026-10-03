# Nächstes Arbeitspaket – ZG9 Taskboard-Verankerung (2026-10-03)

Dieses Paket schließt nach ZG8 die letzte priorisierte P2-Aufgabe aus
`docs/umsetzungscheck_bild_semantik_2026-05-15.md` ab. Die Leitaufgaben sind
nicht mehr nur als Themenliste dokumentiert, sondern als prüfbare Verträge im
zentralen Taskboard verankert.

## Taskboard-Vertrag

Jeder Block von ZG1 bis ZG8 enthält jetzt zwei getrennte Aussagen:

- **Akzeptanz** beschreibt das von außen beobachtbare fachliche Ergebnis.
- **Exit-Bedingung** nennt den Nachweis, der vor dem Schließen der Aufgabe
  vorliegen muss, etwa Regressionstests, stabile Reportcodes oder einen
  reproduzierbaren Benchmarklauf.

ZG9 darf erst geschlossen werden, wenn alle acht Vorgänger abgeschlossen sind,
die beiden Aussagen in jedem Block vorhanden sind und die Definition of Done
des Zielabgleichs damit vollständig auf nachweisbare Aufgaben abgebildet ist.

## Automatisierte Absicherung

`tests/detailtests/test_target_alignment_taskboard.py` liest das reale
Taskboard, verlangt die lückenlose Folge ZG1 bis ZG9 und prüft pro Block die
beiden Vertragsmarker. Zusätzlich darf ZG9 nur gemeinsam mit abgeschlossenen
Vorgängeraufgaben als erledigt dokumentiert sein. Damit wird ein späterer
versehentlicher Rückbau der Akzeptanz- oder Exit-Dokumentation sichtbar.

## Ergebnis

Die priorisierte Zielabgleich-Roadmap ZG1 bis ZG9 ist abgeschlossen. Weitere
Arbeitspakete werden wieder aus den noch offenen, operativen Einträgen in
`docs/open_tasks.md` ausgewählt; ZG9 erzeugt keine neue parallele Aufgabenliste.
