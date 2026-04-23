# Task-Triage + Qualitätsreview (AC08) – 2026-04-23

## Kontext

Diese Notiz beantwortet zwei Fragen:

1. Welche aktuell dokumentierten Aufgaben sind noch sinnvoll (priorisieren), welche sind inzwischen überholt bzw. nur bedingt nützlich?
2. Wie ist die Qualität der aktuell eingecheckten AC08-Konvertierungen auf Basis der vorhandenen Logs einzuschätzen?

Datenbasis:
- `docs/open_tasks.md`
- Run-Logs `AC0800_AC0899_batch_2026-04-23_runT..runY.log`
- AC08-Validierungslogs `artifacts/converted_images/reports/AC08*_element_validation.log`

## 1) Triage der nächsten Aufgaben

### 1.1 Nächste dokumentierte Aufgabe
- **N1 (Vollbereichslauf mit Exit 0)** ist die nächste offene Aufgabe in `docs/open_tasks.md`.
- **Status nach neuem Run Y:** weiterhin offen (Timeout-Exit `124`, kein finaler Exit `0`).

### 1.2 Was ist weiterhin sinnvoll?

- **Sinnvoll / beibehalten:**
  - **N1/N2 als Zielzustand** (voller Exit-`0` + Stabilitätsnachweis ohne MuPDF-Crash) bleiben fachlich sinnvoll.
  - **N4 (Rückpflege)** bleibt sinnvoll, damit der Dokumentationsstand sauber und auditierbar bleibt.

### 1.3 Was ist überholt bzw. ineffizient geworden?

- **Überholt als Arbeitsmodus:** immer wieder identische Vollbereichs-Reruns ohne zusätzliche Diagnoseinstrumentierung.
- Die letzten Runs (`T..Y`) zeigen wiederholt denselben frühen Fortschrittsbereich (`AC0800_*`, teilweise `AC0811_*`) ohne Abschluss bis `AC0899`.
- Reine Wiederholung desselben Befehls bringt aktuell nur begrenzten neuen Erkenntnisgewinn.

### 1.4 Konkrete Empfehlung

Statt weiterer identischer Vollbereichs-Runs sollte als nächster sinnvoller Schritt ein **gezielter Engpass-Task** dokumentiert werden (z. B. enger Zwischenbereich `AC0811..AC0820` mit zusätzlicher Laufzeit-/Iterationstelemetrie), danach erst wieder N1-Vollbereich.

## 2) Qualitätsreview der vorhandenen AC08-Logs

## 2.1 Statusverteilung in AC08-Validierungslogs

Auswertung von `AC08*_element_validation.log` (aktueller Snapshot):

- Gesamt: **64** AC08-Validierungslogs
- `semantic_ok`: **38**
- `conversion_failed`: **19**
- `skipped_manual_review`: **7**

## 2.2 Familien mit stabilem `semantic_ok`

Beispiele mit durchgehend positivem Status in den vorhandenen Varianten:
- `AC0800` (`L/M/S`)
- `AC0811` (`L/M/S`)
- `AC0814` (`L/M/S`)
- `AC0831`, `AC0832`, `AC0837`, `AC0838`, `AC0839`

Zusätzliche positive Teilfamilien im Snapshot:
- `AC0812_S`, `AC0813_L/M`, `AC0835_M`, `AC0836_M/S`, `AC0870_L/S`, `AC0881_L/M`, `AC0882_S`.

## 2.3 Familien mit klarem Nacharbeitsbedarf

- **Conversion failed dominiert** u. a. bei:
  - `AC0840`, `AC0841`, `AC0842`, `AC0843`, `AC0850`, `AC0861`, `AC0862`, `AC0863`, `AC0864`, `AC0884`, `AC0890`.
- **Manual-review-Backlog** sichtbar bei:
  - `AC0845`, `AC0846`, `AC0847`, `AC0848`, `AC0849`.

## 2.4 Einordnung zur ursprünglichen Frage („immer wieder AC08… sinnvoll?“)

Kurz: **teilweise ja, teilweise nein**.

- **Ja**, weil AC08 weiterhin den kritischen Serienbereich für den offenen Vollbereichs-Nachweis enthält.
- **Nein**, wenn nur noch derselbe Vollbereichs-Run wiederholt wird, ohne den lokalen Engpass technisch enger zu isolieren.

Pragmatisch ist ein Wechsel von „Vollbereich wiederholen“ zu „Engpassbereich instrumentiert isolieren → Fix/Parametrik verbessern → dann Vollbereich“.
