# Arbeitspaket – Quadrat mit oberem Griff, Strich und Punkt (2026-10-10)

Branch: `codex/successful-images-ac0713-2026-10-10`.
Das nächste dokumentierte Ziel `AC0713_1_L` und alle fünf Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.

## Allgemeine Erkennung

Beide XML-Kataloge beschreiben eigenständig das Quadrat, den mittigen oberen
Griff, den Strich von rechts oben nach links unten und den Punkt links neben
dessen unterem Ende. Die bestehende Quadrat-/Griffregistrierung wird auf den
oberen Griff erweitert. Nur Körper und Griff werden für die Registrierung
gedreht; die Innenmarkierung wird in ihrer ursprünglichen Orientierung
beobachtet. Lage, Maße, Konturbreiten und Farben kommen aus dem Eingabebild.
Es gibt keine neue Runtime-Katalogkennung oder hinterlegte Vorlage.

Bei kleinen JPEGs können Randpixel beide Markierungen verbinden. Stärkere
Kontrastkerne oder eine Geradenregression über die oberen Strichzeilen trennen
sie. Die bestehenden Richtungs-, Größen- und Lageprüfungen bleiben verbindlich.
Eine begrenzte Pixelsuche verfeinert die beobachteten Parameter. Das Ergebnis
enthält ein Rechteck und drei native Pfade.

## Frische Abnahme

Der CLI-Vorlauf wurde vor der Änderung mit Originalbeschreibungen und neutralen
Namen eingefroren. Der Reproduktionsrunner schaltet im Vorher-Lauf nur die neue
Registrierung für den oberen Griff ab. Alle sechs Vorher-SVGs bleiben bytegleich.
Gespeicherte Nachher-SVGs werden erneut gerendert; die unabhängige Semantikprüfung
verlangt auch beide Innenmarkierungen. Null verbotene Referenz-SVG-Zugriffe.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0713_1_L | 1972.475586 | 120.847115 |
| AC0713_1_M | 1856.842896 | 97.677139 |
| AC0713_1_S | 2194.829346 | 90.655998 |
| AC0713_L | 7643.030273 | 15.842667 |
| AC0713_M | 6105.064453 | 46.255714 |
| AC0713_S | 7064.728027 | 19.520000 |

**6/6 bestehen Good-Solution- und Quality-Complexity-Gate, null
Pflichtmetrikregressionen.** Manifest, Vorher-/Nachher-SVGs, synthetische
Vorlage und JSON-Nachweis liegen unter
`artifacts/evaluation/top_stem_marked_square_recheck_v1/`.
Die unabhängige Vorlage besteht mit Seed `20261010` **17/17** strenge Plan-B-
Prüfungen. Alle sechs JPGs bestehen auch die zusätzliche strengere Plan-B-
Pixelprüfung. Weitere Tests variieren Farben, Lage, Auflösung und Pixelphasen und
verwerfen fehlende/falsche Markierungen, zusätzliche Objekte, nicht endliche
Daten und fehlendes Rendering. Andere Innenzeichen, der offene Gesamtpool
und die bisherigen Graufall-/U-Bogen-Stressaufgaben bleiben separat offen.

## Erfolgsübersicht und erweiterte Prüfung

`artifacts/satisfactory_conversions/` enthält **146** nachgewiesene Bild-/SVG-
Paare samt Beschreibungen, Qualitätswerten, Quellen und SHA-256-Hashes.
`images/` enthält Originalbildkopien, `svgs/` akzeptierte Vektoren; `README.md`
verlinkt alle Paare. Katalogquellen bleiben für vorhandene Fixtures verfügbar.
Normale erfolgreiche Batches verwenden weiterhin `succesessfulConvertedImages`.

Die Sammlung umfasst regulär akzeptierte Paketfälle und 48 vorhandene,
erneut vermessene Bestenlisteneinträge. Technischer Abschluss allein reicht
für die Aufnahme nicht. Das erweiterte Pytest-Profil konvertiert sämtliche
Einträge auf Wegwerfkopien neu: 98 neuere Fälle in `semantic-only`, 48 ältere
im dokumentierten Kompatibilitätsmodus. Es verwendet die gespeicherte
Beschreibung der jeweiligen Abnahme und prüft die bestehende Reviewgrenze
`normalized_mse <= 0.045945679012345676` sowie den Ausschluss von Raster-SVGs.
Höhere Fehler gegenüber den archivierten Vektoren werden zusätzlich ausgewiesen.
Diese Prüfung ist von den strengeren Paketgates und dem bestehenden
31-Fälle-Bestandsschutz zu unterscheiden.

Die vollständige erneute Konvertierung besteht mit **146/146** Review-Pässen
und null Referenz-SVG-Zugriffen im `semantic-only`-Teil. Alle 98 neueren Fälle
haben unveränderte oder bessere Mean-Delta²-Werte. **22 ältere Einträge**
erzeugen größere Pixelabweichungen als ihre archivierten Vektoren, bestehen
aber weiterhin die Reviewgrenze. Die akzeptierten Vektoren bleiben erhalten;
diese Drift wird im Nachweis `artifacts/satisfactory_conversions/recheck_2026-10-10.json`
einzeln ausgewiesen. Die sechs Bestandsschutztests bestehen mit 31 Varianten
und null Regressionen gegen deren separate Baseline.

Die ursprüngliche Erfolgsablage verschiebt keine Quellen mit fehlenden,
fehlgeschlagenen, eingebetteten Raster- oder leeren Ausgaben. Abweichende
gleichnamige Quellen werden nicht überschrieben; erneutes Prüfen erzeugt keine
verschachtelten Erfolgsordner. Qualitätsreview, Quellenauflösung, Bestandsschutz
und explizite Regressionsauswahl finden auch die dort abgelegten Bilder.

## Reproduktion und Rotation

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_top_stem_square_recheck artifacts/evaluation/top_stem_marked_square_recheck_v1/manifest.json --output-dir .tmp/top-square-reproduction
.venv/Scripts/python.exe -m tools.refresh_satisfactory_archive
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/satisfactory-reproduction
.venv/Scripts/python.exe -m tools.run_pytest_profile extended --basetemp .tmp/extended-reproduction
```

90 fokussierte Tests bestehen. Weitere Abschlussnachweise stehen im JSON-
Nachweis; vollständige Logs liegen lokal unter `.tmp/`. Der erneuerte Review
enthält 1.000 Einträge und 993 renderbare Paare. Alle 48 bisherigen
Erfolgsvarianten bleiben unter der Grenze. Nach Ausschluss erledigter Pakete
ist die nächste reguläre Aufgabe **`AC0721_1_S`**, gefolgt von `AC0711_1_M`,
`GE9014_1M`, `GE9012_1M`, `AC0712_1_S`. Der vollständige Review-Aufruf steht
in `review_arguments.json`.

Der vollständige Standardtestlauf besteht mit **2.075 Tests, 0 Fehlern und
30 Skips** in 1.047,59 Sekunden. 29 Skips betreffen bestehende Windows-/POSIX-
Unterschiede; ein zusätzlicher Skip delegiert die gesamte Archivkonvertierung
an das erweiterte Profil. Die finale Archivabsicherung wurde zusätzlich mit
42 Helper-Tests und dem letzten Nachlauf mit 11 Tests geprüft. Die finale
Runtime-Fassung ist durch 28 fokussierte Tests, alle sechs gespeicherten
Gate-Abnahmen, die Plan-B-Zufallsprüfung und die gesamte Archivkonvertierung
abgedeckt. Syntaxprüfung, CLI-Hilfe, Diff-Prüfung und Runtime-ID-Nullprüfung
bestehen.

Der letzte Quellenauflösungs-Nachlauf besteht mit 16 Tests; er sichert auch
die bisherige JPEG-Priorität bei mehreren Rasterformaten ab. Ein Skip delegiert
die bereits vollständig separat ausgeführte Archivkonvertierung an das
erweiterte Profil.
