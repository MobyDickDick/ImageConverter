# Fortschritt durch andere Konstruktionen

Mehr Seed-Varianten können keine Konstruktion finden, die vor der Suche bereits
verworfen wird oder in der Vorlagensuche gar nicht angeboten wird. Genau diese
beiden Probleme liessen sich an AC0140_M nachweisen.

## Nachgewiesene Ursachen

Die bisherige Beobachtung bestimmte die Mitte der kleinen Raute aus dem
Begrenzungsrechteck ihrer sichtbaren Konturreste. Bei M verdecken die Diagonalen
Teile der Spitzen. Die Schätzung lag deshalb bei ungefähr `(24.5, 110.5)` statt
bei `(25, 115)`. Die daraus berechneten Halbachsen `(20.1, 27.3)` verletzten die
Konturprüfung. M wurde ohne eine einzige Registrierung verworfen; L wurde erkannt.

Die Mitte und beide Halbachsen werden jetzt gemeinsam aus den vier beobachteten
Seiten geschätzt. Sichtbare Spitzen sind dafür nicht erforderlich; Belege für
alle vier Seiten bleiben Pflicht. M liefert damit ungefähr `(24.8, 114.2)` und
Halbachsen `(21.0, 21.3)` vor der eigentlichen Rasteranpassung.

Die Formulierung mit zwei parallelen Linien war zudem nicht mit der älteren
Formulierung einer innen ausgeschnittenen Diagonale gleichgesetzt. Beide
beschreiben jetzt dieselbe prüfbare Beziehung. Die beiden Linien werden als
zwei vollständige schmale Polygone mit dem Rechteck geschnitten. Ein darüber
gemalter Streifen in Hintergrundfarbe ist dafür nicht mehr nötig. Die physisch
drei Diagonalstriche werden nicht mit den zwei logisch beschriebenen Diagonalen
verwechselt; die bestehende sichtbare Strukturprüfung prüft ihre Beziehung.

## Gemeinsame Suche statt Bindung an die Vorlage

Die bestehende Liste vollständiger Rasterrekonstruktionen ist jetzt eine
gemeinsame Registry. Die frische Konvertierung und die native Fortsetzung von
Vorlagen verwenden dieselben eingetragenen Modellfamilien. Eine ungeeignete
Vorlage kann dadurch vollständig ersetzt werden, bevor weitere lokale
Verschiebungen und Löschungen ausprobiert werden. Das gilt für die Registry
insgesamt, ohne einen Dateinamen oder einen M/L-Sonderzweig einzuführen.

Rekonstruktionen teilen das bestehende Bildzeitbudget und Kandidatengedächtnis.
Ein rekonstruiertes SVG muss die vollständige Beschreibung und den Rastervergleich
bestehen. Danach bleibt die gemeinsame Auswahl des besten gültigen Ergebnisses
zuständig. Ein erfolgreicher Modellaufruf allein erteilt keine Freigabe.

Auch die allgemeine Formzählung verwendet jetzt die dargestellten Koordinaten:
Ein durch Gruppentransformation gestrecktes Quadrat ist kein Quadrat mehr; ein
entsprechend gestreckter Kreis ist eine Ellipse. Das betrifft native Elemente
und aus geraden Teilstücken aufgebaute Polygone und Pfade.

Ein zusätzlicher zentraler Renderfehler wurde behoben: SVG wurde bisher mit dem
Dokumenttyp `pdf` geöffnet. Die automatische Erkennung akzeptierte `<svg>`,
verwarf aber gleichwertige Wurzeln wie `<ns0:svg>`. Der Renderer öffnet SVG jetzt
ausdrücklich als `svg`. Gültige Vorschläge hängen damit nicht mehr von einer
vorherigen globalen ElementTree-Namensraumregistrierung ab.

## Reales Ergebnis

Ein regulärer Vorlagenworker erhielt das unveränderte M-JPEG, die aktuelle
Benutzerbeschreibung, den bisherigen falschen M-Entwurf und Seed 17. Er suchte
mit dem vollen schnellen Profil von 45 Sekunden. Die neue Konstruktion wurde
aus dem M-Raster geschätzt. Ein separates L-SVG oder ein gespeichertes Muster
wurde dafür nicht als zusätzliche Referenz geladen.

| Messung | Bisheriger Entwurf | Neuer Vorlagenlauf |
| --- | ---: | ---: |
| Normalisierter quadratischer Pixelfehler | 0.002431 | 0.000449 |
| Kantendeckung | 0.8263 | 0.9196 |
| Vordergrund-IoU | 0.9266 | 0.9553 |

Die tatsächlichen SVGs wurden für diesen Vergleich nochmals auf dem Originalraster
von 50 × 230 Pixeln gerendert. Das neue Ergebnis besteht die Beschreibungsprüfung.
Das strengere interne Suchziel ist noch offen; deshalb wurde das Budget weiter
genutzt. Die Messung belegt einen konkreten Fortschritt bei M und keine universell
korrekte Rekonstruktion beliebiger Motive.

[Vergleichsbild](../artifacts/evaluation/clipped_parallel_lines_2026-11-17/comparison.png),
[SVG](../artifacts/evaluation/clipped_parallel_lines_2026-11-17/template-result.svg),
[Messbericht](../artifacts/evaluation/clipped_parallel_lines_2026-11-17/comparison.json).

Die Regressionen prüfen verdeckte Spitzen an unabhängig erzeugten Motiven,
beide Beschreibungsvarianten, echte begrenzte Linienpaare, die Umkonstruktion
einer falschen Vorlage, unveränderte Pixel bei SVG-Namensraumpräfixen und die
gemeinsame Rekonstruktionsauswahl einschliesslich RGB/BGR und Beschreibungsfehlern.
Die Nachprüfversion gespeicherter GUI-Ergebnisse steigt auf 8; beim nächsten
Serverstart werden alte Ergebnisbewertungen erneut geprüft.

Abschliessend bestanden 393 verschiedene Tests in zwei Läufen: 123 Prüfungen
für Formdarstellung, Strukturwechsel, die reale M-Rekonstruktion und
Renderkompatibilität sowie 270 Prüfungen für Seeds, Beschreibung, Vorlagen,
GUI-Vorschau und -Nachbesserung, vorhandene SVGs und Strichbreiten. Die
Protokolle liegen im Vergleichsverzeichnis.

## Weiterer Ansatz

Die Registry ist weiterhin endlich. Für unbekannte Motive braucht die Suche
allgemein kombinierbare Beziehungen wie „parallel“, „im Rechteck begrenzt“,
„ungefüllt“ und „von einem anderen Objekt verdeckt“. Solche Beziehungen müssen
als gemeinsame geometrische Parameter gelten und durch lokale Bildbelege
geprüft werden. Weitere Zufallsvarianten derselben falschen Objektanordnung
ersetzen diesen Schritt nicht.
