# Geometrische Konvertierung mit unvollständiger Beschreibung

Eine unbestätigte Beschreibung darf einen vorhandenen geometrischen Entwurf
nicht unterdrücken. Der Start bleibt auch mit unbekannten Formulierungen oder
unauflösbaren Ähnlichkeitsreferenzen möglich. Eine erfolgreiche Rekonstruktion
ist dadurch nicht für jedes Motiv garantiert.

Der Ausweichpfad prüft analytische geometrische Modelle innerhalb des vorhandenen
Zeitlimits. Er erzeugt weder eingebettete Rasterbilder noch Pixelstreifen,
Rasterkonturen oder zeilenweise nachgezeichnete Bildflächen. Falls kein Modell
gefunden wird, endet der Auftrag mit einer verständlichen Meldung. Ein direkter
Ausweichversuch hat eine harte Prozessgrenze von 15 Sekunden.

Der zuvor eingeführte Bildflächenpfad war eine Fehlentscheidung: Er kodierte
Rasterzeilen als kleine SVG-Teilflächen. Seine hohen Pixelvergleichswerte waren
kein Nachweis geometrischer Rekonstruktion. Dieser Generator ist entfernt.
Die Import-, Vorschau- und Exportprüfung erkennt seine alte Streifengeometrie
auch ohne Jobmetadaten. Solche Dateien werden nicht erneut als Sample verwendet;
vorhandene Dateien bleiben als Belege gespeichert.

Der vorhandene Zweiwegventil-Ansatz versteht jetzt auch eine native Beschriftung
im Motorkreis und wiederholte, identische Angaben nach Referenzauflösung. Kreis,
gerader Griff, zwei verbundene Dreiecke und ein gemeinsamer linearer Verlauf
werden geometrisch angepasst. Der Buchstabe bleibt ein SVG-Textobjekt. Zusätzliche
unverbrauchte oder widersprüchliche Aussagen erhalten keine vollständige Freigabe.

Die Tests laufen ausschliesslich auf GitHub Actions. Sie prüfen den echten
GUI-Worker mit dem unveränderten Benutzertext und neutralem Dateinamen, die
Wiederholung mit altem Pixelstreifen-Sample, native Elemente statt Pixelkopie,
Neustart, Export und Fälle ohne passendes Modell. Original, SVG, vergrösserte
Vorschau und Protokolle liegen im Artefakt `description-guided-evidence-*`.
CI-Ergebnisse und noch offene allgemeine Prüfungen werden im Pull Request benannt.
