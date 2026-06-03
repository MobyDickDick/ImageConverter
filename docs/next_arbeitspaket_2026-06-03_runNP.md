# Nächstes Arbeitspaket 2026-06-03 – Run NP (AC0835_S Plan-B/Perception-Refresh)

Dieses Arbeitspaket folgt der aktuellen Definition aus `docs/open_tasks.md`: nächste dokumentierte Plan-B-/Perception-Aufgabe, genau eine gekoppelte Plan-B-Aufgabe und ein fokussierter Einzelrepro.

## 1) Nächste dokumentierte Aufgabe: AC0835_S als connector-freies VOC-Badge sichern

- Ausgangspunkt: `PLAN_B_KANDIDATEN.md` führte `AC0835_S.jpg` als nächsten regulären Kandidaten.
- Fachliche Beschreibung: grauer Kreis mit grauem Rand, hellgrauem Hintergrund und Text `VOC`, ausdrücklich ohne Griff/Kelle/Anbauteile.
- Problem im Repro: Der echte Einzelpfad war zwar `status=semantic_ok`, konnte aber über den Satisfactory-Baseline-Restore eine degenerierte 0,5-px-Arm-Linie am rechten Rand wieder in das SVG übernehmen.

## 2) Umsetzung

- Der Badge-SVG-Renderer entfernt für connector-freie AC08-Kreis/Text-Symbole stale Arm-/Stem-Parameter aus Optimierungsproben oder Template-Transfer.
- Zusätzlich werden degenerierte Arm-Probes unterhalb der sichtbaren Mindestlänge nicht mehr als `<line>` gerendert. Das schützt insbesondere AC0835_S vor einer semantisch falschen Mini-Connector-Linie, ohne echte AC0836/AC0861-Connectoren zu unterdrücken.
- Die Satisfactory-Baseline für `AC0835_S.svg` wurde semantisch bereinigt, damit der Restore-Pfad nicht erneut den falschen Mini-Arm zurückkopiert.

## 3) Gekoppelte Plan-B-/Perception-Rotation

- `AC0835_S` wurde aus der aktiven Plan-B-Liste rotiert.
- Die aktive Liste enthält nun `AC0861_S`, `AC0862_S` und den neuen Folgepunkt `AC0863_S`.
- Der PF8-Linkage-Report wurde neu geschrieben und bewertet alle drei Kandidaten mit Perception-Lerneffekt `generalisiert`.

## 4) Sicherung

- Gezielter Testblock: `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/test_plan_b_perception_linkage.py` → `8 passed`.
- PF8-Linkage-Report: `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1` → 3/3 Samples evaluiert, alle mit Perception-Lerneffekt.
- Externer AC0835-S-Repro: `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-ac0835-runnp3 --start AC0835_S --end AC0835_S --deterministic-order` → Exit `0`, `status=semantic_ok`, final wiederhergestelltes SVG ohne `<line>`-Connector.

## 5) Nächster sinnvoller Schritt

In der normalen Plan-B-Rotation mit `AC0861_S.jpg` fortfahren; alternativ den seitlich gedrehten Folgepunkt `AC0862_S.jpg` isoliert prüfen.
