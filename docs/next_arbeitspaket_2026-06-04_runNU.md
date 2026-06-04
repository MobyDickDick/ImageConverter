# Nächstes Arbeitspaket – FP-D10 Run NU (2026-06-04)

## Ziel

FP-D10 prüft eine familienübergreifende Harmonisierungshypothese aus
`docs/ac08_improvement_plan.md` praktisch und datenbasiert. Gewählt wurde die
Hypothese **Skalen-Familien ohne Geometrieänderung** mit den Kandidaten
`AC0800_L/M/S` und `AC0820_L/M/S`, weil FP-D9 die Plain-Ring-Seite gerade
stabilisiert hat und AC0820 die gleiche Ringgrundform mit CO₂-Beschriftung nutzt.

## Gegenmaßnahme / Prüfmechanik

Der Harmonization-Report erzeugt zusätzlich
`cross_family_hypothesis_metrics.csv`. Die Datei ist bewusst ein Daten-/Gate-
Report und kein neuer aggressiver Harmonisierungspfad: Aktive Proto-Anker bleiben
unverändert, damit ein textloser AC0800-Anker AC0820 nicht versehentlich die
CO₂-Beschriftung entfernt.

Pro Hypothesengruppe werden protokolliert:

- `hypothesis_group`,
- `bases`,
- `variants`,
- `max_geometry_delta`,
- `topology_signature_count`,
- `topology_signatures`,
- `text_orientation_policies`,
- `status` (`confirmed` oder `rejected`).

Eine Hypothese gilt nur dann als `confirmed`, wenn die normalisierte
Geometriedifferenz klein bleibt und genau eine Topologiesignatur vorliegt. Dadurch
werden gleiche Kreisgeometrie und unterschiedliche Semantik/Texttopologie getrennt
bewertet.

## Datenbasierte Entscheidung

Der AC0800–AC0820-Fokuslauf schrieb:

```text
ac08_ring_scale_no_geometry_change;AC0800,AC0820;AC0800_L|AC0800_M|AC0800_S|AC0820_L;0.1000;2;circle+no_text+no_stem+no_arm+text_mode:none,circle+text+no_stem+no_arm+text_mode:co2;inherit_variant;rejected
```

Damit ist die geprüfte Hypothese in der aktuellen Implementierung **verworfen**:
Die Grundform ist verwandt, aber die Topologie ist nicht identisch, weil AC0800
textlos ist und AC0820 CO₂-Text trägt. Cross-Family-Übernahme darf daher für
diese Gruppe vorerst nur als getrennte Ring-/Text-Hypothese weiterverfolgt werden,
nicht als komplette Proto-Anker-Harmonisierung.

## Sicherung

| Check | Befehl | Exit | Ergebnis |
| --- | --- | ---: | --- |
| Detail-Regression | `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_harmonization_helpers.py` | `0` | `7 passed in 0.08s`; neue Tests belegen `rejected` für AC0800/AC0820 wegen Texttopologie und `confirmed` für kompatible Rotations-Topologie-Fixtures. |
| AC0800–AC0820-Fokuslauf | `timeout 180 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd10-rings --start AC0800 --end AC0820 --deterministic-order` | `0` | Report erzeugt; Evidenz unter `artifacts/converted_images/reports/FP_D10_cross_family_hypothesis_metrics_2026-06-04_runNU.csv`. |

## Ergebnis

- FP-D10-1 ist erfüllt: Die AC0800/AC0820-Hypothese aus dem AC08-Plan wurde
  praktisch geprüft.
- FP-D10-2 ist erfüllt: Der Status ist mit Evidenz `rejected`/`verworfen`
  dokumentiert.
- FP-D10-EXIT ist erfüllt: Die Hypothese ist datenbasiert abgeschlossen; es wurde
  kein riskanter Cross-Family-Anker für textlose vs. beschriftete Ringe aktiviert.

## 5-Zeilen-Log

- **Getestet:** Harmonization-Detailtests und AC0800–AC0820-Fokuslauf.
- **Ergebnis:** Detailtests grün; AC0800/AC0820-Hypothese wird wegen zwei
  Topologiesignaturen (`no_text` vs. `text_mode:co2`) verworfen.
- **Blocker:** Kein technischer FP-D10-Blocker; fachlicher Folgeschritt wäre eine
  getrennte Ringgeometrie-/Textlagen-Hypothese statt kompletter Proto-Anker-
  Übernahme.
- **Nächster Schritt:** FP-D11 bereitet das Release-Kandidaten-Gate mit Kernsuite,
  AC08-Smoke und Qualitätsvergleich vor.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`.
