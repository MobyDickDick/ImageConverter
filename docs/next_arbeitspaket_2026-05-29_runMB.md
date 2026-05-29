# Nächstes Arbeitspaket – Run MB (2026-05-29)

Dieses Arbeitspaket schließt den nach Run MA verbliebenen AC0011-Anschluss ab:
Der echte Call-Path muss trotz `Wie AC0010`-Referenzbeschreibung die vorhandene
`AC0011.svg`-Sample-Datei als valides Endergebnis nutzen.

## 1) Nächste dokumentierte Aufgabe: AC0011-Sample-Priorität im echten Call-Path

- Problem:
  - Der AC0011-Einzelrun erzeugte nach Run MA zwar ein reguläres SVG, schrieb im
    Validation-Log aber noch `status=non_composite_elementwise_symbol_fit` ohne
    aktive Sample-Nutzung.
  - Bei erzwungener Sample-Auswahl wurde zunächst die Referenz aus der
    Beschreibung (`AC0010.svg`) vorgezogen, obwohl `samples/AC0011.svg`
    vorhanden ist.
- Umsetzung:
  - `AC0011` ist nun als forcierte Plan-B-Sample-Variante registriert.
  - Forcierte Varianten behalten ihre exakte Sample-Kandidatenreihenfolge; eine
    Referenzbeschreibung wie `Wie AC0010` darf die vorhandene `AC0011.svg` nicht
    mehr vor `AC0011` einsortieren.
  - Nicht forcierte Varianten behalten das bisherige Referenz-/Fallback-Verhalten.

## 2) Sichernde Detailtests

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py`
- Ergebnis:
  - Exit `0`
  - `21 passed in 0.31s`
- Abdeckung:
  - AC0011 erzwingt die Sample-SVG-Auswahl auch dann, wenn der Render-Fehler des
    Samples schlechter als der generierte Baseline-Fehler ist.
  - AC0011 verwendet bei `Wie AC0010` trotzdem exakt `AC0011.svg` statt der
    Referenz-Sample-Datei `AC0010.svg`.
  - Nicht forcierte Varianten behalten das bisherige Render-Failure-Verhalten.

## 3) AC0011-Repro 2x hintereinander

- Befehl je Lauf:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0011-mb-<n> --start AC0011 --end AC0011 --deterministic-order`
- Ergebnis Lauf 1:
  - Exit `0`
  - `/tmp/ic-ac0011-mb-1/converted_svgs/AC0011.svg` vorhanden.
  - Kein `Failed_AC0011.svg`.
  - Kein `AC0011.jpg;raster_embedded_svg` im Failure-Summary.
  - Validation-Log: `status=non_composite_plan_b_sample_svg_selected`,
    `sample_svg_path=/workspace/ImageConverter/artifacts/images_to_convert/samples/AC0011.svg`,
    `force_sample_svg=1`.
- Ergebnis Lauf 2:
  - Exit `0`
  - `/tmp/ic-ac0011-mb-2/converted_svgs/AC0011.svg` vorhanden.
  - Kein `Failed_AC0011.svg`.
  - Kein `AC0011.jpg;raster_embedded_svg` im Failure-Summary.
  - Validation-Log erneut mit derselben aktiven Sample-Nutzung für `AC0011.svg`.

## 4) Repo-Output-Akzeptanzprobe

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0011 --end AC0011 --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `artifacts/converted_images/converted_svgs/AC0011.svg` wurde erzeugt.
  - Kein `Failed_AC0011.svg`.
  - Kein `AC0011.jpg;raster_embedded_svg` im Failure-Summary.
  - `artifacts/converted_images/reports/AC0011_element_validation.log` zeigte
    `sample_svg_path=/workspace/ImageConverter/artifacts/images_to_convert/samples/AC0011.svg`.
- Hinweis:
  - Die generierten Repo-Output-Artefakte wurden nach der Probe nicht als
    Quelländerung übernommen; der Codepfad ist durch Detailtests und Reproläufe
    abgesichert.

## 5) Erweiterter Detailtest-Block

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_conversion_finalization_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py tests/test_non_composite_sample_candidates.py`
- Ergebnis:
  - Exit `0`
  - `41 passed in 0.35s`

## 6) Volltest

- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`
- Ergebnis:
  - Exit `0`
  - `568 passed, 5 warnings in 6.02s`

## Fazit

Die AC0011-JIRA-Kurzfassung ist im echten Call-Path erfüllt: Der Einzelrun endet
stabil als reguläres `AC0011.svg`, enthält keinen Raster-Failure-Eintrag und
protokolliert aktive Nutzung von `samples/AC0011.svg` in zwei direkten Repros.
