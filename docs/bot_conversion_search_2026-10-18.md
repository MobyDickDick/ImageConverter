# Kooperatives Bot-Modell für die Konvertierung

Die adaptive Parametersuche verwendet sechs Bots je angeschlossenem Modell.
Sie laufen abwechselnd in Abschnitten mit höchstens acht neuen Vorschlägen.
Jeder besitzt einen eigenen Suchzustand. Das sind algorithmische Sucharbeiter
im Konverter; sie benötigen keine Sprachmodell- oder Netzwerkaufrufe.

| Bot | Vorgehen |
|---|---|
| `reverse_coordinates` | Einzelparameter in umgekehrter Reihenfolge verändern |
| `shuffled_coordinates` | Einzelparameter in durch den Seed bestimmter Reihenfolge verändern |
| `fine_coordinates` | Kleine Schritte für die Feinregistrierung |
| `joint_restart` | Mehrere Parameter gemeinsam ändern; auch vom unabhängigen Start aus |
| `geometry_pair` | Zwei Geometrieparameter gemeinsam ändern |
| `color_pair` | Zwei Farbparameter gemeinsam ändern |

## Austausch und Abschaltung

Ein gemeinsames Blackboard hält den besten zulässigen Kandidaten sowie alle
bereits geprüften Parametervektoren mit Verlust, Fehler und Zulässigkeit.
Aktive Bots übernehmen Verbesserungen vor ihrem nächsten Abschnitt. Das
Ereignis `bot_message` protokolliert Absender und Empfänger. Eine Übernahme
allein gilt nicht als eigener Fortschritt und verlängert kein Bot-Budget.

Ein Bot wird nach einem eigenen Geduldsfenster ohne deutliche Verbesserung
deaktiviert. Standardmäßig sind dies 21 neue Messversuche (128 / 6, abgerundet).
Kleine Verbesserungen können sich bis zur bisherigen Ein-Prozent-Schwelle
aufsummieren. Fehlende Parameter und erschöpfte neue Vorschläge deaktivieren
ihn ebenfalls. Andere aktive Bots dürfen weiterarbeiten. Der Status
`all_bots_inactive` beendet die zusätzliche Suche für diesen Modellstart;
ein Wiederholungsaufruf startet diese Bots nicht neu. Andere Modellstarts und
die übergeordnete Qualitätssteuerung behalten ihre eigenen Entscheidungen.
Ein besserer Zwischenstand bedeutet weiterhin keine Qualitätsfreigabe.

Das Blackboard und deaktivierte Bots bleiben im aktiven Bildkontext erhalten.
Ein erneuter Aufruf desselben Suchvertrags verwendet den Zwischenstand und
prüft bekannte Vektoren nicht erneut. Der Vertrag enthält Quellpixel,
Modellkennung, Start-SVG, Startparameter, Startbewertung, Parameteraufteilung,
Seed und Budget. Andere Bilder oder Modellstarts erhalten eigene Zustände.
Auch ein wiederverwendetes SVG muss die aktuellen semantischen Prüfungen
bestehen. Die vorgelagerte Koordinatenregistrierung besitzt weiterhin ihren
eigenen Rendercache; dieser neue Speicher gehört zur zusätzlichen Botsuche.

Im Speicher bleiben kompakte Messergebnisse aller Versuche und höchstens die
besten Raster der Bots erhalten. Die Zeitsteuerung und Vorschlagsgrenzen
begrenzen die Suche. Bei konfiguriertem Suchordner enthält `search/bots/*.json`
zusätzlich die Versuche samt inaktiven Bots. Diese Belege werden bei späteren
Konvertierungen nicht eingelesen. `semantic-only` kann daher das Gedächtnis
des aktuellen Bildes nutzen, ohne gespeicherte Vorlagen zu lesen.

## Grenzen

Die bestehenden Einstellungen gelten weiter: 60 Sekunden reguläre aktive
Bildzeit, bei spätem deutlichem Fortschritt höchstens 120 Sekunden.
`--search-budget` bleibt das gemeinsame Basisbudget der zusätzlichen Suche
je Modell, bei Fortschritt höchstens vierfach. Sechs Bots erhalten zusammen
dieses Budget; es wird nicht versechsfacht. Auch beim Mindestbudget 32 erhält
jeder Bot einen ersten Abschnitt, sofern zuvor weder Erfolg noch Zeitende
eintritt. Ein Seed reproduziert die Folge bei gleichem Ablauf.

`--search-policy fixed` behält den bisherigen Vergleichsablauf. Der neue
Scheduler arbeitet kooperativ und unterbricht einen blockierten nativen
Renderer weiterhin nicht. Die bestehende externe Prozessgrenze des
Katalogrunners bleibt dafür notwendig. Einzelheiten:
[adaptive Zeitsteuerung](adaptive_conversion_search_2026-10-18.md).

## Nächste algorithmische Verbesserung

Der nächste sinnvolle Ausbau ist aus unserer Sicht ein **Bot für unerklärte
Bildbereiche**: Er vergleicht das gerenderte Zwischenresultat mit dem Raster,
sucht zusammenhängende Restfehler und schlägt dort eine zusätzliche Grundform,
einen fehlenden Anschluss oder den Austausch einer Form vor. Beschreibung,
Objektzahl, Beziehungen und Komplexitätsgrenze müssen jede Strukturänderung
begrenzen. Eine kleine Menge verschiedener Szenen sollte erhalten bleiben,
damit nicht alle Bots dieselbe falsche Struktur optimieren.

Dies ist eine aus dem vorhandenen Code abgeleitete Empfehlung und noch keine
implementierte allgemeine Struktursuche. Die aktuelle Botsuche verändert
Parameter vorhandener Modelle. LIVE zeigt einen veröffentlichten Ansatz für
schichtweisen SVG-Aufbau unter Berücksichtigung der Bildtopologie:
[LIVE, CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Ma_Towards_Layer-Wise_Image_Vectorization_CVPR_2022_paper.html).
Für eine spätere gemeinsame Geometrie-/Farboptimierung ist differenzierbares
Rendern eine weitere untersuchenswerte Richtung:
[DiffVG, SIGGRAPH 2020](https://people.csail.mit.edu/tzumao/diffvg/).
Beide Verfahren ersetzen die bestehenden unabhängigen Qualitätsprüfungen nicht.

## Prüfung

Die Regressionen in `tests/test_conversion_search_bots.py` prüfen Austausch,
Abschaltung, erhaltene Fehlschläge, Wiederholungen, Bild-/Modelltrennung,
gemeinsame Grenzen, aktuelle Semantik und das Verlassen einer Falle, aus der
Einzelparameteränderungen nicht herausführen. Die bereits vorhandenen
Steuerungstests prüfen zusätzlich begrenzte Verlängerungen mit injizierter Uhr.
Echte CLI-Gegenproben und der abschließende Teststand stehen im zugehörigen
Nachweisbericht unter `artifacts/evaluation/bot_search_v1/`.

Ergebnis dieses Laufs: **274/274 betroffene Tests** und **8/8 adaptive echte
CLI-Fälle** bestehen. Die CLI-Protokolle enthalten 20 Verbesserungsnachrichten
und sechs individuelle Bot-Abschaltungen. Die acht Ausgaben bestehen die
unabhängigen strengen Pixelgates und die jeweilige Objekt-/Textprüfung;
der Zugriffswächter meldet keine verbotenen Referenz-SVG-Lesezugriffe.
Der ausgewählte Lux-Fit benötigt 250 Renderaufrufe gegenüber 492 im festen
Vergleich. Die 377 bestehenden Archivpaare und ihre Metadaten stimmen mit den
vorherigen Prüfsummen überein. Es wurde keine neue Konvertierung des gesamten
Archivs und kein vollständiger Repository-Testlauf durchgeführt.
