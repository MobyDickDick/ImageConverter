# Arbeitspaket – GE1003_M Haken vor grauer Kreisscheibe (2026-10-05)

Der erste offene Kandidat nach dem Quadrat-P-Recheck ist abgeschlossen.
Die Registrierung verwendet das aktuelle Raster und eine eigenständige
Beschreibung, ohne Katalogkennungen in der Runtime oder Zugriff auf Sample-SVGs.

## Ursache und Beschreibungsqualität

Die bisherige XML verweist ausschließlich auf andere Katalogbilder:
„Hintergrund GE1002, Vordergrund Haken wie in GE1001“. Damit fehlen dem
Zwei-Quellen-Vertrag die Hintergrundgeometrie und eine eigenständige Hakenbeschreibung.
Der vorhandene Hakenpfad erzeugt einen weißen Hintergrund und feste Startpunkte;
er registriert die überlagerte Kreisscheibe nicht.

Die gemeinsame Beschreibung für M, L und S lautet jetzt:
**„Grüner Haken aus zwei dicken schrägen Liniensegmenten mit kurzem linken und
langem rechten Schenkel. Dahinter liegt unten eine graue Kreisscheibe mit grauem
Rand und radialem Helligkeitsverlauf, innen hell und außen dunkler. Weißer
Hintergrund.“** Die Beschreibung bestimmt die Topologie; Maße, Lage,
Hakenfarbe und Scheibenfarben stammen aus dem Raster.

## Allgemeiner Algorithmus und Rendervertrag

Der Beschreibungspfad ergänzt eine `CircleBackground` hinter dem vorhandenen
zweischenkligen Haken, wenn ausdrücklich eine Kreisscheibe beschrieben ist.
Unbeschriftete Haken auf Weiß und Checkboxen behalten ihren bisherigen Pfad.
Die Scheibe besitzt einen nativen SVG-Radialverlauf mit drei Farbstopps.

`imageCompositeConverterCheckmark.py` findet die zusammenhängende grüne
Rasterkomponente anhand ihres Grünüberschusses. Eine Regression zweier Geraden
auf die gewichteten Spaltenmittel liefert kurzen Schenkel, Knick und langen
Schenkel. Die größte neutrale Komponente liefert den sichtbaren unteren
Scheibenbogen; dessen Durchmesser rekonstruiert die verdeckte Oberseite.
Die Farbstopps und Randfarbe werden aus radialen Rasterzonen geschätzt.

Eine begrenzte Suche mit höchstens `169` Renderproben registriert Scheibenlage,
Durchmesser, Randbreite, drei Hakenpunkte und die Breite von Haken und neutraler
Außenkontur. Reihenfolge, verbundene Schenkel und Scheibenproportionen bleiben
erhalten. Die Suche exportiert keine Rasterkontur. Sie akzeptiert ausschließlich
einen endlichen, strikt kleineren Renderfehler und verändert ihre Eingabe nicht.
Für diese Topologie entfallen vorgelagerte unabhängige Elementprobes des
allgemeinen Optimierers, weil sie Hintergrund und Überlagerung verzerren können.

Der Produktionsrenderer PyMuPDF zeichnet native SVG-Radialverläufe teilweise
schwarz. Der katalogfreie Adapter
`_expand_centered_radial_gradients_for_fitz` ersetzt deshalb ausschließlich
im privaten Renderinput zentrierte radiale Kreis-/Ellipsenfüllungen durch
konzentrische Vektorfüllungen. Das gespeicherte SVG behält **eine Ellipse mit
nativem Radialverlauf**, zwei Hakenpfade und den weißen Hintergrund.
Nicht unterstützte verschobene, transformierte oder transparente Verläufe
werden nicht stillschweigend umgedeutet.

Die Registrierung ist auf einen grünen, nach rechts oben gerichteten Haken
vor einer weitgehend neutralen, annähernd runden Scheibe begrenzt. Beliebige
Hakenfarben, Drehungen und andere Hintergrundtopologien sind nicht nachgewiesen.
JPEG-, Kontur- und Antialiasing-Restfehler bleiben sichtbar; auch die bestehende
CLI-Warnung über konzentrierte Restfehler bleibt erhalten.

## Harte Abnahme an gespeicherten CLI-SVGs

Ziel und Größen-Holdouts laufen mit fremden Dateinamen, Seed `0`, derselben
korrigierten Beschreibung und `semantic-only`. Der kontrollierte Vorlauf
deaktiviert ausschließlich die neue Rasterregistrierung; Beschreibung,
Renderadapter und Optimiererrouting entsprechen dem Nachlauf. Die historische
Review-Metrik `17817,699219` gehört zu einer anderen Sammelausgabe und wird
nicht als kontrollierter Vorlauf ausgegeben.

| Rolle | mean_delta2 vorher | mean_delta2 nachher | normalized MSE | Edge-Alignment | Masken-IoU | Beide Gates |
|---|---:|---:|---:|---:|---:|---|
| Ziel M | 14698,368164 | 401,955200 | 0,002061 | 0,922646 | 0,950943 | bestanden |
| Holdout L | 15251,604492 | 435,635559 | 0,002233 | 0,854600 | 0,958549 | bestanden |
| Holdout S | 13350,464844 | 742,352478 | 0,003805 | 0,899163 | 0,938202 | bestanden |

Alle Pflichtmetriken verbessern sich oder bleiben unverändert. Die Grenzen
beider Gates bleiben unverändert. Der unabhängige Semantikcheck verlangt eine
neutrale radiale Scheibe hinter dem grünen Haken, dessen kurzen linken und
längeren rechten Schenkel sowie eine verbundene Außenkontur. Falsche Farbe,
falsche Schenkelrichtung, abgetrennte Scheibe, vertauschte Ebenen und zusätzliche
Primitive bestehen den Check nicht. Ein identisch gerendertes PNG/SVG-Paar
kalibriert Fehler, Kanten, Maske, Semantik und Dimensionen auf ihre Idealwerte.

## Perception-Lerneffekt: generalisiert

Ziel und zwei Größen-Holdouts bestehen beide harten Gates ohne Regression.
Synthetische Variationen sichern zwei Grüntöne, verschobene Lage und doppelte
Größe. Fehlender Haken, fehlende Scheibe, konstante Fehler und nicht endliche
Fehler erzeugen keinen akzeptierten Fit. Runtime-Tests verbieten Sample-SVGs
und Raster-Embedding und belegen identische SVGs nach Umbenennung.

## Belege und Reproduktion

Manifest, versiegelte Baseline, sechs eingefrorene CLI-SVGs, Quell-/Artefakthashes,
CLI-Logs und Gatebericht liegen in
`artifacts/evaluation/checkmark_disk_recheck_v1/`. Zwei unabhängige CLI-Läufe
reproduzieren alle SVG-Bytes und Gateentscheidungen exakt.

Der verbindliche Abschluss umfasst `compileall` für `src`, `tests`, `tools`,
CLI-Help-Smoke, die Runtime-ID-Nullprüfung und das vollständige Defaultprofil.
**268 fokussierte Tests ohne Skips/Warnungen** und **1532 bestandene Tests
mit 29 bestehenden Windows-Skips im vollständigen Defaultprofil** sind grün.
Die Skips betreffen die POSIX-Shell-Integration. Die bekannte defekte lokale `.venv`
wird mit isoliertem CPython `3.12.14` und kompatiblen temporären Abhängigkeiten
umgangen: NumPy `2.5.3`, OpenCV `4.14.0`, PyMuPDF `1.26.7`. Ein temporärer
Bootstrap lädt diese Abhängigkeiten auch in Test-Unterprozessen vor.

In einer funktionierenden Umgebung mit `requirements-dev.txt`:

```bash
python -m tools.run_checkmark_disk_recheck \
  artifacts/evaluation/checkmark_disk_recheck_v1/manifest.json \
  --output-dir .tmp/checkmark-disk-reproduction
python -m tools.evaluate_checkmark_disk_recheck \
  artifacts/evaluation/checkmark_disk_recheck_v1/manifest.json \
  --output .tmp/checkmark-disk-gates.json
python -m compileall src tests tools
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Der erneuerte Review über `688` renderbare Paare liegt in `full_review/`.
`review_reproduction_2026-10-05.json` hält den vollständigen Aufruf inklusive
aller Ausschlüsse als Argumentliste fest.
Die bereits separat belegten Gate-Passes werden aus der Kandidatenauswahl
ausgeschlossen, weil die historische Sammelausgabe weiterhin alte SVGs enthält.
Die Rotation beginnt jetzt mit **`AC0404_1_L`**, gefolgt von `GE9011_6M`,
`AC0404_1_S`, `GE0281` und `GE0300`.
