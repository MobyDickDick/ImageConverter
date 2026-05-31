# Nächstes Arbeitspaket – Run NA (2026-05-31)

Dieses Arbeitspaket schliesst nach Run MZ den nächsten regulären Plan-B-Kandidaten
`AC0881_M.jpg` ab. Der Kandidat war aktiv, weil zwar ein Originalbild vorhanden
war, aber der mittlere `AC0881`-Artefaktstand in den kanonischen
Konvertierungs-/Baseline-Pfaden fehlte.

## 1) Nächste dokumentierte Aufgabe: AC0881-M Qualitätsrefresh

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0881_M.jpg` als nächste reguläre Rotation.
  - Für `AC0881_M` fehlten im kanonischen `src/artifacts/converted_images`-Stand
    SVG-, Log- und Snapshot-Artefakte, obwohl `AC0881_L` und `AC0881_S`
    bereits vorhanden waren.
- Umsetzung:
  - Ein isolierter Re-Konvertierungslauf wurde gegen
    `artifacts/images_to_convert/nonconvertable/AC0881_M.jpg` ausgeführt.
  - Die erzeugten SVG-/Log-/Snapshot-Artefakte wurden nach
    `src/artifacts/converted_images/...` übernommen; das binäre Diff-PNG bleibt bewusst uncommitted.
  - Der Ranking-Eintrag wurde mit `mean_delta2=2780.935791`,
    `std_delta2=6173.261719` und `error_per_pixel=0.02234898` ergänzt.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Welches einfache Rahmen-, Kreis- oder Linienprimitive ist vor der ersten
    Iteration sichtbar?“
- Ergebnis:
  - `AC0881_M` wurde aus der aktiven Plan-B-Liste rotiert, weil der frische
    Re-Konvertierungsstand mit `error_per_pixel=0.02234898` deutlich unter der
    bisherigen Review-Grenze liegt.
  - Die aktive Liste enthält nun `AC0234_S`, `AC0835_S` und neu `AC0820_S` aus
    der Priorität-A-Weak-Family-Rotation.
  - Der PF8-Linkage-Report wurde neu geschrieben und weist für alle drei aktiven
    Kandidaten eine `generalisiert`-Entscheidung mit `CircleBackground`-Seed aus.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --output-dir /tmp/ic-ac0881-next --start AC0881_M --end AC0881_M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `conversion_bestlist.csv`: `error_per_pixel=0.02234898`, `mean_delta2=2780.935791`, `std_delta2=6173.261719`
  - Element-Validation-Log enthält die semantische Kreis-/Text-/Griff-Strecke und endet ohne Failure-Status.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0820_S`, `AC0234_S` und `AC0835_S`, jeweils `decision=generalisiert`.
- Befehl:
  - `python -m pytest -q tests/test_plan_b_perception_linkage.py`
- Ergebnis:
  - Exit `0`
  - `2 passed`
- Befehl:
  - `python -m pytest -q`
- Ergebnis:
  - Exit `0`
  - `657 passed`, mit den bekannten SWIG-Deprecation-Warnings aus der importierten Bildverarbeitungsumgebung.

## 4) Kandidatenrotation

- `AC0881_M.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0234_S.jpg` bleibt der nächste reguläre Kandidat.
- `AC0835_S.jpg` bleibt als Priorität-A-Weak-Family-Kandidat aktiv.
- `AC0820_S.jpg` wurde als nächster Priorität-A-Weak-Family-Kandidat ergänzt.

## 5) Fazit

Run NA schliesst den `AC0881_M`-Folgepunkt vollständig ab: Der fehlende mittlere
`AC0881`-Artefaktstand wurde kanonisch ergänzt, die Plan-B-/PF8-Rotation wurde
aktualisiert, und die sichernden Einzel- sowie Volltests laufen grün.
