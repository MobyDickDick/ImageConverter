# Nächstes Arbeitspaket – ZG7.6 Plan-B-Pilot ohne Sonderwissen (2026-10-04)

Dieses Paket schließt die dokumentierte ZG7-Folge mit dem aktuellen
Plan-B-Spitzenkandidaten ab. Der Pilot verwendet ausschließlich Bild und die
katalogfreie Beschreibung eines grünen Farbfelds mit Rand und dachförmiger
Polyline. Weder der Algorithmus noch sein Primitive-Builder erhalten eine
Katalogkennung.

## Ein Algorithmus-/Primitive-Track

Der Track `envelope_polyline_over_vertical_color_field_v1` erzeugt ein
skalierbares Rechteck mit vertikalem Farbverlauf sowie eine zusammenhängende
Polyline. `tools/run_plan_b_pilot.py` misst das gespeicherte SVG nach dem
erneuten Rendern. Als Holdout dient die strukturell entsprechende kleinere
Rastervariante; im Manifest und Report trägt sie bewusst den fremden Namen
`renamed_holdout`.

## Vorher/Nachher und Gates

| Rolle | Fall | normalized MSE vorher | normalized MSE nachher | Edge-Alignment nachher | Good-Solution | Quality-Complexity |
|---|---|---:|---:|---:|---|---|
| Pilot | `pilot_target` | 0,183361 | 0,020389 | 0,605547 | bestanden | nicht bestanden |
| Holdout | `renamed_holdout` | 0,044143 | 0,021072 | 0,675175 | bestanden | nicht bestanden |

Beide Läufe sind technisch beendet und verbessern die Pixelmetrik deutlich;
auch der Holdout wird nicht schlechter. Trotzdem ist das Ergebnis ausdrücklich
**nicht positiv**: Beide End-SVGs verfehlen das harte Edge-Alignment-Minimum
von `0,72`. Der dominante Fehler ist daher `edge_alignment`, und
`AC0554_2_L` bleibt offen. Ein Exit `0` oder der niedrigere Pixelverlust wird
nicht als Zufriedenheitsbeleg umgedeutet.

Der maschinenlesbare Beleg liegt unter
`artifacts/evaluation/semantic_only_plan_b_pilot_v1/report_2026-10-04.json`.
Er lässt sich reproduzieren mit:

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. python \
  tools/run_plan_b_pilot.py \
  config/semantic_only_zg7_plan_b_pilot_v1.json \
  --output artifacts/evaluation/semantic_only_plan_b_pilot_v1/report_2026-10-04.json \
  --svg-dir artifacts/evaluation/semantic_only_plan_b_pilot_v1/svgs
```

ZG7.6 ist als Pilot und Entscheidungspunkt abgeschlossen. Die nächste Arbeit
soll den allgemeinen Polyline-Kantenfit verbessern; ein katalogspezifischer
Patch oder weiteres Farb-Subpixel-Tuning ist durch diesen Befund nicht
gerechtfertigt.
