# Nächstes Arbeitspaket – FP-D7 Run NR (2026-06-04)

## Ziel

FP-D7 bearbeitet den in FP-D5 priorisierten Engpass #2: kumulative
`global-search`-Kosten. Das Paket bleibt bewusst eng: eine Gegenmaßnahme im
Global-Search-Helfer, ein deterministischer Detailtest und ein kleiner
AC08-Smoke als Praxisnachweis.

## Gegenmaßnahme

Der Global-Search-Helfer merkt sich jetzt eine kompakte
`no-improvement`-Signatur im Parameter-Dictionary. Wenn ein vorheriger
Global-Search-Lauf für dieselben aktiven Parameter, Werte und Bounds keine
relevante Verbesserung geliefert hat, wird ein direkt folgender identischer Lauf
übersprungen.

Begründung: Der dokumentierte Engpass ist nicht ein einzelner Hänger, sondern
die Summe vieler globaler Suchrunden. Wiederholte Läufe auf unveränderter
Parameterbasis erzeugen dabei Renderkosten, obwohl der vorherige Lauf bereits
`keine relevante Verbesserung` protokolliert hat. Sobald eine andere Phase die
Parameter ändert oder Global Search selbst eine Verbesserung übernimmt, greift
die Signatur nicht mehr bzw. wird zurückgesetzt.

## Sicherung und Messsignal

| Check | Befehl | Exit | Ergebnis |
| --- | --- | ---: | --- |
| Detailtest | `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py` | `0` | `22 passed in 0.57s`; neuer Test belegt `render_calls` bleiben beim zweiten identischen No-Improvement-Lauf unverändert. |
| Kernsuite | `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs` | `0` | `695 passed in 27.20s`. |
| AC08-Smoke | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd7-after/ac0814 --start AC0814 --end AC0814 --deterministic-order` | `0` | `AC0814_L/M/S` wurden verarbeitet; `AC0814_L` und `AC0814_S` protokollieren direkte `unveränderte_no-improvement_signatur`-Skips mit `global_search_elapsed ... 0.00s`. |

## Beobachtetes Praxisverhalten im AC0814-Smoke

- `AC0814_L`: erster Global-Search-Lauf mit `keine relevante Verbesserung`,
  danach zwei identische Folgeaufrufe mit `global-search: übersprungen
  (grund=unveränderte_no-improvement_signatur, ...)` und jeweils
  `global_search_elapsed ... 0.00s`.
- `AC0814_S`: nach zwei No-Improvement-Läufen werden Runde 3 und 4 analog
  übersprungen und als `0.00s` protokolliert.
- `AC0814_M`: Verbesserungen werden weiterhin übernommen; dadurch wird die
  Signatur zurückgesetzt und Global Search bleibt für tatsächlich wirksame
  Folgeoptimierung aktiv.

## Ergebnis

- FP-D7-1 ist umgesetzt: die Gegenmaßnahme reduziert wiederholte identische
  No-Improvement-Global-Search-Kosten ohne Global Search generell abzuschalten.
- FP-D7-2 ist erfüllt: die Kernsuite bleibt grün (`695 passed`).
- FP-D7-EXIT ist erfüllt: Engpass #2 ist messbar verbessert bzw. im Smoke
  sichtbar eingegrenzt, weil identische No-Improvement-Folgeaufrufe keine neuen
  Renderbewertungen mehr auslösen.

## 5-Zeilen-Log

- **Getestet:** Global-Search-Detailtest, vollständige Pytest-Kernsuite und
  AC0814-Smoke mit Timeout-Guard.
- **Ergebnis:** Detailtest und Kernsuite grün; AC0814-Smoke zeigt echte
  No-Improvement-Skips mit `0.00s` Global-Search-Zeit.
- **Blocker:** Kein FP-D7-Blocker; vollständige Vorher/Nachher-Wallclock bleibt
  wegen systemabhängiger Start-/Renderkosten nur ergänzend aussagekräftig.
- **Nächster Schritt:** FP-D8 startet die erste Semantik-Fokusfamilie und ergänzt
  pro Familie gezielten Regressionsschutz.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
