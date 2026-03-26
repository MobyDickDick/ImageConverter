# Forms Model (Circle + Handle)

This document describes the strict form model used by the converter.
Atomic values remain numbers and strings; the Python API enforces this with
types and constraints.

## Core Types

- `RGBValue(r, g, b)` with `0 <= channel < 256`.
- `Point(x, y)`.
- `Distance(point1, point2)` as Euclidean distance.
- `Circle(center, radius, stroke_width, stroke_color, fill_color)` with constraint `stroke_width <= radius`.
- `Handle(start, end)` with derived field `length`.
- `Scoop(handle, circle)` with constraints:
  - `handle.start == circle.center`
  - `handle.length > circle.radius`

## Rendering Rules

- Draw order: **handle first, circle second** (`draw(Handle) < draw(Scoop)`).
- Objects may be computed outside the canvas bounds.
- Final output is clipped to the drawing area.

## Labeled Circle Rule (CO²)

For AC08 badges with CO2 text, the conversion must keep **CO²** (raised 2 / superscript),
not CO₂ as a subscript.

Formal shorthand:

```text
CircleWithLabelCO^2{
  Circle,
  CO^2: String,
  Constraints = {
    CO^2 = "$CO^2$",
    2 * Circle.radius < p_o.width,
    for every pixel in glyph(CO^2):
      Distance(pixel, Circle.center) < Circle.radius
  }
}
```

Meaning of `CO^2 in Circle`:

- Every pixel of the rendered text glyph `"CO^2"` must satisfy
  `Distance(pixel, Circle.center) < Circle.radius`.
- The circle diameter must be strictly smaller than the output image width:
  `2 * Circle.radius < p_o.width`.
- In plain language: every text pixel has a distance to the circle center that is
  smaller than the circle radius.

## Alignment Policy for CO²

- CO² is **not required** to be centered inside the circle.
- The optimizer should place CO² to best match the source image text shape.
- Superscript readability and in-circle containment constraints still apply.

## Orientations

`build_oriented_kelle(...)` supports:
- `left`
- `top` / `up`
- `right`
- `bottom` / `down`

This allows generating left/up/right/down oriented scoops and rendering them as SVG.
