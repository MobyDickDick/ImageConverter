# Erste lokale Bilderkennung

`summary.json` enthält einen reproduzierbaren Vergleich mit 24 bekannten
Familien, identischen decodierten Bildpunkten und einer Grössenänderung auf 125 %.
Dies ist eine Referenzsuche, kein Test einer allgemeinen Erkennung unbekannter
Familien. Die echte Konvertierung ohne Beschreibung und die Gegenproben sind
in `tests/test_image_recognition.py` abgesichert.

Aufruf: `python -m tools.evaluate_image_recognition --output artifacts/evaluation/image_recognition_v1 --limit 24`.
