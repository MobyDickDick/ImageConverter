# Frozen Plan-B regression templates

These seven fixtures preserve the accepted templates and description from the parent
of commit `e955203aa` (the move to the manually edited `artifacts/samples` collection).
Tests rasterize and vary these inputs; conversion receives only the raster and its
description. The converter must never read these vectors. Keeping regression
inputs here lets the user edit `artifacts/samples` without changing past tests.

Blank-line trailing spaces in AR0030.svg are normalized; rendered pixels are identical.

`AC0022_canvas.svg` is the SVG source from the user-provided Workbench ZIP
(seed 472, 35 × 112 raster; line endings and blank lines normalized). It freezes
the tightly cropped motif that exposed clipping when a variant grew within the
unchanged canvas. This additional fixture does not belong to the seven
historical templates described above.
