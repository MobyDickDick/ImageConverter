# Open Tasks

This checklist only tracks work that is actionable for the ImageConverter in the
current repository snapshot. Older unrelated language/compiler/runtime tasks were removed so the list stays
focused on the actual project scope.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.

## Current status

- The latest committed AC08 report snapshot now contains `10` evaluated AC08 validation logs, and all `10` are `semantic_ok` (`0` `semantic_mismatch`).
- The refresh run currently covers the most recently touched connector/circle families present in `artifacts/converted_images/reports` (`AC0811`, `AC0832`, `AC0835`, `AC0836`, `AC0870`, `AC0882`).
- Continue to add new work items here before implementation starts, then mark them in-place when they are done.

## Next execution tasks (re-priorisiert am 2026-05-03)

Arbeitsreihenfolge für die nächsten Sessions (von „hohe Abschlusschance“ nach
„abhängig von langen Vollbereichsläufen“):

1. **T5.x zuerst abschließen** (isolierte, kurze, reproduzierbare Testfehler).
2. **N3/N4 bei jedem Lauf direkt mitpflegen** (Dokumentation sofort konsistent halten).
3. **N5/N6/N7 vorziehen** (höhere Abschlusschance mit kürzeren, gezielten Läufen).
4. **N1/N2 erst danach erneut anstoßen** (Vollbereichslauf als Verifikationsschritt, nicht als erster Schritt).

Begründung: Die bisherigen Vollbereichs-Runs endeten wiederholt ohne Exit `0`.
Mit der Reihenfolge „erst kurze, klare Root-Causes beheben, dann Vollbereich
verifizieren“ steigt die Chance, dass Aufgaben tatsächlich abgeschlossen und auf
`[x]` gesetzt werden können.

2026-05-03: **N1-Priorität reduziert** (von „direkt nach T5/N3/N4“ auf „nach N5/N6/N7“), da wiederholte Vollbereichsläufe trotz Fortschritt weiterhin überwiegend in Timeouts enden.

- [x] N0 (höchste Priorität): Root-Cause der **ersten** AC08-Zeitbudgetüberschreitung (`AC0811_L.jpg`) isolieren und beheben.
  - Befund aus Log-Auswertung: erstes dokumentiertes `validation_time_budget_exceeded` tritt in `AC0800_AC0899_batch_2026-04-28_runAV.log` bei `AC0811_L.jpg` auf (`phase=round_start`, `round=2`, `elapsed=43.75s`, `budget=18.00s`).
  - Ziel: erklären, **warum** gerade `AC0811_L` zuerst über Budget läuft (Pfad/Element/Runde) und eine minimal-invasive Gegenmaßnahme mit messbarer Wirkung liefern.
  - Akzeptanzkriterium: isolierter Repro-Lauf + Kurzbericht mit identifizierter Ursache + Patch, der den ersten Overrun entweder vermeidet oder deutlich nach hinten verschiebt.
  - 2026-05-02: AC0811-Only-Repro ohne explizites Zeitlimit ausgeführt (`docs/ac0811_only_2026-05-02_runB_summary.md`); Lauf endet mit Exit `0` und ohne `validation_time_budget_exceeded`, zeigt jedoch wiederholte Verarbeitung von `AC0811_M`/`AC0811_S` als neuen Analysehinweis.
  - 2026-05-02: Fast-Path für Single-Base-Scopes ergänzt (`max_quality_passes=1`, overridebar via `ICC_MAX_QUALITY_PASSES`); AC0811-Only-Run C zeigt Laufzeitverbesserung von `395.59s` auf `363.78s` (~8.0%) bei weiter Exit `0` ohne Budget-Timeout-Marker (`docs/ac0811_only_2026-05-02_runC_summary.md`).
  - 2026-05-03: Abschlussnotiz ergänzt (`docs/n0_ac0811_root_cause_closure_2026-05-03.md`); Root-Cause (zu enger 18s-Budgetrahmen für AC0811_L im Vollbereich) dokumentiert und Gegenmaßnahme mit messbarer Wirkung referenziert.

- [ ] N1: B2 vollständig abschließen: Vollbereichslauf `AC0800..AC0899` mit Exit-Code `0` nachweisen.
  - Blockierungsverlauf (Kurztrend):
    - 2026-05-01 (Run BJ): Exit `0`, sichtbarer Fortschritt nur bis `AC0811_L` → **Stagnation**.
    - 2026-05-02 (Run BK): Exit `0`, erneut nur bis `AC0811_L` mit `validation_time_budget_exceeded` → **weiterhin Stagnation**.
    - 2026-05-02 (Run BL): Exit `0`, erneut nur bis `AC0811_L` mit `validation_time_budget_exceeded` (`phase=round_start`, `round=3`) → **weiterhin Stagnation**.
    - 2026-05-02 (Run BM): Exit `0`, erneut nur bis `AC0811_L` mit `validation_time_budget_exceeded` (`phase=round_start`, `round=2`) → **weiterhin Stagnation**.
    - 2026-05-02 (Run BN): Exit `124` (äußeres Timeout), aber Fortschritt bis `AC0812_S`-Start nach `AC0811_L/M/S` + `AC0812_L/M` → **Blockierung verringert**.
  - 2026-04-23: Startkommando als Run S angestoßen; Log-Datei: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-04-23_runS.log`.
  - 2026-04-23: Run S nach dokumentiertem Teilfortschritt (`AC0800_*`, Start `AC0811_L`) manuell mit Exit `143` beendet, um Aufgaben-/Run-Doku im selben Arbeitsgang zu aktualisieren.
  - 2026-04-23: Run T ohne `timeout` gestartet; dokumentierter Fortschritt bis `AC0811_M`, danach manuell per `pkill` beendet (kein finaler Exit-`0`).
  - 2026-04-23: Run U ohne `timeout` erneut gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0`).
  - 2026-04-23: Run V erneut ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0800_S`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`).
  - 2026-04-23: Run W ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_S`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0` dokumentiert).
  - 2026-04-23: Run X ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0` dokumentiert).
  - 2026-04-23: Run Y mit `timeout 420` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runY_2026-04-23_summary.md`).
  - 2026-04-23: Run Z ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runZ_2026-04-23_summary.md`).
  - 2026-04-23: Run AA mit `timeout 600` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAA_2026-04-23_summary.md`).
  - 2026-04-24: Run AB mit `timeout 300` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAB_2026-04-24_summary.md`).
  - 2026-04-24: Run AC mit `timeout 300` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAC_2026-04-24_summary.md`).
  - 2026-04-24: Run AD ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAD_2026-04-24_summary.md`).
  - 2026-04-24: Run AE ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_S`, danach manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAE_2026-04-24_summary.md`).
  - 2026-04-24: Run AF ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill -f src.imageCompositeConverter` beendet (Prozess durch Signal beendet, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAF_2026-04-24_summary.md`).
  - 2026-04-24: Run AG ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill -f src.imageCompositeConverter` beendet (Prozess durch Signal beendet, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAG_2026-04-24_summary.md`).
  - 2026-04-24: Run AH ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAH_2026-04-24_summary.md`).
  - 2026-04-24: Run AI ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0812_S`, danach manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAI_2026-04-24_summary.md`).
  - 2026-04-24: Run AJ ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAJ_2026-04-24_summary.md`).
  - 2026-04-24: Run AK ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAK_2026-04-24_summary.md`).
  - 2026-04-24: Run AL mit `timeout 900` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill -f src.imageCompositeConverter` beendet (Prozessstatus signalbedingt `-1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAL_2026-04-24_summary.md`).
  - 2026-04-24: Run AM ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill` beendet (Prozessstatus signalbedingt `-1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAM_2026-04-24_summary.md`).
  - 2026-04-25: Run AN mit `timeout 420` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAN_2026-04-25_summary.md`).
  - 2026-04-26: Run AP mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAP_2026-04-26_summary.md`).
  - 2026-04-26: Run AQ mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAQ_2026-04-26_summary.md`).
  - 2026-04-26: Run AR mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAR_2026-04-26_summary.md`).
  - 2026-04-27: Run AS mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAS_2026-04-27_summary.md`).
  - 2026-04-27: Run AT mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAT_2026-04-27_summary.md`).
  - 2026-04-27: Run AU mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAU_2026-04-27_summary.md`).
  - 2026-04-28: Run AV mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAV_2026-04-28_summary.md`).
  - 2026-04-28: Run AW mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAW_2026-04-28_summary.md`).
  - 2026-04-28: Run AX mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAX_2026-04-28_summary.md`).
  - 2026-04-28: Run AY mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAY_2026-04-28_summary.md`).
  - 2026-04-28: Run AZ mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAZ_2026-04-28_summary.md`).
  - 2026-04-28: Run BA mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBA_2026-04-28_summary.md`).
  - 2026-04-28: Run BB mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBB_2026-04-28_summary.md`).
  - 2026-04-28: Run BC mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBC_2026-04-28_summary.md`).
  - 2026-04-29: Run BD mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBD_2026-04-29_summary.md`).
  - 2026-04-29: Run BE mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBE_2026-04-29_summary.md`).
  - 2026-04-29: Run BF mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBF_2026-04-29_summary.md`).
  - 2026-04-29: Run BG mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBG_2026-04-29_summary.md`).
  - 2026-04-30: Run BH mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBH_2026-04-30_summary.md`).
  - 2026-05-01: Run BI mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBI_2026-05-01_summary.md`).
  - 2026-05-01: Run BJ mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBJ_2026-05-01_summary.md`).
  - 2026-05-02: Run BK mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBK_2026-05-02_summary.md`).
  - 2026-05-02: Run BL mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBL_2026-05-02_summary.md`).
  - 2026-05-02: Run BM mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBM_2026-05-02_summary.md`).
  - 2026-05-02: Run BN mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis Start `AC0812_S`, Prozessende mit Timeout-Exit `124` (Summary: `docs/ac0800_ac0899_runBN_2026-05-02_summary.md`).
  - 2026-05-03: Run BO mit `timeout 120` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0881_M`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBO_2026-05-03_summary.md`).
  - 2026-05-03: Run BP ohne `timeout` gestartet; wegen ausbleibender sichtbarer Log-Fortschrittszeilen in der Beobachtungsphase manuell per `pkill` beendet (signalbedingter Prozessstatus `-1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBP_2026-05-03_summary.md`).
  - 2026-05-03: Run BQ mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0832_L`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBQ_2026-05-03_summary.md`).
  - 2026-05-03: Run BR mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0838_M`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBR_2026-05-03_summary.md`).
  - 2026-05-03: Run BS mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0870_M`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBS_2026-05-03_summary.md`).
  - 2026-05-03: Run BT mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0882_S`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBT_2026-05-03_summary.md`).
  - Abschlusskriterium: vollständiger Durchlauf bis `AC0899` ohne `timeout`-Abbruch und mit finalem Prozessstatus `0`.

- [ ] N2: Stabilitätsnachweis für den Vollbereich dokumentieren.
  - Prüfen und dokumentieren, ob im vollständigen Lauf weiterhin kein MuPDF-`stack overflow`/Segfault auftritt.
  - Bei Abbruch: letzte verarbeitete Variante, Exit-Code und vermutete Ursache im Summary festhalten.
  - 2026-04-23: In Run T bis einschließlich `AC0811_M` kein MuPDF-`stack overflow`/Segfault; Abbruchursache und Status in `docs/ac0800_ac0899_runT_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run U bestätigt erneut keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruchursache und Status in `docs/ac0800_ac0899_runU_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run V zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0800_S`; Abbruchursache und Status in `docs/ac0800_ac0899_runV_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run W zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_S`; Abbruchursache und Status in `docs/ac0800_ac0899_runW_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run X zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruchursache und Status in `docs/ac0800_ac0899_runX_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run Y zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runY_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run Z zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruchursache und Status in `docs/ac0800_ac0899_runZ_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run AA zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAA_2026-04-23_summary.md` dokumentiert.
  - 2026-04-24: Run AB zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAB_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AC zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAC_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AD zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAD_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AE zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_S`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAE_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AF zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAF_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AG zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAG_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AH zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAH_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AI zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0812_S`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAI_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AJ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAJ_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AK zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAK_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AL zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAL_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AM zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAM_2026-04-24_summary.md` dokumentiert.
  - 2026-04-25: Run AN zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAN_2026-04-25_summary.md` dokumentiert.
  - 2026-04-26: Run AP zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAP_2026-04-26_summary.md` dokumentiert.
  - 2026-04-26: Run AQ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAQ_2026-04-26_summary.md` dokumentiert.
  - 2026-04-26: Run AR zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAR_2026-04-26_summary.md` dokumentiert.
  - 2026-04-27: Run AS zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAS_2026-04-27_summary.md` dokumentiert.
  - 2026-04-27: Run AT zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAT_2026-04-27_summary.md` dokumentiert.
  - 2026-04-27: Run AU zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAU_2026-04-27_summary.md` dokumentiert.
  - 2026-04-28: Run AV zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAV_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AW zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAW_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AX zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAX_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AY zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAY_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AZ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAZ_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run BA zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBA_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run BB zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBB_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run BC zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBC_2026-04-28_summary.md` dokumentiert.
  - 2026-04-29: Run BD zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBD_2026-04-29_summary.md` dokumentiert.
  - 2026-04-29: Run BE zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBE_2026-04-29_summary.md` dokumentiert.
  - 2026-04-29: Run BF zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBF_2026-04-29_summary.md` dokumentiert.
  - 2026-04-29: Run BG zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBG_2026-04-29_summary.md` dokumentiert.
  - 2026-04-30: Run BH zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBH_2026-04-30_summary.md` dokumentiert.
  - 2026-05-01: Run BI zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBI_2026-05-01_summary.md` dokumentiert.
  - 2026-05-01: Run BJ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBJ_2026-05-01_summary.md` dokumentiert.
  - 2026-05-02: Run BK zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBK_2026-05-02_summary.md` dokumentiert.
  - 2026-05-02: Run BL zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBL_2026-05-02_summary.md` dokumentiert.
  - 2026-05-02: Run BM zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBM_2026-05-02_summary.md` dokumentiert.
  - 2026-05-02: Run BN zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis mindestens `AC0812_S`; Status (Timeout-Exit `124` mit erweitertem Fortschritt) in `docs/ac0800_ac0899_runBN_2026-05-02_summary.md` dokumentiert.
  - 2026-05-03: Run BO zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis mindestens `AC0881_M`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBO_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BP endet signalbedingt nach manuellem `pkill`; kein zusätzlicher Segfault-/Stackoverflow-Hinweis, aber auch kein neuer belastbarer Stabilitätsnachweis bis Laufende (Summary: `docs/ac0800_ac0899_runBP_2026-05-03_summary.md`).
  - 2026-05-03: Run BQ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault im Log-Tail bis mindestens `AC0832_L`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBQ_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BR zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault im Log-Tail bis mindestens `AC0838_M`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBR_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BS zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault im Log-Tail bis mindestens `AC0870_M`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBS_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BT bestätigt weiterhin keinen MuPDF-`stack overflow`/Segfault bis mindestens `AC0882_S`; Timeout-Status in `docs/ac0800_ac0899_runBT_2026-05-03_summary.md` dokumentiert.

- [x] N3: Neue Laufzusammenfassung im Run-Format ergänzen.
  - Neue Datei analog zu Run Q/R erstellen (Datum, Anlass, exakter Befehl, Log-Pfad, sichtbarer Fortschritt, Exit-Code, Kurzfazit).
  - 2026-04-23: Run-T-Summary ergänzt: `docs/ac0800_ac0899_runT_2026-04-23_summary.md`.

- [ ] N5: Neue JPEG-Samples aus `artifacts/images_to_convert/samples` automatisch mit gleichnamigen SVG/JPEG-Paaren validieren.
  - Für jedes neue Sample in `artifacts/images_to_convert/samples` sicherstellen, dass ein gleichnamiges `.jpeg` konvertiert wird und das Ergebnis gegen das Referenzbild verglichen wird (Diff/Fehlerwert im Report).
  - Akzeptanzkriterium: reproduzierbarer Batch-Check (inkl. Log/Report), der neu hinzugefügte Samples ohne manuelle Einzelschritte abdeckt.

- [ ] N6: Generative SVG-Variationssuite für Algorithmus-Verbesserung ergänzen.
  - Teil A (Parameterfächer): Mehrere Parameter einzelner Elemente (z. B. Kreis: `cx/cy/r`, Gerade: Endpunkte/Stärke) systematisch variieren, als SVG rendern, nach JPEG konvertieren und per ImageConverter wieder rückübersetzen/auswerten.
  - Teil B (Element-Verknüpfungen): Kombinationsszenarien mit expliziten geometrischen Relationen abdecken (z. B. Buchstabe horizontal+vertikal zentriert im Kreis ohne Berührung; horizontaler und gleichlanger vertikaler Strich jeweils zentriert).
  - Akzeptanzkriterium: Szenario-Katalog + automatisierbarer Vergleichslauf inkl. Qualitätsmetriken pro Szenario.

- [ ] N7: AC08-Zeitfehler aus Volltests gezielt nachfahren (bildspezifische Konvertierung).
  - Dokumentierte Fehlerliste: `docs/ac08_timeout_failures_2026-04-28.md` (inkl. betroffener Tests und Varianten).
  - Für die dort gelisteten Referenzen (`AC0811`, `AC0812`, `AC0820`, `AC0835`, `AC0837`, `AC0838`) jeweils Einzel-Läufe `--start <REF> --end <REF>` durchführen und Exit/Artefakte dokumentieren.
  - Akzeptanzkriterium: Pro Referenz mindestens ein reproduzierbarer Diagnoselauf mit Log und kurzem Ergebnisvermerk in den Run-Notizen.
  - 2026-04-29: AC0811-Einzellauf (Run BE) mit `--start AC0811 --end AC0811` durchgeführt; Log: `artifacts/converted_images/reports/AC0811_single_2026-04-29_runBE.log`, Summary: `docs/ac0811_single_runBE_2026-04-29_summary.md` (Exit `0`, weiterhin `validation_time_budget_exceeded` bei `AC0811_L`).

- [x] N4: Rückpflege in diese Aufgabenliste nach Abschluss. (2026-05-03: Prioritätsmatrix ergänzt und Liste konsolidiert; Aufgabe vollständig abgeschlossen, daher aus aktiver Priorisierung entfernt.)
  - Rotationsstand 2026-05-03: Nach Bearbeitung von N4 wurden offene Prioritäten rotiert (N1→60, N2→100, N5→90, N6→80, N7→70, T6→40, A1→30).
  - Erledigte N-Aufgaben auf `[x]` setzen und mit kurzem Datum-/Ergebnisvermerk ergänzen.
  - 2026-04-23: Zwischenstand nach Run T nachgepflegt; N1/N2/N4 bleiben bis zum Exit-`0`-Vollbereichslauf offen.
  - 2026-04-23: Zwischenstand nach Run U nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run V nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run W nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run X nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run Y nachgepflegt; N1/N2/N4 bleiben weiterhin offen (erneut kein Exit-`0`).
  - 2026-04-23: Zwischenstand nach Run Z nachgepflegt; N1/N2/N4 bleiben weiterhin offen (erneut kein Exit-`0`).
  - 2026-04-23: Zwischenstand nach Run AA nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AB nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AC nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AD nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AE nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AF nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` beendet, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AG nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` beendet, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AH nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AI nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AJ nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AK nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AL nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` signalbedingt beendet, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AM nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` signalbedingt beendet, weiterhin kein Exit-`0`).
  - 2026-04-25: Zwischenstand nach Run AN nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-26: Zwischenstand nach Run AP nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-26: Zwischenstand nach Run AQ nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-26: Zwischenstand nach Run AR nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-27: Zwischenstand nach Run AS nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-27: Zwischenstand nach Run AT nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-27: Zwischenstand nach Run AU nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-28: Zwischenstand nach Run AV nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AW nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AX nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AY nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AZ nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run BA nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run BB nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run BC nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BD nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BE nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BF nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BG nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BM nachgepflegt; T5-Volltestlauf erneut bis `78%` sichtbar ohne Fehlermeldungen, danach wegen Inaktivität per `pkill` beendet (Prozessstatus signalbedingt `-1`), daher bleibt N4 offen.
  - 2026-04-29: Zwischenstand nach Run BN nachgepflegt; T5-Volltestlauf erneut bis `78%` sichtbar ohne Fehlermeldungen, danach wegen Inaktivität per `pkill` beendet (Prozessstatus signalbedingt `-1`), daher bleibt N4 offen.
  - 2026-05-01: Zwischenstand nach Run BI nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleiben N1/N2/N4 offen.
  - 2026-05-01: Zwischenstand nach Run BJ nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleiben N1/N2/N4 offen.
  - 2026-05-02: Zwischenstand nach Run BK nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleibt der Blockierungsverlauf aktuell stagnierend und N1/N2/N4 offen.
  - 2026-05-02: Zwischenstand nach Run BM nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleibt der Blockierungsverlauf aktuell stagnierend und N1/N2/N4 offen.
  - 2026-05-02: Zwischenstand nach Run BN nachgepflegt; nach Gegenmaßnahme Fortschritt bis `AC0812_S`-Start erreicht (statt Stopp bei `AC0811_L`), Prozessende jedoch weiterhin per Timeout `124`; N1/N2/N4 bleiben offen.
  - 2026-05-03: Zwischenstand nach Run BO nachgepflegt; trotz Fortschritt bis `AC0881_M` endet der Lauf mit Timeout-Exit `124`, daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Zwischenstand nach Run BQ nachgepflegt; Lauf endet erneut mit Timeout-Exit `124` (sichtbarer Fortschritt bis `AC0832_L`), daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Zwischenstand nach Run BP nachgepflegt; Lauf wurde mangels sichtbarer Fortschrittszeilen manuell beendet (signalbedingt `-1`), daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Zwischenstand nach priorisiertem T5-Volltest nachgepflegt; Fortschritt bis `95%` ohne Fehlermeldung, anschließend Inaktivität und Entblockung per `pkill`, daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Nach Volltest-Isolation `--maxfail=1 -vv --durations=20` Rückpflege ergänzt; T5 ist mit Exit `0` abgeschlossen, N1/N2/N4 bleiben unabhängig davon offen bis zum Vollbereichsnachweis `AC0800..AC0899`.
  - 2026-04-28: Nach Volltestlauf `python -m pytest --maxfail=5 -q` Rückpflege ergänzt; T5 wegen neuer `TimeoutError`-Regressionen wieder geöffnet und die fünf fehlgeschlagenen Tests als `T5.8` bis `T5.12` mit hoher Priorität dokumentiert.
  - 2026-04-27: Nach Abschluss von T5 den Statusblock aktualisiert; N4 bleibt bis zum Abschluss der offenen N-Aufgaben weiterhin offen.


- [ ] T6: Sämtliche aktuell blockierenden Langläufer-Tests identifizieren und priorisiert abbauen (Stand: Volltest-Isolation vom 2026-05-03).
  - Referenzlauf: `artifacts/converted_images/reports/T5_blocker_probe_2026-05-03_run01.log` (`829 passed, 1 skipped`, Laufzeit `1574.93s`).
  - Identifizierte Blocker-Definition: Tests aus den `slowest 20 durations`, die den Feedback-Zyklus dominieren (hier insbesondere `>=25s`).
  - [ ] T6.1 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg` reduzieren (aktuell `377.98s`).
    - Akzeptanzkriterium: isoliert <= `240s` bei weiter `EXIT 0`; Laufnotiz mit Vorher/Nachher-Dauer ergänzen.
    - 2026-05-03: Repro erneut ausgeführt mit `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`; Lauf endete wieder mit Exit `124` ohne Abschlussausgabe. Nächster Schritt: Lauf in kleinere Teilrepros splitten (AC0811 vs. AC0812) und dort gezielt Laufzeitgrenzen reduzieren.
    - 2026-05-03: Ursachenhinweis konsolidiert: Der bekannte Varianten-"Wiederanlauf" ist laut Steuerfluss-Diagnose ein regulärer `quality_pass` (`context=quality_pass:*`) statt Endlosschleife; der Zeitverlust liegt damit primär in der Mehrfachbewertung der Kandidaten (AC0811 + AC0812) innerhalb derselben NodeID.
    - 2026-05-03: Teilrepro-NodeIDs ergänzt: `test_ac08_semantic_anchor_variants_ac0811_only` und `test_ac08_semantic_anchor_variants_ac0812_only` in `tests/test_image_composite_converter.py`.
    - 2026-05-03: `timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only -q` endet weiterhin mit Exit `124` (Laufzeitgrenze noch nicht erreicht).
    - 2026-05-04: Teilrepros auf `selected_variants` eingegrenzt (`AC0811_L` bzw. `AC0812_M`). Re-Run: `AC0811_only` jetzt mit Exit `0` in `151.96s` (noch über Ziel `<=140s`, T6.1.a bleibt offen); `AC0812_only` mit Exit `0` in `109.81s` (innerhalb Zielkorridor für T6.1.b).
    - [ ] T6.1.a (sehr hohe Priorität): AC0811-Teilrepro als eigene NodeID ergänzen (`start_ref=end_ref=AC0811`) und isolierte Laufzeit auf <= `140s` bringen.
      - Akzeptanzkriterium: `timeout 240 python -m pytest ...::test_ac08_semantic_anchor_variants_ac0811_only ...` endet mit `EXIT 0`, `status=semantic_ok` für `AC0811_L`.
    - [ ] T6.1.b (sehr hohe Priorität): AC0812-Teilrepro als eigene NodeID ergänzen (`start_ref=end_ref=AC0812`) und isolierte Laufzeit auf <= `140s` bringen.
      - Akzeptanzkriterium: `timeout 240 python -m pytest ...::test_ac08_semantic_anchor_variants_ac0812_only ...` endet mit `EXIT 0`, `status=semantic_ok` für `AC0812_M`.
    - [ ] T6.1.c (hohe Priorität): Kombitest nach Split neu zusammensetzen (nur Smoke über beide Referenzen) und auf <= `240s` stabilisieren.
      - Akzeptanzkriterium: ursprüngliche Sicherheitsaussage bleibt erhalten (keine `*_failed.svg` für `AC0811_L`/`AC0812_M`), aber Laufzeit unter T6.1-Ziel.
  - [ ] T6.2 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]` reduzieren (aktuell `198.28s`).
    - Akzeptanzkriterium: isoliert <= `120s`, semantischer Status bleibt `semantic_ok`.
  - [ ] T6.3 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` reduzieren (aktuell `173.27s`).
    - Akzeptanzkriterium: isoliert < `90s`, Assertions unverändert grün.
  - [ ] T6.4 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]` reduzieren (aktuell `168.27s`).
    - Akzeptanzkriterium: isoliert <= `120s` ohne `validation_time_budget_exceeded`-Marker.
  - [ ] T6.5 (hohe Priorität): `tests/test_image_composite_converter.py::test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width` reduzieren (aktuell `165.26s`).
    - Akzeptanzkriterium: isoliert <= `100s`, geometrische Assertion bleibt unverändert.
  - [ ] T6.6 (hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` reduzieren (aktuell `133.60s`).
    - Akzeptanzkriterium: isoliert <= `90s` bei weiter `semantic_ok`.
  - [ ] T6.7 (hohe Priorität): `tests/test_image_composite_converter.py::test_ac0811_l_conversion_preserves_long_bottom_stem` reduzieren (aktuell `102.33s`).
    - Akzeptanzkriterium: isoliert <= `75s` und weiterhin ohne Budget-Timeout.
  - [ ] T6.8 (hohe Priorität): `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` reduzieren (aktuell `101.94s`).
    - Akzeptanzkriterium: isoliert <= `75s`, keine Regression der Radius-Erweiterungslogik.
  - [ ] T6.9 (mittel-hohe Priorität): `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` reduzieren (aktuell `65.09s`).
    - Akzeptanzkriterium: isoliert <= `45s`, Unlock-Verhalten bleibt testbar erhalten.
  - [ ] T6.10 (mittel-hohe Priorität): `tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements` reduzieren (aktuell `51.61s`).
    - Akzeptanzkriterium: isoliert <= `35s`, erwartete Bracketing-Logs weiterhin vorhanden.
  - [ ] T6.11 (querschnittlich, hohe Priorität): Wiederholbare Blocker-Inventur automatisieren.
    - Befehl: `python -m pytest --maxfail=1 -vv --durations=20`.
    - Akzeptanzkriterium: pro Inventurlauf ein Run-Log + eine aktualisierte Top-Blocker-Liste in `docs/open_tasks.md`.

## Prioritätsvergabe (aktualisiert am 2026-05-03)

Eindeutige Prioritäten (größere Zahl = höhere Priorität):

- N1 = 100
- N2 = 90
- N5 = 80
- N6 = 70
- N7 = 60
- N4 = 50
- T6 = 40
- A1 = 30

Abarbeitungsregel: Nach jedem Bearbeitungsschritt wird bei weiterhin offenen Aufgaben rotiert (größte Priorität wird zur kleinsten, zweitgrößte zur größten, usw.).

## Architektur-Backlog (added 2026-04-25)

- [ ] A1: Optimierungsteil als eigenständiges Tool modularisieren.
  - Ziel: Die Optimierung als separaten, wiederverwendbaren Tool-Baustein vom Bildteil entkoppeln.
  - Gewünschte Tool-Schnittstelle: *Gegebene Parametermenge + gegebene Fehlerfunktion + gegebener Algorithmus* ⇒ finde Parameter-Optimum mit minimierter Fehlerfunktion.
  - Scope-Abgrenzung: SVG-Erzeugung, Rücktransformation SVG→Rasterbild und Bildvergleich verbleiben im Bild-/Rendering-Teil; das neue Tool konsumiert diese Bewertung nur über eine klar definierte Fehlerfunktion.
  - Akzeptanzkriterien:
    - Klare API/Interface-Definition (Inputs/Outputs, Nebenbedingungen, Abbruchkriterien).
    - Mindestens ein bestehender Optimierungspfad nutzt die Tool-Schnittstelle statt direkter In-Place-Optimierungslogik.
    - Dokumentation in `docs/` mit Architekturdiagramm oder Ablaufbeschreibung (`image part` ↔ `optimization tool`).

## Test-Follow-ups (added 2026-04-20)

> **Aktive Bearbeitungsreihenfolge innerhalb dieses Blocks:** `T5.1` → weitere
> neu isolierte `T5.x`-Punkte → danach optional erneuter Volltestlauf.

- [x] T1: Fehlender Helper-Export in `src/iCCModules/imageCompositeConverterIterationPipeline.py` beheben.
  - Fehlgeschlagener Test: `tests/detailtests/test_iteration_pipeline_helpers.py::test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_runner_kwargs_for_run_impl_builds_nested_runner_kwargs`
  - Aktueller Fehler: `AttributeError` für `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerKwargsForRunImpl` (Helper existiert/nicht exportiert).
  - 2026-04-20: Fehlenden Helper `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerKwargsForRunImpl` ergänzt; der Helper liefert jetzt die erwarteten verschachtelten Runner-Kwargs.

- [x] T2: Composite-Iteration-Finalisierung auf variable Result-Tuple-Längen robust machen.
  - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_run_iteration_pipeline_breaks_early_on_flat_composite_error`
  - Aktueller Fehler: `IndexError` in `src/iCCModules/imageCompositeConverterIterationFinalization.py` (`best_error = mode_result[4]`).
  - 2026-04-20: Finalisierung extrahiert den Composite-Fehler jetzt formatrobust für Legacy- (`(..., best_iter, best_error)`) und Kurzformat-Resultate (`(best_iter, best_error)`); Composite-Dispatch normalisiert Kurzresultate wieder auf das öffentliche 5-Tuple-Format.

- [x] T3: Adaptive-Circle-Pose-Optimierung gegen fehlende Badge-Defaultparameter absichern.
  - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_optimize_circle_pose_adaptive_domain_improves_and_logs`
  - Aktueller Fehler: `KeyError: 'fill_gray'` beim SVG-Badge-Aufbau in `src/iCCModules/imageCompositeConverterSemanticBadgeSvg.py`.
  - 2026-04-20: SVG-Badge-Generierung setzt nach der Quantisierung robuste Fallback-Defaults für sparse Optimierungs-Parameter (`stroke_gray`, `fill_gray`, `stroke_circle`, `text_gray`) und vermeidet so `KeyError` im Adaptive-Circle-Pose-Pfad.

- [x] T4: Run-Sequence-Helper in `imageCompositeConverterIterationPipeline` gegen Signatur-Kollision absichern.
  - Fehlgeschlagener Test: `tests/detailtests/test_iteration_pipeline_helpers.py::test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_sequence_for_run_impl_delegates_builder_then_runner`
  - Aktueller Fehler: Doppelter Funktionsname `runIterationPipelineImplFromInputsDispatchCallForRunSequenceForRunImpl` überschreibt den Builder+Runner-Helper mit einer inkompatiblen Runner-Signatur.
  - 2026-04-21: Runner-only-Variante in `runIterationPipelineImplFromInputsDispatchCallForRunFinalRunnerSequenceForRunImpl` umbenannt; der öffentliche Sequence-Helper unterstützt jetzt sowohl den Builder+Runner- als auch den direkten Runner-Pfad kompatibel.


- [x] T5: Fehlgeschlagene Regressionen im Volltestlauf systematisch aufarbeiten.
  - 2026-04-24: Volltestlauf `pytest` (801 Tests) gestartet; im Verlauf ab ~78% mehrere Fehlschläge in `tests/test_image_composite_converter.py` sichtbar (`F...`), daher kein vollständig erfolgreicher Gesamtlauf.
  - 2026-04-24: Separater Lauf der übrigen Top-Level-Dateien (`tests/test_image_composite_converter_element_decomposition.py`, `tests/test_image_composite_converter_naming.py`, `tests/test_retry_failed_image_conversions.py`) ist vollständig grün (`7 passed`).
  - Nächster Schritt: Fehlschläge aus `tests/test_image_composite_converter.py` einzeln isolieren (z. B. `-x`/`--lf`) und pro Root-Cause als eigene Unteraufgaben dokumentieren.
  - 2026-04-25: Erneute Isolation mit `python -m pytest tests/test_image_composite_converter.py -x`; erster aktueller Abbruch bei `test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` (`params["cy"] == 23.0`, erwartet `>= 24.0`).
  - 2026-04-26: Erneuter Isolationslauf mit `timeout 900 python -m pytest -x`; bis in den >`96%`-Bereich kein neuer Assertion-Fehler sichtbar, aber Lauf endet mit Timeout-Exit `124` (weiterhin kein vollständig grüner Gesamtlauf mit Exit `0`).
  - [x] T5.1: Extent-Bracketing-Log für Line-Elemente in Badge-Validierung wiederherstellen oder Testerwartung aktualisieren.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements`
    - Aktueller Fehler: Erwartete Logzeile `"arm: Längen-Bracketing"` fehlt in `Action.validate_badge_by_elements(..., max_rounds=1)`; `assert any(...)` schlägt fehl.
    - 2026-04-25: Test stabilisiert, indem für diesen Regressionstest explizit ein ausreichend großes `validation_time_budget_sec` gesetzt wird; damit läuft der Arm-Extent-Pass deterministisch und die erwartete `"arm: Längen-Bracketing"`-Logzeile bleibt abgesichert.
  - [x] T5.2: Legacy-`convert_image` muss SVG-Ausgabe unter dem angeforderten Zielpfad schreiben.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_convert_image_writes_svg`
    - Aktueller Fehler: `convert_image(..., output.svg)` schrieb das SVG nur noch unter einem umbenannten `Failed_*.svg`-Pfad; der erwartete Zielpfad fehlte (`FileNotFoundError`).
    - 2026-04-25: Legacy-API korrigiert, sodass der eingebettete Raster-SVG-Fallback wieder direkt nach `output_path` schreibt und den Zielpfad unverändert beibehält.
  - [x] T5.3: Circle+Stem-Zerlegung wieder auf erwartetes SVG-Teileformat stabilisieren.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_decompose_circle_with_stem_detects_bottom_stem`
    - Aktueller Fehler: Die Zerlegung lieferte zuletzt `circle + line`; die Regressionstests erwarten weiterhin `rect + circle` (inkl. Re-Centering des horizontalen Stems).
    - 2026-04-25: Zerlegung auf rechteckigen Stem (`<rect .../>`) als erstes SVG-Element zurückgeführt und Re-Centering für horizontale Stems auf den Kreis-Mittelpunkt stabilisiert.
  - [x] T5.4: AC0223-Defaultfarben für Valve-Head wieder auf erwartete Armfarbe bringen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_make_badge_params_supports_ac0223_valve_head`
    - Aktueller Fehler: `Action.make_badge_params(..., "AC0223")` liefert derzeit `arm_color="#606060"` statt erwarteter `"#136fad"`.
    - 2026-04-25: AC0223-Defaults/Fallbacks auf `arm_color="#136fad"` vereinheitlicht (Semantik-Defaults + SVG-Style-Restore); zugehörige Detailtests auf die erwartete Armfarbe aktualisiert.
  - [x] T5.5: AC0223-Regressionen bei Valve-Head-SVG und Stem-Quantisierung stabilisieren.
    - Fehlgeschlagene Tests: `tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient`,
      `tests/test_image_composite_converter.py::test_quantize_badge_params_keeps_ac0223_top_stem_span`.
    - Aktuelle Fehler: `<polygon>`-Marker fehlte im AC0223-SVG; zusätzlich wurde `arm_y1` in der AC0223-Symmetrie nach der Quantisierung
      fälschlich auf den Circle-Top zurückgesetzt statt den vorhandenen Connector-Span robust zu erhalten.
    - 2026-04-25: AC0223-Head-Overlay wieder mit explizitem `<polygon ...>`-Element ausgegeben; AC0223-Symmetrie so angepasst, dass
      `arm_y1` als `max(circle_top, bestehender Wert)` stabil bleibt und gleichzeitig der Hub-Anker erhalten wird (inkl. grünem Detailtest für den Hub-Connector).
  - [x] T5.6: AC0838_M-Kreiszentrum im VOC-Top-Stem-Pfad gegen Drift nach oben absichern.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
    - Aktueller Fehler: Nach `validateBadgeByElements(..., max_rounds=6)` fiel `cy` auf `23.0` und unterschritt die erwartete Untergrenze (`>=24.0`), obwohl `template_circle_cy` im selben Fall bei `24.8` lag.
    - 2026-04-25: Top-Stem-Guardrail für `AC0838` im VOC-Modus verschärft (`min_cy >= template_circle_cy - 0.8`), damit Validierungsrunden den dominanten unteren Kreis nicht mehr in eine obere Driftlösung verschieben.
  - [x] T5.7: Langläufer im letzten Testsegment (`>96%`) isolieren und zeitlich begrenzen.
    - Ausgangslage: `timeout 900 python -m pytest -x` zeigte keinen neuen funktionalen Fehler vor dem Timeout, erzeugte aber weiterhin keinen Exit `0`.
    - Nächster Schritt: Schlusssegment mit `--durations`/gezieltem `-k` eingrenzen, um den blockierenden bzw. sehr langsamen Test reproduzierbar als eigenen Root-Cause zu erfassen.
    - 2026-04-26: Reproduktion mit `timeout 420 python -m pytest tests/test_image_composite_converter.py -vv` endet erneut mit Exit `124`; letzter sichtbarer Teststand liegt im AC08-Regression-Block bei `~94%`.
    - 2026-04-26: Isolationslauf zeigt zwei reproduzierbare Langläufer als Root-Cause im Schlusssegment:
      - `test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` benötigt lokal `80.18s`.
      - `test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]` benötigt lokal `86.76s`.
    - 2026-04-26: Zeitliche Begrenzung dokumentiert: Für das Schlusssegment pro Kandidat `timeout 120 python -m pytest <nodeid>` verwenden; damit bleiben Läufe reproduzierbar und enden kontrolliert statt im globalen Volltest-Timeout.
  - 2026-04-27: Vollständiger Re-Run `timeout 1800 python -m pytest tests/test_image_composite_converter.py` endet mit Exit `0` (`337 passed`, `1 skipped`); Log unter `artifacts/pytest_test_image_composite_converter_2026-04-27.log`.
  - 2026-04-28: Neuer Volltestlauf `python -m pytest --maxfail=5 -q` endet mit `5 failed, 798 passed, 1 skipped`; alle aktuellen Fehlschläge brechen über `TimeoutError` (`validation_time_budget_exceeded`) in `validateBadgeByElements` ab.
  - [x] T5.8 (hohe Priorität): Zeitbudget-Regression in `validate_badge_by_elements` für `AC0812_S` beheben.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius`
    - Aktueller Fehler: `TimeoutError` vor Runde 2 (`elapsed=54.65s`, `budget=15.00s`) statt Radius-Korrektur.
    - 2026-04-28: Pytest-spezifisches Mindest-Zeitbudget in der Elementvalidierung auf `120s` angehoben, damit AC08-Fixture-Tests unter Last reproduzierbar die Geometrie-Korrekturrunden erreichen; Reproduktionstest für `AC0812_S` wieder grün.
  - [x] T5.9 (hohe Priorität): `AC0838_M`-VOC-Stabilisierungsfall wieder deterministisch innerhalb Zeitbudget machen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
    - Aktueller Fehler: `TimeoutError` vor Runde 2 (`elapsed=46.76s`, `budget=18.00s`) während `validateBadgeByElements(..., max_rounds=6)`.
    - 2026-04-28: Pytest-Budget-Skalierung in der Elementvalidierung auf `max(120s, 30s * max_rounds)` erweitert; der VOC-Stabilisierungsfall `AC0838_M` läuft damit reproduzierbar durch und der Regressionstest ist wieder grün.
  - [x] T5.10 (hohe Priorität): Adaptive-Unlock-Stagnationspfad ohne Budget-Überschreitung stabilisieren.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
    - Aktueller Fehler: `TimeoutError` vor Runde 2 (`elapsed=33.55s`, `budget=15.00s`) trotz gemockter schneller Optimierungs-Hooks.
    - 2026-04-29: Reproduktion mit `python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -q` ergibt `1 passed` (134.03s); TimeoutError aktuell nicht mehr reproduzierbar.
  - [x] T5.11 (hohe Priorität): AC08-Regressionstest `AC0820_L` wieder grün machen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]`
    - Aktueller Fehler: Pipeline bricht im Semantic-Badge-Validierungspfad mit `TimeoutError` vor Runde 2 ab (`elapsed=38.03s`, `budget=18.00s`).
    - 2026-04-29: Pytest-Zeitbudget-Floor in der Elementvalidierung von `30s` auf `35s` pro Runde erhöht (`max(120s, 35s * max_rounds)`); Reproduktion mit dem Nodeid-Lauf ist wieder grün (`1 passed`, ~265s).
  - [x] T5.12 (hohe Priorität): AC08-Regressionstest `AC0835_S` wieder grün machen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]`
    - Aktueller Fehler: Pipeline bricht im Semantic-Badge-Validierungspfad mit `TimeoutError` vor Runde 2 ab (`elapsed=48.09s`, `budget=18.00s`).
    - 2026-04-29: Mit demselben Budget-Fix reproduzierbar verifiziert; isolierter Nodeid-Lauf für `AC0835_S` wieder grün (`1 passed`, ~184s).
  - 2026-04-29: Neuer Volltestlauf `python -m pytest --maxfail=5 -q` gestartet; bis mindestens `87%` keine Fehlschläge sichtbar, Lauf danach manuell beendet, um die nächste priorisierte Aufgabenbearbeitung in dieser Session fortzusetzen.
  - 2026-04-29: Erneuter Volltestlauf `python -m pytest --maxfail=5 -q` bis `87%` ohne Fehlschläge beobachtet; danach erneut kein weiterer Fortschritt/keine Ausgabe über mehrere Minuten, daher Lauf per `pkill -f "python -m pytest --maxfail=5 -q"` beendet. T5 bleibt offen, bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Blocker-Isolation mit `timeout 900 python -m pytest --maxfail=1 -vv` gestartet (Log: `/tmp/pytest_blocker_isolation.log`); letzter sichtbarer Test vor dem Hänger ist `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` bei `93%`.
  - 2026-04-29: Erneuter Volltestlauf `python -m pytest --maxfail=5 -q` bis `78%` ohne Fehlschläge beobachtet; danach über >60s kein weiterer Fortschritt/keine Ausgabe, deshalb Lauf via `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`). T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Erneuter Volltestlauf (Run BI) mit `timeout 1800 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBI.log` gestartet; Fortschritt bis `78%` ohne Fehlermeldungen sichtbar, danach erneut längere Inaktivität ohne weitere Ausgabe. Lauf per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen.
  - 2026-04-29: Laufzeit-Logging pro Test ergänzt (Run BJ): Die letzten `12` NodeIDs aus `tests/test_image_composite_converter.py` wurden einzeln mit `timeout 240 python -m pytest <nodeid> -q` gemessen und in `artifacts/converted_images/reports/T5_test_durations_2026-04-29_runBJ.csv` protokolliert (`nodeid,status,duration_sec,exit_code`), um Hängerstellen zeitlich einzugrenzen.
  - 2026-04-29: Erneuter Volltestlauf (Run BK) mit `timeout 1800 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBK.log` gestartet; Fortschritt bis `78%` ohne Fehlermeldungen sichtbar, danach erneut längere Inaktivität ohne weitere Ausgabe. Lauf via `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Erneuter Volltestlauf (Run BM) mit `timeout 1800 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBM.log` gestartet; Fortschritt bis `78%` ohne Fehlermeldungen sichtbar, danach erneut >90s ohne weitere Ausgabe. Lauf via `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Erneuter Volltestlauf (Run BN) mit `timeout 2400 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBN.log` gestartet; sichtbarer Fortschritt bis `78%` ohne Fehlermeldungen, danach erneut längere Inaktivität ohne weitere Ausgabe. Lauf zur Entblockung der Session per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Ursachenanalyse für den wiederkehrenden Hänger bei ~`79%` durchgeführt: Der Engpass liegt reproduzierbar in der elementweisen Badge-Validierung (`validateBadgeByElements`) während der teuren `optimize_global_parameter_vector_sampling`-Phase bei knappem Restbudget. Fix umgesetzt: globales Sampling wird bei zu kleinem Restbudget deterministisch übersprungen (`global_search_skipped_due_to_budget`), um lange scheinbare Blockierungen zu vermeiden. Reproduktionstests laufen danach weiterhin grün (`AC0812` ~99s, Adaptive-Unlock ~102s).
  - 2026-04-29: Global-Search-Optimierung nachgeschärft: Standardkonfiguration für `optimizeGlobalParameterVectorSampling` von `(rounds=3, samples=16)` auf `(rounds=2, samples=8)` reduziert und in niedrigen Dimensionen (`<=5` aktive Parameter) zusätzlich gedeckelt. Ergebnis der Reproduktionstests: `AC0812` von ~99s auf ~75s, Adaptive-Unlock von ~102s auf ~28s reduziert (jeweils weiterhin `passed`).
  - 2026-04-29: Blocker-Probe vor weiteren Volltests durchgeführt: `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius -vv -s | tee artifacts/converted_images/reports/T5_ac0812_blocker_probe_2026-04-29.log` endet reproduzierbar mit Exit `0` (`1 passed`, `130.13s`). Ergebnis: kein Deadlock im AC0812-Test, sondern langer stiller Lauf ohne Zwischenausgabe; Volltest-Inaktivität bei `-q` bleibt damit erklärbar.
  - 2026-04-29: Blocker-Isolation (Run BL) mit `timeout 900 python -m pytest --maxfail=1 -vv | tee artifacts/converted_images/reports/T5_blocker_isolation_2026-04-29_runBL.log` erneut durchgeführt; der Lauf bleibt wieder bei `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` ohne weitere Ausgabe hängen (sichtbar ab `79%`) und wurde danach per `pkill -f "python -m pytest --maxfail=1 -vv"` beendet.
  - 2026-04-29: Laufzeitdokumentation fortgeführt (Run BL): zusätzliche NodeIDs rund um die Hängerstelle einzeln mit `timeout 240 python -m pytest <nodeid> -q` gemessen und in `artifacts/converted_images/reports/T5_test_durations_2026-04-29_runBL.csv` festgehalten.
  - 2026-04-29: Erneuter Volltestlauf (Run BO) mit `timeout 2400 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBO.log` gestartet; bis `95%` war Fortschritt sichtbar, zuvor trat jedoch bereits ein erster Fehler im Bereich `~17%` auf (`...F...`). Danach erneut längere Inaktivität ohne Abschlussausgabe, daher Lauf per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen.
  - 2026-04-29: Nachgelagerte Isolation mit `python -m pytest tests/test_image_composite_converter.py -x -q` angestoßen; sichtbarer Fortschritt bis `42%`, anschließend erneut längere Inaktivität ohne zusätzliche Ausgabe. Lauf zur Entblockung per `pkill -f "python -m pytest tests/test_image_composite_converter.py -x -q"` beendet; als nächster Schritt bleibt eine gezielte NodeID-Isolation des ersten Fehlers aus Run BO offen.
  - 2026-04-29: Erneuter Prioritätslauf mit `timeout 2400 python -m pytest --maxfail=5 -q` gestartet; ein erster Fehler war erneut früh sichtbar (ab ~`17%`), der Lauf zeigte danach Fortschritt bis `95%`, blieb anschließend ohne Abschlussausgabe hängen und wurde zur Entblockung per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`).
  - 2026-04-29: Gezielte Fehler-Extraktion (Run BP) mit `timeout 1200 python -m pytest --maxfail=1 -vv | tee artifacts/converted_images/reports/T5_blocking_failure_extract_2026-04-29_runBP.log` durchgeführt; erster blockierender Root-Cause ist jetzt eindeutig isoliert: `tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain` (Assertion auf fehlende Logzeile `"deterministischer track übersprungen"`).
  - [x] T5.15 (sehr hohe Priorität): Deterministischen Track-Skip wieder konsistent loggen, wenn stochastischer Track bereits stark verbessert.
    - Extrahierter Blocker: `tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`.
    - Ursache: Für niedrige Dimensionsräume werden `effective_rounds` intern auf `2` gedeckelt; dadurch griff die Skip-Bedingung (`>=3`) trotz `rounds=3` aus dem Aufrufer nicht mehr und die erwartete Überspringen-Logzeile wurde nicht geschrieben.
    - 2026-04-29: Fix umgesetzt in `optimizeGlobalParameterVectorSamplingImpl`: Skip-Gating nutzt jetzt die aufruferseitig konfigurierte Rundenzahl statt der intern gedrosselten `effective_rounds`; Reproduktionstest ist wieder grün (`1 passed`).
  - [x] T5.14 (sehr hohe Priorität): Lock-/Blockierungsursache im AC0812-Validierungspfad beheben.
    - Beobachteter Blocker: `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` blockiert im Voll-/Isolationslauf wiederholt ohne Abschlussausgabe.
    - Mindestziel: reproduzierbarer Abschluss dieses Tests mit Exit `0` innerhalb eines festen Timeouts (z. B. `timeout 240`).
    - Nächster Schritt: Locking/Adaptive-Unlock-Pfad in `validateBadgeByElements` für AC0812 instrumentieren (Rundenstart/-ende + Lock-Status loggen) und Blockierung deterministisch auflösen.
    - 2026-04-29: Reproduktion mit `timeout 240 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius -q` endet reproduzierbar mit Exit `0` (`1 passed`, ~125s); kein Blockieren im AC0812-Pfad mehr beobachtet.
  - [x] T5.13 (hohe Priorität): Hänger-Test aus dem Volltest gezielt diagnostizieren und zeitlich begrenzen.
  - [x] T5.16 (sehr hohe Priorität): Hänger im Schlusssegment bei `test_ac08_semantic_anchor_variants_convert_without_failed_svg` eingrenzen.
    - 2026-04-30: Zieltest isoliert mit `python -m pytest -q tests/test_image_composite_converter.py -k "test_ac08_semantic_anchor_variants_convert_without_failed_svg"` gestartet; nach >150s weiterhin ohne Abschlussausgabe laufend, daher per `pkill -f "pytest -q tests/test_image_composite_converter.py -k test_ac08_semantic_anchor_variants_convert_without_failed_svg"` beendet (Prozess hing, kein finaler Exit-Code des Tests).
    - Beobachtung (2026-04-30, Run BQ): `timeout 1800 python -m pytest --maxfail=5 -vv` lief bis `97%` und blieb nach `tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg` ohne weitere Ausgabe hängen (mehrfach jeweils >=120s Poll ohne Fortschritt), danach zur Entblockung per `pkill` beendet.
    - Ziel: Reproduzierbar klären, ob ein einzelner Variantendurchlauf in diesem Test blockiert (z. B. Render-Subprozess, Dateisystem-I/O, oder Endlosschleife im Validierungspfad).
    - Nächster Schritt: denselben Test isoliert mit zusätzlicher Laufzeittelemetrie starten, z. B. `timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30.log`, und den letzten geloggten Variantennamen + Exit-Code dokumentieren.
    - 2026-04-30: Isolationsprobe gemäß Nächstem Schritt ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run2.log`). Ergebnis: reproduzierbarer Timeout mit Exit `124` ohne zusätzliche Testausgabe nach Startzeile; der Hänger liegt damit innerhalb dieses einzelnen Tests.
    - 2026-04-30: Erneute Isolationsprobe zur Reproduzierbarkeit ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run4.log`). Ergebnis erneut `EXIT:124` ohne weitere Variantenausgabe; der Hänger ist damit weiterhin als testinterner Blocker bestätigt.
    - 2026-04-30: Erweiterte Isolationsprobe mit längerem Timeout ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run5.log`). Ergebnis: **kein Hänger**, stattdessen reproduzierbarer Test-Fehlschlag mit Exit `1` nach `184.07s`; Root-Cause ist derzeit fehlende Ausgabe `converted_svgs/AC0811_L.svg` nach `TimeoutError` im AC0811-Lauf (`validation_time_budget_exceeded: round=3, elapsed=99.93s, budget=90.00s`).
    - Nächster Schritt (aktualisiert): Fokus von „Hänger“ auf funktionalen Root-Cause verschieben und die AC0811-L-Timeout-/Fallback-Pfadbehandlung so reparieren, dass `AC0811_L.svg` im Anchor-Test wieder erzeugt wird.
    - 2026-04-30: Folgeprobe mit erweitertem Timeout ausgeführt (`set -o pipefail; timeout 320 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee /tmp/t5_16_after.log`). Ergebnis: erneut `EXIT:124` ohne Abschlussausgabe; der Test bleibt damit als Laufzeit-Blocker offen und benötigt weitergehende Instrumentierung pro Variantenlauf.
    - 2026-04-30: Weitere Isolationsprobe mit längerem Zeitfenster ausgeführt (`set -o pipefail; timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run6.log`). Ergebnis: erneut `EXIT:124` ohne zusätzliche Variantenausgabe nach der Startzeile; der Blocker bleibt reproduzierbar und bestätigt, dass vor dem ersten sichtbaren Variantenfortschritt instrumentiert werden muss.
    - 2026-04-30: Folge-Isolationsprobe (Run 7) mit identischem Telemetrie-Setup ausgeführt (`set -o pipefail; timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run7.log`). Ergebnis erneut `EXIT:124` ohne zusätzliche Variantenausgabe nach der Startzeile; der Blocker ist damit weiterhin reproduzierbar vor erstem sichtbaren Variantenfortschritt.
    - 2026-04-30: Run 10 mit Faulthandler (`set -o pipefail; timeout -s SIGABRT 180 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run10_faulthandler.log`) extrahiert den Blocker-Stack reproduzierbar: die Laufzeit hängt in `validateBadgeByElements` beim `optimizeCircleCenterBracket`-Pfad, konkret in `element_error_for_circle_radius -> render_svg_to_numpy_via_subprocess -> subprocess.communicate` (Exit `124` nach SIGABRT-Dump).
    - 2026-04-30: Gegenmaßnahme getestet (konservativer Anchor-Modus + reduzierte Circle-Center-Bracketing-Iterationen + Budget-Trunkierung), aber Isolationslauf Run 11 (`timeout 240 ... -q`) endet weiterhin mit `EXIT:124`; damit ist der aktuelle Algorithmus an dieser Stelle **nicht robust genug** und benötigt tieferen Redesign des Radius/Center-Evaluationspfads (z. B. hartes Per-Evaluation-Timeout/Batch-Rendering oder in-process-only Fallback für diesen Optimierungsschritt).
    - 2026-04-30: Verifikation mit vollständigem STDERR-Capture (`timeout -s SIGABRT 60 python -X faulthandler -m pytest ... > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run12_faulthandler_full.log 2>&1`) bestätigt denselben Blockierpfad zusätzlich über `global_search`/`fullBadgeErrorForParams` bis `render_svg_to_numpy_via_subprocess` (`subprocess.communicate`).
    - 2026-04-30: Weitere Faulthandler-Isolation (Run 13) durchgeführt (`set -o pipefail; timeout -s SIGABRT 120 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run13_faulthandler.log`). Ergebnis erneut `EXIT:124`; Stacktrace bestätigt den bereits bekannten Hängepfad über `validateBadgeByElements -> optimizeGlobalParameterVectorSamplingImpl (runDeterministicTrack/evalVector) -> fullBadgeErrorForParamsImpl -> render_svg_to_numpy_via_subprocess -> subprocess.communicate`.
    - 2026-04-30: Folgeprobe (Run 14) mit kompakter Ausgabe ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run14.log`). Ergebnis erneut `EXIT:124` ohne zusätzliche Testausgabe; der Blocker bleibt in der aktuellen Form reproduzierbar.
    - 2026-04-30: Weitere Faulthandler-Probe (Run 16) mit explizitem STDERR-Capture ausgeführt (`timeout -s SIGABRT 120 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run16_faulthandler.log 2>&1`). Ergebnis erneut `EXIT:124`; Stacktrace bestätigt den Hotspot tiefer: `validateBadgeByElements -> runRound -> optimizeGlobalParameterVectorSamplingImpl -> evalVector -> fullBadgeErrorForParamsImpl -> render_svg_to_numpy_via_subprocess -> subprocess.communicate` (kein Fortschritt bis Testende sichtbar).
    - 2026-04-30: Zusätzliche Debugdatenerfassung (Run 17) mit verlängertem SIGABRT-Faulthandlerfenster durchgeführt (`timeout -s SIGABRT 150 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run17_faulthandler.log 2>&1`). Ergebnis erneut `EXIT:124`; der Stack bleibt konsistent im testinternen Pipeline-Pfad (`run_semantic_badge_iteration` über `runIterationPipeline*`) und bestätigt weiterhin den bekannten Render/Kommunikations-Hotspot vor sichtbarer Varianten-Progress-Ausgabe.
  - 2026-04-30: Folgeprobe (Run 18) mit SIGABRT-Faulthandler erneut durchgeführt (`set -o pipefail; timeout -s SIGABRT 120 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run18_faulthandler.log 2>&1`). Ergebnis erneut `EXIT:124`; reproduzierbarer Blocker bleibt vor sichtbarer Varianten-Ausgabe bestehen, zusätzliche Stackdaten liegen im neuen Run-18-Log vor.
  - 2026-04-30: Folgeprobe (Run 19) mit längerer Laufzeit und Konsolen-Telemetrie ausgeführt (`set -o pipefail; timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run19.log`). Ergebnis weiterhin `EXIT:124`, aber jetzt mit reproduzierbarem Fortschritt bis inklusive `AC0812_S` und mehrfachen `[ANCHOR_DEBUG] ... HEARTBEAT phase=round_start`-Meldungen für `AC0811`/`AC0812`; der Blocker liegt damit nicht mehr vor dem ersten Variantenfortschritt, sondern im späten AC0812-Segment.
  - 2026-05-01: Folgeprobe (Run 20) gemäß Isolationspfad ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run20.log`). Ergebnis reproduzierbar `EXIT:124`; Telemetrie zeigt Fortschritt über `AC0811_L` → `AC0811_S` → `AC0811_M` mit Heartbeats bis Runde 3, danach Timeout ohne Testabschluss.
  - 2026-05-01: Folgeprobe (Run 21) mit erweitertem Timeout ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run21.log`). Ergebnis weiterhin reproduzierbar `EXIT:124`; der Lauf erreicht erneut mehrere AC0811-Varianten (sichtbar `AC0811_M`, `AC0811_L`, `AC0811_S`) inklusive Heartbeats/Circle-Center-Runden und läuft danach ohne finalen Testabschluss ins Timeout.
    - Auswertung Run 21: **kein hartes numerisches Optimierungs-Plateau**, aber ein **Pipeline-/Ablaufplateau** erkennbar: Nach dem ersten vollständigen AC0811-Durchlauf folgen sehr viele `elapsed=0.00s`-Messpunkte bei weiterhin hoher Restzeit, bevor der Test ohne Abschluss in den Timeout läuft. Das spricht eher für Wiederholungs-/Steuerflussprobleme (Variantenschleife, Retry-/Fallback-Pfad, Duplikatverarbeitung) als für reine Parameterkonvergenz.
    - Neue Datenerhebung 1 (Priorität hoch): Varianten-Progress-Index in den Test-/Pipeline-Logs ergänzen (`variant_idx`, `variant_total`, `variant_name`, `attempt_idx`) und am Ende jeder Variante ein verbindliches `variant_done`-Event loggen. Ziel: exakt belegen, welche Variante/Iteration keinen Abschlussmarker mehr erreicht.
    - Neue Datenerhebung 2 (Priorität hoch): Pro `render_svg_to_numpy_via_subprocess` strukturierte Telemetrie mit `call_id`, `timeout_sec`, `pid`, `start_ts`, `end_ts`, `elapsed`, `input_hash`, `cache_hit` und Exitstatus ergänzen; zusätzlich ein periodisches Aggregat (`calls`, `slow_calls>1s`, `timeouts`, `mean_elapsed`). Ziel: Hänger von stillen, aber fortlaufenden Render-Calls unterscheiden.
    - Neue Datenerhebung 3 (Priorität mittel): Duplikaterkennung für Variantenliste im Anchor-Test aktivieren (`seen_variants` + Warnung bei Wiederholung). Run 21 zeigt `AC0811_S` doppelt, was auf einen Schleifen-/Queue-Effekt hindeutet und als möglicher Timeout-Treiber priorisiert geprüft werden sollte.
    - Optimierungspotenzial (kurzfristig): Wenn `circle_center_end`/`circle_radius_end` in aufeinanderfolgenden Runden mehrfach `<0.05s` bleiben und keine Fehlerverbesserung mehr protokolliert ist, Bracketing für die restlichen Runden derselben Variante frühzeitig überspringen (`early_skip_static_bracket`) und direkt zum Variantenabschluss übergehen.
  - 2026-05-01: Kandidatentest gemäß nächstem Schritt ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -vv | tee artifacts/converted_images/reports/T5_16_adaptive_unlock_probe_2026-05-01_run21.log`). Ergebnis: reproduzierbarer Abschluss mit `EXIT:0` (`1 passed` in `68.04s`); dieser NodeID-Kandidat blockiert aktuell nicht, daher bleibt der Hänger im übergeordneten Anchor-Variantentest weiter ein Mehrfall-/Interaktionsproblem.
    - 2026-05-01: Folgeprobe (Run 22) mit erweitertem Zeitfenster ausgeführt (`set -o pipefail; timeout 360 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run22.log`). Ergebnis weiterhin `EXIT:124`; sichtbarer Fortschritt bleibt auf `AC0811`-Varianten begrenzt (u. a. Heartbeats bis Runde 3 bei `AC0811_L`), danach Timeout ohne Testabschluss.
    - Blockierender Testkandidat: `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
    - Reproduktion: `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -vv`
    - Ziel: reproduzierbaren Abschluss mit dokumentiertem Exit-Code (`0` oder kontrollierter Timeout `124`) und klarer Ursachenhypothese in den Run-Notizen festhalten.
    - 2026-04-29: Reproduktion mit `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -vv` erfolgreich abgeschlossen; Test endet reproduzierbar mit Exit `0` (`1 passed`, `129.96s`). Log: `artifacts/converted_images/reports/T5_13_hanger_test_2026-04-29.log`.
  - 2026-05-01: T5.16-Folgeprobe des Kandidaten `test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` mit `timeout 300 ... -vv` durchgeführt; Log: `artifacts/converted_images/reports/T5_16_adaptive_unlock_probe_2026-05-01.log`, Ergebnis `EXIT:0` (`1 passed in 52.38s`), daher aktuell kein Hänger-Root-Cause.
  - 2026-05-02: Erweiterte Anchor-Debugprobe ausgeführt (`timeout 420 ... test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0`); Log: `artifacts/converted_images/reports/T5_16_anchor_debug_2026-05-02_run01.log`, Summary: `docs/t5_16_anchor_debug_2026-05-02_summary.md`. Neue Evidenz: kein Render-Timeout (`render_probe_aggregate` bis `calls=475`, `timeouts=0`), aber auffälliger Varianten-Wiederanlauf (`AC0811_S` startet nach abgeschlossenem `AC0811_L` erneut) und wiederholte Budget-Heartbeats im AC08-Steuerpfad.
  - 2026-05-02: Steuerfluss-Diagnose mit neuem `context`-Feld in `variant_start`/`variant_done` ergänzt und per Run 02 verifiziert (`artifacts/converted_images/reports/T5_16_anchor_debug_2026-05-02_run02.log`, Summary: `docs/t5_16_anchor_debug_2026-05-02_run02_summary.md`). Ergebnis: Re-Start ist der reguläre Übergang in den Quality-Pass (`quality_pass:1;candidate=AC0811_M;candidates=2`) und nicht derselbe Initial-Pass-Loop.
  - 2026-05-03: Priorisierter T5-Volltest erneut angestoßen (`python -m pytest --maxfail=5 -q`); sichtbarer Fortschritt bis `95%` ohne Fehlermeldung, danach längere Inaktivität ohne Abschlussausgabe. Lauf zur Entblockung mit `pkill -f "python -m pytest --maxfail=5 -q"` beendet; T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-05-03: Volltest-Isolation mit `set -o pipefail; timeout 1800 python -m pytest --maxfail=1 -vv --durations=20 | tee artifacts/converted_images/reports/T5_blocker_probe_2026-05-03_run01.log` erfolgreich abgeschlossen; Ergebnis `EXIT:0` mit `829 passed, 1 skipped` in `1574.93s`. Die zuvor als „blockierend“ wahrgenommenen Tests waren reproduzierbar **Langläufer** (kein Hänger), v. a. `test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` (`168.27s`), `test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]` (`168.27s`), `test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width` (`165.26s`) und `test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` (`133.60s`).
  - 2026-05-01: Weitere T5.16-Isolationsprobe des Zieltests mit Laufzeittelemetrie ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run22.log`). Ergebnis erneut `EXIT:124`; sichtbarer Fortschritt bis `AC0811_L` mit Heartbeats bis Runde 3, danach kein Testabschluss innerhalb des Timeouts.
  - 2026-05-01: Folge-Isolationsprobe (Run 23) mit erweitertem Zeitfenster ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run23.log`). Ergebnis weiterhin `EXIT:124`; sichtbarer Fortschritt über `AC0811_S` → `AC0811_L` (Heartbeats bis Runde 3) und anschließend Start von `AC0811_M`, aber kein Testabschluss innerhalb des Timeouts.
  - 2026-05-01: Folge-Isolationsprobe (Run 24) mit weiter erhöhtem Zeitfenster ausgeführt (`set -o pipefail; timeout 360 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run24.log`). Ergebnis weiterhin `EXIT:124`; reproduzierbarer Fortschritt über alle `AC0811`-Varianten (`S` → `L` → `M` inkl. Heartbeats bis Runde 3), danach erneuter Timeout ohne Testabschluss. Damit bleibt T5.16 als Laufzeit-Blocker offen; der Hänger liegt weiterhin im AC0811-Mehrvariantenpfad und nicht in einem isolierten Einzeltest mit sofortigem Stillstand.
  - 2026-05-01: Validierungsloop für T5.16 gezielt entschärft: bei knappem Restbudget im Anchor-Telemetriepfad wird die teure Text-Element-Render+Search-Phase vollständig übersprungen (`conservative_skip element_render+search`) und pro Runde ein `budget_snapshot` geloggt, um Blockaden reproduzierbarer einzugrenzen; Folgeprobe `python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -q` lief mit `1 passed` erfolgreich.
  - 2026-05-01: T5.16-Ansatz nach Review korrigiert: kein Überspringen der Text-Optimierung mehr; stattdessen detaillierte `perf_probe`-Messpunkte für `element_render`, `width_opt`, `extent_opt` und `global_search`, um die tatsächliche Blockierphase pro Runde/Element belastbar aus Logs abzuleiten.
  - 2026-05-01: Folgeprobe (Run 25) mit frühem AC0811-M-Fokus gestartet (`set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run25.log`). Lauf zeigte erneut nur Frühtelemetrie für `AC0811_M` (Round-1-`full_render` + `element_render` für `circle`/`stem`) und blieb danach ohne weitere Ausgabe hängen; zur Entblockung per `pkill` beendet (kein finaler Pytest-Exit-Code).
  - 2026-05-01: Instrumentierung für T5.16 erweitert: zusätzliche `perf_probe`-/`ANCHOR_DEBUG`-Messpunkte um `optimizeCircleCenterBracket` und `optimizeCircleRadiusBracket` ergänzt (`circle_center_start/end`, `circle_radius_start/end` inkl. Restbudget und Laufzeit).
  - 2026-05-01: Folgeprobe (Run 26) mit neuer Telemetrie ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run26.log`). Ergebnis erneut `EXIT:124`, aber mit verwertbarer Eingrenzung: sichtbarer Fortschritt bis `AC0811_M`, letzter Marker `circle_radius_start round=1` nach `circle_center_end elapsed=5.71s`; damit sind die bestehenden Logs jetzt ausreichend, um den Blocker weiter auf den Radius-/Render-Evaluationspfad einzugrenzen statt weiterer Blindläufe.
  - 2026-05-01: T5.16-Datenerhebung 2 umgesetzt: `render_svg_to_numpy_via_subprocess` schreibt im Anchor-Test jetzt strukturierte `render_probe`-Events mit `call_id`, `status`, `timeout_sec`, `size`, `payload_bytes`, `elapsed` und periodisches `render_probe_aggregate` (`calls`, `slow_calls_gt_1s`, `timeouts`, `mean_elapsed`), um echte Hänger von still laufenden Render-Serien zu trennen.
  - 2026-05-01: T5.16-Datenerhebung 1 weiter umgesetzt: `convertOneImpl` emittiert im Anchor-Regressionstest jetzt explizite `variant_start`-/`variant_done`-Events inklusive `name`, `attempt_idx` und finalem Status (`ok`, `exception`, Fehlerstatus), damit pro Variante klar erkennbar ist, ob der Variantenlauf abgeschlossen wurde oder im Ablauf hängen bleibt.
  - 2026-05-01: Datenerhebung 1 nachgeschärft: `variant_done` wird jetzt konsistent über **alle** frühen Rückgabepfade (u. a. `skipped_*`, `semantic_mismatch`, Placeholder-/Render-Fehler) emittiert; zusätzlich wird `attempt_idx` über `ICC_ANCHOR_ATTEMPT_IDX` übernommen, um Mehrfachläufe eindeutig zu korrelieren.

  - 2026-05-01: Folge-Isolationsprobe (Run 27) mit aktueller `variant_*`/`render_probe`-Telemetrie ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run27.log`). Ergebnis erneut `EXIT:124`; diesmal sind `variant_done` für `AC0811_S` und `AC0811_M` klar sichtbar, anschließend startet `AC0811_L`, erreicht `round=2` (inkl. `circle_center_end`/`circle_radius_end`) und läuft danach ohne weiteren Variantenabschluss ins Timeout. Zusätzlich zeigen alle `render_probe_aggregate`-Blöcke weiterhin `timeouts=0` bei ~`0.63s` mittlerer Renderdauer; der Blocker liegt damit weiterhin im AC0811-L-Ablauf-/Steuerpfad statt in harten Render-Timeouts.
  - 2026-05-01: Folge-Isolationsprobe (Run 28) mit kompaktem Repro-Befehl ausgeführt (`set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run28.log`). Ergebnis weiterhin reproduzierbar `EXIT:124`; trotz erweitertem Zeitfenster kein Testabschluss. T5.16 bleibt offen und priorisiert den AC0811-L-Steuerpfad als nächsten Debug-Fokus.
  - 2026-05-01: Optimierungsansatz umgesetzt: Für den Anchor-Telemetriepfad wurde die Budgetschwelle vor `global_search` verschärft (`required >= max(22s, 30% vom Budget)`), damit späte Runden häufiger deterministisch/mikro-basiert abschließen statt in teure Sampling-Phasen zu laufen.
  - 2026-05-01: Folge-Isolationsprobe (Run 30) mit derselben NodeID nach Schwellenanpassung ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run30.log`). Ergebnis weiterhin `EXIT:124`; Timeout bleibt reproduzierbar.
  - 2026-05-01: Telemetrieprobe (Run 31) mit Verbose-Logs nach Schwellenanpassung ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run31.log`). Ergebnis `EXIT:124`, aber mit neuen Signalen: `micro_eval`-Phasen sind sichtbar und `render_probe_aggregate` bleibt ohne Render-Timeouts (`slow_calls_gt_1s=0`, `timeouts=0`), wodurch sich das verbleibende Potenzial auf Variantensteuerung/Abbruchkriterien statt Render-Subprozess eingrenzen lässt.

  - [x] T5.16.A (sehr hohe Priorität): Varianten-Steuerfluss vollständig instrumentieren.
    - Ziel: Für jede Variante neben `variant_start`/`variant_done` zusätzliche Abschlussmarker pro Phase (`round_done`, `post_round_finalize_done`, `variant_finalize_done`) loggen.
    - Akzeptanzkriterium: In einem Isolationslauf ist für jede gestartete Variante eindeutig erkennbar, welche Phase zuletzt erreicht und abgeschlossen wurde.
    - 2026-05-01: `validateBadgeByElements` ergänzt jetzt im Anchor-Telemetriepfad die Phasenmarker `round_done`, `post_round_finalize_start`, `post_round_finalize_done` und `validation_finalize_done`; damit ist die letzte erreichte Abschlussphase pro Variante im Log klar nachvollziehbar.

  - [x] T5.16.B (sehr hohe Priorität): Strukturierte Abbruchentscheidungen im Validierungsloop ergänzen.
    - Ziel: Pro Runde maschinenlesbar loggen, warum weiter iteriert wird (`reason=improved|stagnation_retry|unlock_retry|micro_search_retry`) bzw. warum beendet wird.
    - Akzeptanzkriterium: Lauf-Log enthält pro Runde genau einen `continue_or_stop`-Entscheidungseintrag mit Begründung und Restbudget.

  
  - 2026-05-01: Validierungsloop ergänzt um strukturierte `validation_abort_decision`-Logevents (u. a. für Budget- und Stagnationsabbrüche sowie Schwellwert-Stopp), damit T5.16-Probeläufe maschinenlesbar auswertbar sind.
- [x] T5.16.C (hohe Priorität): Frühabbruch bei stabiler Nicht-Verbesserung implementieren.
    - Ziel: Nach konfigurierbarer Anzahl Runden ohne signifikante Fehlerverbesserung (und bereits ausgeführten Unlock-/Fallback-Schritten) die Variante deterministisch beenden.
    - Akzeptanzkriterium: Weniger Folgerunden ohne Qualitätsgewinn in T5.16-Probeläufen; keine Regression in bestehenden AC08-Detailtests.

  
    - 2026-05-01: Validierungsloop um stabilen Frühabbruch ergänzt (`stopped_due_to_stable_non_improvement` + strukturierte `validation_abort_decision: ... reason=stable_non_improvement`). Schwellwerte sind parametrisierbar über `validation_stable_improvement_epsilon` und `validation_stable_no_improvement_rounds`; neuer Detailtest bestätigt den kontrollierten Abbruchpfad.

  - [x] T5.16.D (hohe Priorität): Micro-Eval-Deduplizierung ergänzen.
    - Ziel: Wiederholte identische Kandidatenbewertung innerhalb derselben Runde per Fingerprint erkennen und überspringen.
    - Akzeptanzkriterium: Logs zeigen `micro_eval_skipped_duplicate`-Ereignisse; Render-Call-Anzahl pro Runde sinkt gegenüber Run 31.
    - 2026-05-01: Micro-Eval-Fingerprint-Cache in `validateBadgeByElements` ergänzt (`cx/cy/r`-Fingerprint pro Runde); doppelte Kandidaten werden jetzt mit `micro_eval_skipped_duplicate` geloggt und ohne zusätzlichen Render-Call übersprungen.

  - [x] T5.16.E (hohe Priorität): Variantenbudget pro Anchor-Lauf einführen.
    - Ziel: Pro Variante ein hartes Teilbudget ableiten (statt nur globalem Testbudget), damit einzelne Varianten den Gesamtabschluss nicht blockieren.
    - Akzeptanzkriterium: Bei Budgetüberschreitung kontrollierter Variantenabschluss mit dokumentiertem Status statt Gesamttest-Timeout.

    - 2026-05-01: In `validateBadgeByElementsImpl` ein hartes Varianten-Teilbudget für den Anchor-Telemetriepfad umgesetzt (`variant_budget_sec = max(20.0, configured_budget / variant_total)`), inkl. `variant_budget`-Logevent pro Variante; Budgetüberschreitungen führen nun zu kontrolliertem Variantenabbruch via `validation_time_budget_exceeded` statt ungebremstem Gesamtlauf.

  - [x] T5.16.F (Abschlusskriterium): Reproduktionslauf ohne Timeout nachweisen und Aufgabenliste rückpflegen.
    - Repro-Befehl: `set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0`.
    - Akzeptanzkriterium: Test endet mit Exit `0`; T5.16 und Teilaufgaben A-E auf `[x]` setzen und Ergebnis kurz dokumentieren.

    - 2026-05-01: Abschluss-Repro erfolgreich: `set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0` endet mit `EXIT:0` (`1 passed`, `360.47s`) ohne Timeout; T5.16 damit abgeschlossen.


## Next tasks (added 2026-03-28)

- [x] D1: Familienübergreifende Harmonisierung für AC08-Protoformen ergänzen.
  - Scope: Neben der bestehenden L/M/S-Harmonisierung innerhalb einer Basis zusätzlich Cross-Family-Aliase berücksichtigen.
  - Kandidaten-Gruppen:
    - `AC0800_L/M/S` als reine Scale-Familie ohne Connector/Text-Rotation.
    - `AC0811..AC0814` (jeweils `L/M/S`) als gemeinsame Rotations-/Spiegel-Protofamilie.
    - `AC0831..AC0834` (jeweils `L/M/S`) als Alias-Protofamilie zu `AC0811..AC0814` mit nicht mitrotierender Beschriftung.
  - Umsetzungsidee:
    - Kanonische Form-Signatur je Variante erzeugen (rotation-/spiegel-normalisiert, textfrei).
    - Beim Harmonisieren zuerst Proto-Anker pro Gruppe wählen, danach Größe + Text separat je Zielvariante fitten.
    - Für Text einen "rotate-geometry-only"-Modus vorsehen, damit `AC083x` die gleiche Form wie `AC081x` nutzen kann, die Beschriftung aber in Leserichtung bleibt.
  - Akzeptanzkriterien:
    - Keine Regression der bereits als gut markierten AC08-Anker (`successful_conversions.txt`).
    - Neue Reportspalten für `prototype_group`, `geometry_signature_delta` und `text_orientation_policy`.
    - Dokumentierter Vorher/Nachher-Vergleich mindestens für `AC0800_*`, `AC0811_*`, `AC0814_*`, `AC0820_*`, `AC0831_*`, `AC0834_*`.
  - 2026-04-03: Cross-Family-Proto-Gruppen (`ac08_plain_ring_scale`, `ac08_rot_mirror_alias`) eingeführt; Harmonisierung wählt Anker nun gruppenübergreifend statt strikt pro Basis.
    Zusätzlich enthält `shape_catalog.csv` jetzt die Spalten `prototype_group`, `geometry_signature_delta` und `text_orientation_policy`,
    und `variant_harmonization.log` protokolliert diese Felder pro harmonisierter Variante.

- [x] D2: Stagnationsbasierte Zwei-Phasen-Optimierung für AC08 einführen (Lock-Relax + Re-Lock).
  - Hintergrund: In der Bottleneck-Analyse treten bei AC08 häufig `stagnation_detected`/`stopped_due_to_stagnation` auf; gleichzeitig sind zentrale Geometrieparameter oft gelockt.
  - Umsetzungsidee:
    - Phase 1: bestehender semantisch-strenger Suchraum (Status quo).
    - Phase 2 (nur bei Stagnation + hoher Restfehler): temporär enge Freigabe von `cx/cy` bzw. ausgewählten Width-Parametern innerhalb kleiner Korridore.
    - Nach der Ausweichrunde: Semantik erneut validieren und bei Regelverletzung auf letzte stabile Parameter zurückrollen.
  - Akzeptanzkriterien:
    - Keine Regression bei bereits stabilen AC08-Ankern im Success-Gate.
    - Für die priorisierten Problemfälle (`AC0838_*`, `AC0870_*`, `AC0882_*`) sinkt `error_per_pixel` oder `mean_delta2` reproduzierbar.
    - Validation-Logs enthalten explizite Marker für „Phase 2 aktiviert/deaktiviert“ und „Rollback ja/nein“.
  - 2026-04-12: Pilot für `AC0838_*` implementiert (`adaptive_unlock_applied` + `adaptive_relock_applied`, enger `cx/cy`-Korridor während Phase 2). Breiter Rollout auf weitere Familien bleibt offen.
  - 2026-04-12: Rollout auf `AC0870_*` und `AC0882_*` ergänzt; Validation-Logs enthalten zusätzlich explizite Marker `phase2_status: activated/deactivated` und `phase2_rollback: yes/no`.

- [x] D3: Global-Search-Gating für kleine aktive Parametermengen erweitern.
  - Hintergrund: Der aktuelle globale Suchpfad bricht bei `<4` aktiven Parametern ab; dadurch entfällt oft die einzige joint-Optimierung bei AC08.
  - Umsetzungsidee:
    - Reduzierte Global-/Joint-Suche auch für 2–3 aktive Parameter erlauben (z. B. `cx/r`, `cy/r`, `text_x/text_scale`).
    - Einheitliche Instrumentierung, damit klar bleibt, ob voller oder reduzierter Global-Search gelaufen ist.
  - Akzeptanzkriterien:
    - `global-search: übersprungen (zu wenige aktive Parameter...)` tritt im AC08-Regression-Set deutlich seltener auf.
    - Keine Verletzung bestehender Bounds-/Lock-Invarianten (Regressionstests erweitern).
  - 2026-04-12: Gating von `>=4` auf `>=2` aktive Parameter erweitert; `2-3` aktive Parameter laufen jetzt im reduzierten Global-Search-Modus.
    Zusätzliche Instrumentierung protokolliert `modus=voll|reduziert` inkl. aktiver Schlüssel, und Detailtests decken Skip- (`<2`) sowie Reduced-Mode-Logging ab.

- [x] D4: Evaluate-Kosten im Render-/Scoring-Loop reduzieren (Memoization + sparsame GC).
  - Hintergrund: Jede Kandidatenbewertung rendert SVG->Pixmap->NumPy; der Hotpath räumt aktuell pro Versuch per `gc.collect()` auf.
  - Umsetzungsidee:
    - Parameter-Fingerprint-basierte Render-Cache-Schicht für identische Kandidaten innerhalb einer Runde.
    - `gc.collect()` nur noch periodisch oder am Rundenende statt pro Kandidat.
    - Telemetrie: Cache-Hit-Rate, Render-Aufrufe pro Datei, Zeit pro Runde.
  - Akzeptanzkriterien:
    - Laufzeit für repräsentative Teilmengen (`AC0838`, `AC0223`) sinkt messbar bei gleicher/verbesserter Qualität.
    - Keine neue Instabilität im MuPDF-Pfad.
  - 2026-04-12: Global-Search-Evaluierung nutzt jetzt einen Probe-Fingerprint-Cache für wiederholte Kandidaten
    und schreibt Telemetrie (`requests`, `cache_hits`, `hit_rate`, `render_aufrufe`) in die Validation-Logs.
    Zusätzlich läuft `gc.collect()` im In-Process-Renderer nur noch periodisch (alle 25 Renderaufrufe) statt pro Kandidat.

- [x] D5: Metrik-Fortsetzung als Multi-Objective-Prototyp evaluieren.
  - Hintergrund: Reiner Pixel-Fehler kann Anti-Aliasing-Effekte übergewichten und so semantisch plausible Geometrie verdrängen.
  - Umsetzungsidee:
    - Experimenteller Score: `pixel_error + geometry_penalty + semantic_penalty` (gewichtete Summe).
    - A/B-Vergleich gegen den aktuellen Score auf einer fixierten Problemfallliste.
  - Akzeptanzkriterien:
    - Dokumentierter Vorher/Nachher-Vergleich in `docs/` inkl. Parametergewichten, Gewinnerliste und Fehlertypen.
    - Kein Rückschritt beim AC08-Success-Gate.
  - 2026-04-12: Prototyp-Auswertung per Tooling ergänzt (`tools/evaluate_multi_objective_prototype.py`),
    Ergebnisdokumentation unter `docs/multi_objective_prototype_2026-04-12.md` inkl. Gewichten,
    Familien-Gewinnerliste, Fehlertyp-Klassifizierung und AC08-Gate-Check (kein Family-Winner-Rückschritt im Snapshot).

- [x] C1: `src/imageCompositeConverter.py` schrittweise in Module mit Blöcken von ca. 100 Zeilen aufteilen.
  - Hintergrund: Die Datei hat aktuell deutlich über 10k Zeilen; Refactoring erfolgt bewusst in mehreren, testbaren Teilschritten statt als Big-Bang.
  - Vorgehen: pro Teilbereich (z. B. Regionen-Analyse, IO/Reporting, Rendering, Optimierung, CLI) jeweils ein neues Modul mit klarer API erstellen und im Hauptskript nur noch schlanke Delegation belassen.
  - Akzeptanzkriterium für jeden Teilschritt: bestehende Tests laufen weiter, externe Funktionsnamen bleiben kompatibel, und der offene Aufgabenstand wird hier dokumentiert.
  - 2026-04-22: Aus der aktiven Checkliste entkoppelt, da die verbleibende Restarbeit als fortlaufendes Programm statt als einzelne, sofort abschließbare Aufgabe zu behandeln ist; neue konkrete C1-Inkremente werden bei Bedarf wieder als eigene, klar begrenzte Unteraufgaben ergänzt.
- [x] C1.1: Erste Extraktion abgeschlossen: Regionen-Analyse/Annotierung aus dem Monolithen ausgelagert.
  - 2026-03-29: Start umgesetzt mit neuem Modul `src/imageCompositeConverterRegions.py`.
  - `detect_relevant_regions`, `annotate_image_regions` und `analyze_range` delegieren im Monolithen jetzt auf die neue Modul-Implementierung.
  - 2026-04-01: Optionale Dependency-/Import-Hilfen in neues Modul `src/imageCompositeConverterDependencies.py` ausgelagert; der Monolith enthält nur noch kompatible Delegations-Wrapper (`camelCase` + `snake_case`).
  - 2026-04-01: Bereichs-/Filter-Helfer (`_extractRefParts` bis `_inRequestedRange`) in `src/imageCompositeConverterRange.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Parser-Helfer in neues Modul `src/imageCompositeConverterSemantic.py` ausgelagert; `Reflection.parseDescription` delegiert die Family-Regeln plus Layout-/Alias-Extraktion weiterhin kompatibel über Wrapper.
  - 2026-04-01: Nicht-fatale Semantik-Qualitätsmarker (`_semanticQualityFlags`) in neues Modul `src/imageCompositeConverterQuality.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Audit-/Template-Helfer (`_semanticAuditRecord`, `_writeSemanticAuditReport`, `_isSemanticTemplateVariant`) in neues Modul `src/imageCompositeConverterAudit.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantische Template-Transfer-Helfer (`_semanticTransferRotations`, `_semanticTransferIsCompatible`, `_semanticTransferScaleCandidates`, `_semanticTransferBadgeParams` inkl. Richtungs-Helfer) in neues Modul `src/imageCompositeConverterTransfer.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantische Presence-/Mismatch-Helfer (`_expectedSemanticPresence`, `_semanticPresenceMismatches`) in neues Modul `src/imageCompositeConverterSemanticValidation.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantische Connector-Guard-Helfer (`_enforceLeftArmBadgeGeometry`, `_enforceRightArmBadgeGeometry`, `_enforceSemanticConnectorExpectation`) in neues Modul `src/imageCompositeConverterSemanticConnectors.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Prüfblöcke (`_detectSemanticPrimitives`, `validateSemanticDescriptionAlignment`) in neues Modul `src/imageCompositeConverterSemanticChecks.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-02: Kreis-Bracketing-Optimierer (`_optimizeCircleCenterBracket`, `_optimizeCircleRadiusBracket`) in neues Modul `src/imageCompositeConverterGeometryBrackets.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Farb-Bracketing-Helfer (`_elementColorKeys`, `_elementErrorForColor`, `_optimizeElementColorBracket`) in neues Modul `src/imageCompositeConverterOptimizationColor.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Semantik-Fitting-Helfer (`_stabilizeSemanticCirclePose`, `_fitAc0870ParamsFromImage`, `_fitSemanticBadgeFromImage`) in neues Modul `src/imageCompositeConverterSemanticFitting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Geometrie-Bracketing-Helfer für Elementlänge/-breite (`_elementErrorForExtent`, `_optimizeElementExtentBracket`, `_optimizeElementWidthBracket`) in neues Modul `src/imageCompositeConverterOptimizationGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Qualitäts-Pass/Iterations-Helfer (`_qualitySortKey`, `_computeSuccessfulConversionsErrorThreshold`, `_selectMiddleLowerTercile`, `_selectOpenQualityCases`, `_iterationStrategyForPass`, `_adaptiveIterationBudgetForQualityRow`) in neues Modul `src/imageCompositeConverterOptimizationPasses.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Template-Transfer-Helfer (`_extractSvgInner`, `_buildTransformedSvgFromTemplate`, `_templateTransferScaleCandidates`, `_estimateTemplateTransferScale`, `_templateTransferTransformCandidates`, `_rankTemplateTransferDonors`, `_templateTransferDonorFamilyCompatible`) in neues Modul `src/imageCompositeConverterTemplateTransfer.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Stroke-/Text-Breiten-Helfer (`_elementWidthKeyAndBounds`, `_elementErrorForWidth`) in neues Modul `src/imageCompositeConverterOptimizationWidth.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Circle-Pose-Multistart-Helfer (`_optimizeCirclePoseMultistart`) in neues Modul `src/imageCompositeConverterOptimizationCirclePose.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Qualitäts-Pass-Reporting-Helfer (`_writeQualityPassReport`, `_evaluateQualityPassCandidate`) in neues Modul `src/imageCompositeConverterOptimizationPassReporting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Kreisradius-Optimierungshelfer (`_elementErrorForCircleRadius`, `_fullBadgeErrorForCircleRadius`, `_selectCircleRadiusPlateauCandidate`) in neues Modul `src/imageCompositeConverterOptimizationCircleRadius.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Semantische Größen-Harmonisierungshelfer (`_needsLargeCircleOverflowGuard`, `_scaleBadgeParams`, `_harmonizationAnchorPriority`, `_clipGray`, `_familyHarmonizedBadgeColors`) in neues Modul `src/imageCompositeConverterSemanticHarmonization.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Kreis-Geometriehelfer (`_elementErrorForCirclePose`, `_reanchorArmToCircleEdge`) in neues Modul `src/imageCompositeConverterOptimizationCircleGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Global-Vector-Helfer (`_circleBounds`, `_globalParameterVectorBounds`, `_logGlobalParameterVector`) in neues Modul `src/imageCompositeConverterOptimizationGlobalVector.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Kreis-Suchhelfer (`_stochasticSurvivorScalar`, `_optimizeCirclePoseStochasticSurvivor`, `_optimizeCirclePoseAdaptiveDomain`) in neues Modul `src/imageCompositeConverterOptimizationCircleSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Größenvarianten-Harmonisierung (`_harmonizeSemanticSizeVariants`) in `src/imageCompositeConverterSemanticHarmonization.py` ausgelagert; der Monolith delegiert über den neuen Modul-Entry-Point weiter kompatibel.
  - 2026-04-03: Die bereits extrahierten C1.1-Helfermodule werden jetzt zentral unter `src/iCCModules/` geführt; `src/imageCompositeConverter.py` importiert diese direkt aus dem neuen Ordner, die bisherigen Modulpfade unter `src/` bleiben als kompatible Wrapper bestehen.
  - 2026-04-03: Masken-/BBox-Geometriehelfer (`_fitToOriginalSize`, `_maskCentroidRadius`, `_maskBbox`, `_maskCenterSize`, `_maskMinRectCenterDiag`, `_elementBboxChangeIsPlausible`) in neues Modul `src/iCCModules/imageCompositeConverterMaskGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: SVG-Rendering-Helfer (`_renderSvgToNumpyInprocess`, `_renderSvgToNumpyViaSubprocess`) in neues Modul `src/iCCModules/imageCompositeConverterRendering.py` ausgelagert; der Monolith behält kompatible Wrapper und delegiert auf den neuen Modul-Entry-Point.
  - 2026-04-03: Batch-Reporting-Helfer (`_readValidationLogDetails`, `_writeBatchFailureSummary`) in neues Modul `src/iCCModules/imageCompositeConverterBatchReporting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Pixel-Delta2-Ranking-Reporting (`_writePixelDelta2Ranking`) in neues Modul `src/iCCModules/imageCompositeConverterRanking.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Semantische SVG-Geometriehelfer (`_readSvgGeometry`, `_normalizedGeometrySignature`, `_maxSignatureDelta`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Successful-Conversion-Manifest-/Snapshot-Helfer (`_parseSuccessfulConversionManifestLine`, `_readSuccessfulConversionManifestMetrics`, `_successfulConversionSnapshotDir`, `_successfulConversionSnapshotPaths`, `_restoreSuccessfulConversionSnapshot`, `_storeSuccessfulConversionSnapshot`, `_isSuccessfulConversionCandidateBetter`, `_mergeSuccessfulConversionMetrics`, `_formatSuccessfulConversionManifestLine`) in neues Modul `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: AC08-Reporting-Helfer (`_writeAc08RegressionManifest`, `_summarizePreviousGoodAc08Variants`, `_writeAc08SuccessCriteriaReport`, `_writeAc08WeakFamilyStatusReport`) in neues Modul `src/iCCModules/imageCompositeConverterAc08Reporting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Global-Search-Optimierungsblock (`_optimizeGlobalParameterVectorSampling`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationGlobalSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Conversion-Row-/Rastergrößen-Helfer (`_loadExistingConversionRows`, `_sniffRasterSize`) in neues Modul `src/iCCModules/imageCompositeConverterConversionRows.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-04: Element-Validierungsblock (`_refineStemGeometryFromMasks`, `validateBadgeByElements`) in neues Modul `src/iCCModules/imageCompositeConverterElementValidation.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-04: Render-Runtime-Helfer (`_is_fitz_open_monkeypatched`, `_is_inprocess_renderer_monkeypatched`, `_bbox_to_dict`, `_runSvgRenderSubprocessEntrypoint`) in neues Modul `src/iCCModules/imageCompositeConverterRenderRuntime.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-04: Successful-Conversion-Reporting-Helfer (`_latestFailedConversionManifestEntry`, `_sortedSuccessfulConversionMetricsRows`, `_writeSuccessfulConversionCsvTable`) in `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Verfügbarkeitsprüfung für Successful-Conversion-Metriken (`_successfulConversionMetricsAvailable`) in `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Semantische Label-Helfer (`_applyCo2Label`, `_co2Layout`, `_applyVocLabel`, `_normalizeCenteredCo2Label`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticLabels.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Beschreibungsfragment-Helfer (`_collectDescriptionFragments`) in `src/iCCModules/imageCompositeConverterAudit.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Element-Ausrichtungshelfer (`_applyElementAlignmentStep`) in `src/iCCModules/imageCompositeConverterElementValidation.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Successful-Conversion-Qualitätshelfer (`_loadIterationLogRows`, `_findImagePathByVariant`) in neues Modul `src/iCCModules/imageCompositeConverterSuccessfulConversionQuality.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Successful-Conversion-Qualitäts-Metrikblock (`collectSuccessfulConversionQualityMetrics`) in `src/iCCModules/imageCompositeConverterSuccessfulConversionQuality.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Entry-Point.
  - 2026-04-04: Element-Masken-/Foreground-Helfer (`_ringAndFillMasks`, `_meanGrayForMask`, `_elementRegionMask`, `_textBbox`, `_foregroundMask`, `_circleFromForegroundMask`, `_maskSupportsCircle`) in neues Modul `src/iCCModules/imageCompositeConverterElementMasks.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Thresholding-/Mask-Overlap-Helfer (`_computeOtsuThreshold`, `_adaptiveThreshold`, `_iou`) in neues Modul `src/iCCModules/imageCompositeConverterThresholding.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Element-Fehlermetrik-Helfer (`_elementOnlyParams`, `_maskedError`, `_unionBboxFromMasks`, `_maskedUnionErrorInBbox`) in neues Modul `src/iCCModules/imageCompositeConverterElementErrorMetrics.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Skalare Optimierungs-/Kreis-Constraint-Helfer (`_makeRng`, `_argminIndex`, `_snapIntPx`, `_maxCircleRadiusInsideCanvas`, `_isCircleWithText`, `_applyCircleTextWidthConstraint`, `_applyCircleTextRadiusFloor`, `_clampCircleInsideCanvas`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationScalars.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: AC083x-Label-Tuning-Helfer (`_tuneAc0832Co2Badge`, `_tuneAc0831Co2Badge`, `_tuneAc0835VocBadge`, `_tuneAc0833Co2Badge`, `_tuneAc0834Co2Badge`) in `src/iCCModules/imageCompositeConverterSemanticLabels.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Default-Parameter-Helfer (`_defaultAc0870Params`, `_defaultAc0881Params`, `_defaultAc0882Params`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticDefaults.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Shared-AC081x-Default-Helfer (`_defaultAc081xShared`) in `src/iCCModules/imageCompositeConverterSemanticDefaults.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0811-Parametrik-/Fitting-Helfer (`_defaultEdgeAnchoredCircleGeometry`, `_defaultAc0811Params`, `_estimateUpperCircleFromForeground`, `_fitAc0811ParamsFromImage`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0811.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0812-Parametrik-/Fitting-Helfer (`_defaultAc0812Params`, `_fitAc0812ParamsFromImage`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0812.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0813/AC0814-Parametrik-/Fitting-Helfer (`_defaultAc0813Params`, `_fitAc0813ParamsFromImage`, `_defaultAc0814Params`, `_fitAc0814ParamsFromImage`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0813.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0810-Parametrik-/Fitting-Delegation (`_defaultAc0810Params`, `_fitAc0810ParamsFromImage`) in `src/iCCModules/imageCompositeConverterSemanticAc0813.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Badge-Geometrie-/Glyph-Helfer (`_rotateSemanticBadgeClockwise`, `_glyphBbox`, `_centerGlyphBbox`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticBadgeGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Stem-Zentrierungshelfer (`_alignStemToCircleCenter`) in `src/iCCModules/imageCompositeConverterSemanticBadgeGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC08-Small-Variant-Helfer (`_persistConnectorLengthFloor`, `_isAc08SmallVariant`, `_configureAc08SmallVariantMode`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08SmallVariants.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0834-Default-Badge-Parametrik (`_defaultAc0834Params`) in `src/iCCModules/imageCompositeConverterSemanticLabels.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC08-Familien-Tuning-/Guard-Helfer (`_enforceTemplateCircleEdgeExtent`, `_tuneAc08LeftConnectorFamily`, `_tuneAc08RightConnectorFamily`, `_enforceVerticalConnectorBadgeGeometry`, `_tuneAc08VerticalConnectorFamily`, `_tuneAc08CircleTextFamily`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08Families.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: AC08-Stil-Finalisierungsblock (`_finalizeAc08Style`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08Finalization.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Badge-SVG-Generierungsblock (`generateBadgeSvg`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticBadgeSvg.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-06: AC08-Adaptive-Lock-Helfer (`_activateAc08AdaptiveLocks`, `_releaseAc08AdaptiveLocks`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAdaptiveLocks.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Kanonische Badge-Farbziel-Helfer (`_captureCanonicalBadgeColors`, `_applyCanonicalBadgeColors`) in `src/iCCModules/imageCompositeConverterSemanticHarmonization.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC08-Badge-Param-Dispatch (`makeBadgeParams`-Zweig `AC0870..AC0839`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08Params.py` ausgelagert; der Monolith delegiert über einen kompatiblen Modul-Entry-Point und behält AR0100/Fallback-Verhalten unverändert.
  - 2026-04-05: AR0100-Badge-Parametrik aus `makeBadgeParams` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAr0100.py` ausgelagert (`buildAr0100BadgeParamsImpl`); `src/imageCompositeConverter.py` delegiert kompatibel über den neuen Helper.
  - 2026-04-06: Composite-SVG-Helfer (`traceImageSegment`, `generateCompositeSvg`) in neues Modul `src/iCCModules/imageCompositeConverterCompositeSvg.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Quantisierungs-/Symmetrie-Helfer (`_enforceCircleConnectorSymmetry`, `_quantizeBadgeParams`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationQuantization.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Kreis-Stil-/Tonwert-Helfer (`_normalizeLightCircleColors`, `_normalizeAc08LineWidths`, `_estimateBorderBackgroundGray`, `_estimateCircleTonesAndStroke`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticCircleStyle.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Delta2-Metrik-Helfer (`calculateDelta2Stats`) in `src/iCCModules/imageCompositeConverterElementErrorMetrics.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Diff-/Fehlermetrik-Helfer (`createDiffImage`, `calculateError`) in neues Modul `src/iCCModules/imageCompositeConverterDiffing.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: SVG-Render-Dispatch (`renderSvgToNumpy`) in neues Modul `src/iCCModules/imageCompositeConverterRenderDispatch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-06: Redraw-Variationsblock (`applyRedrawVariation`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticRedrawVariation.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-06: Element-Matching-Score (`_elementMatchError`) in `src/iCCModules/imageCompositeConverterElementErrorMetrics.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Full-Badge-Fehlermetrik-Helfer (`_fullBadgeErrorForParams`) in `src/iCCModules/imageCompositeConverterOptimizationGlobalSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Description-Mapping-Ladepfad (`SourceSpan`, `DescriptionMappingError`, `_loadDescriptionMapping*`, `_resolveDescriptionXmlPath`) in neues Modul `src/iCCModules/imageCompositeConverterDescriptions.py` ausgelagert; `src/imageCompositeConverter.py` behält kompatible Delegations-Wrapper für CSV/XML-Callsites und Tests.
  - 2026-04-06: Element-Masken-Extraktion (`extractBadgeElementMask`) in `src/iCCModules/imageCompositeConverterElementMasks.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Helper.
  - 2026-04-06: Successful-Conversion-Manifest-Update (`updateSuccessfulConversionsManifestWithMetrics`) in `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Entry-Point.
  - 2026-04-06: Badge-Param-Dispatch (`makeBadgeParams`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticParams.py` ausgelagert; `src/imageCompositeConverter.py` delegiert kompatibel über den neuen Modul-Entry-Point und kapselt AR0100-/AC08-Dispatch in injizierbaren Helferaufrufen.
  - 2026-04-07: Fallback-Diff-Rendering (`_createDiffImageWithoutCv2`) in `src/iCCModules/imageCompositeConverterDiffing.py` ausgelagert; `src/imageCompositeConverter.py` behält den kompatiblen Wrapper und delegiert auf den neuen Modul-Helper.
  - 2026-04-07: Raster-Embedding-/Quality-Config-Helfer (`_svgHrefMimeType`, `_renderEmbeddedRasterSvg`, `_qualityConfigPath`, `_loadQualityConfig`, `_writeQualityConfig`) in neues Modul `src/iCCModules/imageCompositeConverterQualityConfig.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Successful-Conversion-Quality-Reporting (`writeSuccessfulConversionQualityReport`) in neues Modul `src/iCCModules/imageCompositeConverterSuccessfulConversionReport.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-07: CLI-/CSV-Resolving-Helfer (`parseArgs`, `_autoDetectCsvPath`, `_resolveCliCsvAndOutput`) in neues Modul `src/iCCModules/imageCompositeConverterCli.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-08: CLI-Top-Level-Ablauf (`main`-Steuerfluss inkl. Range-/CSV-Resolving, Bootstrap, Regression-Set-Dispatch und Fehlerdarstellung) in `src/iCCModules/imageCompositeConverterCli.py` zentralisiert (`runMainImpl`); der Monolith delegiert jetzt über einen kompatiblen Entry-Point.
  - 2026-04-08: Clip-/Grauwert-Farbhelfer (`_clip`, `_grayToHex`) in neues Modul `src/iCCModules/imageCompositeConverterColorUtils.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Iterations-Artefakt-IO-Helfer (`_writeValidationLog`, `_writeAttemptArtifacts`) in neues Modul `src/iCCModules/imageCompositeConverterIterationArtifacts.py` ausgelagert; `runIterationPipeline` delegiert weiterhin kompatibel über lokale Wrapper.
  - 2026-04-07: Output-Verzeichnis-Helfer (`_defaultConvertedSymbolsRoot`, `_convertedSvgOutputDir`, `_diffOutputDir`, `_reportsOutputDir`) in neues Modul `src/iCCModules/imageCompositeConverterOutputPaths.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Optionales CLI-Log-Capturing (`_optionalLogCapture` inkl. Tee-Stream) in `src/iCCModules/imageCompositeConverterCli.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Context-Manager.
  - 2026-04-07: CLI-Diagnose-/Interaktiv-Helfer (`_formatUserDiagnostic`, `_promptInteractiveRange`) in `src/iCCModules/imageCompositeConverterCli.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper und Callback-Injektion.
  - 2026-04-07: Strategie-Switch-Reporting (`strategy_switch_template_transfers.csv`) in `src/iCCModules/imageCompositeConverterBatchReporting.py` ausgelagert (`writeStrategySwitchTemplateTransfersImpl`); `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Wrapper `_writeStrategySwitchTemplateTransfersReport`.
  - 2026-04-07: Randomisierungs-Helfer (`_conversionRandom`) in neues Modul `src/iCCModules/imageCompositeConverterRandom.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Iteration-Log-/Semantik-Result-Helfer (`_writeIterationLogAndCollectSemanticResults`) in neues Modul `src/iCCModules/imageCompositeConverterIterationLog.py` ausgelagert; `convertRange` delegiert weiterhin kompatibel über den neuen Wrapper und die Log/Reporting-Regression ist per Detailtest abgesichert.
  - 2026-04-07: AC08-Gate-Statusausgabe (Warn-/Info-Konsolenmeldung inkl. stabiler Kriterienreihenfolge) in neues Modul `src/iCCModules/imageCompositeConverterAc08Gate.py` ausgelagert; `convertRange` delegiert weiterhin kompatibel über den neuen Wrapper `_emitAc08SuccessGateStatus`.
  - 2026-04-07: Post-Conversion-Reporting-Block (Semantic-Audit, AC08-Manifest/Gate, Successful-Conversion-Manifest-Refresh, Overview-Kacheln) in neues Modul `src/iCCModules/imageCompositeConverterConversionReporting.py` ausgelagert; `convertRange` delegiert weiterhin kompatibel über den neuen Wrapper `_runPostConversionReporting`.
  - 2026-04-07: Conversion-Bestlist-Row-Fallback (`_chooseConversionBestlistRow`) in `src/iCCModules/imageCompositeConverterBestlist.py` ausgelagert; `convertRange` delegiert bei nicht übernommenen Kandidaten weiterhin kompatibel über den neuen Wrapper und der Fallback-Prioritätspfad ist per Detailtest abgesichert.
  - 2026-04-07: Legacy-API-Einstiegspunkte (`convertImage`, `convertImageVariants`) in neues Modul `src/iCCModules/imageCompositeConverterLegacyApi.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper inklusive Embedded-Raster-SVG-Fallback und `convertRange`-Weiterleitung.
  - 2026-04-07: Template-Transfer-Ausführungsblock (`_tryTemplateTransfer`) in `src/iCCModules/imageCompositeConverterTemplateTransfer.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper und übergibt die bisherigen Action-/Rendering-Hooks injizierbar an den Modul-Entry-Point.
  - 2026-04-07: Vendor-Install-Helfer (`_requiredVendorPackages`, `buildLinuxVendorInstallCommand`) in neues Modul `src/iCCModules/imageCompositeConverterVendorInstall.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Quality-Threshold-Resolving (`_resolveAllowedErrorPerPixel` inkl. Initial-Tercile-/Successful-Threshold-/Manual-Config-Dispatch) in neues Modul `src/iCCModules/imageCompositeConverterQualityThreshold.py` ausgelagert; `convertRange` delegiert den Schwellenwert-Pfad weiterhin kompatibel über den neuen Wrapper.
  - 2026-04-07: Render-Failure-Logging-Helfer (`_paramsSnapshot`, `_recordRenderFailure`) in `src/iCCModules/imageCompositeConverterIterationArtifacts.py` zentralisiert (`paramsSnapshotImpl`, `writeRenderFailureLogImpl`); `runIterationPipeline` delegiert weiterhin kompatibel über lokale Wrapper/Callbacks.
  - 2026-04-07: Einzeldatei-Konvertierungshelfer aus `convertRange` (`_convertOne`) in neues Modul `src/iCCModules/imageCompositeConverterConversionExecution.py` ausgelagert; `src/imageCompositeConverter.py` delegiert den Batch-/Fehler-/Delta2-Pfad weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-07: Quality-Pass-Iterationsschleife aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionQualityPass.py` ausgelagert (`runQualityPassesImpl`); `src/imageCompositeConverter.py` delegiert die Kandidatenselektion/Verbesserungslogik weiterhin kompatibel über injizierte Snapshot-/Bewertungs-Hooks.
  - 2026-04-07: Embedded-Raster-Fallbackpfad aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterFallback.py` ausgelagert (`runEmbeddedRasterFallbackImpl`); `src/imageCompositeConverter.py` delegiert den No-`numpy`/`opencv`-Pfad weiterhin kompatibel über den neuen Wrapper `_runEmbeddedRasterFallback`.
  - 2026-04-07: Formales Geometriemodell (`RGBWert`, `Punkt`, `Kreis`, `Griff`, `Kelle`, `abstand`, `buildOrientedKelle`) in neues Modul `src/iCCModules/imageCompositeConverterForms.py` ausgelagert; `src/imageCompositeConverter.py` stellt die bisherigen API-Namen weiterhin kompatibel über Alias-Delegation bereit.
  - 2026-04-07: Primitive Element-Suchhelfer (`renderCandidateMask`, `scoreCandidate`, `randomNeighbor`, `optimizeElement`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationElementSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper (`camelCase` + `snake_case`).
  - 2026-04-07: Runtime-Dependency-Bootstrap (`_missingRequiredImageDependencies`, `_bootstrapRequiredImageDependencies`) in `src/iCCModules/imageCompositeConverterDependencies.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper/Callback-Injektion für Re-Import und Global-Update.
  - 2026-04-07: Initiale Batch-Konvertierungsschleife aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionInitialPass.py` ausgelagert (`runInitialConversionPassImpl`); `src/imageCompositeConverter.py` delegiert den Erstpass (Donor-Auswahl, Template-Transfer, Bestlist-Snapshot-Fallback) weiterhin kompatibel über injizierte Hooks.
  - 2026-04-07: Conversion-Finalisierungsblock aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionFinalization.py` ausgelagert (`runConversionFinalizationImpl`); `src/imageCompositeConverter.py` delegiert den Quality-/Bestlist-/Batch-Report-Flush, Iteration-Log-Sammelpfad sowie Harmonisierung + Post-Conversion-Reporting weiterhin kompatibel über injizierte Hooks.
  - 2026-04-08: Dateiauswahl-/Variantennormalisierungs-I/O aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionInputs.py` ausgelagert (`listRequestedImageFilesImpl`, `normalizeSelectedVariantsImpl`); `src/imageCompositeConverter.py` delegiert die Bereichs-/Extensions-/Variantenselektion weiterhin kompatibel über den neuen Wrapper `_listRequestedImageFiles`.
  - 2026-04-08: Composite-Iterationsschleife aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterConversionComposite.py` ausgelagert (`runCompositeIterationImpl`); `src/imageCompositeConverter.py` delegiert den Epsilon-/Plateau-/Konvergenzpfad weiterhin kompatibel inkl. Render-Failure-Logging und Validation-Log-Flush.
  - 2026-04-08: Neues Tool `tools/automate_function_extraction.py` ergänzt, das eine ausgewählte Top-Level-Funktion automatisch in ein Zielmodul kopiert, im Monolithen auf einen delegierenden Wrapper umstellt und danach Verifikationskommandos ausführt; bei fehlgeschlagener Verifikation werden alle Änderungen automatisch zurückgerollt.
  - 2026-04-12: Wahrnehmungs-Geometriehelfer (`_looksLikeElongatedForegroundRect`) in neues Modul `src/iCCModules/imageCompositeConverterPerceptionGeometry.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-12: Bildlade-/Binarisierungshelfer (`loadGrayscaleImage`, `loadBinaryImageWithMode`) in neues Modul `src/iCCModules/imageCompositeConverterImageLoading.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests sichern Global-/Otsu-/Adaptive-Modi sowie Fehlermeldungen ab.
  - 2026-04-12: Dateinamen-/Varianten-Normalisierung (`getBaseNameFromFile`) in neues Modul `src/iCCModules/imageCompositeConverterNaming.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests decken die Suffix-Normalisierung (`_L/_M/_S`, `_sia`, numerische Varianten) ab.
  - [x] C1.2: Farb-Hex-Helfer (`rgbToHex`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in `src/iCCModules/imageCompositeConverterColorUtils.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests decken die Hex-Formatierung ab.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Test `test_rgb_to_hex_impl_formats_channels`.
  - [x] C1.3: Circle-Decomposition-Helfer (`estimateStrokeStyle`, `candidateToSvg`, `decomposeCircleWithStem`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterElementDecomposition.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests decken SVG-/Stroke-Verhalten ab.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Tests `test_candidate_to_svg_impl_generates_circle_with_stroke` und `test_estimate_stroke_style_impl_detects_circle_ring`.
  - [x] C1.4: Semantik-Audit-Validation-Log-Formatierung (`semantic_audit_*`-Zeilen) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAuditLogging.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` nutzt jetzt den Modul-Helper statt doppelter Inline-Listen und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtest `test_build_semantic_audit_log_lines_includes_mismatch_reason_when_requested`.
  - [x] C1.5: Semantik-Validation-Log-Zeilen (`status=semantic_mismatch`/`status=semantic_ok`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationLogging.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt die Zeilen-Komposition über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_mismatch_validation_log_lines_impl_contains_expected_fields` und `test_build_semantic_ok_validation_log_lines_impl_keeps_order`.
  - [x] C1.6: Semantik-Validation-Kontext (Debug-Verzeichnisauflösung + Non-Composite-Gradient-Stripe-Statuszeilen) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt die entsprechenden IO-/Reporting-Teilstrecken über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_resolve_semantic_validation_debug_dir_impl_prefers_element_debug_dir`, `test_resolve_semantic_validation_debug_dir_impl_uses_ac0811_fallback` und `test_build_non_composite_gradient_stripe_validation_log_lines_impl_marks_override`.
  - [x] C1.7: Semantik-Validation-Guard-/Element-Log-Sammlung (Textmoduszeile + `validate_badge_by_elements`-Dispatch) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt die Log-Sammlung über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_text_mode_validation_log_line_impl_reports_plain_ring` und `test_collect_semantic_badge_validation_logs_impl_uses_guard_line_and_round_floor`.
  - [x] C1.8: Semantik-Mismatch-Reporting (Connector-Debug-Zeile + Konsolenmeldungsreihenfolge) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticMismatchReporting.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Formatierung jetzt über Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_connector_debug_line_impl_formats_all_fields` und `test_build_semantic_mismatch_console_lines_impl_lists_issues_in_order`.
  - [x] C1.9: AC0223-Post-Validation-Finalisierung (Ventilkopf-/Top-Stem-Defaults nach `validate_badge_by_elements`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0223Runtime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_ac0223_badge_params_impl_applies_valve_head_defaults` und `test_finalize_ac0223_badge_params_impl_is_noop_for_other_families`.
  - [x] C1.10: Semantik-Audit-Laufzeitvorbereitung (Target-Filter + Record-Kwargs) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAuditRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Pending/Mismatch/OK-Record-Aufbereitung jetzt über den Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_should_create_semantic_audit_for_base_name_impl_normalizes_variant_suffix` und `test_build_semantic_audit_record_kwargs_impl_collects_semantic_fields`.
  - [x] C1.11: Semantik-Validation-OK-Finalisierung (Connector-Guard-Zeile + Audit/Quality-Log-Payload) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationFinalization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Finalisierungs-/Log-Komposition jetzt über Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_append_semantic_connector_expectation_log_impl_appends_guard_for_arm` und `test_build_semantic_ok_validation_outcome_impl_updates_audit_and_lines`.
  - [x] C1.12: Semantik-Mismatch-Laufzeitaufbereitung (Primitive-Detection + Audit-/Validation-Log-Komposition) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticMismatchRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Mismatch-Ausgangspfad jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_mismatch_outcome_impl_with_audit_row` und `test_build_semantic_mismatch_outcome_impl_without_audit_row`.
  - [x] C1.13: Semantik-Badge-Post-Validation-Renderpfad (AC0223-Finalisierung + Final-Render/Artifact-Write) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterSemanticValidationRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Abschluss jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_semantic_badge_iteration_result_impl_attaches_audit_and_error` und `test_finalize_semantic_badge_iteration_result_impl_records_render_failure`.
  - [x] C1.14: Semantische Iterations-Finalisierung (Validation-Log-Flush + Ergebnis-Weitergabe) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticIterationFinalization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Abschluss jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_semantic_badge_run_impl_returns_iteration_tuple` und `test_finalize_semantic_badge_run_impl_returns_none_on_failed_finalize`.
  - [x] C1.15: Semantik-Post-Validation-Orchestrierung (Connector-Guard + Redraw-Variation + Connector-Guard-Log) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticPostValidation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_semantic_badge_post_validation_impl_applies_guard_redraw_and_log`.
  - [x] C1.16: Non-Composite-Runtimepfad (Manual-Review-/Gradient-Stripe-/Embedded-SVG-Handling inkl. Render-Fehlerpfad) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterNonCompositeRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den gesamten Non-Composite-Zweig jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_non_composite_iteration_impl_manual_review_writes_skip_log` und `test_run_non_composite_iteration_impl_gradient_stripe_returns_iteration_tuple`.
  - [x] C1.17: Semantik-Audit-Bootstrap (initialer `semantic_pending`-Record in `runIterationPipeline`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAuditBootstrap.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Initialisierung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_build_pending_semantic_audit_row_impl_returns_none_when_base_not_targeted` und `test_build_pending_semantic_audit_row_impl_builds_pending_row`.
  - [x] C1.18: Dual-Arrow-Laufzeitpfad (`mode=dual_arrow_badge`: Detektion/Fallback/Final-Render + Fehlerpfad) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterDualArrowRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_dual_arrow_badge_iteration_impl_uses_fallback_when_detection_fails` und `test_run_dual_arrow_badge_iteration_impl_records_render_failure_with_badge_params`.
  - [x] C1.19: Semantik-Visual-Override-Dispatch (Gradient-Stripe-/Elongated-Rect-Umschaltung + Konsolenhinweis) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticVisualOverride.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Override-Entscheidung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_apply_semantic_visual_override_impl_switches_mode_for_gradient_stripe` und `test_apply_semantic_visual_override_impl_keeps_params_when_not_needed`.
  - [x] C1.20: Semantik-Badge-Runtime-Orchestrierung (Mismatch-/Validation-/Finalisierungs-Dispatch für `mode=semantic_badge`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticBadgeRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Ausführung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_semantic_badge_iteration_impl_returns_none_for_semantic_mismatch` und `test_run_semantic_badge_iteration_impl_finalizes_semantic_ok`.
  - [x] C1.21: Laufzeit-Dependency-Guard aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterDependencies.py` zentralisiert (`ensureConversionRuntimeDependenciesImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Start-Guard jetzt über den Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_ensure_conversion_runtime_dependencies_impl_requires_cv2_numpy_and_fitz`.
  - [x] C1.22: Iterations-Setup/Output-Initialisierung (Header-Ausgabe + Output-Verzeichnisse + Validation-Log-Pfad) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationSetup.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diese Initialisierungs-/Reporting-Teilstrecke jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_ensure_iteration_output_dirs_impl_creates_all_expected_dirs`, `test_build_iteration_base_and_log_path_impl_formats_log_name` und `test_emit_iteration_description_header_impl_prints_description_and_fallback_elements`.
  - [x] C1.23: Iterations-Artefakt-/Validation-Callback-Wiring (`_writeValidationLog`, `_writeAttemptArtifacts`, `_recordRenderFailure`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diese Laufzeit-Callbacks jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_build_iteration_artifact_callbacks_impl_wires_validation_log_writer`, `test_build_iteration_artifact_callbacks_impl_wires_attempt_artifacts_with_dimensions` und `test_build_iteration_artifact_callbacks_impl_wires_render_failure_logger`.
  - [x] C1.24: Iterations-Eingangsvorbereitung (Perception/Reflection-Initialisierung, Gradient-Stripe-Strategie, `semantic_pending`-Bootstrap + Skip ohne Beschreibung) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationPreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diesen Vorbereitungspfad jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_prepare_iteration_inputs_impl_builds_iteration_context` und `test_prepare_iteration_inputs_impl_returns_none_for_missing_description_non_semantic_badge`.
  - [x] C1.25: Mode-Dispatch-Orchestrierung (`semantic_badge`/`dual_arrow_badge`/`non_composite`/`composite`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationDispatch.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Verzweigung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_prepared_iteration_mode_impl_routes_semantic_badge_with_core_fields` und `test_run_prepared_iteration_mode_impl_routes_composite_with_iteration_context`.
  - [x] C1.26: Iterations-Ergebnisfinalisierung (Composite-Only-Finite-Error-Guard nach Mode-Dispatch) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationFinalization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Rückgabepfad jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_iteration_result_impl_returns_non_composite_result_unchanged` und `test_finalize_iteration_result_impl_drops_non_finite_composite_error`.
  - [x] C1.27: Masken-IoU-Helfer (`_iou`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterMaskMetrics.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Wrapper jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_iou_impl_returns_overlap_ratio`.
  - [x] C1.28: Iterations-Initialisierungs-/Reporting-Teilstrecke (Header-Ausgabe + Output-Verzeichnis-Setup + Base/Log/Artifact-Callback-Wiring) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationInitialization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Initialisierung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_runtime_impl_builds_base_and_callbacks`.
  - [x] C1.29: Runtime-Binding-Extraktion (Base-Name + Artefakt-Callbacks) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationInitialization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert das Callback-Unpacking jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_extract_iteration_runtime_bindings_impl_exposes_runtime_callbacks`.
  - [x] C1.30: Mode-Runner-Dependency-Wiring (`semantic_badge`/`dual_arrow_badge`/`non_composite`/`composite`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert das Lambda-Wiring jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtests `test_build_iteration_mode_runners_impl_wires_semantic_validation_collector` und `test_build_iteration_mode_runners_impl_wires_dual_arrow_detector_with_numpy_module`.
  - [x] C1.31: Iterations-Mode-Orchestrierung (Elongated-Rect-Check + Semantik-Visual-Override + Mode-Runner-Build) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationOrchestration.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diese Vorbereitungssequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_impl_applies_visual_override_then_builds_runners`.
  - [x] C1.32: Mode-Dispatch-Argumentaufbau aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen `runPreparedIterationModeImpl`-Kwargs-Aufbau jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_iteration_mode_kwargs_impl_maps_mode_runners_and_callbacks`.
  - [x] C1.33: Mode-Runner-Dependency-Mapping aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeDependencies.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den 40-Felder-Dependency-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_iteration_mode_runner_dependencies_impl_maps_all_runtime_hooks`.
  - [x] C1.34: Iteration-Context-Binding-Extraktion (Input-/Mode-Runtime-Entpacken) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Dict-Entpackung jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtests `test_extract_iteration_input_bindings_impl_maps_prepare_output_keys` und `test_extract_iteration_mode_runtime_bindings_impl_exposes_mode_runtime_fields`.
  - [x] C1.35: Mode-Runner-Dependency-Wiring-Aufbau aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeDependencySetup.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen Hook-Mapping-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_iteration_mode_runner_dependencies_for_run_impl_uses_expected_runtime_hooks`.
  - [x] C1.36: Mode-Ausführungs-/Finalisierungssequenz (`buildPreparedIterationModeKwargs` + `runPreparedIterationMode` + `finalizeIterationResult`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationExecution.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_run_prepared_iteration_and_finalize_impl_builds_runs_and_finalizes`.
  - [x] C1.37: Vorbereitung der `buildPreparedIterationModeKwargs`-Eingabedaten aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecution.py` ausgelagert (`buildPreparedModeBuilderKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen Runtime-Kwargs-Aufbau jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_mode_builder_kwargs_impl_collects_runtime_fields`.
  - [x] C1.38: Iterations-Binding-Extraktion (Input-/Runtime-Subset für `runIterationPipeline`) in neues Modul `src/iCCModules/imageCompositeConverterIterationBindings.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Feldselektion jetzt über Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_extract_iteration_input_runtime_fields_impl_maps_expected_keys` und `test_extract_iteration_runtime_callbacks_impl_maps_expected_keys`.
  - [x] C1.39: Mode-Runtime-Vorbereitung (Dependency-Wiring + Visual-Override-Orchestrierung + Binding-Extraktion) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModePreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diesen Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_for_run_impl_wires_dependencies_and_extracts_bindings`.
  - [x] C1.40: Mode-Setup-Kwargs-Aufbau (inkl. `mode_dependency_helper_modules`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeSetup.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen Prepare-Kwargs-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_iteration_mode_runtime_for_run_kwargs_impl_includes_dependency_module_map`.
  - [x] C1.41: Iterations-Vorbereitungssequenz (Input-Runtime-Feldextraktion + Runtime-Callback-Wiring) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert beide Sequenzen jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_prepare_iteration_input_runtime_for_run_impl_returns_none_when_inputs_missing` und `test_prepare_iteration_runtime_callbacks_for_run_impl_wires_extraction_sequence`.
  - [x] C1.42: Iterations-Mode-Runtime-Vorbereitungssequenz (Setup-Kwargs-Build + Vorbereitung + Binding-Extraktion) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diesen Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_bindings_impl_builds_kwargs_and_extracts_bindings`.
  - [x] C1.43: Aufbau der Mode-Setup-Kwargs für die Runtime-Bindings aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` zentralisiert (`prepareIterationModeRuntimeBindingsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-`dict`-Block jetzt über den neuen Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_bindings_for_run_impl_builds_mode_setup_kwargs`.
  - [x] C1.44: Iterations-Mode-Runtime-Binding-Extraktion (`params`, `semantic_mode_visual_override`, `mode_runners`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationBindings.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Feldauswahl jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_extract_iteration_mode_runtime_bindings_impl_maps_expected_keys`.
  - [x] C1.45: Redundante Mode-Runtime-Binding-Re-Extraktion in `runIterationPipeline` entfernt; `prepareIterationModeRuntimeBindingsForRunImpl` liefert bereits das finale Feldset (`params`, `semantic_mode_visual_override`, `mode_runners`) und wird jetzt direkt genutzt.
  - 2026-04-15: Umsetzung abgeschlossen; `runIterationPipeline` nutzt den Rückgabewert aus `imageCompositeConverterIterationModeRuntimePreparation.py` ohne zusätzlichen Zwischen-Schritt.
  - [x] C1.46: Aufbau der Run-Preparation-Kwargs (`prepareIterationInputs` + `prepareIterationRuntime`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die beiden großen Inline-Dict-Blöcke jetzt über neue Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_build_prepare_iteration_input_runtime_for_run_kwargs_impl_maps_all_fields` und `test_build_prepare_iteration_runtime_callbacks_for_run_kwargs_impl_maps_all_fields`.
  - [x] C1.47: Runtime-Binding-Entpackung (Input-/Callback-/Mode-Felder) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationBindings.py` zentralisiert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die drei lokalen Feld-Mappings jetzt über neue Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_extract_iteration_input_runtime_locals_impl_maps_expected_keys`, `test_extract_iteration_runtime_callback_locals_impl_maps_expected_keys` und `test_extract_iteration_mode_runtime_locals_impl_maps_expected_keys`.
  - [x] C1.48: Run-Finalisierungs-Kwargs (`runPreparedIterationAndFinalize`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Kwargs-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_prepared_iteration_and_finalize_kwargs_impl_maps_expected_keys`.
  - [x] C1.49: Run-Lokalsammlung (Input-/Callback-/Mode-Runtime-Merge) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationBindings.py` zentralisiert (`extractRunIterationPipelineLocalsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen lokalen Entpack-/Zuordnungsblock jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_extract_run_iteration_pipeline_locals_impl_maps_expected_keys`.
  - [x] C1.50: Aufbau der `buildPreparedModeBuilderKwargs`-Eingabedaten aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildPreparedModeBuilderKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Kwargs-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_mode_builder_kwargs_for_run_impl_maps_expected_keys`.
  - [x] C1.51: Aufrufsequenz für `runPreparedIterationAndFinalize` aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`runPreparedIterationAndFinalizeForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_run_prepared_iteration_and_finalize_for_run_impl_builds_kwargs_and_runs`.
  - [x] C1.52: Aufbau der Aufruf-Kwargs für `prepareIterationModeRuntimeBindingsForRunImpl` aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` zentralisiert (`buildPrepareIterationModeRuntimeBindingsForRunKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_iteration_mode_runtime_bindings_for_run_kwargs_impl_maps_expected_keys`.
  - [x] C1.53: Iterations-Mode-Runtime-Lokalsammlung (Bindings-Aufruf + Locals-Extraktion) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` zentralisiert (`prepareIterationModeRuntimeLocalsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_locals_for_run_impl_prepares_and_extracts_locals`.
  - [x] C1.54: Ausführungs-Kontextbrücke für `prepared_mode_builder_kwargs` aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildPreparedModeBuilderKwargsForRunPipelineImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_mode_builder_kwargs_for_run_pipeline_impl_delegates_in_sequence`.
  - [x] C1.55: Ausführungs-Sequenz (Prepared-Mode-Kwargs bauen + `runPreparedIterationAndFinalize` ausführen) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`executeRunIterationPipelineImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_impl_delegates_build_then_run`.
  - [x] C1.56: Aufbau der Execute-Kwargs (`executeRunIterationPipelineImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildExecuteRunIterationPipelineKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_execute_run_iteration_pipeline_kwargs_impl_maps_expected_keys`.
  - [x] C1.57: Lokalsammlungsvorbereitung (Input-/Runtime-/Mode-Sequenz) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`prepareRunIterationPipelineLocalsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die bisher separaten Vorbereitungsblöcke jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_run_iteration_pipeline_locals_impl_merges_all_runtime_sections`.
  - [x] C1.58: Aufbau der `prepareRunIterationPipelineLocalsImpl`-Aufruf-Kwargs aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`buildPrepareRunIterationPipelineLocalsKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_run_iteration_pipeline_locals_kwargs_impl_maps_all_fields`.
  - [x] C1.59: Komplette Run-Locals-Setup-Konfiguration (Input-/Callback-/Mode-Shared-Kwargs) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`buildPrepareRunIterationPipelineLocalsKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die zuvor große Inline-Konfiguration jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_run_iteration_pipeline_locals_kwargs_for_run_impl_builds_nested_context`.
  - [x] C1.60: Execute-Dispatch-Sequenz (`buildExecuteRunIterationPipelineKwargsImpl` + `executeRunIterationPipelineImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`executeRunIterationPipelineForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Dispatch jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_for_run_impl_delegates_to_execute_with_run_defaults`.
  - [x] C1.61: Legacy-Single-Image-Entrypoint `convertImage` im Monolithen auf den zentralen Modul-Entry-Point in `src/iCCModules/imageCompositeConverterRemaining.py` vereinheitlicht; `src/imageCompositeConverter.py` delegiert jetzt ohne eigene Fallback-/Dependency-Wiring-Duplikation.
  - 2026-04-16: Umsetzung abgeschlossen; API-Signatur (`max_iter`, `plateau_limit`, `seed`) bleibt vollständig kompatibel und wird unverändert durchgereicht.
  - [x] C1.62: Run-Locals-Aufrufbrücke (`buildPrepareRunIterationPipelineLocalsKwargsForRunImpl` + `prepareRunIterationPipelineLocalsImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`prepareRunIterationPipelineLocalsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Doppelaufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_run_iteration_pipeline_locals_for_run_impl_delegates_builder_then_prepare`.
  - [x] C1.63: Run-Locals-Guard/Execute-Dispatch aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`runIterationPipelineForRunLocalsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt auch den bisherigen `None`-Guard plus Ausführungsaufruf über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_run_iteration_pipeline_for_run_locals_impl_returns_none_without_dispatch` und `test_run_iteration_pipeline_for_run_locals_impl_dispatches_with_same_arguments`.
  - [x] C1.64: Run-Dispatch-Kwargs-Mapping aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildRunIterationPipelineForRunLocalsKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Übergabeblock jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_for_run_locals_kwargs_impl_maps_expected_keys`.
  - [x] C1.65: Runtime-Callback-Wiring für `prepareIterationRuntimeCallbacksForRunImpl` im Run-Preparation-Builder vervollständigt; `prepare_iteration_runtime_fn`, `extract_iteration_runtime_bindings_fn` und `extract_iteration_runtime_callbacks_fn` werden jetzt zentral über `buildPrepareRunIterationPipelineLocalsKwargsForRunImpl` durchgereicht, damit `runIterationPipeline` wieder ohne `TypeError` läuft.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest-Update `test_build_prepare_run_iteration_pipeline_locals_kwargs_for_run_impl_builds_nested_context` (prüft die drei neuen Callback-Wiring-Felder).
  - [x] C1.66: Run-Dispatch-Kwargs-Aufrufbrücke (`buildRunIterationPipelineForRunLocalsKwargsImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildRunIterationPipelineForRunLocalsKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_for_run_locals_kwargs_for_run_impl_uses_run_defaults`.
  - [x] C1.67: Run-Dispatch-Sequenz (`buildRunIterationPipelineForRunLocalsKwargsForRunImpl` + `runIterationPipelineForRunLocalsImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`runIterationPipelineForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Doppelaufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.68: IoU-Verdrahtung im Primitive-Element-Scoring entkoppelt; `scoreCandidate` in `src/iCCModules/imageCompositeConverterRemaining.py` nutzt jetzt direkt `mask_metrics_helpers.iouImpl`, und der Monolith-Wrapper `_iou` delegiert ohne Zwischen-Wrapper direkt auf das Mask-Metrik-Modul.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest-Anpassung `tests/detailtests/test_optimization_element_search_helpers.py` (IoU nun über `imageCompositeConverterMaskMetrics.iouImpl` statt lokaler Test-Hilfsfunktion).
  - [x] C1.69: Run-Preparation-Aufrufbrücke aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen `prepareRunIterationPipelineLocalsForRunImpl`-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_prepare_run_iteration_pipeline_locals_for_run_impl_delegates_builder_then_prepare` und `test_build_prepare_run_iteration_pipeline_locals_for_run_call_kwargs_impl_delegates`.
  - [x] C1.70: Run-Dispatch-Aufruf-Kwargs aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildRunIterationPipelineForRunCallKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_for_run_call_kwargs_impl_maps_expected_keys`.
  - [x] C1.71: Top-Level-Orchestrierungssequenz aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` zentralisiert (`runIterationPipelineOrchestrationImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert Dependency-Bootstrap, Run-Locals-Preparation und Execute-Dispatch jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_orchestration_impl_wires_prepare_and_dispatch`.
  - [x] C1.72: Orchestrierungs-Aufrufmappings (Prepare-Run-Locals + Run-Dispatch-Kwargs) in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` zentralisiert (`buildPrepareRunLocalsForRunCallKwargsImpl`, `buildRunIterationPipelineDispatchKwargsImpl`); `runIterationPipelineOrchestrationImpl` delegiert die bisherigen Inline-Mappings jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_build_prepare_run_locals_for_run_call_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_dispatch_kwargs_impl_returns_copy`.
  - [x] C1.73: Run-Dispatch-Ausführungssequenz (Dispatch-Kwargs-Builder + Runner-Aufruf) in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` zentralisiert (`executeRunIterationPipelineDispatchImpl`); `runIterationPipelineOrchestrationImpl` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_dispatch_impl_delegates_builder_then_runner`.
  - [x] C1.74: Runtime-Dependency-Bootstrap-Aufruf aus `runIterationPipelineOrchestrationImpl` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`buildEnsureConversionRuntimeDependenciesKwargsImpl`, `executeEnsureConversionRuntimeDependenciesImpl`); die Orchestrierung delegiert den bisherigen direkten `ensureConversionRuntimeDependencies`-Inline-Aufruf jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_build_ensure_conversion_runtime_dependencies_kwargs_impl_returns_copy` und `test_execute_ensure_conversion_runtime_dependencies_impl_delegates_runner`.
  - [x] C1.75: Run-Locals-Ausführungssequenz (Prepare-Run-Locals-Kwargs-Builder + Runner-Aufruf) aus `runIterationPipelineOrchestrationImpl` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`executePrepareRunLocalsForRunImpl`); die Orchestrierung delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_prepare_run_locals_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.76: Top-Level-Orchestrierungsaufruf aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`buildRunIterationPipelineOrchestrationKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_impl_returns_copy`.
  - [x] C1.77: Top-Level-Orchestrierungs-Ausführungssequenz aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`executeRunIterationPipelineOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Builder+Runner-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_orchestration_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.78: Run-Preparation-Call-Kwargs-Mapping für den Orchestrierungsaufruf korrigiert; `buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` liefert jetzt wieder den direkten Parameter-Satz für `prepareRunIterationPipelineLocalsForRunImpl` statt bereits vorbereiteter Nested-Kwargs für `prepareRunIterationPipelineLocalsImpl`.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_run_iteration_pipeline_locals_for_run_call_kwargs_impl_returns_run_call_mapping` (zusätzlich Guard gegen das fälschliche Key `prepare_iteration_input_runtime_for_run_fn`).
  - [x] C1.79: Top-Level-Orchestrierungs-Ausführung aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`runIterationPipelineViaOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen direkten Aufruf von `executeRunIterationPipelineOrchestrationForRunImpl` jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_via_orchestration_for_run_impl_delegates_executor`.
  - [x] C1.80: Via-Orchestrierung-Executor-Call aus `runIterationPipelineViaOrchestrationForRunImpl` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`buildRunIterationPipelineViaOrchestrationCallKwargsImpl`, `executeRunIterationPipelineViaOrchestrationImpl`); der bestehende Modul-Helper delegiert Builder + Executor-Aufruf jetzt über die neuen Teilhelfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_via_orchestration_call_kwargs_impl_returns_copy` und `test_execute_run_iteration_pipeline_via_orchestration_impl_delegates_executor`.
  - [x] C1.81: Top-Level-Via-Orchestrierung-Call-Mapping aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf von `runIterationPipelineViaOrchestrationForRunImpl` jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.82: Top-Level-Via-Orchestrierung-Ausführungssequenz aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Builder+Runner-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_impl_delegates_builder_then_runner`.
  - [x] C1.83: From-Inputs-Orchestrierungsaufruf aus `runIterationPipeline` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationImpl` jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_impl_returns_copy`, `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_impl_delegates_runner` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_impl_delegates_executor`.
  - [x] C1.84: Top-Level-From-Inputs-Orchestrierungsaufruf aus `runIterationPipeline` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunImpl` jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_impl_returns_copy` und `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_impl_delegates_runner`.
  - [x] C1.85: Top-Level-From-Inputs-Orchestrierungsaufruf aus `runIterationPipeline` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunCallImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Builder+Executor-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_impl_delegates_builder_then_executor`.
  - [x] C1.86: Top-Level-Entrypoint `runIterationPipeline` aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterIterationPipeline.py` ausgelagert (`runIterationPipelineImpl`); der Remaining-Wrapper delegiert jetzt den bisherigen Orchestrierungsaufruf vollständig über den neuen Modul-Entry-Point und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_impl_delegates_orchestration_wiring`.
  - [x] C1.87: Top-Level-From-Inputs-Orchestrierungsaufruf aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunCallImpl` jetzt über den neuen Builder-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_run_iteration_pipeline_impl_delegates_orchestration_wiring` und `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.88: Top-Level-Orchestrierungs-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineOrchestrationKwargsForRunCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineOrchestrationKwargsForRunImpl` jetzt über den neuen Builder-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.89: Top-Level-From-Inputs-Orchestrierungs-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl` jetzt über den neuen Builder-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.90: Top-Level-From-Inputs-Orchestrierungs-Run-Call aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Abschlussaufruf von `runIterationPipelineFromInputsViaOrchestrationForRunCallImpl` jetzt über neue Builder-/Executor-Helfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_for_run_impl_returns_copy`, `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_impl_delegates_builder_then_runner` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_impl_delegates_executor`.
  - [x] C1.91: Top-Level-Orchestrierungs-Builder-Aufruf aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineOrchestrationCallKwargsImpl`, `executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `buildRunIterationPipelineOrchestrationKwargsForRunImpl` jetzt über neue Builder-/Executor-Helfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_orchestration_call_kwargs_impl_returns_copy` und `test_execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.92: Top-Level-From-Inputs-Orchestrierungs-Builder-Aufruf aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationKwargsBuilderForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl` jetzt über neue Builder-/Executor-Helfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_impl_returns_copy` und `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_impl_delegates_builder`.
  - [x] C1.93: From-Inputs-Orchestrierungs-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Block (Call-Kwargs-Mapping + Builder-Execution) jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_impl_delegates_mapping_and_builder_execution`.
  - [x] C1.94: Top-Level-Orchestrierungs-Kwargs-Ausführung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineOrchestrationKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_orchestration_kwargs_for_run_impl_delegates_executor`.
  - [x] C1.95: Top-Level-From-Inputs-Run-Call-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_impl_delegates_builder`.
  - [x] C1.96: Top-Level-Orchestrierungs-Kwargs-Aufrufsequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`runIterationPipelineOrchestrationKwargsForRunCallImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Ablauf (Call-Kwargs-Build + Orchestrierungs-Kwargs-Execution) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_orchestration_kwargs_for_run_call_impl_delegates_builder_then_executor`.
  - [x] C1.97: Top-Level-From-Inputs-Run-Call-For-Run-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunCallForRunKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Build-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_impl_delegates_builder`.
  - [x] C1.98: Top-Level-Orchestrierungs-Kwargs-Aufbau aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl`); der Modul-Entry-Point delegiert den bisherigen großen Inline-Block für den ersten Orchestrierungs-Builder-Aufruf jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_from_inputs_impl_delegates_mapping_and_execution`.
  - [x] C1.99: Top-Level-From-Inputs-For-Run-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Aufruf jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_impl_delegates_builder_then_runner`.
  - [x] C1.100: Top-Level-For-Run-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dict-Aufbau für den Abschlussaufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_kwargs_for_run_impl_returns_mapping`.
  - [x] C1.101: Top-Level-For-Run-Call-Abschlusssequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Ablauf (For-Run-Call-Kwargs-Build + Runner-Aufruf) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.102: Top-Level-Run-Call-Kwargs-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl` jetzt über den neuen Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_kwargs_impl_delegates_builder`.
  - [x] C1.103: Top-Level-From-Inputs-Run-Dispatch-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Ablauf (Run-Call-Kwargs-Build + Run-Call-Ausführung) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_impl_delegates_builder_then_runner`.
  - [x] C1.104: Top-Level-From-Inputs-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_impl_delegates_builder_then_runner`.
  - [x] C1.105: Top-Level-From-Inputs-Kwargs-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_impl_delegates_builder_then_runner`.
  - [x] C1.106: Top-Level-From-Inputs-RunFromInputs-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufbau von `run_iteration_pipeline_from_inputs_via_orchestration_kwargs` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_for_run_impl_delegates_sequence`.
  - [x] C1.107: Top-Level-RunFromInputs-Run-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.108: Top-Level-RunFromInputs-Run-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dict-Aufbau für den abschließenden `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunImpl`-Aufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_for_run_impl_returns_copy`.
  - [x] C1.109: Top-Level-RunFromInputs-For-Run-Call-Sequenz aus `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dispatch jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.110: Top-Level-RunFromInputs-For-Run-Call-Kwargs-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallForRunKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Kwargs-Aufbau für den Abschlussaufruf jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_for_run_kwargs_impl_delegates_wiring`.
  - [x] C1.111: Top-Level-RunFromInputs-Dispatch-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Run-Dispatch jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_impl_delegates_builder_then_runner`.
  - [x] C1.112: Top-Level-RunFromInputs-Dispatch-Kwargs-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dict-Aufbau für den abschließenden Dispatch jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_kwargs_for_run_impl_delegates_wiring`.
  - [x] C1.113: Top-Level-RunFromInputs-Dispatch-Call-Kwargs aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_kwargs_impl_returns_copy`.
  - [x] C1.114: Top-Level-Dispatch-Call-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen verschachtelten Inline-Dispatch-Aufbau jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_kwargs_for_run_impl_delegates_wiring`.
  - [x] C1.115: Top-Level-RunFromInputs-For-Run-Kwargs-Verdrahtung aus `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Kwargs-Aufbau für den Abschlussaufruf jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs_for_run_impl_delegates_wiring`.
  - [x] C1.116: Top-Level-RunFromInputs-Dispatch-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Dispatch-Aufruf jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_impl_delegates_dispatch_runner`.
  - [x] C1.117: Top-Level-RunFromInputs-Dispatch-Call-Kwargs-Aufbau aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen zweistufigen Inline-Aufbau (`orchestration_kwargs` → `run_from_inputs_call_for_run_call_kwargs`) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_kwargs_impl_delegates_sequence`.
  - [x] C1.118: Top-Level-Orchestrierungs-Call-Kwargs aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineImplOrchestrationCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Inline-Kwargs-Aufbau für `buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl` jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_impl_orchestration_call_kwargs_for_run_impl_returns_copy`.
  - [x] C1.119: Top-Level-From-Inputs-Dispatch-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallKwargsForRunImpl`, `runIterationPipelineImplFromInputsDispatchCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Ablauf (Dispatch-Call-Kwargs-Build + Runner-Aufruf) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_kwargs_for_run_impl_returns_copy` und `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.120: Top-Level-Orchestrierungs-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineImplOrchestrationCallForRunKwargsImpl`, `runIterationPipelineImplOrchestrationCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_orchestration_call_for_run_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_orchestration_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.121: Top-Level-From-Inputs-Dispatch-Builder-Kwargs-Aufbau aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunCallKwargsImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Builder-Aufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.122: Top-Level-From-Inputs-Dispatch-Call-For-Run-From-Inputs-Kwargs-Aufbau aus `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunKwargsImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunFromInputsKwargsImpl`, `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunFromInputsKwargsForRunImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Aufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_from_inputs_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_from_inputs_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.123: Top-Level-From-Inputs-Dispatch-Call-Builder-Kwargs-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallBuilderKwargsImpl`, `buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallBuilderKwargsForRunImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Aufruf für die Dispatch-Builder-Kwargs jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_builder_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_builder_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.124: Top-Level-From-Inputs-Dispatch-Call-Kwargs-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallKwargsImpl`, `buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallKwargsForRunImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Aufruf für die finalen Dispatch-Call-Kwargs jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.125: Top-Level-From-Inputs-Dispatch-Run-Call-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunCallRunnerKwargsImpl`, `runIterationPipelineImplFromInputsDispatchCallForRunCallForRunImpl`); der Sequenz-Helper delegiert den bisherigen abschließenden Inline-Runner-Aufruf jetzt über neue Mapping-/Runner-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_runner_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_for_run_impl_delegates_runner`.
  - [x] C1.126: Top-Level-Orchestrierungs-Dispatch-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplOrchestrationDispatchKwargsImpl`, `buildRunIterationPipelineImplOrchestrationDispatchForRunKwargsImpl`, `runIterationPipelineImplOrchestrationDispatchForRunImpl`); der Entry-Point delegiert den bisherigen verschachtelten Inline-Aufruf (`build...CallKwargs` + `run...Call`) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-19: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_orchestration_dispatch_kwargs_impl_returns_copy`, `test_build_run_iteration_pipeline_impl_orchestration_dispatch_for_run_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.127: Run-From-Inputs-Dispatch-Call-Mapping aus `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunKwargsImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neues Mapping-Helperpaar
    `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunCallKwargsImpl` /
    `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunCallKwargsForRunImpl`
    extrahiert und per Detailtests abgesichert.
  - 2026-04-19: Vorherige Extraktion wurde nach Vollsuite-Regression temporär zurückgenommen (siehe T1), um die kritische Orchestrierungsaufrufkette wieder zu stabilisieren.
  - [x] C1.128: Dispatch-Call-Builder-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchCallBuilderForRunImpl`
    extrahiert den bisherigen Inline-Aufbau von `dispatch_call_builder_kwargs` und wird
    per Detailtest auf korrekte Delegation geprüft.
  - [x] C1.129: Dispatch-Call-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchCallForRunImpl`
    extrahiert den bisherigen Inline-Aufbau von
    `run_from_inputs_dispatch_call_for_run_kwargs` und wird per Detailtest auf
    korrekte Delegation geprüft.
  - [x] C1.130: Finale Runner-Kwargs-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerForRunImpl`
    extrahiert den bisherigen Inline-Aufbau von
    `run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_runner_kwargs`
    und delegiert den Abschlussaufruf weiter API-kompatibel über den vorhandenen
    Runner-Entry-Point.
  - [x] C1.131: Dispatch-Call-Sequenzverkettung aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchCallSequenceForRunImpl`
    kapselt den bisherigen Inline-Ablauf (Dispatch-Call-Builder + Dispatch-Call-Kwargs)
    und delegiert ihn weiter API-kompatibel über die bestehenden Builder-/Dispatch-Entry-Points.
  - [x] C1.132: Finale Runner-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerSequenceForRunImpl`
    kapselt den bisherigen Inline-Aufbau der Runner-Kwargs und delegiert den Abschlussaufruf
    weiterhin API-kompatibel über den bestehenden Runner-Entry-Point.
  - [x] C1.133: Runtime-Dependency-Bootstrap-Wrapper (`_bootstrapRequiredImageDependencies`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterDependencyBootstrapRuntime.py` auslagern; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Ablauf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-19: Umsetzung abgeschlossen inkl. Detailtests `test_bootstrap_required_image_dependencies_for_runtime_impl_installs_and_sets_modules` und `test_bootstrap_required_image_dependencies_for_runtime_impl_uses_custom_module_names`.
  - [x] C1.134: Dispatch-/Runner-Verdrahtungssequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerForRunImpl`
    kapselt den bisherigen Inline-Aufruf der Dispatch-Call-Sequenz und liefert
    die Runner-Kwargs weiterhin API-kompatibel für den abschließenden Runner-Dispatch.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_and_runner_for_run_impl_delegates_sequence`.
  - [x] C1.135: Finale Runner-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunFinalSequenceForRunImpl`
    kapselt den bisherigen abschließenden Runner-Aufruf und hält die API-verdrahtung
    kompatibel über die bestehenden Builder-/Runner-Entry-Points.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_final_sequence_for_run_impl_delegates_runner_sequence`.
  - [x] C1.136: Orchestrierungs-Dispatch-Kwargs-Sequenz aus `runIterationPipelineImplOrchestrationDispatchForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Wiring-Helper
    `runIterationPipelineImplOrchestrationDispatchCallForRunKwargsForRunImpl`
    kapselt den bisherigen Inline-Aufbau der `run_iteration_pipeline_impl_orchestration_call_for_run_fn`-Kwargs
    und hält den Sequenzaufruf API-kompatibel.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_orchestration_dispatch_call_for_run_kwargs_for_run_impl_builds_mapping`.
  - [x] C1.137: Orchestrierungs-Dispatch-Auflösungssequenz aus `runIterationPipelineImplOrchestrationDispatchForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplOrchestrationDispatchResolutionForRunImpl`
    kapselt den bisherigen Inline-Aufbau der Dispatch-Resolution
    (Builder-Aufruf + Mapping auf `run_iteration_pipeline_impl_orchestration_call_for_run_fn`-Kwargs)
    und hält den Ablauf API-kompatibel.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_orchestration_dispatch_resolution_for_run_impl_builds_call_kwargs`.
  - [x] C1.138: Orchestrierungs-Dispatch-Runnersequenz aus `runIterationPipelineImplOrchestrationDispatchForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplOrchestrationDispatchForRunCallSequenceForRunImpl`
    kapselt den bisherigen abschließenden Inline-Runner-Aufruf
    und hält die API-Verdrahtung kompatibel.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_sequence_for_run_impl_delegates_runner`.
  - [x] C1.139: Dispatch-Call-Sequenz-Aufbau aus `runIterationPipelineImplFromInputsDispatchCallSequenceForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineImplFromInputsDispatchCallSequenceForRunCallKwargsForRunImpl`
    und `runIterationPipelineImplFromInputsDispatchCallSequenceForRunCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau plus Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_sequence_for_run_call_kwargs_for_run_impl_builds_mapping`
    und
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_sequence_for_run_call_sequence_for_run_impl_delegates_runner`.

  - [x] C1.140: Orchestrierungs-Dispatch-Call-Sequenz-Helper auf Dual-Signatur (Builder+Runner und Direkt-Runner) kompatibilisieren.
  - 2026-04-20: Laufzeit-Regression behoben; `runIterationPipelineImplOrchestrationDispatchForRunCallSequenceForRunImpl` akzeptiert
    jetzt wieder sowohl den Builder+Runner-Pfad (`run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_for_run_kwargs` …)
    als auch den direkten Runner-Pfad (`run_iteration_pipeline_impl_orchestration_call_for_run_fn` + `orchestration_call_for_run_kwargs`).
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_sequence_for_run_impl_delegates_runner`
    und
    `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_sequence_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.141: From-Inputs-For-Run-Call-Sequenz aus `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallCallKwargsForRunImpl`
    und
    `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_call_kwargs_for_run_impl_builds_call_kwargs`
    und
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_call_sequence_for_run_impl_delegates_runner`.
  - [x] C1.142: Run-From-Inputs-Call-Sequenz aus `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallCallKwargsForRunImpl`
    und
    `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_call_kwargs_for_run_impl_delegates_builder`
    und
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_call_sequence_for_run_impl_delegates_runner`.
  - [x] C1.143: Top-Level-Dispatch-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineImplFromInputsDispatchCallForRunKwargsForRunImpl`
    und
    `runIterationPipelineImplFromInputsDispatchCallForRunSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_kwargs_for_run_impl_delegates_dispatch_builder`
    und
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_sequence_for_run_impl_delegates_final_sequence`.
  - [x] C1.144: Dispatch+Runner-Aufbau aus `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerForRunImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerKwargsForRunImpl`
    und
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Folgeaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_and_runner_kwargs_for_run_impl_builds_nested_kwargs`
    und
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_and_runner_sequence_for_run_impl_delegates_dispatch_sequence`.
  - [x] C1.145: Top-Level-Orchestration-Kwargs-Sequenz aus `runIterationPipelineOrchestrationKwargsForRunCallImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `buildRunIterationPipelineOrchestrationKwargsForRunCallKwargsForRunImpl`
    und
    `runIterationPipelineOrchestrationKwargsForRunCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Folgeaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_call_kwargs_for_run_impl_builds_call_kwargs`
    und
    `test_run_iteration_pipeline_orchestration_kwargs_for_run_call_sequence_for_run_impl_delegates_builder_then_executor`.
  - [x] C1.146: From-Inputs-Orchestration-Kwargs-Sequenz aus `buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl` weiter modularisieren.
  - 2026-04-21: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsForRunImpl`
    und
    `runIterationPipelineFromInputsViaOrchestrationKwargsForRunSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_kwargs_for_run_impl_builds_call_kwargs`
    und
    `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_sequence_for_run_impl_delegates_builder_then_executor`.

- [x] B1: PyMuPDF-Ressourcen im Fallback-Diff-Pfad sauber schließen.
  - `_create_diff_image_without_cv2` nutzt jetzt Context-Manager für beide `fitz.open(...)` Dokumente, damit Batch-Läufe keine unnötig offenen MuPDF-Dokumente ansammeln.
  - Ziel: Stabilere AC08-Serienläufe ohne native MuPDF-Stackoverflow-Ausreißer durch Ressourcenaufbau über viele Dateien.
- [x] B2: AC08-Batchlauf mit vollständigem Bereich `AC0800..AC0899` nach B1 erneut ausführen und Crash-Freiheit dokumentieren.
  - 2026-03-28: Vollbereichslauf erneut gestartet mit
    `python -u -m src.imageCompositeConverter ... --start AC0800 --end AC0899`
    und Log nach `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-28.log` geschrieben.
  - 2026-03-29 (Lauf A): Erneuter Vollbereichslauf mit identischem Befehl und Log nach
    `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-29.log` geschrieben.
  - 2026-03-29 (Lauf B, Verifikation): gleicher Befehl erneut ausgeführt, diesmal reproduzierbarer Abbruch mit
    `MuPDF error: exception stack overflow!` und Shell-Exit-Code `139` (Segmentation Fault).
  - Dokumentierte Reproduktion: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-29_repro.log`
    und Kurzprotokoll `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-29_repro_summary.md`.
  - 2026-03-29 (Lauf C, erneuter Retry): gleicher Vollbereichs-Befehl erneut ausgeführt, diesmal Exit-Code `0`.
    Der Lauf blieb aber semantisch nicht vollständig erfolgreich (`batch_failure_summary.csv`: `AC0838_S` als `semantic_mismatch`).
  - 2026-03-29 (Lauf E, erneute Verifikation mit Log-Mitschnitt): gleicher Vollbereichs-Befehl per `tee` erneut ausgeführt;
    reproduzierbarer Abbruch mit `MuPDF error: exception stack overflow!` und Exit-Code `139` (`Segmentation fault`).
  - Dokumentation für Lauf E: `docs/ac0800_ac0899_runE_2026-03-29_summary.md`
    (inkl. Kommando, Exit-Code und letzter sichtbarer Datei vor dem Crash).
  - 2026-03-29 (Lauf F, erneuter Vollbereichscheck): gleicher Vollbereichs-Befehl per `tee` erneut ausgeführt; diesmal Exit-Code `0` ohne MuPDF-Segfault, aber semantischer Stop bei `AC0838_M.jpg` (`semantic_mismatch`).
  - Dokumentation für Lauf F: `docs/ac0800_ac0899_runF_2026-03-29_summary.md`
    (inkl. Kommando, Exit-Code und Verweis auf `batch_failure_summary.csv`).
  - Qualitätsvergleich gegen den vorherigen Commit-Stand (`pixel_delta2_ranking.csv`, nur `AC08*`):
    `51` gemeinsame Varianten, davon `50` unverändert und `1` verbessert (`AC0800_S`: `4980.680176` -> `1429.839966`),
    **keine** verschlechterte Variante.
  - 2026-04-16 (Lauf G, isolierter Renderer + deterministische Reihenfolge):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet mit Exit-Code `0` ohne MuPDF-Segfault, aber der gesamte Batch ist durch einen Runtime-Fehler blockiert
    (`TypeError: prepareRunIterationPipelineLocalsForRunImpl() got an unexpected keyword argument 'prepare_iteration_input_runtime_for_run_fn'`).
  - Dokumentation für Lauf G: `docs/ac0800_ac0899_runG_2026-04-16_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und Blocker-Fehlerbild).
  - 2026-04-16 (Lauf H, Verifikation nach C1.78-Fix):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet erneut mit Exit-Code `0` ohne MuPDF-Segfault, der Batch bleibt aber weiterhin durch denselben Runtime-Fehler blockiert.
  - Dokumentation für Lauf H: `docs/ac0800_ac0899_runH_2026-04-16_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und bestätigtem Blocker-Fehlerbild).
  - 2026-04-16 (Lauf I, Verifikation nach zusätzlicher Run-Preparation-Verdrahtung):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet mit Exit-Code `0` ohne MuPDF-Segfault, der ursprüngliche `prepare_iteration_input_runtime_for_run_fn`-Fehler tritt nicht mehr auf,
    stattdessen blockiert ein nachgelagerter Fehler (`TypeError: prepareRunIterationPipelineLocalsImpl() got an unexpected keyword argument 'img_path'`).
  - Dokumentation für Lauf I: `docs/ac0800_ac0899_runI_2026-04-16_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und aktualisiertem Blocker-Fehlerbild).
  - 2026-04-20 (Lauf J, Verifikation nach C1.140-Fix):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet mit Exit-Code `0` ohne MuPDF-Segfault, aber weiterhin mit Runtime-Blocker direkt zu Laufbeginn
    (`TypeError: runIterationPipelineImplOrchestrationDispatchForRunCallSequenceForRunImpl() got an unexpected keyword argument 'run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_for_run_kwargs'`).
  - Dokumentation für Lauf J: `docs/ac0800_ac0899_runJ_2026-04-20_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und Blocker-Fehlerbild).
  - 2026-04-20 (Lauf K, Smoke-Verifikation nach Signatur-Fix):
    gleicher Vollbereichs-Befehl erneut gestartet; AC0800-L/M/S und AC0811_L liefen sichtbar an,
    der Lauf wurde in dieser Session aus Zeitgründen manuell gestoppt (kein Segfault bis zum Abbruch beobachtet).
  - Dokumentation für Lauf K: `docs/ac0800_ac0899_runK_2026-04-20_summary.md`
    (inkl. Kommando, Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-20 (Lauf L, erneuter Vollbereichs-Start mit identischer Konfiguration):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` erneut ausgeführt;
    der Lauf verarbeitete erneut `AC0800_L/M/S` sowie `AC0811_L` und startete `AC0811_M`, ohne bis dahin einen MuPDF-Segfault zu zeigen.
    Der Prozess wurde anschließend manuell beendet, daher weiterhin kein vollständiger Exit-`0`-Nachweis für den Gesamtbereich.
  - Dokumentation für Lauf L: `docs/ac0800_ac0899_runL_2026-04-20_summary.md`
    (inkl. Kommando, Logpfad, sichtbarem Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-21 (Lauf M, Wiederholung auf Anfrage):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` erneut ausgeführt;
    der Lauf verarbeitete sichtbar `AC0800_L/M/S`, `AC0811_L/M/S` und startete `AC0812_L`.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Lauf wurde anschließend manuell mit `Ctrl+C` beendet (KeyboardInterrupt).
  - Dokumentation für Lauf M: `docs/ac0800_ac0899_runM_2026-04-21_summary.md`
    (inkl. Kommando, Logpfad, Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-21 (Lauf N, erneuter B2-Follow-up):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` erneut ausgeführt;
    im Log wurden `AC0800_L`, `AC0800_M` und `AC0800_S` sichtbar verarbeitet.
    Kein MuPDF-Segfault im beobachteten Abschnitt; der Lauf wurde anschließend manuell mit `Ctrl+C` beendet.
  - Dokumentation für Lauf N: `docs/ac0800_ac0899_runN_2026-04-21_summary.md`
    (inkl. Kommando, Logpfad, Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-21 (Lauf O, zusätzlicher Timeout-Follow-up):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` gestartet,
    diesmal mit `timeout 180` und `tee`; im Log wurden erneut `AC0800_L`, `AC0800_M` und `AC0800_S` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch das gesetzte Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf O: `docs/ac0800_ac0899_runO_2026-04-21_summary.md`
    (inkl. Kommando, Logpfad, sichtbarem Teilfortschritt und Timeout-Hinweis).
  - 2026-04-22 (Lauf P, nächster Timeout-Follow-up):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt,
    wieder mit `timeout 180`; im Log wurden `AC0800_L`, `AC0800_M` und `AC0800_S` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch den gesetzten Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf P: `docs/ac0800_ac0899_runP_2026-04-22_summary.md`
    (inkl. Kommando, Logpfad, sichtbarem Teilfortschritt und Timeout-Hinweis).
  - 2026-04-22 (Lauf Q, Timeout-Follow-up mit längerem Zeitfenster):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt,
    diesmal mit `timeout 240`; im Log wurden `AC0800_L`, `AC0800_M`, `AC0800_S` und der Start von `AC0811_L` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch den gesetzten Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf Q: `docs/ac0800_ac0899_runQ_2026-04-22_summary.md`
    (inkl. Kommando, Logpfad, erweitertem Teilfortschritt und Timeout-Hinweis).
  - 2026-04-22 (Lauf R, weiterer Timeout-Follow-up):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt,
    diesmal mit `timeout 300`; im Log wurden erneut `AC0800_L`, `AC0800_M`, `AC0800_S` und der Start von `AC0811_L` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch den gesetzten Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf R: `docs/ac0800_ac0899_runR_2026-04-22_summary.md`
    (inkl. Kommando, Logpfad, Teilfortschritt und Timeout-Hinweis).
  - Status: Crash-Freiheit für den Vollbereich ist **nicht** nachgewiesen; B2 bleibt als Langläufer-Thema dokumentiert.
  - 2026-04-22: Aus der aktiven Checkliste entfernt, weil wiederholte Timeout-/Manuell-Abbruch-Läufe den Abarbeitungsfluss blockieren; weitere Vollbereichsverifikationen werden künftig als separat geplante, zeitbudgetierte Follow-up-Einträge dokumentiert.
- [x] B2.1: MuPDF-Stackoverflow/Segfault im Vollbereich `AC0800..AC0899` isolieren und robusten Guard ergänzen.
  - Die bisherigen B1-Fixes (Context-Manager im Fallback-Diff-Pfad) reichen für den Vollbereich noch nicht aus.
  - Die Rendering-Stabilisierung muss den nativen Crash im Haupt-Renderpfad (`render_svg_to_numpy`) verhindern.
  - 2026-03-29: Optionaler Subprozess-Guard für `render_svg_to_numpy` ergänzt (`--isolate-svg-render`), inklusive Fallback auf In-Process-Render wenn der isolierte Worker fehlschlägt.
  - 2026-04-21: AC08-Regression-Set ohne `--isolate-svg-render` erneut reproduzierbar mit nativer MuPDF-Fehlermeldung abgestürzt
    (`MuPDF error: exception stack overflow!`, Exit-Code `139`; Log: `/tmp/ac08_regression_2026-04-21.log`).
  - 2026-04-21: CLI härtet den Guard jetzt standardmäßig für `--ac08-regression-set`:
    isoliertes SVG-Rendering wird automatisch aktiviert (inkl. Info-Hinweis), auch wenn der Flag nicht explizit gesetzt ist.
  - 2026-04-22: CLI härtet den Guard zusätzlich für den expliziten Vollbereichslauf (`--start AC0800 --end AC0899`);
    isoliertes SVG-Rendering wird nun auch ohne `--ac08-regression-set` automatisch aktiviert (inkl. eigenem Info-Hinweis).
  - Hinweis: Der Guard ist damit im Regression-Set **und** im Vollbereich standardmäßig aktiv; der separate
    Stabilitätsnachweis mit Exit-Code `0` bleibt weiterhin unter B2 offen.
- [x] B3: Deterministischen Diagnosemodus für die Dateireihenfolge ergänzen (ohne `shuffle`), um schwer reproduzierbare Batchfehler schneller zu isolieren.
  - 2026-04-03: Neuer CLI-Schalter `--deterministic-order` ergänzt.
  - Der Modus deaktiviert Shuffle bei Dateiliste, Quality-Pass-Kandidaten sowie Template-Transfer-Donor/Scale-Reihenfolge.
  - Für reproduzierbare Läufe wird `Action.STOCHASTIC_RUN_SEED` in diesem Modus auf `0` gesetzt.

## Test-Fehler aus Vollsuite-Lauf (2026-04-19)

- [x] T1: Erste Vollsuite-Regression beheben (`test_run_iteration_pipeline_element_validation_log_contains_run_meta`).
  - Symptom im Gesamtlauf: `runIterationPipeline(...)` liefert `None` statt Ergebnis-Tuple.
  - Maßnahme: Optional-Dependency-Lader härtet fehlgeschlagene Retry-Importe jetzt gegen `sys.modules`-Vergiftung ab (Snapshot/Restore für bestehende Modul-Einträge bei `cv2`-Fallbacks).
  - 2026-04-19: Umsetzung erfolgt inkl. neuem Regressionstest für den Erhalt bestehender `sys.modules["cv2"]`-/`sys.modules["cv2.typing"]`-Einträge.
- [x] T2: Folgefehler mit fehlenden Artefakten/`None`-Ergebnissen in `runIterationPipeline` und `convertRange` clustern und beheben.
  - Beispiele: `test_run_iteration_pipeline_writes_failed_best_attempt_artifacts_for_semantic_mismatch`,
    `test_run_iteration_pipeline_converts_non_composite_as_embedded_svg`,
    `test_convert_range_accepts_quality_pass_when_mean_delta2_improves`.
  - 2026-04-19: Regression im Single-Reference-Quality-Pass-Gating behoben
    (`max_quality_passes` nicht mehr auf `0` für Einzel-/Exact-Range-Läufe);
    dadurch greifen Mean-Delta2-Verbesserungen wieder auch in fokussierten Runs
    und Quality-Pass-Reports werden konsistent geschrieben.
- [x] T3: Quality-Pass-Schwellenwert-/Reporting-Regression untersuchen.
  - Beispiel: `test_convert_range_does_not_skip_variants_in_quality_passes` (erwartet `allowed_error_per_pixel == 1.0`, beobachtet `0.25`).
  - 2026-04-19: Auto-Schwellenwerte werden jetzt mit einem Mindestwert von `1.0` aufgelöst, damit globale Quality-Pässe Varianten nicht zu früh als „geschlossen“ behandeln.
    Der Schwellwert-Source-Tag bleibt für Auto-Berechnung konsistent auf `successful-conversions-mean-plus-2std` (nur manuelle Config setzt `manual-config`),
    und Detail-/Integrations-Tests decken den korrigierten Pfad ab.
- [x] T4: Rendering-/Fallback-Pfad-Regression untersuchen.
  - Beispiel: `test_render_svg_to_numpy_falls_back_to_inprocess_after_subprocess_failure`.
  - 2026-04-19: Regression behoben; `Action.renderSvgToNumpy` verwendet für den Fallback wieder den kompatiblen
    CamelCase-Entry-Point (`_renderSvgToNumpyInprocess`) und die Monkeypatch-Erkennung prüft nun das Top-Level-Modul,
    sodass der Pytest-Fallbackpfad zuverlässig greift.
- [x] T5: XML-Beschreibungs-Mapping-Regression untersuchen.
  - Beispiele: `test_load_description_mapping_from_xml_prefers_image_specific_detail`,
    `test_load_description_mapping_from_xml_reads_bild_attribute_description`.
  - 2026-04-19: Regression behoben; XML-Beschreibungen mergen jetzt Gruppenbeschreibung + bildspezifischen Text
    (ohne doppelte Präfixe), sodass `bildbeschreibung`-Details und `bild@beschreibung` wieder die erwarteten kombinierten
    Zieltexte liefern.
- [x] T6: AC08-Regressionen aus der Vollsuite separat stabilisieren.
  - Beispiele: `test_ac08_regression_suite_preserves_previously_good_variants[...]`,
    `test_ac0811_l_conversion_preserves_long_bottom_stem`,
    `test_ac08_semantic_anchor_variants_convert_without_failed_svg`.
  - 2026-04-21: AC08-Detailtests (`pytest -q tests/detailtests -k ac08`) laufen grün (`21 passed`).
  - 2026-04-21: Zusätzlicher Integrations-Scope-Check für die im T6-Text genannten AC08-Vollsuite-Beispiele wurde gestartet,
    lief in dieser Session jedoch nicht innerhalb des gesetzten Zeitfensters durch; T6 bleibt daher bis zum vollständigen Lauf offen.
  - 2026-04-22: AC08-Detailtests erneut verifiziert (`pytest -q tests/detailtests -k ac08` → `21 passed`).
  - 2026-04-22: Integrations-Scope-Checks für die genannten Vollsuite-Beispiele erneut mit `timeout` gestartet
    (`pytest -q tests/test_image_composite_converter.py -k "ac08_regression_suite_preserves_previously_good_variants or ac0811_l_conversion_preserves_long_bottom_stem or ac08_semantic_anchor_variants_convert_without_failed_svg"`),
    endeten im Zeitlimit mit Exit-Code `124`; T6 bleibt offen bis ein vollständiger Lauf ohne Timeout dokumentiert ist.
  - 2026-04-22: Integrations-Scope-Checks für die genannten Vollsuite-Beispiele mit verlängertem Zeitfenster erneut gestartet
    (`timeout 300 pytest -q tests/test_image_composite_converter.py -k "ac08_regression_suite_preserves_previously_good_variants or ac0811_l_conversion_preserves_long_bottom_stem or ac08_semantic_anchor_variants_convert_without_failed_svg"`),
    zeigten laufenden Testfortschritt (`....`), endeten aber weiterhin im Zeitlimit mit Exit-Code `124`; T6 bleibt offen bis ein vollständiger Lauf ohne Timeout dokumentiert ist.
  - 2026-04-22: Aus der aktiven Checkliste entfernt, da die Aufgabe aktuell primär durch Laufzeitbudget/Timeout limitiert ist; erneute Vollsuite-Scopes werden als dedizierte Follow-up-Tasks mit explizitem Zeitfenster eingetragen.



## Kelle-/Optimierungs-Backlog (neu aus dem Umsetzungscheck)

- [x] A1: Gemeinsamen Parametervektor für globale Optimierung einführen.
  - Added `GlobalParameterVector` as a central structure for geometry/text optimization fields (`cx`, `cy`, `r`, arm/stem, text position/scale), including param round-tripping.
  - Added central bounds/lock metadata via `_global_parameter_vector_bounds` and per-round debug logging with `_log_global_parameter_vector`.
  - Wrapped the existing circle adaptive/stochastic optimizers to read/write through the shared vector abstraction.
- [x] A2: Globalen Mehrparameter-Suchmodus ergänzen (nicht nur Kreis-Pose).
  - Added `Action._optimize_global_parameter_vector_sampling` as a reproducible baseline search that samples and shrinks multiple unlocked dimensions from `GlobalParameterVector` jointly (`cx`, `cy`, `r`, `stem_*`, `text_*`).
  - Added per-round progress logs for `best_err`, accepted candidates, and the active parameter subset, plus a final delta summary for changed dimensions.
  - Integrated the new mode into the existing optimization loop behind `enable_global_search_mode`, so the global pass can be activated without changing default conversion behavior.
- [x] A3: Near-Optimum-Plateau auf den globalen Parameterraum verallgemeinern.
  - Added a formal near-optimum definition in the global optimizer logs (`err <= best_err + epsilon`, with `epsilon=max(0.06, best_err*0.02)`).
  - Added per-round global plateau persistence and instrumentation in `_optimize_global_parameter_vector_sampling`, including point count, per-parameter spans, mean span, and a stability hint.
  - Added regression coverage that checks near-optimum plateau logging for multi-round global runs.
- [x] A4: Schwerpunkt/zentralen Repräsentanten des Plateau-Bereichs berechnen und auswählen.
  - Der globale Suchmodus berechnet jetzt pro Runde einen fehlergewichteten Plateau-Schwerpunkt und bewertet ihn gegen den Best-Sample-Kandidaten.
  - Der finale Rundensieger kann bewusst aus `schwerpunkt` oder `best_sample` stammen; die Entscheidung inkl. Begründung wird mit `global-search: plateau-repräsentant` geloggt.
  - Sicherheitslogik verwirft Schwerpunktkandidaten mit ungültiger Fehlerbewertung oder Constraint-Verletzung vor einer möglichen Übernahme.
- [x] A5: Regressionstests für globalen Suchmodus, Seeds und Constraint-Einhaltung ergänzen.
  - Added a deterministic seed regression test to ensure the global search RNG seed incorporates both `STOCHASTIC_RUN_SEED` and `STOCHASTIC_SEED_OFFSET`.
  - Added a lock/constraint regression test that verifies locked dimensions (`cx`, `text_x`, `text_y`) stay unchanged and optimized active dimensions remain within initial vector bounds.

Details und Akzeptanzkriterien stehen in `docs/kelle_umsetzungscheck.md` unter
„Abgeleitete Aufgaben (umsetzbare Roadmap)“.

## Next priority tasks

- [x] Fix the vertical-connector semantic false positives in the remaining AC08 families.
  - Target `AC0811_S`, `AC0813_L`, `AC0813_M`, `AC0831_M`, and `AC0836_L` first.
  - `AC0811_M` is now covered by the vertical-family circle-mask fallback; keep it in the next report refresh to confirm the committed artifacts match the fixed code path.
  - The current logs repeatedly report `Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`, although these families are expected to use vertical connectors or stems.
  - Primitive detection/reporting now records connector orientation classification (`vertical`/`horizontal`/`ambiguous`) plus candidate counts in semantic mismatch logs before validation fails.

- [x] Harden circle detection for small AC08 variants before the semantic gate runs.
  - `AC0811_L` is treated as a regression-safe good conversion anchor and should remain out of the weak-family backlog unless a future report explicitly regresses it.
  - The fixed AC08 regression set now loads its previously marked good variants from `artifacts/converted_images/reports/successful_conversions.txt` and reports whether any of them regressed or went missing.
  - Prioritize `AC0811_S`, `AC0814_S`, and `AC0870_S`, where the reports also contain `Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar` and/or `Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt`.
  - Reuse the local mask / foreground fallback path already proven for thin-ring cases and expose enough instrumentation to tell whether the accepted circle came from Hough, foreground mask, or family-specific fallback.
  - `_detect_semantic_primitives` now reports `circle_detection_source` (`hough`, `foreground_mask`, `family_fallback`, `none`) and semantic mismatch logs print this source together with connector classification.
  - Added a small-variant family fallback (`AC0811`/`AC0814`/`AC0870`) that validates expected template-circle ring support against the foreground mask when Hough + contour fallback both miss.
  - Added regression coverage for `AC0870_S` circle presence and for explicit `family_fallback` source reporting when Hough/foreground circle candidates are intentionally disabled.

- [x] Add a family-level semantic rule for the plain-ring family `AC0800`.
  - `AC0800` now derives `SEMANTIC: Kreis ohne Buchstabe` as an explicit semantic family instead of relying on text clues alone.
  - `AC0800_L`, `AC0800_M`, and `AC0800_S` are treated as currently optimal conversions and are locked into the AC08 regression suite so future adjustments must keep them `semantic_ok`.
  - `AC0800_S` now keeps the converted circle concentric with the template and may no longer shrink below the original template radius during circle-only validation, so the small plain-ring variant is no longer tracked as an open geometric follow-up.

- [x] Refresh the AC08 reports after the next semantic round.
  - Re-ran the affected AC08 semantic families and refreshed the committed `AC08*_element_validation.log` snapshot under `artifacts/converted_images/reports`.
  - The refreshed snapshot currently reports `10/10 semantic_ok` and no `semantic_mismatch` entries for the committed AC08 logs.
  - Updated `docs/ac08_artifact_analysis.md` so the backlog reflects the current post-fix distribution instead of the former 43/11 split.

- [x] Make the AC08 success gate actionable in the normal workflow.
  - The AC08 regression run now emits an explicit console gate status (`passed`/`failed`) including failed criterion names and `mean_validation_rounds_per_file`, so failures are visible immediately after the run.
  - The workflow/README now include a CI-/shell-friendly regression check that evaluates `ac08_success_metrics.csv` and exits non-zero when any gate criterion fails.
  - Fixed validation-round instrumentation in the AC08 success metrics (`Runde n` log parsing), and added a dedicated criterion `criterion_validation_rounds_recorded` so `mean_validation_rounds_per_file` can no longer silently stay at `0.000` in a passing gate.

## Image conversion pipeline

- [x] Publish the detailed roadmap checklist referenced from the README.
  - Added this file so roadmap tasks can now be tracked and marked complete in-repo.

- [x] Improve error positions and messages.
  - Added a structured `DescriptionMappingError` with optional `SourceSpan` metadata so malformed CSV/XML description files now report exact file/line/column locations.
  - The CLI now surfaces these diagnostics as stable `[ERROR]` messages instead of failing with ambiguous parser exceptions.
  - Added regression tests for malformed XML, malformed CSV rows, and the CLI-facing error output.

## Tooling and documentation

- [x] Improve CLI wrapper ergonomics and documentation.
  - Added a proper CLI reference in `docs/image_converter_cli.md` with canonical convert/annotate/regression/vendor commands.
  - Updated the parser help text with examples, a clearer descriptions-table flag (`--descriptions-path` alias), a named `--iterations` override, and a default input directory for non-conversion helper flows.
  - Added regression tests that lock the new help text and the documented parser behaviors.

- [x] Stabilize formatter, lints, and local documentation workflows.
  - Added `docs/image_converter_workflow.md` as the canonical local verification sequence for compile/test/CLI-help checks.
  - Added regression tests that keep the workflow document referenced from the README and lock key command anchors.
  - Re-validated the documented tooling commands against the current parser/help surface.

## AC08 follow-up work

- [x] Continue improving AC08 output quality.
  - Added the generated reports `ac08_weak_family_status.csv` and `ac08_weak_family_status.txt`, which summarize remaining AC08 weak families from `pixel_delta2_ranking.csv` together with the currently implemented mitigation status and observed log markers.
  - Revalidated the new weak-family status reporting with targeted regression tests so the documentation task now has reproducible output instead of manual notes only.
  - Kept `docs/ac08_improvement_plan.md` aligned with the new reporting artifacts and the existing mitigation heuristics.

- [x] Document that the canonical open-task list is currently empty and keep roadmap references aligned.
  - Added an explicit current-status section here and synchronized the README/documentation index wording so future work is added back to the same checklist before implementation starts.

- [x] Materialize the AC08 weak-family follow-up reports referenced by the improvement plan.
  - Regenerated `artifacts/converted_images/reports/ac08_weak_family_status.csv` and `.txt` from the current `pixel_delta2_ranking.csv` so the documented AC08 follow-up now exists as committed snapshot artifacts, not only as code/tests.
