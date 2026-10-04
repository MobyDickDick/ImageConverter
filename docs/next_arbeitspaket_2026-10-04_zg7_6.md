# Nächstes Arbeitspaket – ZG7.6 Plan-B-Pilot ohne Sonderwissen (2026-10-04)

Dieses Paket schließt die dokumentierte ZG7-Folge mit dem aktuellen
Plan-B-Spitzenkandidaten ab. Der Pilot verwendet ausschließlich Bild und die
katalogfreie Beschreibung eines grünen Farbfelds mit Rand und dachförmiger
Polyline. Weder der Algorithmus noch sein Primitive-Builder erhalten eine
Katalogkennung.

## Ein Algorithmus-/Primitive-Track

Der Track `envelope_polyline_over_vertical_color_field_v1` erzeugt ein
skalierbares Rechteck mit vertikalem Farbverlauf sowie eine zusammenhängende
Polyline. Die allgemeine Kantenkorrektur nutzt eine dünne helle Randkontur und
eine dachförmige Polyline mit größenabhängiger Schulterlage; sie erhält
weiterhin keine Fall- oder Katalogkennung. `tools/run_plan_b_pilot.py` misst
das gespeicherte SVG nach dem erneuten Rendern. Als Holdout dient die
strukturell entsprechende kleinere Rastervariante; im Manifest und Report
trägt sie bewusst den fremden Namen `renamed_holdout`.

## Vorher/Nachher und Gates

| Rolle | Fall | normalized MSE vorher | normalized MSE nachher | Edge-Alignment nachher | Good-Solution | Quality-Complexity |
|---|---|---:|---:|---:|---|---|
| Pilot | `pilot_target` | 0,183361 | 0,019818 | 0,722800 | bestanden | bestanden |
| Holdout | `renamed_holdout` | 0,044143 | 0,022540 | 0,750983 | bestanden | bestanden |

Beide Läufe sind technisch beendet, verbessern Pixel- und Kantenmetrik und
bestehen nach dem erneuten Rendern sowohl das Good-Solution- als auch das
Quality-Complexity-Gate. Das Ergebnis ist deshalb erstmals ein positiver
ZG7.6-Pilotbefund. Der Holdout wird nicht schlechter; die Entscheidung hängt
nicht an einem Prozess-Exit, sondern an den gespeicherten SVGs und den beiden
harten Gates.

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

ZG7.6 ist als Pilot und Entscheidungspunkt abgeschlossen. Der nächste
Plan-B-Schritt kann zur Rotation nach `AC0713_1_S` weitergehen; ein
katalogspezifischer Patch für `AC0554_2_L` ist durch diesen Befund nicht
gerechtfertigt.
