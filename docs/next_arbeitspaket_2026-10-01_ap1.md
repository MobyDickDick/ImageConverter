# Nächstes Arbeitspaket – AP1 skalierte Kreis-Evidenz (2026-10-01)

Dieses Paket bearbeitet **AP1** aus
`next_arbeitspakete_aus_artifacts_2026-10-01.md`. Die grobe semantische
Kreisprüfung erhält einen zweiten, größenrelativen Hough-Pass für sehr kleine
Anschluss- und Symbolvarianten, ohne das bestehende Semantik-Gate pauschal zu
lockern.

## Umsetzung

- Der zweite Pass skaliert Radius, Mindestabstand und Akkumulatorschwelle an
  der kleineren Canvas-Kante.
- Ein Kandidat gilt nur bei ausreichender Vordergrundabdeckung in mindestens
  sechs Winkelbereichen. Am Canvas abgeschnittene Kandidaten werden verworfen;
  dadurch wird insbesondere eine Rechteckkante nicht als Kreis akzeptiert.
- Die Strukturtelemetrie nennt jetzt Detektorquelle, Mittelpunkt/Radius,
  Confidence und einen maschinenlesbaren Ablehnungsgrund. Diese Angaben werden
  auch an die bestehende Debug-Zeile des Semantikfehlers angehängt.

## Fixture-Ergebnis

Der maschinenlesbare Bericht liegt unter
`artifacts/evaluation/scaled_circle_evidence_v1/ap1_fixture_report.json`.

- `AC0714_M.jpg` liefert reproduzierbar einen `scaled_hough`-Kandidaten bei
  `(17, 12)` mit Radius `6` und Confidence `0.7787`.
- `AC0703_1_M.jpg` bleibt bewusst `needs_review`: Der schwache Kandidat wäre am
  Canvas abgeschnitten und wird deshalb nicht als Kreis ausgegeben.
- `AC0704_1_S.jpg` bleibt ebenfalls `needs_review`, weil auch der skalierte Pass
  keinen belastbaren Kreis findet. Das Gate behauptet somit keinen
  `semantic_ok`-Status ohne Bildevidenz.
- Ein weißes 25×15-Negativbild bleibt negativ. Die fokussierten bestehenden
  Ringtests bleiben grün.

## Ergebnis und nächster Schritt

AP1 ist für die drei dokumentierten Problem-Fixtures abgeschlossen: ein zuvor
übersehener kleiner Kandidat wird erkannt, die beiden widersprüchlichen Fälle
werden mit konkretem Ablehnungsgrund zur fachlichen Prüfung belassen. Als
nächstes kann AP2 den Bild-/Beschreibungs-Konflikt von `AC0843_L` mit derselben
evidenzbasierten Trennung untersuchen.
