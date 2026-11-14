# AC0026: echte Vektoren statt Raster-Fehlerartefakt

Die beiden gemeldeten GUI-Versuche enthielten ausschliesslich ein SVG-`image`
mit eingebettetem Rasterbild. Der Worker hatte zuvor
`DescriptionRejected: missing_described_horizontal_bar` gemeldet. Die GUI
übernahm das nachfolgend erzeugte Fehlerartefakt dennoch als SVG-Entwurf.

## Korrektur

- Der native Pfeilpaar-Fit toleriert unmittelbar neben einem beobachteten
  Dreieck maximal zwei schmale, zentrierte JPEG-Artefaktzeilen. Breite,
  Abstand und Zentrierung bleiben begrenzt. Fremde Markierungen werden
  weiterhin zurückgewiesen.
- Die GUI sperrt SVGs mit `image`-Elementen vor Vorschau und Download,
  auch bei gemischten Vektor-/Rasterausgaben, XML-Namensraumpräfixen und
  angeblich erfolgreichem CLI-Status. Das gilt auch für Sample-Ausgaben
  und beim Wiederherstellen alter Aufträge mit gecachten Pixelwerten.
- Die Katalogbeschreibung benennt nun die tatsächlich sichtbaren Seiten,
  Pfeilrichtungen und die rote Querlinie eigenständig, in beiden XML-Kopien.

## Nachweis

Ein echter GUI-Workerlauf mit neutralem internem Namen `UPLOAD.png` und der
unveränderten Nutzerbeschreibung aus
`tests/fixtures/descriptions/arrow_pair_red_crossbar_user.txt` besteht die
unveränderte Modell-/Beschreibungs- und Pixelprüfung. Die Ausgabe wurde über
die reguläre GUI-Projektablage nach
`artifacts/converted_images/converted_svgs/AC0026.svg` übernommen; die bisherige
Projektversion bleibt in `gui_history` erhalten.

Die Ausgabe enthält drei Rechtecke und zwei Dreiecke, ohne Rasterelement,
ohne Pixelkontur und ohne Übernahme des Sample-SVGs. Die rote Querlinie
verbindet die beiden Schäfte im unteren Drittel. Die linke rote Spitze zeigt
nach unten, die rechte blaue nach oben.

`checks.json` bindet Quelle und SVG per SHA-256 und enthält die unabhängigen
Messungen: MuPDF und librsvg bestehen sämtliche unveränderten Gates.
Normalisierter MSE: 0,001868 / 0,002018; Kantenabgleich: 0,988851 / 0,991249;
Vordergrund-IoU: jeweils 0,959441. Fünf Vektorelemente, null Rasterelemente.

Die lokalen Rohdaten (`jobs`, SVG, PNG-Vorschau) bleiben reproduzierbare
Arbeitsartefakte. Die beiden ursprünglichen fehlgeschlagenen Versuche werden
als Diagnosebelege erhalten, aber beim Serverneustart nicht mehr als Ergebnis
angeboten.

Der aktualisierte Webserver bestätigt dies auch über seine echten HTTP-Routen:
beide alten Aufträge sind `error`, `result=false`; ihre Ergebnis-URLs liefern
HTTP 404. Ein neuer AC0026-Auftrag besteht und wurde über den regulären
asynchronen Nachtrag mit beiden Renderern als `pixel_pass` in die laufende
Katalogübersicht übernommen. Ein paralleler vollständiger Inventarlauf wurde
vor der Veröffentlichung beendet, damit er die aktive Katalogübersicht nicht
überschreibt.

114 gezielte Tests bestehen. Vier HTTP-/Prozesstests mussten wegen der
Socket-/Prozessgrenzen der Sandbox ausserhalb der Sandbox wiederholt werden;
dort bestehen alle vier. Syntaxprüfung, CLI-Hilfe und der Runtime-Check gegen
neue dateinamenabhängige Sonderfälle bestehen ebenfalls.

Der Gesamtlauf findet daneben zwei unabhängig reproduzierte Fehler in
`test_narrow_rectangle_gradient_preserves_native_mask_and_pixel_center_colors`:
bei gerundeten Rechtecken stimmen 18 von 360 Alphawerten nicht mit der nativen
MuPDF-Maske überein. Der betroffene Renderer ist bytegleich mit `HEAD` (nach
Zeilenendennormalisierung); diese bestehende Abweichung gehört nicht zur
Pfeilpaar-/GUI-Korrektur. Die beiden scharfkantigen Varianten bestehen.

Die vollständige Suite (6.350 gesammelte Tests) wurde nicht abgeschlossen.
Nach dem seriellen Anlauf wurde sie in vier vollständige Modulpartitionen
verteilt (1.603 / 1.782 / 1.357 / 1.608 Tests) und nach weiteren Fehlern sowie
dem separaten Renderer-Nachweis beendet. Es wird kein grüner Gesamtlauf
behauptet; die 114 gezielten Tests und die beiden tatsächlichen SVG-Messungen
sind die abgeschlossenen Abnahmen dieser Korrektur.
