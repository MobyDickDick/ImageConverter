# Arbeitspaket – AC0404_1_L Links-Dreieck im Kreis (2026-10-05)

Der erste offene Kandidat nach dem Haken-/Scheiben-Recheck ist abgeschlossen
auf dem separaten Branch `codex/ac0404-plan-b`.

## Ursache und tatsächlicher Vorlauf

Der historische Kandidatenwert `mean_delta2=17112.675781` stammt aus einer
alten Sammelausgabe. Das tatsächlich erzeugte aktuelle CLI-SVG erreicht bereits
vor der Änderung `89.825623` und besteht beide harten Gates. Dieser Wert bleibt
unverändert; er wird nicht als neue Qualitätsverbesserung ausgegeben.

Vier ergänzende SIA-Varianten fallen hingegen durch: Die konvexe Hülle eines
gekrümmten Kreissegments vereinfacht sich ebenfalls zu drei Punkten. Die
bisherige Erkennung akzeptiert dessen Fläche auch dann, wenn sie deutlich
größer als die Dreiecksfläche ist. Zusammen mit dem echten Innen-Dreieck
entstehen zwei Kandidaten, die Registrierung verwirft die mehrdeutige Szene.

Die gemeinsame XML enthielt außerdem ausschließlich Katalogreferenzen und
eine relative Drehung. Sie beschreibt nun eigenständig:
**„Pumpensymbol: Kreis mit einem gefüllten Dreieck, dessen Spitze nach links
zeigt. Weißer Hintergrund.“** Farben, Maße und Lage stammen aus dem Raster.

## Allgemeiner Algorithmus

Die vorhandene Kreis-/Dreieckregistrierung bleibt erhalten. Zusätzlich muss
das Verhältnis der beobachteten Regionsfläche zur vereinfachten Dreiecksfläche
zwischen `0.8` und `1.25` liegen. Die obere Schranke verwirft gekrümmte
Kreissegmente; die Toleranz erhält kleine, antialiaste Dreiecke. Weder
Dateinamen noch Katalogkennungen oder gespeicherte Konturen bestimmen die
Entscheidung. Die begrenzte Render-/Fehlersuche ermittelt weiterhin Geometrie
und Farben aus dem Raster. Das SVG enthält genau eine Ellipse und ein Polygon.

Der Geometry-IR-Seed übernimmt außerdem ausdrücklich beschriebene Richtungen
`links`, `rechts`, `oben`, `unten`. Absolute Richtungen haben Vorrang vor
relativer Drehungsprosa; unbestimmte historische Beschreibungen behalten ihren
vorherigen Seed. Der unabhängige SVG-Semantikcheck unterstützt dieselben vier
Richtungen und verwirft ein Dreieck in der falschen Richtung.

Die Registrierung bleibt auf einen annähernd runden Körper mit einem einzelnen
kontrastierenden Dreieck beschränkt. Texte, Griffe und andere Innenformen
werden nicht in diese Topologie umgedeutet. JPEG-/Antialiasing-Restfehler und
die bestehende CLI-Warnung über konzentrierte Differenzpixel bleiben sichtbar.

## Harte Abnahme an gespeicherten CLI-SVGs

Ziel und 17 Prüfvarianten laufen mit fremden Dateinamen, Seed `0`,
`semantic-only` und dem Produktionsrenderer. Der Vorlauf verwendet die alte
Beschreibung und die am Ausgangscommit eingefrorene Kreis-/Dreieckregistrierung.
Die übrige Runtime entspricht dem Nachlauf; die neue absolute Richtungsregel
greift für die alte Beschreibung nicht. Das Manifest hält Revision und Hash
des alten Fitters sowie die aktuellen Quellhashes fest. Baseline und beide
SVG-Ausgaben liegen eingefroren im Repository.

| Variante | mean_delta2 vorher | mean_delta2 nachher | Edge-Alignment nachher | Masken-IoU nachher |
|---|---:|---:|---:|---:|
| Ziel AC0404_1_L | 89,825623 | 89,825623 | 0,937732 | 0,973225 |
| AC0404_1L_sia | 12225,253906 | 82,056877 | 0,883906 | 0,979570 |
| AC0404_2L_sia | 10594,894531 | 331,403748 | 0,822943 | 0,983731 |
| AC0404_L_sia | 7995,996094 | 132,243744 | 0,949414 | 0,942901 |
| AC0404_S_sia | 6756,424805 | 136,005005 | 0,945217 | 0,916667 |

Alle 18 Varianten bestehen beide unveränderten Qualitätsgates ohne
Metrikregression. Vier verbessern sich, die übrigen 14 bleiben metrisch
unverändert. Der maschinenlesbare Report enthält jede einzelne Variante.
Ein identisch gerendertes Links-Dreieck-PNG/SVG-Paar kalibriert Pixel,
Kanten, Maske, Semantik und Dimensionen auf ihre Idealwerte.

## Perception-Lerneffekt: generalisiert

Die flächenbasierte Abgrenzung erkennt das echte Dreieck auch dann, wenn der
Kreishintergrund ebenfalls eine dreieckige Näherung besitzt. Die Prüfung gilt
für rote, grüne und graue Körper, Größen von 20 bis 40 Pixeln und unterschiedliche
Dreiecksflächen. Synthetische Tests sichern weitere Farben, verschobene Lage,
doppelte Größe und vier Richtungen. Runtime-Tests verbieten Sample-SVG-Zugriff
und Raster-Embedding; identische Pixel und Beschreibungen erzeugen unter
verschiedenen Namen identische SVGs. Rechteck, Punkt, fehlendes Dreieck,
widersprüchliche Richtung und zusätzliche beschriebene Objekte werden verworfen.

## Belege und Reproduktion

`artifacts/evaluation/left_pump_recheck_v1/` enthält Manifest, versiegelte
Baseline, 36 gespeicherte CLI-SVGs, CLI-Logs, Gatebericht und Reproduktionsbeleg.
Zwei unabhängige CLI-Läufe erzeugen exakt dieselben 36 SVG-Bytes, dieselbe
Baseline und dieselben Gateentscheidungen. `471` fokussierte Tests sind grün.
Das vollständige Defaultprofil meldet `1556 passed, 29 skipped` ohne Warnungen;
die 29 Skips betreffen die bestehenden POSIX-Shell-Tests unter Windows.
`compileall` für `src`, `tests`, `tools`, CLI-Help-Smoke und die absolute
Runtime-ID-Nullprüfung sind ebenfalls grün (`0 occurrences`). Die Loghashes
und Einzelurteile stehen in `completion_checks_2026-10-05.json`.

Mit funktionierenden Abhängigkeiten aus `requirements-dev.txt`:

```bash
python -m tools.run_pump_recheck \
  artifacts/evaluation/left_pump_recheck_v1/manifest.json \
  --output-dir .tmp/left-pump-reproduction
python -m tools.evaluate_pump_recheck \
  artifacts/evaluation/left_pump_recheck_v1/manifest.json \
  --output .tmp/left-pump-gates.json
python -m compileall src tests tools
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Die bekannte defekte lokale `.venv` wird mit isoliertem CPython `3.12.14`
und kompatiblen temporären Abhängigkeiten umgangen: NumPy `2.5.3`, OpenCV
`4.14.0`, PyMuPDF `1.26.7`. Ein temporärer Bootstrap lädt die Abhängigkeiten
auch in Test-Unterprozessen vor. Die ersten beiden Umgebungsausfälle des
Defaultprofils wurden auf den Windows-PYTHONPATH-Aufbau zurückgeführt und
mit korrigiertem Bootstrap erneut geprüft.

Der erneuerte Review enthält `688` Einträge, davon `684` renderbare Paare.
Die vier bereits vorher fehlenden SVG-Paare sind im Report weiterhin markiert.
Alle separat belegten Gate-Passes werden aus der Kandidatenauswahl ausgeschlossen;
der genaue Aufruf steht in `review_reproduction_2026-10-05.json`.
Die nächste Rotation beginnt mit **GE9011_6M**, gefolgt von GE0281, GE0300,
GE1420_S und AC0403_1_L.
