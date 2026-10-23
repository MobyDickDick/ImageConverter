# Nächstes Arbeitspaket – Run NB (2026-05-31)

Dieses Arbeitspaket arbeitet nach Run NA den nächsten dokumentierten Plan-B-
Kandidaten `AC0234_S.jpg` ab. Der Kandidat war aktiv, weil die AC0231-verwandte
3-Wege-Ventilform zwar ein vorhandenes Diff-Artefakt hatte, aber die
hauptdiagonal gespiegelte M-Kelle noch nicht als eigene Geometry-IR-Folgeform
modelliert war.

## 1) Nächste dokumentierte Aufgabe: AC0234-S als hauptdiagonal gespiegelte M-Kelle

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0234_S.jpg` als nächsten regulären Kandidaten.
  - Die Beschreibung lautet: `Wie AC0231 ... Geometrische Variante: Hauptdiagonal gespiegelt`.
  - PF8 fordert für diesen Kandidaten, Kreis-/Kellen- und `M`-Signal vor der ersten Iteration abzusichern.
- Umsetzung:
  - Die Description-Geometry-IR erkennt AC0234 nun als
    `MainDiagonalMirroredTopKelleThreeWayValveGlyph` mit `label=M`.
  - Das neue Glyph nutzt dieselbe Ventil-Rendering-Strecke wie die bestehenden
    AC0231-/AC0232-/AC0233-/AC0224-Glyphs und rendert Body-Pfade, Connector,
    Kreis und Label in hauptdiagonal gespiegelter Lage.
  - Der Non-Composite-Pfad vergleicht Perception-seeded Geometry-IR,
    Description-Geometry-IR und elementweisen Symbol-Fit nach Pixel-Fehler;
    der daraus gewählte Vektor-Baseline-Fehler bleibt im Sample-Vergleich als
    `baseline_error` nachvollziehbar.
  - Für `AC0234_S` wurde das bisher beste Plan-B-Sample explizit als kuratierter
    Sample-Fallback abgelegt; der echte Einzellauf wählt es weiterhin, weil es
    mit `error_per_pixel=0.05805278` klar besser als die frisch generierte
    Geometry-IR ist.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann die gespiegelte M-Beschriftung oder die runde Kelle vorab als
    TextGlyph/CircleBackground dokumentiert werden?“
- Ergebnis:
  - `AC0234_S` wurde aus der aktiven Plan-B-Liste rotiert, weil der Kandidat nun
    eine explizite hauptdiagonal gespiegelte Geometry-IR-Form besitzt und der
    kanonische Artefaktstand durch den Sample-Fallback reproduzierbar bleibt.
  - Die aktive Liste enthält nun `AC0835_S`, `AC0820_S` und neu `AC0870_S` aus
    der Priorität-A-Weak-Family-Rotation.
  - Der PF8-Linkage-Report wurde neu geschrieben und weist für alle drei aktiven
    Badge-Kandidaten eine `generalisiert`-Entscheidung mit `CircleBackground`-
    Seed aus.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0234-runnb --start AC0234_S --end AC0234_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `conversion_bestlist.csv`: `error_per_pixel=0.05805278`, `mean_delta2=8331.138672`, `std_delta2=13348.888672`
  - Element-Validation-Log wählt `non_composite_plan_b_sample_svg_selected` und dokumentiert den frisch generierten Vektor-Baseline-Pfad mit `baseline_error=59.826111` gegenüber dem kuratierten Sample mit `sample_error=34.831667`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0820_S`, `AC0870_S` und `AC0835_S`, jeweils `decision=generalisiert`.
- Befehl:
  - `python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py`
- Ergebnis:
  - Exit `0`
  - `57 passed`
- Befehl:
  - `python -m pytest -q tests/test_plan_b_perception_linkage.py`
- Ergebnis:
  - Exit `0`
  - `2 passed`

## 4) Kandidatenrotation

- `AC0234_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0835_S.jpg` ist nun der nächste reguläre Kandidat.
- `AC0820_S.jpg` bleibt als Priorität-A-Weak-Family-Kandidat aktiv.
- `AC0870_S.jpg` wurde als nächster Priorität-A-Weak-Family-Kandidat ergänzt.

## 5) Fazit

Run NB schließt `AC0234_S.jpg` ab: Die hauptdiagonal gespiegelte AC0231-
Folgeform ist jetzt als eigene Geometry-IR modelliert, der Non-Composite-Pfad
protokolliert den Qualitätsvergleich der verfügbaren Vektorstrategien, der
kuratierte Artefaktstand bleibt reproduzierbar, und die Plan-B-/PF8-Rotation ist
auf die nächste runde Text-Badge-Familie weitergezogen.
