# Nächstes Arbeitspaket – ZG7.3 Constraint-Fusion und Hypothesen-Beam (2026-10-03)

Dieses Paket setzt nach ZG7.2 den dritten Schritt der dokumentierten Folge
`ZG7.1 → ZG7.2 → ZG7.3 → ZG7.4 → ZG7.5 → ZG7.6` um. Weil der ZG7.2-Befund
vor allem fehlende Primitivsemantik zeigte, wird zunächst die Topologie
abgesichert und ausdrücklich noch kein Antialiasing-Feintuning begonnen.

## Versionierter Fusionsvertrag

`tools/constraint_fusion_beam.py` erzeugt den Record
`constraint_fusion_beam_v1`. Beschreibungselemente werden über normalisierte
Primitivtypen sowie optionale relative Lage und Anschlussrichtung
Perception-Kandidaten zugeordnet. Kandidatenkennungen werden ausschließlich aus
Geometrie und Evidenz abgeleitet; Quellpfad und Dateiname beeinflussen weder ID
noch Reihenfolge.

Der Beam hält standardmäßig die drei besten zulässigen Geometry-IR-Hypothesen.
Die feste Rangfolge lautet: harte Constraints, Semantik, Confidence und erst
danach Pixelabweichung. Ein pixelnäherer Kreis, ein Rechteck an der falschen
Stelle oder ein Anschluss in Gegenrichtung kann deshalb keinen harten
Beschreibungsconstraint kompensieren. Jeder verworfene Kandidat und jede wegen
Relationen verworfene Kombination erhält maschinenlesbare Gründe.

## Konfliktverhalten und Abnahme

Existiert für ein erforderliches Element kein kompatibles Bildsignal oder
erfüllt keine Kombination die harten Relationen, enthält der Record keine
scheinbar sichere Auswahl. Er endet reproduzierbar mit `semantic_conflict` und
nennt die betroffenen Constraints. Die CLI gibt dafür den bereits
dokumentierten kanonischen Exit-Code `23` zurück.

Die fokussierten Tests decken mehrdeutige Kreis-/Rechteckkandidaten, eine harte
Anschlussrichtung, ein fehlendes Textsignal, den Drei-Hypothesen-Vertrag und
die Umbenennungsinvarianz ab. Der maschinenlesbare Abnahmebeleg liegt unter
`artifacts/evaluation/constraint_fusion_beam_v1/report_2026-10-03.json`.

ZG7.3 ist damit abgeschlossen. Das nächste dokumentierte Paket ist **ZG7.4 –
Mehrzieloptimierung**; sie darf nur innerhalb der hier semantisch zulässigen
Topologien arbeiten.
