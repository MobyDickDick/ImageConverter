# AC0140_M: eigene Rekonstruktion und begrenztes Linienpaar

`comparison.png` zeigt das Original, den bisherigen falschen Entwurf und den
neuen regulären Vorlagenlauf auf derselben Rastergrösse, jeweils dreifach ohne
Interpolation vergrössert. `comparison.json` enthält die nachträgliche Messung
der tatsächlichen SVG-Ausgaben und SHA-256-Werte der Eingaben und Ausgaben.

Der neue Vorlagenworker lief 45 Sekunden mit Seed 17. `template-result.svg`
ist sein bestes gültiges Ergebnis; `template-result.json` ist sein Bericht.
Der normalisierte Pixelfehler sank von 0.002431 auf 0.000449, die Kantendeckung
stieg von 0.8263 auf 0.9196. Das strengere Suchziel ist weiter offen. Das
Ergebnis wurde zur Prüfung hier abgelegt; die Projektablage wurde nicht ersetzt.

`AC0140_M.svg` und `AC0140_L.svg` sind separate direkte Prüfungen des korrigierten
Beobachters und Fitters. Die M-Konstruktion wird aus den M-Pixeln geschätzt.
Die Beschreibung im Vorlagenlauf ist als `description.txt` eingefroren.

Die aktuelle Prüfung besteht aus 123 Kern- und 270 weiteren Anwendungstests,
ohne Überschneidung der Testdateien. `core-tests.log` und `application-tests.log`
enthalten die Abschlussprotokolle.

Reproduktion des Vorlagenlaufs aus dem Projektverzeichnis:

```powershell
.venv/Scripts/python.exe -m src.imageConverterSample --source artifacts/images_to_convert/AC0140_M.jpg --sample artifacts/evaluation/general_search_expansion_2026-11-16/AC0140_M.svg --output artifacts/evaluation/clipped_parallel_lines_2026-11-17/template-result.svg --description artifacts/evaluation/clipped_parallel_lines_2026-11-17/description.txt --seconds 45 --seed 17
```

[Ursachen, Einbindung und Grenzen](../../../docs/structural_reconstruction_2026-11-17.md).
