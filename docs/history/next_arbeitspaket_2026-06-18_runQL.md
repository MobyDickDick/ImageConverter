# Nächstes Arbeitspaket – IDO-12 Z-Order und Negativfälle Run QL (2026-06-18)

Dieses Paket setzt den nach Run QK dokumentierten IDO-12-Ausbau fort: Vertikale
Kreis-Connectoren sollen nicht nur oben/unten erkannt werden, sondern auch bei
teilweiser Überdeckung eine explizite Z-Order-/Fortsetzungsrelation erhalten.
Connector-freie Kreise werden parallel als Negativfall abgesichert, damit die
Beschreibung „ohne Anschluss“ keinen impliziten Vertikalstrich erzeugt.

## Umsetzung

- Der beschreibungsgetriebene Geometry-IR-Pfad erkennt generische
  Überdeckungssignale wie `teilweise verdeckt`, `hinter dem Kreis` oder
  `Kreis verdeckt` bei oberen und unteren Kreis-Connectoren.
- Teilverdeckte vertikale Connectoren werden vor dem Kreis gerendert und tragen
  maschinenlesbar `z_order="behind_target"` sowie
  `continues_behind_ref="described_circle"`; daraus entsteht in den
  Description-Constraints eine `continues_behind`-Relation.
- Connector-freie Kreisformulierungen wie `ohne Anschluss`, `anschlussfrei` und
  `connector-frei` erzeugen nur einen `CircleBackground` mit
  `connector_policy="forbid"` und keine Connector-Relation.

## Sicherung

- `tests/detailtests/test_description_contract_helpers.py` prüft jetzt
  teilverdeckte obere und untere Vertikal-Connectoren inklusive Z-Order- und
  `continues_behind`-Relation.
- Derselbe Testbereich enthält einen connector-freien Negativfall, der nur den
  Kreis zulässt und leere Relations-Constraints erwartet.
- Der Runtime-Ratchet gegen neue Bild-ID-Sonderfälle bleibt unverändert grün.

## Ergebnis

IDO-12 deckt nun die in der Akzeptanz genannte Kombination aus Anschluss oben,
Anschluss unten, teilweise verdecktem Anschluss und connector-freiem Kreis im
katalogfreien Beschreibungspfad ab. Offen bleibt die spätere Kopplung an echte
Bildgeometrie-/Perception-Evidenz, wenn neue Rasterfälle eine robuste
Occlusion-Messung erfordern.
