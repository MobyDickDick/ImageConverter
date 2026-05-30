# Qualitätsreview bisher konvertierter Bilder – 2026-05-30

## Ziel

Die bisher als erfolgreich geführten Konvertierungen aus `successed_conversions.txt`
wurden erneut gegen die vorhandenen Originalbilder und SVG-Artefakte geprüft. Ziel
war eine schnelle Entscheidung, ob einzelne Bilder erneut auf die Konvertierungs-
oder Plan-B-Aufgabenliste müssen.

## Prüfmethode

- Kandidatenbasis: alle 48 Varianten aus `successed_conversions.txt`.
- Bildsuche: `artifacts/images_to_convert`, `artifacts/images_to_convert/nonconvertable`,
  `artifacts/regression_baseline/satisfactory/images`.
- SVG-Suche: `artifacts/converted_images/converted_svgs`,
  `src/artifacts/converted_images/converted_svgs`,
  `artifacts/regression_baseline/satisfactory/svgs`.
- Render-/Pixelvergleich: SVG wurde mit `Action.renderSvgToNumpy` auf die jeweilige
  Originalgröße gerendert; ausgewertet wurden `mean_delta2`, `normalized_mse`
  (`mean_delta2 / (3 * 255²)`) und kanalbezogener RMSE.
- Qualitätsgrenze: als pragmatische Review-Grenze wurde die vorhandene
  Satisfactory-Konfiguration `0.045945679012345676` aus
  `src/artifacts/converted_images/reports/quality_tercile_config.json` genutzt.

Ausgeführter Prüfcode:

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. python3 - <<'PY'
from pathlib import Path
import csv, cv2, numpy as np
from src.imageCompositeConverter import Action
search_img=[Path('artifacts/images_to_convert'),Path('artifacts/images_to_convert/nonconvertable'),Path('artifacts/regression_baseline/satisfactory/images')]
search_svg=[Path('artifacts/converted_images/converted_svgs'),Path('src/artifacts/converted_images/converted_svgs'),Path('artifacts/regression_baseline/satisfactory/svgs')]
variants=[l.strip() for l in Path('successed_conversions.txt').read_text().splitlines() if l.strip()]
def find(paths,v,ext):
    for d in paths:
        p=d/f'{v}{ext}'
        if p.exists(): return p
    return None
rows=[]
for v in variants:
    imgp=find(search_img,v,'.jpg'); svgp=find(search_svg,v,'.svg')
    logp=Path('artifacts/converted_images/reports')/f'{v}_element_validation.log'
    status='missing_log'
    if logp.exists():
        for line in logp.read_text(errors='replace').splitlines():
            if line.startswith('status='):
                status=line.split('=',1)[1].strip(); break
    if not imgp or not svgp:
        rows.append([v,status,str(imgp or ''),str(svgp or ''),'','','','missing_pair']); continue
    img=cv2.imread(str(imgp)); render=Action.renderSvgToNumpy(svgp.read_text(errors='replace'), img.shape[1], img.shape[0])
    if render is None:
        rows.append([v,status,str(imgp),str(svgp),'','','','render_failed']); continue
    d2=np.sum((img.astype(np.float32)-render.astype(np.float32))**2,axis=2)
    mean=float(np.mean(d2)); norm=mean/(3*255*255); rmse=(mean/3)**0.5
    rows.append([v,status,str(imgp),str(svgp),f'{mean:.6f}',f'{norm:.8f}',f'{rmse:.6f}','ok'])
print('count',len(rows),'missing',sum(1 for r in rows if r[-1]!='ok'))
print('over_threshold',[r[0] for r in rows if r[-1]=='ok' and float(r[5]) > 0.045945679012345676])
print('missing_pairs',[r[0] for r in rows if r[-1]!='ok'])
PY
```

## Ergebnisübersicht

| Kategorie | Anzahl | Bewertung |
| --- | ---: | --- |
| Varianten in `successed_conversions.txt` | 48 | vollständige Review-Basis |
| Renderbare Bild/SVG-Paare | 47 | erneut pixelmetrisch geprüft |
| Fehlende Bild/SVG-Paare | 1 | nicht zufriedenstellend, muss erneut auf die Aufgabenliste |
| Varianten mit `semantic_ok`-Validierungslog | 16 | fachlich zusätzlich bestätigt |
| Varianten ohne aktuelles Validierungslog | 32 | nicht automatisch schlecht, aber nur pixelmetrisch geprüft |
| Varianten oberhalb der Review-Grenze | 1 | nicht zufriedenstellend, muss erneut auf die Aufgabenliste |
| Nahe an der Review-Grenze | 1 | Beobachtung, noch keine Re-Konvertierungsaufgabe |

## Nicht zufriedenstellende Befunde

| Variante | Befund | Messwert | Konsequenz |
| --- | --- | ---: | --- |
| `AC0838_M` | Renderbares Paar vorhanden, aber `normalized_mse` überschreitet die Review-Grenze. | `0.04729276` | Re-Konvertierung/Plan-B-Verbesserung einplanen. |
| `AC0881_M` | Originalbild vorhanden, aber kein passendes SVG-Artefakt in den geprüften Konvertierungs-/Baseline-Pfaden. | n/a | SVG-Artefakt rekonstruieren oder Variante erneut konvertieren. |

## Grenzfall ohne neue Aufgabe

| Variante | Befund | Messwert | Entscheidung |
| --- | --- | ---: | --- |
| `AC0835_S` | Knapp unterhalb der Review-Grenze. | `0.04467485` | Beobachten, aber vorerst nicht auf die Re-Konvertierungsliste setzen. |

## Aufgabenrückpflege

Die nicht zufriedenstellenden Varianten wurden in `PLAN_B_KANDIDATEN.md` als aktive
Plan-B-/Re-Konvertierungskandidaten ergänzt und in `docs/open_tasks.md` als neue
Review-Folgeaufgaben dokumentiert.
