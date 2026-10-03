# Merge-Recovery-Audit (2026-10-03)

## Umfang

Geprüft wurde der Stand nach den zusammengeführten Paketen ZG3 bis ZG9. Ziel
war, funktionierende Änderungen nicht pauschal zurückzudrehen, aber
Merge-Folgen zu entfernen, die den neuen Semantic-only- und
Good-Solution-Vertrag nur scheinbar erfüllen.

## Beibehalten

- Der Default `semantic-only` und der explizite Kompatibilitätsmodus bleiben
  erhalten. Im Semantic-only-Pfad sind Wiederverwendung, Template-Transfer,
  Checkpoint-Resume und Bestlist-Restore abgeschaltet.
- Das Good-Solution-Gate mit der Hierarchie Semantik/Dimension vor Pixelfehler
  bleibt erhalten.
- Die einheitlichen `NR001` bis `NR004`-Klassifikationen und Exitcodes bleiben
  erhalten.
- Der Semantic-only-Stabilitätsbenchmark bleibt erhalten.

Diese Teile werden von der vollständigen Standardtestsuite sowie den
zielgerichteten Detailtests abgedeckt.

## Verworfen beziehungsweise korrigiert

1. **Wiederverwendete Benchmark-Sandboxes:** Ein bereits vorhandenes
   Wiederholungsverzeichnis konnte alte SVGs, Donoren oder Checkpoints
   enthalten. Damit war ein späterer Lauf nicht mehr sicher nur aus JPEG und
   Beschreibung gespeist. Jeder Wiederholungslauf entfernt nun zuerst seine
   komplette Sandbox.
2. **Zu grobe Nicht-Erreichbar-Klassifikation:** Die kanonischen Statuswerte
   `budget_exceeded`, `dimension_violation` und `stagnation` wurden vom Gate
   nicht als `not_reachable` erkannt. Außerdem wurde fehlende physische
   Dimensionsevidenz als allgemeine Stagnation gemeldet. Das Gate übernimmt
   nun alle vier kanonischen Statuswerte und meldet fehlende
   Dimensionsevidenz als `NR003`.

## Prüfergebnis

- Keine Konfliktmarker oder Syntaxfehler im Python-Bestand.
- Git-Objektdatenbank ist konsistent; zwei unerreichbare ältere Commits sind
  lediglich Dangling Objects und kein beschädigter aktueller Branch.
- Die Standardtestsuite ist grün.
- Der vorhandene Report-Konsistenzcheck meldet die eingecheckten historischen
  Reports weiterhin als `stale/mixed-run`. Das ist ein bekannter Datenstand
  und kein Grund, funktionierenden Runtime-Code zurückzurollen; die Reports
  dürfen nicht als Nachweis eines frischen Laufs verwendet werden.

## Entscheidung

Kein vollständiger Revert der Merge-Serie: Die ausführbaren Verträge sind
untereinander kompatibel und die Tests sind grün. Übernommen werden die
Semantic-only-, Gate-, Klassifikations- und Taskboard-Anpassungen. Verworfen
wird ausschließlich das Verhalten, bei dem alte Benchmark-Artefakte als neue
Evidenz gelten konnten oder spezifische Nicht-Erreichbar-Ursachen zu
`stagnation` verflacht wurden.
