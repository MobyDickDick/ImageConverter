# Nächstes Arbeitspaket – AC0840_L rF-Kreisbadge Textregistrierung Plan-B Run VX (2026-07-08)

Dieses Arbeitspaket formalisiert und schließt die Plan-B-Aufgabe für `AC0840_L`:
ein 28×28-Kreisbadge mit hellgrauer Füllung, grauer Kontur und zentralem
`rF`-Text. Der Fix bleibt katalogfrei: Der Runtime-Code verzweigt nicht auf
`AC0840_L`, sondern erweitert den generischen Kreisbadge-Textpfad um optische
Textregistrierungsparameter für kleine kurze rF-Badges.

## 1) Umsetzung

- Der allgemeine Beschreibungspfad für Kreis-/Text-Badges erkennt kleine
  28×28- beziehungsweise kleine `rF`-Badges und erzeugt weiterhin
  `CircleBackground` + `TextGlyph`.
- `TextGlyph` trägt nun für diese kurzen rF-Badges eine größere, an der
  Referenzhöhe orientierte `font_size`, graue Textfarbe, Font-Gewicht `600` und
  optische Registrierungsparameter (`anchor_x`, `anchor_y`, `baseline_adjust`,
  `scale_x`, `scale_y`).
- Der generische Geometry-IR-SVG-Renderer wertet diese Textparameter aus:
  Textanker, Baseline-Korrektur und optionale nicht-uniforme Skalierung werden
  ohne eingebettete Rasterdaten ausgegeben.

## 2) Perception-Lerneffekt

Der Lerneffekt ist `generalisiert`: Die Änderung koppelt an messbare
Badge-/Glyph-Eigenschaften (`CircleBackground`, kurzer `TextGlyph`, kleine
Rastergröße) und nicht an den Dateinamen. `AC0840_L` bleibt ausschließlich
Dokumentations-/Plan-B-Kontext.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_small_rf_circle_badge_description_uses_optical_text_registration tests/test_image_composite_converter.py::test_text_glyph_renderer_honors_anchor_baseline_and_scale_parameters` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0840-runVX --start AC0840_L --end AC0840_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der isolierte Einzellauf bleibt im semantischen rF-Badge-Pfad bei `Mean-Delta²=7034.253418`.

## 4) Ergebnis / nächster Schritt

Run VX schließt den dokumentierten AC0840_L-Textregistrierungs-Refresh ab. Kleine
rF-Kreisbadges können nun über generische optische Textparameter größer und
mittiger gerendert werden. Das nächste Arbeitspaket kann in der aktiven
Plan-B-Rotation fortfahren oder weitere allgemeine Text-/Antialiasing-Probes
prüfen.
