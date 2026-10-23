# Nächstes Arbeitspaket – Versuchssicheres Telemetrie-Alias-Artefakt Run ACK (2026-08-04)

Run ACK führt die in Run ACJ ergänzte Bindung des Verifikationsbelegs an den
Workflow-Versuch bis zur Artefaktablage fort. Der Inhalt eines Belegs benennt
bereits den konkreten Versuch; sein bisheriger Artefaktname enthielt jedoch nur
die Run-ID und war deshalb für erneut ausgeführte Läufe nicht eindeutig.

## 1) Versuchsspezifischer Artefaktname

Der Upload verwendet nun das Schema
`optimization-render-telemetry-alias-verification-<run-id>-<run-attempt>`.
Damit besitzt jeder Versuch eines GitHub-Workflow-Laufs einen eigenen,
deterministisch auffindbaren Beleg. Ein Rerun kann weder mit dem Artefakt eines
früheren Versuchs verwechselt werden noch dessen Namen wiederverwenden.

## 2) Automatischer Vertragscheck

Der Workflow-Strukturtest prüft den vollständigen Artefaktnamen einschließlich
`github.run_id` und `github.run_attempt` im Upload-Schritt. Die bereits
vorhandenen Inhaltsprüfungen stellen weiterhin sicher, dass dieselben Werte im
Beleg selbst persistiert und vom eigenständigen Gate validiert werden.

## 3) Ergebnis

Persistierter Beleg und hochgeladenes Artefakt tragen jetzt dieselbe
Versuchsidentität. Auch bei mehreren Ausführungsversuchen bleibt jeder positive
Nachweis eindeutig adressierbar und separat abrufbar.
