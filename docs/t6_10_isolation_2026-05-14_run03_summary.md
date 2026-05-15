# T6.10 Isolationslauf – 2026-05-14 (Run 03)

## Ziel
Erneute, timeout-gesicherte Isolation von
`test_validate_badge_logs_extent_bracketing_for_line_elements` als nächster dokumentierter T6.10-Schritt.

## Befehl
`timeout 180 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`

## Ergebnis
- Exit-Code: `0`
- Pytest-Resultat: `1 skipped`
- Laufzeit: `2.55s`
- Log: `artifacts/converted_images/reports/t6_10_isolation_2026-05-14_run03.log`

## Einordnung
Der Test ist weiterhin nicht rot, sondern in dieser Umgebung `skipped`.
Das Laufzeitziel (`<=35s`) bleibt bis zu einem laufenden (nicht geskippten)
Durchlauf in voll ausgestatteter Runtime offen.
