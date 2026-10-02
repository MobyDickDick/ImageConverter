# Nächstes Arbeitspaket – AP2 AC0843-Bild-/Beschreibungs-Konflikt (2026-10-02)

Dieses Paket schließt **AP2** aus
`next_arbeitspakete_aus_artifacts_2026-10-01.md` ab. Die Konvertierung wurde für
alle drei AC0843-Größen selbst ausgeführt. Der zuvor gemeldete senkrechte
Strich ist kein JPEG- oder Kreisrandartefakt, sondern der reale obere Griff:
Er liegt außerhalb des Kreisrings, bleibt über L/M/S kontinuierlich und wird
bei L und M bereits durch Hough-Linien erkannt.

## Ursache und Korrektur

Die alte Kurzbeschreibung „Wie AC0842, jedoch nach rechts gedreht“ übernahm den
waagrechten linken Griff des Referenzsymbols, obwohl die zweite Drehung im Bild
einen oberen vertikalen Griff erzeugt. Deshalb meldete das Semantik-Gate bei L
und M zu Recht einen Bild-/Beschreibungs-Konflikt. Die Quelldatenbeschreibung
nennt Kreis, `rF` und die Relation „senkrechte Linie oberhalb des Kreises“ nun
explizit; dies ist als **Datenkorrektur** markiert und keine Bild-ID-Regel.

Bei S ist derselbe echte Griff zu kurz für den bisherigen Hough-Schwellwert.
Ein allgemeiner, größenrelativer Fallback prüft daher die längste
Vordergrundkontinuität spaltenweise außerhalb des erkannten Kreisrings. Er
läuft nur, wenn Hough weder Stiel noch waagrechten Arm gefunden hat. Damit
bleiben die horizontalen AC0842-/AC0844-Kontrollen horizontal.

## Evidenz und Ergebnis

Der maschinenlesbare Bericht liegt unter
`artifacts/evaluation/ac0843_semantic_conflict_ap2/evidence_report.json`. Er
referenziert die bereits versionierten Rohbilder und das Failed-SVG und hält
Canvasgröße, Kreisgeometrie, Detektorquelle, Confidence sowie horizontale und
vertikale Kandidatenzahlen fest. Dadurch bleibt die Evidenz ohne ein weiteres
binäres Bildartefakt reproduzierbar und im Text-Diff vollständig prüfbar.

Nach der Korrektur liefern AC0843 L/M/S jeweils `circle=true`, `stem=true`,
`arm=false` und `connector_orientation=vertical`. Die selbst ausgeführten
Konvertierungen für L, M und S durchlaufen damit den normalen semantischen Pfad.
AC0842_L und AC0844_L sichern als verwandte Gegenproben weiterhin die
horizontale Klassifikation. Als nächstes kann AP4 das dokumentierte
Report-Konsistenzgate umsetzen.
