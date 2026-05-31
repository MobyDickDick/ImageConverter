# Nächstes Arbeitspaket – AC0870_S Path-T-Refresh (Run NE, 2026-05-31)

## Ziel

Der nächste Kandidat aus `PLAN_B_KANDIDATEN.md` war `AC0870_S.jpg`: ein kleines rundes `T`-Badge mit auffälligem Fehler bei Textgröße, Zentrierung und Antialiasing. Ziel war, den bestehenden semantischen Badge-Pfad nicht durch einen Sonderfall zu ersetzen, sondern den generischen Optimizer so zu erweitern, dass pfadbasierte `T`-Glyphen (`text_mode=path_t`) genauso wie die textbasierten `CO₂`-/`VOC`-/`rF`-Labels an der Optimierung teilnehmen.

## Umsetzung

- Der globale Parametervektor übernimmt bei `text_mode=path_t` nun die vorhandenen SVG-Pfadparameter `tx`, `ty` und `s` als `text_x`, `text_y` und `text_scale` und schreibt Änderungen wieder auf die SVG-Pfadparameter zurück.
- Die Bounds für `path_t`-Textskalierung verwenden nun die kleine SVG-Skalendomäne um `s` statt den generischen Font-Multiplikatorbereich `0.5..1.8`.
- Die Breiten-/Skalenoptimierung kennt `path_t` als Textmodus und kann `s` bracketingfähig prüfen.
- Die stochastische Redraw-Variation behandelt `path_t`-Skalen als kleine SVG-Skalenwerte und hebt sie nicht mehr versehentlich auf generische Font-Multiplikatoren an.

## Repro / Ergebnis

- **Befehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0870-run5 --start AC0870_S --end AC0870_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- **Exit-Code:** `0`
- **Status:** `semantic_ok`
- **Metrik vorher:** `mean_delta2=6616.799805` aus `src/artifacts/converted_images/reports/pixel_delta2_ranking.csv`
- **Metrik nachher:** `mean_delta2=5075.666504`, `std_delta2=8480.436523`
- **Log-Artefakt:** `src/artifacts/converted_images/reports/AC0870_S_element_validation.log`

## PF8 / Kandidatenrotation

`AC0870_S.jpg` wurde aus der aktiven Kandidatenliste entfernt. Die Liste rotiert jetzt auf `AC0850_M.jpg` und `AC0836_S.jpg`; als neuer Folgepunkt wurde `AC0844_S.jpg` ergänzt. Der PF8-Linkage-Report wurde entsprechend neu erzeugt und zeigt für `AC0844_S` eine generalisierte `CircleBackground`-Seed-Entscheidung.

## Nächster sinnvoller Schritt

Mit `AC0850_M.jpg` rotieren oder den neuen `AC0844_S.jpg`-rF-Kreis/Connector-Lerneffekt als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.
