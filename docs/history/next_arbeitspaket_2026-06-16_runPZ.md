# Nächstes Arbeitspaket – IDO-09 Unsicherheitsvertrag Run PZ (2026-06-16)

## Ziel

Run PZ schließt nach der T6.11–T6.15-Langläuferrotation das nächste offene
Arbeitspaket aus der allgemeinen Priorisierung ab: **IDO-09 –
Unsicherheitsvertrag definieren**. Die Beschreibung-/Perception-Fusion soll
widersprüchliche, mehrdeutige oder nicht durch Bildkandidaten belegte Evidenz
nicht als sichere Geometrie ausweisen, sondern einen maschinenlesbaren
Review-Status liefern.

## Umsetzung

- `fuse_description_constraints_with_perception_candidates(...)` erzeugt nun
  zusätzlich zum bestehenden Fusionsstatus einen `fusion_uncertainty_v1`-
  Vertrag mit Status, Grund, betroffenen Constraint-Zielen, Confidence und
  `review_required`-Flag.
- Sicher renderbare Geometrie wird separat als `safe_geometry_ir` ausgewiesen
  und enthält ausschließlich eindeutig gematchte Fusions-Elemente.
- Negative Fälle mit fehlender Bildevidenz oder widersprüchlicher Evidenz
  behalten zwar den erklärenden Entscheidungs-Trace, werden aber nicht mehr als
  sichere Geometrie markiert.
- Der bestehende IDO-08-Fusionsvertrag bleibt kompatibel: `geometry_ir`,
  `decisions`, `relations`, `status` und Gewichtung bleiben erhalten.

## Laufzeit- und Akzeptanznachweis

```bash
python -m pytest -q tests/test_description_perception_fusion.py
```

| Kriterium | Gefordert | Run PZ |
| --- | --- | --- |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `7 passed` |
| Fehlende Bildevidenz | maschinenlesbarer Review-/Unsicherheitsstatus | `insufficient_evidence`, `review_required=true` |
| Widerspruch | keine sichere Geometrie halluzinieren | `contradictory`, leeres `safe_geometry_ir` |
| Eindeutiger Match | sichere Geometrie separat nutzbar | `resolved`, ein Element in `safe_geometry_ir` |

## 5-Zeilen-Log

- **Getestet:** IDO-08/IDO-09-Fusionspfad mit neutralen synthetischen Kandidaten und erfundenem Constraint-Namen.
- **Ergebnis:** Exit `0`, `7 passed in 0.53s`.
- **Blocker:** Kein IDO-09-Blocker; Review-Status und sichere Geometrie sind maschinenlesbar getrennt.
- **Dokumentation:** IDO-09 ist in `docs/image_description_only_tasks.md` und `docs/open_tasks.md` abgeschlossen.
- **Nächster Schritt:** Mit IDO-10 als erstem vertikalem Migrationspaket für linke Kreis-Connectoren fortfahren.
