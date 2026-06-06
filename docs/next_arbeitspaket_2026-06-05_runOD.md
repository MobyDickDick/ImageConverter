# Nächstes Arbeitspaket – isoliertes Refinement Run OD (2026-06-05)

## Ziel

Run OD schließt den in Run OC dokumentierten Restblocker: Ein-Datei-Segmente
müssen genau einen expliziten Refinement-Versuch ausführen können, auch wenn
das initiale Ergebnis bereits unter dem offenen Fehlergrenzwert liegt und der
Terzil-Fallback wegen der Batchgröße nicht greift. Eine neue Ausgabe darf den
initialen Zustand weiterhin nur bei einer echten Verbesserung ersetzen.

## Implementierung

`runQualityPassesImpl` verwendet die bestehenden Selektoren unverändert und
fügt erst dann einen isolierten Fallback hinzu, wenn beide keine Kandidaten
liefern. Der Fallback ist absichtlich eng:

- genau ein endlicher Ergebnisdatensatz im Segment,
- die Variante ist nicht in `skip_variants` enthalten,
- keine Änderung des offenen Qualitätsgrenzwerts,
- keine Änderung der bestehenden Accept/Reject-Bewertung.

Mehrdatei-Batches behalten damit ihre bisherige Open-Case-/Terzil-Politik. Der
Ein-Datei-Fallback führt höchstens den bereits von der Fokus-Policy erlaubten
einen Refinement-Pass aus. Die dokumentierte AC0811-Sonderregel bleibt
initial-pass-only und wird nicht umgangen.

## Automatisierter Nachweis

Die Helper-Regression erzwingt leere Open-Case- und Terzil-Selektionen und
belegt trotzdem den Refinement-Aufruf für einen einzelnen Datensatz unterhalb
des Grenzwerts. Ein zusätzlicher Test belegt, dass eine explizit übersprungene
Variante nicht durch den Fallback reaktiviert wird.

Die beiden bestehenden Ein-Datei-Integrationstests verwenden ebenfalls leere
Selektoren. Sie belegen damit jetzt direkt:

1. Eine echte `mean_delta2`-Verbesserung wird als `accepted_improvement`
   protokolliert und übernommen.
2. Eine Verschlechterung wird als `rejected_regression` protokolliert; das
   vorherige SVG bleibt erhalten.

Gezielter Testlauf:

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
python -m pytest -q \
  tests/detailtests/test_conversion_quality_pass_helpers.py \
  tests/detailtests/test_quality_pass_policy_helpers.py \
  tests/test_image_composite_converter.py \
  -k 'quality_pass or success_metrics' \
  tests/detailtests/test_local_completion_checks_tool.py
```

Ergebnis: `16 passed, 376 deselected`.

## Vollständiger Abnahmelauf

```bash
RC_GATE_NAME=fp-recovery-run-od \
RC_GATE_WORK_PACKAGE=FP-RECOVERY-ISOLATED-REFINEMENT \
RC_GATE_OUTPUT_DIR=/tmp/ic-runod-output \
RC_GATE_AC08_SEGMENTS_DIR=/tmp/ic-runod-segments \
RC_GATE_EVIDENCE_DIR=/tmp/ic-runod-evidence \
RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS=600 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
./tools/run_release_candidate_gate.sh
```

| Schritt | Ergebnis | Befund |
| --- | --- | --- |
| Kernsuite | `PASS` | `716 passed in 50.76s` |
| AC08-Smoke | `PASS` | 14/14 Segmente und 14/14 Iteration-Datensätze |
| Qualitätsgate | `PASS` | 3 akzeptierte Verbesserungen, 4 verworfene Regressionen |
| Gesamtgate | `PASS` | `overall_success=1` |

## Harte FP-D14-Schwellen

| Kriterium | Mindestwert | Run OD | Urteil |
| --- | ---: | ---: | --- |
| Varianten mit Iteration-Datensatz | `14/14` | `14/14` | erfüllt |
| Erhaltene Previously-Good-Anker | `6/6` | `6/6` | erfüllt |
| Gemessene Qualitätsverbesserungen | `>= 1` bei `0` akzeptierten Regressionen | `3` bei `0` akzeptierten Regressionen | erfüllt |

Der zusammengeführte Quality-Pass-Report enthält sieben ausgewertete
Refinement-Versuche: drei `accepted_improvement` und vier
`rejected_regression`. Verbessert wurden `AC0831_L`, `AC0834_S` und
`AC0835_S`. Keine Verschlechterung wurde übernommen. Zusätzlich blieben
semantische Mismatches sowie Batch-/Render-Abbrüche bei `0`.

## Abschluss

Das in Run OC definierte Folgepaket ist vollständig erfüllt. Die
segmentierungsfeste Verbesserungsmessung ist implementiert, beide
Accept/Reject-Pfade sind getestet, der feste 14er-Satz ist vollständig, alle
Previously-Good-Anker bleiben erhalten und das Release-Gate endet grün.

## 5-Zeilen-Log

- **Getestet:** Helper-/Integrationstests sowie vollständiges Release-Gate mit 716 Kernsuite-Tests und 14 isolierten AC08-Varianten.
- **Ergebnis:** 14/14 Reports, 6/6 Anker, 3 echte Verbesserungen, 0 akzeptierte Regressionen, `overall_success=1`.
- **Blocker:** Kein verbleibender FP-D14-Blocker.
- **Nächster Schritt:** Reguläre Roadmap-/Plan-B-Rotation fortsetzen; das Finish-Playbook nicht weiter verlängern.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q -rs`.
