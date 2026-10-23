# Nächstes Arbeitspaket – FP-D6 Run NQ (2026-06-04)

## Ziel

FP-D6 bearbeitet den in FP-D5 priorisierten Engpass #1: den fokussierten
`AC0811`-Batch. Das Paket bleibt bewusst eng: genau eine Gegenmaßnahme,
danach ein Vorher/Nachher-Repro mit identischem Batch-Schnitt.

## Gegenmaßnahme

Fokussierte Single-Base-Batches behalten weiterhin die schnelle
Qualitätspass-Politik, aber `AC0811` ist jetzt eine explizite Ausnahme:
`AC0811`-only-Repros laufen initial-pass-only, sofern `ICC_MAX_QUALITY_PASSES`
nicht bewusst gesetzt wird.

Begründung: Im identischen AC0811-Repro re-queue-te die generische
Middle-/Lower-Tercile-Qualitätspass-Auswahl vor der Änderung vor allem `M`/`S`
noch einmal, ohne einen besseren Bestlist-Eintrag zu akzeptieren. Für den
dokumentierten Engpass ist dieser blanket retry damit Laufzeitrauschen statt
wirksamer Qualitätsarbeit.

## Vorher/Nachher-Repro

| Lauf | Befehl | Exit | Laufzeit | Verarbeitete Dateien | Log |
| --- | --- | ---: | ---: | ---: | --- |
| Vorher | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd6-before/ac0811-clean --start AC0811 --end AC0811 --deterministic-order` | 0 | 3.70s | 5 | `artifacts/converted_images/reports/FP_D6_AC0811_before_2026-06-04_runNQ.log` |
| Nachher | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd6-after/ac0811 --start AC0811 --end AC0811 --deterministic-order` | 0 | 3.16s | 3 | `artifacts/converted_images/reports/FP_D6_AC0811_after_2026-06-04_runNQ.log` |

## Qualitätsvergleich

| Variante | Vorher error_per_pixel | Vorher mean_delta2 | Nachher error_per_pixel | Nachher mean_delta2 |
| --- | ---: | ---: | ---: | ---: |
| AC0811_L | 0.00615822 | 1013.082642 | 0.00465383 | 670.709351 |
| AC0811_M | 0.01227347 | 1690.979980 | 0.01205714 | 1184.785767 |
| AC0811_S | 0.02479644 | 1066.456055 | 0.02479644 | 1066.456055 |

## Ergebnis

- Laufzeit im gemessenen fokussierten Batch: `3.70s -> 3.16s` (`-0.54s`, ca.
  `-14.6%`).
- Wiederholte Qualitätsretries im AC0811-only-Batch: `5 -> 3`
  Verarbeitungseinträge.
- Keine sichtbare Qualitätsregression in der Bestlist; `L` und `M` verbessern
  sich im Nachher-Lauf, `S` bleibt identisch.

## 5-Zeilen-Log

- **Getestet:** AC0811 Vorher/Nachher-Batch mit identischem Range-Schnitt und
  Timeout-Guard; zusätzlich gezielter Unit-Test für die neue Qualitätspass-Policy.
- **Ergebnis:** Gegenmaßnahme messbar wirksam (`3.70s -> 3.16s`) und Exit `0`.
- **Blocker:** Kein FP-D6-Blocker; die historische globale
  `threshold_mean_delta2=18.000` bleibt für AC0811 erwartungsgemäß nicht das
  Abnahmekriterium.
- **Nächster Schritt:** FP-D7 mit Engpass #2 (`global-search`-Kosten) separat
  bearbeiten.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
