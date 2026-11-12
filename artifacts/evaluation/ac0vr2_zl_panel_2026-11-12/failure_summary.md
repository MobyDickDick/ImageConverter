# Plan-B-Fehler und Folgeaufgaben

### Plan B: AC0VR2_ZL_M.svg – variations

Lauf: lokal; Bericht: `report.json`.

Status: completed; bestanden: 13/17.

| Fall | Fehlergründe | RGB-MSE | Vordergrund-MSE | Kontur | IoU |
|---|---|---:|---:|---:|---:|
| probe_01 | foreground_iou_outside_limit | 0.000450 | 0.000818 | 0.750324 | 0.836389 |
| probe_05 | edge_alignment_outside_limit | 0.000080 | 0.000050 | 0.000000 | 0.991115 |
| probe_13 | edge_alignment_outside_limit | 0.000085 | 0.000060 | 0.537673 | 0.942806 |
| probe_16 | edge_alignment_outside_limit | 0.001359 | 0.000531 | 0.134765 | 0.985556 |


- [ ] Ursache mit dem dokumentierten SVG- und Beschreibungshash sowie Seed reproduzieren.
- [ ] Gemeinsame Ursache mit vorhandenen Fehleraufgaben gruppieren; Ausführungsfehler getrennt behandeln.
- [ ] Mindestens zwei unterschiedliche Lösungshypothesen mit protokolliertem Budget vergleichen; Suchfortschritt und erfolglose Varianten sichern.
- [ ] Beschreibung oder allgemeinen Rasteralgorithmus korrigieren; Qualitätsgrenzen beibehalten.
- [ ] Original und alle 16 Varianten über die echte CLI abnehmen; Holdouts und Regressionen prüfen.
- [ ] Erfolgreiche Varianten, Vorher-/Nachher-Beleg und fachlichen Regressionstest erhalten; docs/plan_b_learning_workflow.md beachten.

Wiederholung: Beschreibung aus dem Einzelbericht als UTF-8-Datei speichern und
`python -m tools.run_plan_b_variations --svg QUELLE --description-file BESCHREIBUNG --seed SEED`
mit den protokollierten `--iterations` und `--timeout-seconds` ausführen.

<details><summary>Messwerte, Grenzen und Wiederholungsbeleg</summary>

```json
{
  "source_svg": "artifacts/samples/AC0VR2_ZL_M.svg",
  "phase": "variations",
  "seed": 4470433890649107824,
  "status": "completed",
  "source_svg_sha256": "0162b26da51a471006030e68f17f144ed5c95eb2af49a2ec84692aabfbef8fd4",
  "source_description_sha256": "afe166dda09d1623dd2a15471753d221ea8281ba2a4825cf11dfad16eaac7f9b",
  "source_description": "Es gibt einen vertikalen Graustufenübergang (Farbübergang). Die maximale Helligkeit ist ca. 1/3 unter dem oberen Bildrand.\nDas dunkelste Grau dieses Farbübergang ist immer noch leicht heller als der Rand.\n",
  "source_image": "source.png",
  "source_image_sha256": "ec4a77af5836fd086354cb4a56ab7a2f64b01948f7112ca73a0028417d677ff5",
  "original_satisfactory": true,
  "variations_started": true,
  "iterations": 64,
  "timeout_seconds": 60.0,
  "limits": {
    "max_normalized_mse": 0.01,
    "max_foreground_mse": 0.04,
    "min_edge_alignment": 0.72,
    "min_foreground_iou": 0.85,
    "max_svg_elements": 80,
    "max_path_commands": 160
  },
  "summary": {
    "required": 17,
    "completed": 17,
    "passed": 13,
    "failed": 4,
    "satisfactory": false
  },
  "input_pool": null,
  "failures": [
    {
      "case_id": "probe_01",
      "width": 60,
      "height": 30,
      "variation": {
        "scale": 0.98879415,
        "relative_x": -0.00939296,
        "relative_y": 0.01268036
      },
      "variation_generation": {
        "candidates_checked": 1,
        "rejected_duplicates": 0
      },
      "input_sha256": "1d8a09e2093c38ab3ba5e3a381410a3c253d8c8b75a1789dce289701eba53328",
      "reference_svg_sha256": "9f9ba7f66c17262fa695c7577bf4c19ab8a021c1b5a613e7a2bca1d9d1f550ca",
      "satisfactory": false,
      "failures": [
        "foreground_iou_outside_limit"
      ],
      "returncode": 0,
      "blocked_svg_reads": [],
      "metrics": {
        "normalized_mse": 0.00044986692955717444,
        "foreground_mse": 0.000818288535811007,
        "edge_alignment": 0.7503242492675781,
        "foreground_iou": 0.8363892806770099
      },
      "complexity": {
        "parse_error": null,
        "embedded_raster_count": 0,
        "vector_element_count": 5,
        "path_count": 0,
        "path_command_count": 0,
        "path_complexity_ratio": 0.0
      },
      "output_sha256": "f3437c168cb5178760bbe2eb304c5377cd21d78ad67b55126515f13c7c35335f",
      "elapsed_seconds": 34.328
    },
    {
      "case_id": "probe_05",
      "width": 60,
      "height": 30,
      "variation": {
        "scale": 1.03886447,
        "relative_x": -0.00633187,
        "relative_y": -0.01008109
      },
      "variation_generation": {
        "candidates_checked": 1,
        "rejected_duplicates": 0
      },
      "input_sha256": "ba607fee4292c0c780effa55fb547468d974764cfa8f5dd1ba22c800eb9d2504",
      "reference_svg_sha256": "896b4bfc635ced5e1b03b5d6a79edc243736d130c67f760bfaac12560e4b0c00",
      "satisfactory": false,
      "failures": [
        "edge_alignment_outside_limit"
      ],
      "returncode": 0,
      "blocked_svg_reads": [],
      "metrics": {
        "normalized_mse": 8.00262059783563e-05,
        "foreground_mse": 5.0407121307216585e-05,
        "edge_alignment": 0.0,
        "foreground_iou": 0.9911154985192497
      },
      "complexity": {
        "parse_error": null,
        "embedded_raster_count": 0,
        "vector_element_count": 2,
        "path_count": 0,
        "path_command_count": 0,
        "path_complexity_ratio": 0.0
      },
      "output_sha256": "11653ba7dbec9059017a9b6275ccf3ecc05137dd6da7b803f33eca89b1545df8",
      "elapsed_seconds": 34.203
    },
    {
      "case_id": "probe_13",
      "width": 60,
      "height": 30,
      "variation": {
        "scale": 1.04092491,
        "relative_x": 0.0225654,
        "relative_y": -0.01341085
      },
      "variation_generation": {
        "candidates_checked": 1,
        "rejected_duplicates": 0
      },
      "input_sha256": "cd2700cbaaf103439b6b9804854cd2fd42912e50695056ace2ee7778564283e4",
      "reference_svg_sha256": "b19164d7f9a64021c5330b576007e7d128256b1c93c388f791e5a029d5c58371",
      "satisfactory": false,
      "failures": [
        "edge_alignment_outside_limit"
      ],
      "returncode": 0,
      "blocked_svg_reads": [],
      "metrics": {
        "normalized_mse": 8.532899664714932e-05,
        "foreground_mse": 5.954493462922983e-05,
        "edge_alignment": 0.5376733541488647,
        "foreground_iou": 0.9428060768543343
      },
      "complexity": {
        "parse_error": null,
        "embedded_raster_count": 0,
        "vector_element_count": 2,
        "path_count": 0,
        "path_command_count": 0,
        "path_complexity_ratio": 0.0
      },
      "output_sha256": "082e5d56cedfd9877ba14491bf093769a742b46cb101974ae63cc3af283adbda",
      "elapsed_seconds": 33.625
    },
    {
      "case_id": "probe_16",
      "width": 60,
      "height": 30,
      "variation": {
        "scale": 1.03688637,
        "relative_x": -0.00768691,
        "relative_y": -0.01937148
      },
      "variation_generation": {
        "candidates_checked": 1,
        "rejected_duplicates": 0
      },
      "input_sha256": "a284af593cb189583c508e9f4210cd3926eebde1b61e20a4ecb4b835316eb1fb",
      "reference_svg_sha256": "be4e9baf1ec0c2796a0c680ea7af3fbc9c4377d56094d967af0fbd4c44cef233",
      "satisfactory": false,
      "failures": [
        "edge_alignment_outside_limit"
      ],
      "returncode": 0,
      "blocked_svg_reads": [],
      "metrics": {
        "normalized_mse": 0.001359391724690795,
        "foreground_mse": 0.0005312145221978426,
        "edge_alignment": 0.1347649246454239,
        "foreground_iou": 0.9855555555555555
      },
      "complexity": {
        "parse_error": null,
        "embedded_raster_count": 0,
        "vector_element_count": 2,
        "path_count": 0,
        "path_command_count": 0,
        "path_complexity_ratio": 0.0
      },
      "output_sha256": "c534ac35b52b49f7f215874c8f21961287b57d8c38129aefc67657965c2f6777",
      "elapsed_seconds": 33.906
    }
  ],
  "error": null,
  "report": "report.json",
  "run_url": ""
}
```

</details>
