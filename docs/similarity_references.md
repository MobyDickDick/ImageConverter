# Form- und Farbreferenzen in der Bildbeschreibung

In der lokalen Bildkonvertierung können hinterlegte Katalogbeschreibungen als
Hinweise auf eine ähnliche Form, Farbgebung oder einen Farbverlauf dienen.
Eine zusätzliche Familienverwaltung ist dafür nicht nötig.

Beispiele für das Feld **Bildbeschreibung**:

```text
Form ähnlich wie AC0800.
```

```text
Form ähnlich wie AC0811, aber ohne Anschluss.
Farben ähnlich wie AC0800.
```

```text
Ein Kreis mit Rand. Farben ähnlich wie AC0800.
```

Die allgemein unterstützten Schreibweisen sind:

- `Form ähnlich wie BILDNAME` oder `Geometrie wie BILDNAME`.
- `Farben ähnlich wie BILDNAME` oder `Farbgebung wie BILDNAME`.
- `Farbverlauf ähnlich wie BILDNAME`, wenn die Referenzbeschreibung einen
  Verlauf nennt.
- `Form und Farben ähnlich wie BILDNAME` für beide Aspekte derselben Quelle.

`BILDNAME` wird durch die tatsächliche Katalogkennung ersetzt. Eine genaue
Variante wie `AC0800_L` hat Vorrang; auch eine Dateiendung wie `.jpg` oder `.svg`
ist möglich. Fehlt die genaue Variante, wird die vorhandene Familienbeschreibung
verwendet. Beliebige hochgeladene Bilder werden dadurch noch nicht zu neuen
Katalogreferenzen.

Pro Aspekt wird eine Referenz verwendet. Form und Farben dürfen aus verschiedenen
Quellen stammen. Eigene Farbangaben haben Vorrang. Die Ausnahmen `ohne Text`
und `ohne Anschluss` entfernen entsprechende Aussagen der Formreferenz;
eine eigene zitierte Beschriftung ersetzt die übernommene Beschriftung.
Weitere eigene Objekte und Bedingungen bleiben im Text erhalten. Lassen sich
Ausnahmen nicht eindeutig von anderen Formen trennen, wird eine konkrete
Beschreibung verlangt. Beliebige geometrische Umbauanweisungen sind damit
nicht automatisch unterstützt.

Die Auflösung erfolgt ausschliesslich anhand der Beschreibungen. Formreferenzen
übernehmen keine Farbadjektive; Farbreferenzen übernehmen keine Objekte oder
Beschriftungen. Erkannt werden gebräuchliche deutsche Farbnamen, sechsstellige
Hexfarben und einfache horizontale, vertikale oder radiale Verlaufshinweise.
Mehrere Farben bleiben als Palette erhalten; daraus wird keine Zuordnung zu
beliebigen Einzelobjekten behauptet. Die tatsächliche Form, die genauen Farben
und die Qualität werden weiterhin am aktuellen Rasterbild bestimmt. Eine
Referenz garantiert daher keinen Konvertierungserfolg und ist kein Auftrag,
das aktuelle Bild umzufärben.

Im **Konvertierungsprotokoll** erscheinen die gewählten Referenzen und die
aufgelöste Beschreibung. Der ursprüngliche Eingabetext bleibt gespeichert.
Unbekannte Referenzen, widersprüchliche Mehrfachangaben und Referenzzyklen werden
mit einer erklärenden Meldung abgelehnt. Alte ungetrennte `Wie …`-Eingaben bleiben
auf ihrem bisherigen Weg; innerhalb einer neuen Referenz werden solche
Beschreibungsverkettungen mit aufgelöst.

Die Sample-Optimierung erhält ebenfalls die aufgelöste Beschreibung. Plan B
speichert den ursprünglichen Text sowie die aufgelösten Quellen und erstellt
seine 17 Fälle aus dem aufgelösten Text. Spätere Katalogänderungen verändern
die bereits vorbereiteten Fälle dadurch nicht.

Nach einem Codeupdate den lokalen Webserver neu starten und die Seite neu laden.
Unter dem Beschreibungsfeld steht die aufklappbare Hilfe
**Ähnliche Bilder als Hilfe verwenden**.
