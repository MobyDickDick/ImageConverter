import cv2
from pathlib import Path
from src.exploratory import convert

image = cv2.imread("test.png")

result = convert(
    image,
    description="",
    seconds=300
)

print("Abbruchgrund:", result.stop_reason)
print("Kandidaten:", result.generated)
print("Renderings:", result.renderings)
print("Bewertungen:", result.evaluated)
print("Qualität:", result.quality)
print("Fehler:", result.errors)

if result.best is not None:
    Path("draft.svg").write_text(
        result.best.svg,
        encoding="utf-8"
    )