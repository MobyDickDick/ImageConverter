# Plan-B Sample-Gap Analyse (2026-05-14)

## Methode

- Alle verfügbaren Vorlagen wurden aus `artifacts/images_to_convert/samples/*.svg` ermittelt.
- Als „bereits in Plan B verwendet“ gelten Vorlagen, wenn in
  - `artifacts/converted_images/reports/*_element_validation.log` ein `plan_b`-Status vorkommt, oder
  - `imageCompositeConverter.local.log` explizit „Plan B aktiv: verwende vorhandene Sample-SVG ...“ protokolliert ist.

## Ergebnisübersicht

- Gesamtzahl Vorlagen: **42**
- Bereits mit Plan B verwendet: **2**
  - `AC0VR2_M`
  - `AC0VR2_AB_M`
- Noch nicht mit Plan B verwendet: **40**

## Noch nicht verwendete Vorlagen

`AC0040_L`, `AC0080_L`, `AC0100_L`, `AC0110_L`, `AC0120_L`, `AC0130_L`, `AC0151_L`, `AC0153_L`, `AC0223_L`, `AC0511_L`, `AC0511_laeuft`, `AC0511_offen`, `AC0511_zu`, `AC0512_L`, `AC0800`, `AC0814_L`, `AC0814_M`, `AC0838_M`, `AR0030`, `AR0030_1`, `AR0030_offen`, `AR0030_zu`, `AR0140`, `AR0140_laeuft`, `AR0140_offen`, `AR0140_zu`, `DLG0010`, `DLG0011`, `DLG0014`, `DLG0071`, `DdcAnGener22_S1`, `DdcCoValvd21_Cooler`, `DdcCoValvd21_FlapH`, `DdcCoValvd21_FlapV`, `DdcCoValvd21_HeatRecover_air`, `DdcCoValvd21_HeatRecover_rotation`, `DdcCoValvd21_Heat_Recovery`, `DdcCoValvd21_Heater`, `DdcCoValvd21_Humidfyer`, `z_201`

## Konkrete Aufgaben (Backlog)

1. **Batch-Runner für Plan-B-Regression aufsetzen**
   - Skript erweitern/neu anlegen, das für alle 40 Kandidaten einen Plan-B-Lauf ausführt (inkl. Log-Ergebnis pro Vorlage).
   - Ergebnis als CSV schreiben: `sample_name`, `plan_b_used`, `selected_source`, `err_svg`, `err_sample`, `winner`.

2. **Priorisierung nach Variantenfamilien**
   - Reihenfolge: erst `AC08xx`/`AC05xx` (höchste Relevanz für aktuellen Konvertieralgorithmus), dann `AR*`, danach `DLG*`/`Ddc*`.

3. **Abbruch-/Timeout-Guardrails für große Batches**
   - Für die 40er-Serie Laufzeitbudget und Wiederanlauf-Mechanik implementieren (z. B. chunkweise à 10 Samples).

4. **Qualitätsmetriken ergänzen**
   - Neben `err` zusätzlich Element-Checks in Report aufnehmen (`element_validation_passed`, Fehlertyp).

5. **Automatische Follow-up-Task-Erzeugung**
   - Bei `winner=sample_svg_selected` + element validation fail: automatisch Task in `docs/open_tasks.md` erzeugen.

## Sofort ausführbarer nächster Schritt

- Start mit Pilot-Subset `AC0800`, `AC0814_L`, `AC0814_M`, `AC0838_M`.
- Danach Entscheidung, ob Plan-B-Selektionslogik (Schwellwerte/Ranking) vor dem Vollbatch nachjustiert werden soll.
