# Abschlussentscheidung – FP-D14 Run OA (2026-06-05)

## Entscheidung

**Noch offen – keine Release-Freigabe.**

FP-D14 schließt das 14-Tage-Finish-Playbook als Entscheidungs- und
Dokumentationspaket ab. Die Entscheidung selbst bleibt rot: Der technisch
vollständig gestartete FP-D13-Lauf hat keine vollständige fachliche
Artefaktkette und keine messbare Verbesserung gegenüber der Baseline belegt.
Ein grüner Prozess-Exit wird deshalb nicht mit fachlichem Erfolg gleichgesetzt.

## Drei harte Entscheidungskennzahlen

| Kriterium | Mindestwert für „durch“ | FP-D13-Istwert | Urteil |
| --- | ---: | ---: | --- |
| Varianten mit Iteration-Datensatz | `14/14` | `10/14` | nicht erfüllt |
| Erhaltene Previously-Good-Anker | `6/6` | `3/6` | nicht erfüllt |
| Gemessene Qualitätsverbesserungen | `>= 1` bei `0` akzeptierten Regressionen | `0` | nicht erfüllt |

Zusätzlich steht `overall_success=0`. Bereits jedes einzelne nicht erfüllte
Kriterium verhindert „durch“; hier sind alle drei Kriterien rot. Die fehlenden
Iteration-Datensätze betreffen `AC0811_L`, `AC0811_M`, `AC0811_S` und
`AC0831_L`.

## Stabil

- Die Kernsuite lief nach den FP-D13-Korrekturen mit `710 passed`.
- Alle 14 isolierten AC08-Segmentprozesse endeten mit Exit `0`; die frühere
  globale Timeout-Kopplung ist damit technisch aufgelöst.
- Unter den vorhandenen Reportdaten wurden `0` akzeptierte Regressionen und
  `0` semantische Mismatches ausgewiesen.
- Die Finalisierung behandelt einen leeren optionalen Quality-Pass-Report
  transparent und erfindet daraus keine Verbesserung.

## Verbessert

Eine Baselineverbesserung ist **nicht belegt**. Sowohl für
`error_per_pixel` als auch für `mean_delta2` beträgt die Zahl gemessener
Verbesserungen `0`. Die stabilere Segmentausführung und die härtere
Artefaktprüfung verbessern zwar das Gate-Verfahren, erfüllen aber nicht das
fachliche Qualitätsziel und werden daher nicht als Bildqualitätsgewinn
gezählt.

## Offen

1. Für die vier Exit-0-Varianten ohne `Iteration_Log.csv`-Datensatz muss die
   Ursache geklärt und behoben werden.
2. Ein Segment darf erst dann als fachlich vollständig gelten, wenn neben dem
   Prozess-Exit auch der erwartete Varianten-Datensatz vorhanden ist.
3. Der feste 14er-Satz muss danach erneut laufen und alle 6 Previously-Good-
   Anker erhalten.
4. Der Wiederholungslauf muss mindestens eine echte Qualitätsverbesserung,
   keine akzeptierte Regression und `overall_success=1` nachweisen.

## Nachvollziehbarkeit und Wiederaufnahme

Der zugrunde liegende Lauf, die Einzelwerte und die verwendeten Befehle sind
in `docs/next_arbeitspaket_2026-06-05_runNZ.md` dokumentiert. Der relevante
Gate-Lauf ist reproduzierbar mit:

```bash
RC_GATE_NAME=fp-d13-run-nz \
RC_GATE_WORK_PACKAGE=FP-D13 \
RC_GATE_OUTPUT_DIR=/tmp/ic-fpd13-ac08 \
RC_GATE_AC08_SEGMENTS_DIR=/tmp/ic-fpd13-ac08-segments \
RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS=600 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
./tools/run_release_candidate_gate.sh
```

Die Entscheidung darf auf **„durch“** geändert werden, wenn ein solcher
Wiederholungslauf gleichzeitig `14/14` Iteration-Datensätze, `6/6` erhaltene
Previously-Good-Anker, mindestens eine gemessene Verbesserung, `0` akzeptierte
Regressionen und `overall_success=1` liefert. Bis dahin bleibt der Release
explizit blockiert.

## 5-Zeilen-Log

- **Getestet:** FP-D13-Evidenz gegen die drei FP-D14-Entscheidungsschwellen geprüft.
- **Ergebnis:** Alle drei Schwellen sind nicht erfüllt; Entscheidung „noch offen“.
- **Blocker:** 4 fehlende Variantendatensätze, 3 fehlende Previously-Good-Anker, 0 Verbesserungen.
- **Nächster Schritt:** Reportvollständigkeit reparieren und den festen 14er-Satz wiederholen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_local_completion_checks_tool.py`.
