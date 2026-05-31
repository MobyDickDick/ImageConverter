# Nächstes Arbeitspaket – Run NH (2026-05-31)

Dieses Arbeitspaket arbeitet nach Run NF den nächsten dokumentierten Plan-B-
Kandidaten `AC0836_S.jpg` ab. Der Kandidat war aktiv, weil das runde `VOC`-
Badge mit senkrechtem Griff zwar semantisch konvertiert, der PF8-Linkage-Report
aber den Griff bisher nicht als eigenen Linien-Hinweis erkannte.

## 1) Nächste dokumentierte Aufgabe: AC0836-S als VOC-Kreis mit senkrechtem Griff

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0836_S.jpg` als nächsten regulären
    Kandidaten.
  - Die Beschreibung lautet: `Wie AC0835, jedoch mit senkrechtem Griff nach
    unten ... Text im Kreis: "VOC"`.
  - PF8 fordert für diesen Kandidaten, Kreis-, Label- und Griffsignal vor der
    ersten Iteration abzusichern.
- Umsetzung:
  - Die vertikale Linienerkennung nutzt neben dem Hough-Pfad nun einen
    konturbasierten Morphologie-Fallback für sehr kleine Badge-Bilder.
  - Der Fallback erkennt die dunklen, ein Pixel breiten Griffsegmente unterhalb
    des Kreis-Badges als `line`-Kandidaten, ohne den vorhandenen
    `CircleBackground`-Seed zu verdrängen.
  - Der Plan-B-Linkage-Test prüft nun explizit, dass der aktive rF-
    Connector-Folgepunkt `AC0861_S` den senkrechten Griff als vertikale Linie
    matched.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann der dominante VOC-Kreis vorab als `CircleBackground` und der
    senkrechte Griff als Linien-Hinweis festgehalten werden?“
- Ergebnis:
  - `AC0836_S` wurde aus der aktiven Plan-B-Liste rotiert, weil der echte
    Einzellauf weiter `semantic_ok` protokolliert und die PF8-Kopplung nun
    zusätzlich `line` für den senkrechten Griff erkennt.
  - Die aktive Liste enthält nun `AC0835_S`, `AC0861_S` und neu `AC0862_S` als
    gedrehten rF-Connector-Folgepunkt.
  - Der PF8-Linkage-Report wurde neu geschrieben und weist für `AC0861_S` einen
    `line`-Topkandidaten sowie für `AC0862_S` Kreis-/Linien-/HorizontalRule-
    Signale aus.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-ac0836-runnh --start AC0836_S --end AC0836_S --deterministic-order`
- Ergebnis:
  - Exit `0`
  - Das Element-Validation-Log enthält `status=semantic_ok`.
  - `conversion_bestlist.csv`: `error_per_pixel=0.07524978`,
    `mean_delta2=6602.432129`, `std_delta2=12481.682617`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0835_S`, `AC0861_S` und `AC0862_S`, jeweils
    `decision=generalisiert`; `AC0861_S` matched `circle,line` und hat `line`
    als stärksten Kandidaten.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_plan_b_perception_linkage.py tests/test_perception_detection_contract.py`
- Ergebnis:
  - Exit `0`
  - `5 passed`

## 4) Kandidatenrotation

- `AC0836_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0835_S.jpg` ist nun der nächste reguläre Kandidat.
- `AC0861_S.jpg` bleibt als rF-/Vertikalgriff-Anschlussprobe aktiv.
- `AC0862_S.jpg` wurde als nächster gedrehter rF-Connector-Kandidat ergänzt.

## 5) Fazit

Run NH schließt `AC0836_S.jpg` als dokumentierten PF8-Anschluss ab: Die
semantische Konvertierung bleibt grün, und die Perception-Kopplung beschreibt
nicht mehr nur den dominanten Kreis, sondern auch den senkrechten Griff als
Linienkandidat. Damit kann die nächste normale Rotation mit `AC0835_S.jpg` oder
mit dem rF-Connector-Folgepunkt `AC0861_S.jpg` fortfahren.
