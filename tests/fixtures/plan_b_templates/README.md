# Frozen Plan-B regression templates

These seven fixtures preserve the accepted templates and description from the parent
of commit `e955203aa` (the move to the manually edited `artifacts/samples` collection).
Tests rasterize and vary these inputs; conversion receives only the raster and its
description. The converter must never read these vectors. Keeping regression
inputs here lets the user edit `artifacts/samples` without changing past tests.

Blank-line trailing spaces in AR0030.svg are normalized; rendered pixels are identical.
