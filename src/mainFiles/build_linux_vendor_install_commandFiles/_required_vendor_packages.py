from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _required_vendor_packages() -> list[str]:
    return [
        "numpy",
        "opencv-python-headless",
        "Pillow",
        "PyMuPDF",
    ]
