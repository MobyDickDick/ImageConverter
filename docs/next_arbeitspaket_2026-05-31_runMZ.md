# Nächstes Arbeitspaket – Run MZ (2026-05-31)

Dieses Arbeitspaket arbeitet nach Run MY den nächsten dokumentierten Kandidaten
`AC0838_M.jpg` aus der Plan-B-/Qualitätsrotation ab. Anders als bei den direkt
vorherigen AC02-Glyphs war hier keine neue Geometry-IR-Form nötig: Die aktuelle
semantische AC08-Strecke erzeugt bereits einen besseren Re-Konvertierungsstand,
der die Review-Grenze wieder unterschreitet. Das Paket refreshed deshalb die
kanonischen Artefakte, dokumentiert die Messwerte und rotiert die Kandidatenliste
weiter.

## 1) Nächste dokumentierte Aufgabe: AC0838-M Qualitätsrefresh

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0838_M.jpg` als nächste reguläre Rotation.
  - Das Qualitätsreview hatte das vorhandene SVG-Paar mit `normalized_mse=0.04729276`
    oberhalb der Review-Grenze `0.045945679012345676` markiert.
- Umsetzung:
  - Ein isolierter Re-Konvertierungslauf wurde gegen
    `artifacts/images_to_convert/nonconvertable/AC0838_M.jpg` ausgeführt.
  - Die erzeugten SVG-/Log-/Snapshot-Artefakte wurden nach
    `src/artifacts/converted_images/...` übernommen.
  - Der Ranking-Eintrag wurde von `mean_delta2=9225.634766` auf
    `mean_delta2=7789.174316` aktualisiert; daraus folgt
    `normalized_mse=0.03992913` und damit wieder ein Wert unterhalb der Review-Grenze.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann der dominante VOC-Kreis vorab als `CircleBackground` und Label-Signal
    festgehalten werden?“
- Ergebnis:
  - Der aktualisierte Plan-B-Linkage-Stand rotiert `AC0838_M` aus der aktiven
    Liste heraus und hält als nächste Proben `AC0881_M`, `AC0234_S` und
    `AC0835_S` fest.
  - `AC0835_S` übernimmt den frei gewordenen `VOC`-Kreis/Text-Lerneffekt für die
    nächste Priorität-A-Familie.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --output-dir /tmp/ic-ac0838-baseline --start AC0838_M --end AC0838_M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `conversion_bestlist.csv`: `error_per_pixel=0.04151429`, `mean_delta2=7789.174316`, `std_delta2=14684.836914`
  - Element-Validation-Log enthält `status=semantic_ok`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0881_M`, `AC0234_S` und `AC0835_S`.

## 4) Kandidatenrotation

- `AC0838_M.jpg` wurde aus der aktiven Plan-B-Liste entfernt, weil die frische
  Re-Konvertierung die Review-Grenze unterschreitet.
- `AC0881_M.jpg` ist nun die nächste reguläre Rotation.
- `AC0835_S.jpg` wurde aus der Weak-Family-Priorität-A-Liste als neuer aktiver
  Kandidat ergänzt.

## 5) Fazit

Run MZ schließt den `AC0838_M`-Qualitätsfolgepunkt ab: Die aktualisierten
Artefakte liegen unter der bisherigen Review-Grenze, der PF8-Linkage-Report wurde
weiterrotiert, und die nächste reguläre Plan-B-Aufgabe ist `AC0881_M.jpg`.
