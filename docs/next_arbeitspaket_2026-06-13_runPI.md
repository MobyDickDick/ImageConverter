# Nächstes Arbeitspaket – Review-Refresh Run PI (2026-06-13)

## Ziel

Run PI arbeitet den in Run PH dokumentierten nächsten Schritt ab: Nach der
vollständig geleerten Plan-B-Rotation wird der reproduzierbare Qualitätsreview
ohne manuelle Kandidatenvorgabe erneut ausgeführt. Nur ein renderbarer Fall
oberhalb der Review-Grenze `0.045945679012345676` darf die Rotation wieder
öffnen.

## Reproduzierbarer Review

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. \
python tools/review_conversion_quality.py
```

Der Lauf endet mit Exit `0` und wertet sowohl die 48 als erfolgreich geführten
Varianten als auch das aktuelle Diff-Inventar aus.

| Metrik | Wert |
| --- | ---: |
| Erfolgreiche Varianten | `48` |
| Renderbare erfolgreiche Paare | `48` |
| Fehlende/fehlerhafte erfolgreiche Paare | `0` |
| Erfolgreiche Varianten oberhalb der Grenze | `0` |
| Varianten im Diff-Inventar | `132` |
| Renderbare Diff-Paare | `123` |
| Kuratierte Plan-B-Kandidaten | `0` |

Auch das aktuelle Inventar mit 132 Diff-Varianten öffnet keinen neuen
qualifizierten Fall. Die deterministische Triage bleibt leer.

## PF8-Kopplung

Der PF8-Linkage-Report wurde für die leere Triage erneut erzeugt. Er enthält
`0` Samples und bestätigt damit, dass weder ein verwaister Perception-Eintrag
noch eine nicht durch den Qualitätsreview gedeckte Folgeaktion aktiv ist.

## Entscheidung

Das dokumentierte Review-Arbeitspaket ist abgeschlossen. Es ist keine reale
Re-Konvertierung gerechtfertigt: Ein beliebiger Kandidat unterhalb der Grenze
würde die messwertbasierte Auswahlregel umgehen. Die Plan-B-Rotation bleibt
pausiert, bis ein späterer Review einen neuen Fall qualifiziert.

## 5-Zeilen-Log

- **Getestet:** Reproduzierbarer Qualitätsreview über Erfolgs- und Diff-Inventar sowie erneuerter PF8-Linkage-Report.
- **Ergebnis:** `48/48` Erfolgspaare renderbar, `0` oberhalb der Grenze; `123/132` Diff-Paare renderbar und `0` Kandidaten ausgewählt.
- **Blocker:** Kein technischer Blocker; fachlich fehlt weiterhin ein qualifizierter Grenzwertfall.
- **Nächster Schritt:** Rotation pausieren und den Review erst nach neuen oder geänderten Konvertierungsartefakten erneut ausführen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py`.
