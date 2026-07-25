# Nächstes Arbeitspaket – AC0010/AC0100 Renderer-Reparatur (2026-07-25)

## Ausgangslage

Die erneute Prüfung aus `nextPrompt.txt` war reproduzierbar: Der schwere
Familientest war standardmäßig ausgeblendet, und der echte Lauf lieferte für
`AC0010` sowie die kompakten AC0100-Varianten wieder schlechte Ergebnisse.

Die Ursache waren zwei zusammenwirkende allgemeine Regeln:

1. Der elementweise Fit erzeugte seinen Rasterverlauf inzwischen als SVG-
   `linearGradient`. Der lokale Bewertungsrenderer und der abschließende
   Qualitätsrenderer interpretierten diesen Verlauf nicht konsistent.
2. Selbst ein anhand des Eingaberasters besser bewerteter elementweiser
   Kandidat durfte die Beschreibungs-Geometrie erst bei einem willkürlichen
   Faktor-2-Vorsprung ersetzen. Kleine Unterschiede der Vorschaumetrik konnten
   dadurch große Unterschiede der Abschlussmetrik verdecken.

## Umsetzung

- Der gemeinsame Verlaufsrenderer zerlegt horizontale **und** vertikale
  Verläufe wieder in größenabhängige, überlappende Farbbänder. Farben,
  Verlaufsmitte, Ausrichtung, Anzahl und Maße werden aus Beschreibung,
  Rastermessung und Bildgröße berechnet; es werden weder Bild-IDs noch fertige
  SVG-Daten hinterlegt.
- Bei beschriebenen Heizelementen gewinnt nun der bessere algorithmische
  Raster-Fit ohne künstlichen Faktor-2-Abstand. Der Schutz gegen veraltete
  Pixelstreifen-Ausgaben bleibt bestehen.
- Ein katalogneutraler Detailtest sichert die Kandidatenwahl bei einem nur
  moderaten Vorsprung ab. Der bestehende vertikale Verlaufstest prüft jetzt die
  renderer-stabilen Bänder.

## Reale Kurzläufe

| Variante | best_error | mean_delta2 |
|---|---:|---:|
| AC0010 | 19.475521 | 2660.050293 |
| AC0100_L | 9.957708 | 549.534363 |
| AC0100_M | 11.555926 | 835.798889 |
| AC0100_S | 10.986250 | 668.066223 |

Alle vier Ausgaben entstehen über
`non_composite_elementwise_symbol_fit`. Sample-Auswahl und Template-Transfer
sind in diesem Pfad weiterhin ausgeschlossen.
