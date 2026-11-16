# Aktuelles SVG wiederverwenden, Verbesserungen speichern und kleine Zeichen erhalten

**Aktualisierung:** Die unten dokumentierte pauschale Helligkeitssperre und
der Vergleich mit dem Vorlagengrauton waren ein Zwischenstand. Sie sind
inzwischen zurückgenommen: Farben dürfen sich in beide Richtungen an das
Rasteroriginal anpassen. SVG-Wiederverwendung, Sicherung und automatische
Speicherung bleiben erhalten.
[Aktuelle Korrektur und Nachweise](crossed_panel_workbench_2026-11-16.md).

Die Nutzerkorrektur betrifft `AC0130.jpg`: Ein Versuch ohne Vorlage lieferte
eine sichtbar schlechtere Linienkomposition als die vorherige Anpassung einer
Vorlage. Ausserdem waren Plus und Minus im angepassten SVG zu hell.

## Standardverhalten

Die Checkbox **„Aktuelles SVG als Ausgangspunkt verwenden“** ist standardmässig
aktiv. Ihre Auswahl bleibt im Browser gespeichert. Der Backend-Parameter
`use_current_svg` ist ein echter Boolean und standardmässig ebenfalls aktiv.

Beim Start gilt:

1. Eine gerade ausdrücklich geladene Vorlage wird für diesen Versuch verwendet.
2. Danach hat die aktuelle Datei im Projektordner `converted_svgs/` Vorrang.
   Historische Ergebnisse ersetzen diese aktuelle Datei nicht bloss, weil sie
   einen kleineren globalen Pixelfehler aufweisen.
3. Ohne Projektdatei werden vorhandene Vorlagen und Ergebnisse desselben
   Bildinhalts berücksichtigt. Die Zuordnung früherer Jobs erfolgt über den
   Bildhash, nicht allein über den Dateinamen.

Jeder Kandidat wird auf eigenständige native SVG-Inhalte geprüft und gegen
das Original gerendert. Ein leerer oder unlesbarer Kandidat wird nicht benutzt.
Die tatsächlich gewählte Vorlage wird in der GUI benannt.

Ist die Checkbox deaktiviert, läuft die reguläre Konvertierung ohne Vorlage,
auch wenn eine Datei angehängt ist. Die angehängte Vorlage bleibt für einen
späteren Versuch erhalten; die Vergleichsansicht zeigt sie in diesem Modus
nicht als verwendeten Ausgangspunkt an. Die Speicherung eines besseren
Ergebnisses bleibt aktiv.

Ein alter laufender Webserver kündigt die neue Fähigkeit noch nicht über
`/api/config` an. Die neue Oberfläche weist deshalb auf den nötigen Neustart
hin und startet keine Konvertierung mit einer stillschweigend ignorierten
Checkbox.

## Automatische Speicherung

Native, nicht leere Ergebnisse mit bestandenen expliziten Beschreibungsprüfungen
werden mit der bisherigen Projektdatei erneut am Original verglichen.
Ein Entwurf kann gespeichert werden, seine Kennzeichnung bleibt dabei
`warning`; daraus wird keine bestandene Modellprüfung abgeleitet.

Ein bestandener Bildvergleich hat Vorrang vor einem nicht bestandenen. Bei
Vorlagenanpassungen werden bekannte kleine dunkle Details berücksichtigt, wenn
dieselben SVG-Elemente mit ihren IDs erhalten sind. Ein Auswaschen dieser
Details gilt als Verschlechterung. Für den übrigen Bildvergleich verwendet die
Speicherentscheidung

```
normalisierter Pixelfehler
    + 0.2 * (1 - Kantenübereinstimmung)
    + 0.1 * (1 - Vordergrund-IoU)
```

Kleiner ist besser. Das ist eine bewusst festgelegte Vergleichsregel für die
automatische Auswahl, kein allgemeiner Wahrnehmungs- oder Semantikbeweis.
Die absoluten Bildabnahmegrenzen bleiben unverändert.

Die gemeldete Version ohne Vorlage hat zwar einen kleineren Pixelfehler als
die vorherige Vorlagenversion (0,002629 statt 0,003478), aber deutlich
schlechtere Konturen (0,85547 statt 0,90642). Sie überschreibt die sauberere
Datei nach der neuen Vergleichsregel nicht. Jede tatsächlich ersetzte Datei
wird vorher unter `gui_history/<Name>/<SHA256>.svg` gesichert.

## Ursache der hellen Zeichen

Die drei Rechtecke für Plus und Minus hatten in der Vorlage `#696969`.
Die gemeinsame Anpassung von Position, Grösse und Farbpalette änderte sie in
der gemeldeten Ausgabe auf `#a9a9a9`. Die vorhandene Kontrastgrenze erlaubte
dies, solange die globale Pixelabweichung sank. Restfehler der Ausrichtung
konnten dadurch auf Kosten des kleinen Symbols ausgeglichen werden.

Die Vorlagenanpassung schützt jetzt kleine dunkle Grautöne: Im Ausgangsraster
sichtbare Farbgruppen mit Helligkeit höchstens 140 und einer Fläche bis drei
Prozent des Bildes dürfen nicht heller als ihr Ausgangston werden. Abdunkeln,
gemeinsame Ausrichtung und die Anpassung grösserer Flächen bleiben möglich.
Diese begrenzte Regel erhält die kleinen Identitätszeichen; sie ist keine
allgemeine automatische Erkennung beliebiger Beschriftungen.

Am konkreten Nutzer-SVG bleiben alle drei Plus-/Minus-Rechtecke jetzt bei
`#696969`. Native Geometrie und Element-IDs bleiben erhalten, nur die gesamte
Baugruppe wird ausgerichtet. Das Ergebnis besteht weiterhin die Bildprüfung.

## Konkrete Projektübernahme und Prüfung

Der korrigierte Stand wurde mit derselben neuen Speicherentscheidung tatsächlich
nach `artifacts/converted_images/converted_svgs/AC0130.svg` übernommen.
Die vorherige Datei mit SHA256
`fbcaeea245bd67ab57e4e6b0480c6e9bef2f79cec414e1168b81bc9e7ff0f141`
bleibt als Sicherung erhalten.

Gegenüber dieser vorherigen Datei steigt der Kantenwert von 0,85547 auf
0,89475. Der globale Pixelfehler steigt dabei von 0,002629 auf 0,004457 und
die Vordergrund-IoU sinkt leicht von 0,87687 auf 0,86670. Die Ausgabe ist also
nicht nach jeder Kennzahl besser; die neue Entscheidung priorisiert hier die
saubereren Konturen und den erhaltenen Detailkontrast. Alle absoluten
Bildprüfungen bestehen.

Die Regression führt echte GUI-Vorlagenläufe mit beiden gemeldeten früheren
Versionen aus. Sie prüft dunkle Zeichen, automatische Speicherung, die
Sicherung des früheren Standes und die erneute Übernahme nach Neustart des
Jobmanagers. Weitere Tests sichern Checkbox/API, Umbenennung des Rasterbildes,
aktuelle Projektdatei vor älterer Historie und das Ablehnen eines schlechteren
Versuchs trotz kleinerem globalem Pixelfehler.

[Lokale Ausgaben, Projektübernahme und Testprotokolle](../artifacts/evaluation/current_svg_reuse_2026-11-16/README.md).
