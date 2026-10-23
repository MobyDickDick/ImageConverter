# Zeitüberlauf und Standby: SEARCH-DEADLINE-OVERRUN-AUDIT

Die kompakten Belege enthalten den unveränderten ursprünglichen Fehlversuch,
die getrennte vollständige Wiederholung, drei neue echte CLI-Wiederholungen,
eine während der Untersuchung beobachtete Aufsichtslücke und Windows-
Energieereignisse aus beiden Zeitfenstern. Die Ereignisse betreffen nur
Energiezustände; Rechnernamen und andere Systemereignisse werden nicht exportiert.

Der ursprüngliche 261,734-Sekunden-Versuch fällt mit dem Wechsel in den modernen
Standby und dem Aufwachen beim Öffnen des Deckels zusammen. Die Phasenlage des
alten Workers ist mangels damaliger Zeitmarken weiterhin unbekannt. Die neue
967-Sekunden-Beobachtungslücke enthält ebenfalls einen Standby-Zeitraum; nach
dem Wiederaufnehmen benötigt der Prozessabbau nur 0,187 Sekunden.

`observer-gap.jsonl` ist die vollständige neue Phasenspur. `summary.json`
bindet diese Spur, die beiden Energieereignisexporte und die kompakten
Prüfergebnisse an Prüfsummen. Vollständige neue CLI-Ausgaben liegen lokal unter
`.tmp/deadline-audit-replay/` und `.tmp/deadline-audit-quality/`; die alten unter
`.tmp/semantic01/`. Ein frischer Checkout benötigt neue Messläufe.

Die Zeitaufsicht kann auf einem schlafenden oder nicht eingeplanten Rechner
keinen Prozess rechtzeitig beenden. Die Budgets und Qualitätsgrenzen bleiben
erhalten; eine nach Ablauf beobachtete Ausgabe erhält keine neue Freigabe.
Die Aufgabe ist als Ursachenuntersuchung abgeschlossen, nicht als Zusage
einer von Standby und Systemplanung unabhängigen Echtzeitgarantie.

Reproduktion, Änderungen und Grenzen:
[Paketdokumentation](../../../docs/history/next_arbeitspaket_2026-10-22_deadline_overrun_audit.md).
