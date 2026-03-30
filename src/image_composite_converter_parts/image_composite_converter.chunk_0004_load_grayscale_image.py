class GlobalParameterVector:
    """Unified optimization vector for badge/kelle geometry and text layout."""

    cx: float
    cy: float
    r: float
    arm_x1: float | None = None
    arm_y1: float | None = None
    arm_x2: float | None = None
    arm_y2: float | None = None
    arm_stroke: float | None = None
    stem_x: float | None = None
    stem_top: float | None = None
    stem_bottom: float | None = None
    stem_width: float | None = None
    text_x: float | None = None
    text_y: float | None = None
    text_scale: float | None = None

    @staticmethod
    def from_params(params: dict) -> "GlobalParameterVector":
        return GlobalParameterVector(
            cx=float(params.get("cx", 0.0)),
            cy=float(params.get("cy", 0.0)),
            r=float(params.get("r", 1.0)),
            arm_x1=float(params["arm_x1"]) if "arm_x1" in params else None,
            arm_y1=float(params["arm_y1"]) if "arm_y1" in params else None,
            arm_x2=float(params["arm_x2"]) if "arm_x2" in params else None,
            arm_y2=float(params["arm_y2"]) if "arm_y2" in params else None,
            arm_stroke=float(params["arm_stroke"]) if "arm_stroke" in params else None,
            stem_x=float(params["stem_x"]) if "stem_x" in params else None,
            stem_top=float(params["stem_top"]) if "stem_top" in params else None,
            stem_bottom=float(params["stem_bottom"]) if "stem_bottom" in params else None,
            stem_width=float(params["stem_width"]) if "stem_width" in params else None,
            text_x=float(params["text_x"]) if "text_x" in params else None,
            text_y=float(params["text_y"]) if "text_y" in params else None,
            text_scale=float(params["text_scale"]) if "text_scale" in params else None,
        )

    def apply_to_params(self, params: dict) -> dict:
        out = dict(params)
        out["cx"] = float(self.cx)
        out["cy"] = float(self.cy)
        out["r"] = float(self.r)
        optional_values = {
            "arm_x1": self.arm_x1,
            "arm_y1": self.arm_y1,
            "arm_x2": self.arm_x2,
            "arm_y2": self.arm_y2,
            "arm_stroke": self.arm_stroke,
            "stem_x": self.stem_x,
            "stem_top": self.stem_top,
            "stem_bottom": self.stem_bottom,
            "stem_width": self.stem_width,
            "text_x": self.text_x,
            "text_y": self.text_y,
            "text_scale": self.text_scale,
        }
        for key, value in optional_values.items():
            if value is not None:
                out[key] = float(value)
        return out

def load_grayscale_image(path: Path) -> list[list[int]]:
    image_module = _import_with_vendored_fallback("PIL.Image")
    gray = image_module.open(path).convert("L")
    w, h = gray.size
    px = gray.load()
    return [[int(px[x, y]) for x in range(w)] for y in range(h)]


