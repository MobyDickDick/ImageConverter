# Gemeinsame Erweiterung der Vektorsuche

**Aktualisierung 17. November:** Die nachfolgend dokumentierte Grenze von
48 Konstruktionsrunden wurde aufgehoben. Seed-Weitergabe, Vorlagenzeit und
Darstellungskomplexität sind weiter überarbeitet:
[aktueller Stand](seed_and_simple_forms_2026-11-17.md).

Die Änderung betrifft die Standardsuche für alle Bildnamen und Motivklassen.
Es gibt keine neue Sonderbehandlung für AC0140, keinen Austausch einer
Projektdatei und keine Lockerung der bestehenden Abnahmegrenzen.

## Wechsel statt Wiederholung

Die adaptive Parametersteuerung reaktiviert stagnierende Strategien nicht mehr,
um eine Mindestzeit zu füllen. Registrierungen geben nach ausbleibendem
Fortschritt, einem begrenzten Parameterabschnitt oder spätestens einer kurzen
Zeitscheibe den gemeinsamen Bildetat für andere Konstruktionen frei.
Eine bereits vollständig geprüfte Modelllösung darf sofort zurückkehren.

`continue_native_search` führt eine bildbezogene Suchfront. Auch Verbesserungen
werden in die nächste, breitere Stufe übernommen. Stufe 0 prüft bestehende
Konstruktionsalternativen, Stufe 1 ergänzt Gegenproben durch Entfernen beliebiger
SVG-Objekte. Ab Stufe 2 werden gemeinsames Entfernen, unabhängiges Verschieben,
Grössenänderungen und die Zeichenreihenfolge miteinander verschachtelt geprüft.
Dazu kommen ein neuer Aufbau aus dem Raster und alternative Zwischenstände.
Die bisherige 512-Pixel-Sperre entfällt.

Der beste auslieferbare Stand bleibt von den Versuchsästen getrennt. Dadurch
kann ein schlechterer Zwischenstand untersucht werden, ohne eine bessere
gespeicherte Ausgabe zu verlieren. Ein eingefügter weisser Balken ist kein
geschütztes Konstruktionsprinzip: Auch grosse und verschachtelt transformierte
Elemente können einzeln oder gemeinsam entfernt werden. Bereits gemessene
korrekte Details bleiben durch die vorhandenen lokalen Bildprüfungen geschützt.
Die automatische Linienergänzung erkennt bestehende native Linien und Konturen
auch ohne spezielle Gruppenmarkierung und zeichnet diese nicht einfach nach.

## Bildbezogenes Gedächtnis und Grenzen

Gerenderte Kandidaten werden bildbezogen und unabhängig von der jeweiligen
Bewertungsfunktion wiederverwendet. XML-Attributreihenfolge, Präfixe und einfache
Identitätshüllen erzeugen keinen neuen Kandidaten. Relevante Textabstände und
SVG-Inhalte bleiben Teil der Identität. Semantik und Zielfunktion werden beim
Aufruf erneut geprüft; Renderwiederverwendung ist keine Abnahme.

Strukturgegenproben behalten ihr Gedächtnis über Suchrunden hinweg.
Parameterarbeit innerhalb desselben Elementinventars erhält insgesamt höchstens
288 neue Renderings. Die Erweiterung reserviert Kapazität für unterschiedliche
Operationen, statt alle Versuche auf Löschungen oder Farbänderungen zu verwenden.
Die komprimierte Rasterablage ist auf 32 MiB beziehungsweise 8192 Einträge
begrenzt. Die Suchfront bearbeitet höchstens 48 Konstruktionsrunden innerhalb des
bisherigen Bildzeitlimits. Erschöpfung und Zeitlimit werden getrennt gemeldet;
sie lösen keine identische neue Suchperiode aus.

Ein Bestehen der bisherigen Raster- und Beschreibungsprüfungen bleibt ein
brauchbarer Zwischenstand. Die gemeinsame Fortsetzung strebt die bereits
vorhandene strengere `preferred_quality` an. So friert ein nur knapp grüner
Entwurf die weitere Suche nicht sofort ein. Das Suchende und die Abnahme des
gespeicherten Entwurfs sind getrennte Angaben.

Die Auswahl der Zwischenstände nutzt dieselbe Vergleichsregel wie die
Projektablage: normalisierter Pixelfehler plus `0.2 * (1 - Kantenwert)` plus
`0.1 * (1 - Vordergrund-IoU)`. Ein kleinerer globaler Pixelfehler allein kann
damit keinen sichtbar schlechteren Umriss festschreiben. Vollständig bestandene
Entwürfe haben weiter Vorrang vor nicht bestandenen.

## Einbindung und Nachweis

CLI und Stapelverarbeitung rufen die gemeinsame Fortsetzung beim Schreiben
nativer Versuche auf, einschliesslich fehlgeschlagener Entwürfe und ohne
Voraussetzung einer positiven Mindestzeit. Eine fehlgeschlagene Modellprüfung
wird dadurch nicht nachträglich als bestätigt ausgegeben. Die Vorlagenanpassung
reserviert nach der gemeinsamen Ausrichtung Zeit für dieselbe Fortsetzung.
GUI-Nachbesserung und Plan-B-Export verwenden sie ebenfalls. Alle Schritte teilen
das jeweilige vorhandene Zeitbudget.

`tests/test_native_search_expansion.py` prüft unterschiedliche Grundformen,
falsche und richtige weisse Details, gemeinsam zu entfernende Überlagerungen,
verschachtelte Transformationen, grosse Bilder, Kandidatengedächtnis,
Texterhaltung, Stillstand während der Mindestzeit sowie echte CLI- und
Vorlagenpfade. Vorhandene Such-, GUI-, Modell- und Plan-B-Regressionen bleiben
zusätzlich verbindlich.

Das erweitert die verfügbaren Konstruktionen und verhindert konkrete
Wiederholungsschleifen. Es ist kein Beweis, dass jedes beliebige Motiv bereits
richtig rekonstruiert wird. Insbesondere sind die bisherigen globalen
Abnahmegrenzen kein allgemeiner Nachweis einer visuell korrekten Geometrie.
