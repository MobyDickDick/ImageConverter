# AC0030: widersprüchliche Sample-Abnahme

Die beiden GUI-Läufe verwendeten identische Originalpixel und denselben
Benutzertext. Der Sample-Lauf akzeptierte eine verformte blaue Pfeilspitze,
weil globale Pixelwerte allein keine vollständigen Einzelteile belegen.
Der Lauf ohne Sample hatte den kleineren mittleren Fehler, scheiterte aber
mit zu breiten Schäften am Vordergrund-IoU. Seine Ausgabe enthielt außerdem
eine doppelte rote Pfeilgruppe.

| Stand (L) | Normalisierter MSE | Vordergrund-IoU | Kantenwert |
| --- | ---: | ---: | ---: |
| Historisches Sample-Ergebnis | 0.00240684 | 0.91952 | 0.86948 |
| Historischer Entwurf ohne Sample | 0.00078973 | 0.71507 | 0.98409 |
| Korrigierter nativer Fit, MuPDF | 0.00019231 | 0.99848 | 0.99093 |
| Korrigierter nativer Fit, librsvg | 0.00016538 | 0.99848 | 0.99146 |

Die Normalisierung versteht jetzt den Plural-Tippfehler „Dreicke“ sowie
„Pfeil zeigt nach oben“ und „Pfeil nach unten“. Damit erreicht der Originaltext
das bestehende rastergestützte Pfeilmodell. Quoted Labels und Verneinungen
bleiben erhalten; im Runtime-Code gibt es keine Bildkennungen.

Die explizite Beschreibung wird jetzt auch an Form, getrennter Seitenposition
und Richtung der beiden nativen Dreiecke geprüft. Verschachtelte Translationen,
Skalierungen, Spiegelmatrizen und Drehungen werden berücksichtigt. Ein beliebiges
nicht entartetes Dreieck reicht nicht mehr als Beleg für eine vertikale Spitze.
Sample-Schritte dürfen einen anfangs erfüllten Vertrag nicht verletzen.
GUI-Abnahme, Projektablage und beim Neustart geladene alte Erfolgsmeldungen
prüfen die Beschreibung erneut.

`quality.json` enthält Original-Hashes und die unveränderten Pixelabnahmen
für L/M/S mit MuPDF und librsvg (6/6 bestanden). Die drei Dateien
`AC0030_*_corrected.svg` enthalten jeweils vier native Vektorelemente.
`corrected_preview.png` zeigt L mit librsvg in dreifacher Größe.
Die bereits vor dieser Arbeit geänderte Projektdatei wurde nicht überschrieben.

`sample_refined.svg` und `.json` dokumentieren einen neuen 30-Sekunden-Lauf
mit dem tatsächlich hochgeladenen Sample. Die Formprüfung bleibt erfüllt,
die Pixelprüfung wird weiterhin nicht bestanden; der Lauf ist korrekt als
Entwurf ausgewiesen. Die Sample-Optimierung erreicht damit noch nicht die
Qualität des nativen Fits ohne Sample.

Validierung am 14.11.2026:

- Beschreibung, Pfeilmodell, Sample, Bildkennungen: 149 Tests bestanden.
- GUI einschließlich echter Konvertierung und erneuter Sample-Abnahme: 57 bestanden.
- Rastertoleranzen und Ähnlichkeitsreferenzen: 82 bestanden.
- Dual-Arrow-Runtime-Helfer: 3 bestanden.

Drei Socket-Tests und ein Prozessabbruch-Test waren in der Sandbox blockiert
und bestanden anschließend außerhalb der Sandbox. Insgesamt 291 Tests bestanden.
