# Nächstes Arbeitspaket – Merge-sichere Workflow-Kontextprüfung Run ACM (2026-08-04)

Run ACM behebt eine beim Zusammenführen der beiden Run-ACL-Änderungszweige
entstandene Lücke: Die Kommandozeilenparameter für die erwartete Workflow-Run-ID
und den erwarteten Workflow-Versuch waren weiterhin verdrahtet, ihre
Vergleiche im zentralen Prüfhelper waren nach dem Merge jedoch nicht mehr
enthalten.

## 1) Erwarteten Workflow-Kontext strikt prüfen

`verification_errors(...)` vergleicht die im Beleg gespeicherte Run-ID und den
gespeicherten Run-Attempt wieder unabhängig mit den optional übergebenen
Erwartungswerten. Abweichungen werden getrennt und maschinenlesbar gemeldet.
Ohne Erwartungsparameter bleibt die lokale Bestandsprüfung kompatibel.

## 2) Regressionstest auf Helper-Ebene

Ein direkter Test des Prüfhelpers erwartet bei gleichzeitig abweichender Run-ID
und abweichendem Run-Attempt beide Fehlermeldungen. Der bereits vorhandene
CLI-Test sichert zusätzlich den Exitcode und die Ausgabe für einen Beleg aus
einem anderen Workflow-Versuch.

## 3) Dokumentationsbereinigung

Die beiden beim Merge aneinandergehängten Run-ACL-Beschreibungen sind nun ein
einheitliches Dokument ohne Konflikttrenner. Damit dokumentieren Run ACL und
Run ACM wieder eindeutig den beabsichtigten und den tatsächlich geprüften
Vertrag.
