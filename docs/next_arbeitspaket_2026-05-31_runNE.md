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
=======
# Nächstes Arbeitspaket – Run NE (2026-05-31)

Dieses Arbeitspaket arbeitet nach Run ND den nächsten dokumentierten Plan-B-
Kandidaten `AC0870_S.jpg` ab. Der Kandidat war aktiv, weil das runde
`T`-Badge laut Weak-Family-Befund eine einfache, aber weiterhin schwache
Kreis-/Text-Zentrierung zeigt.

## 1) Nächste dokumentierte Aufgabe: AC0870-S als zentriertes T-Badge stabilisieren

- Anlass:
  - `PLAN_B_KANDIDATEN.md` führte `AC0870_S.jpg` als nächsten regulären
    Kandidaten.
  - PF8 fragt für diesen Kandidaten, ob der dominante `T`-Kreis vorab als
    `CircleBackground` und das zentrierte Kurzlabel als `TextGlyph`-Hinweis
    festgehalten werden kann.
  - Der Vorlauf driftete im Validierungsfallback auf eine links/unten liegende
    Kreispose (`cx=4.5000`, `cy=8.0000`, `r=4.0000`), obwohl der dokumentierte
    Kandidat ein zentriertes T-Badge ist.
- Umsetzung:
  - Der AC0870-Default setzt `draw_text=True`, damit die semantische
    Textpräsenz nicht nur implizit über `path_t`, sondern explizit in den
    Parametern steht.
  - Die AC0870-S-Bildinitialisierung ignoriert bei winzigen, stark
    antialiasenden 15px-Badges Hough-Treffer, die auf die dunkle T-Glyphe
    einschnappen, und setzt Kreiszentrum/-radius auf den optischen Badge-Seed.
  - Die AC08-Finalisierung bewahrt für kleine AC0870-`path_t`-Badges
    Kreiszentrum, Textposition, Textskalierung und einen engen Radiuskorridor;
    AC0870 wird deshalb nicht mehr über den AC08-Phase-2-Adaptivunlock aus der
    zentrierten Badge-Pose gelöst.
  - Eine Regression prüft den zentrierten AC0870-S-Seed samt Text-/Radiuslocks.

## 2) Gekoppelte Plan-B-/Perception-Aufgabe

- Perception-Frage aus PF8:
  - „Kann der dominante T-Kreis vorab als `CircleBackground` und das zentrierte
    Kurzlabel als `TextGlyph`-Hinweis festgehalten werden?“
- Ergebnis:
  - `AC0870_S` wurde aus der aktiven Plan-B-Liste rotiert, weil die
    zentrierte Kreis-/T-Semantik nun als stabiler Seed abgesichert ist.
  - Die aktive Liste enthält nun `AC0850_M`, `AC0836_S` und neu `AC0835_S` aus
    der AC08-Weak-Family-Rotation.
  - Der PF8-Linkage-Report wurde neu geschrieben und weist für alle drei
    aktiven Kandidaten eine `generalisiert`-Entscheidung mit
    `CircleBackground`-Seed aus.

## 3) Sichernde Tests und Checks

- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0870-after2 --start AC0870_S --end AC0870_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`
- Ergebnis:
  - Exit `0`
  - `conversion_bestlist.csv`: `error_per_pixel=0.12578765`,
    `mean_delta2=4968.879883`, `std_delta2=7706.695312`
  - Das SVG rendert den Kreis zentriert mit `cx=7.5000`, `cy=7.0000`,
    `r=6.0000` und das `T` als Pfad bei `translate(4.5000,3.5000)`.
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report plan-b-perception-linkage --output-dir artifacts/evaluation/plan_b_perception_linkage_v1`
- Ergebnis:
  - Exit `0`
  - PF8-Linkage-Report enthält `AC0836_S`, `AC0835_S` und `AC0850_M`, jeweils
    `decision=generalisiert`.
- Befehl:
  - `python -m pytest -q tests/test_plan_b_perception_linkage.py tests/test_image_composite_converter.py::test_make_badge_params_ac0870_s_uses_centered_t_badge_seed`
- Ergebnis:
  - Exit `0`
  - `3 passed`

## 4) Kandidatenrotation

- `AC0870_S.jpg` wurde aus der aktiven Plan-B-Liste entfernt.
- `AC0850_M.jpg` ist nun der nächste reguläre Kandidat.
- `AC0836_S.jpg` bleibt als Kreis-/VOC-/Vertikalgriff-Kandidat aktiv.
- `AC0835_S.jpg` wurde als nächster AC08-Weak-Family-Kandidat ergänzt.

## 5) Fazit

Run NE schließt `AC0870_S.jpg` semantisch ab: Die Konvertierung startet und
endet nun mit einem zentrierten Kreis-/T-Seed statt mit einer durch Textmasken
verzogenen Ersatzpose. Der Pixel-Fehler bleibt wegen Antialiasing und
Glyphenrasterung sichtbar, sinkt im dokumentierten Einzelrun aber gegenüber dem
Vorlauf von `mean_delta2=6242.066895` auf `4968.879883` und wird nicht als neuer
Blocker für die Semantik gewertet.
