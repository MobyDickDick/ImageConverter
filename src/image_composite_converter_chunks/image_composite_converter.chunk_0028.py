            "stem_or_arm_len": stem_or_arm_len,
        }

    @staticmethod
    def _default_edge_anchored_circle_geometry(
        w: int,
        h: int,
        *,
        anchor: str,
        radius_ratio: float = 0.43,
        stroke_divisor: float = 15.0,
        edge_clearance_ratio: float = 0.08,
        edge_clearance_stroke_factor: float = 0.75,
    ) -> dict[str, float]:
        """Return circle geometry for connector badges anchored near one canvas edge.

        Elongated AC08 connector badges use a circle that is sized from the narrow
        canvas dimension and visually offset away from the edge where the connector
        originates. Using the same clearance rule for each anchor direction keeps
        the ring from appearing clipped without baking variant-specific offsets into
        one SKU.
        """
        narrow = float(min(w, h))
        stroke_circle = max(0.9, narrow / stroke_divisor)
        r = narrow * radius_ratio
        cx = float(w) / 2.0
        cy = float(h) / 2.0
        edge_clearance = max(stroke_circle * edge_clearance_stroke_factor, narrow * edge_clearance_ratio)

        anchor_key = anchor.lower()
        if anchor_key == "top":
            cy = r + edge_clearance
        elif anchor_key == "bottom":
            cy = float(h) - (r + edge_clearance)
        elif anchor_key == "left":
            cx = r + edge_clearance
        elif anchor_key == "right":
            cx = float(w) - (r + edge_clearance)
        else:
            raise ValueError(f"Unsupported anchor: {anchor}")

        return {
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
        }

    @staticmethod
    def _default_ac0811_params(w: int, h: int) -> dict:
        """AC0811 is vertically elongated: circle sits in the upper square area."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        circle = Action._default_edge_anchored_circle_geometry(w, h, anchor="top")
        cx = float(circle["cx"])
        cy = float(circle["cy"])
        r = float(circle["r"])
        stroke_circle = float(circle["stroke_circle"])
        stem_width = max(1.0, float(w) * 0.10)
        # AC0811 reference symbols use a visually slim vertical handle.
        # Persist an explicit width ceiling so later fitting/validation
        # steps cannot widen the stem beyond the template's intent.
        stem_width_max = max(1.0, float(w) * 0.105)
        stem_len = max(2.0, float(h) - (cy + r))

        return Action._normalize_light_circle_colors({
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
            "stroke_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
            "fill_gray": Action.LIGHT_CIRCLE_FILL_GRAY,
            "draw_text": False,
            "stem_enabled": True,
            "stem_width": stem_width,
            "stem_width_max": stem_width_max,
            "stem_x": cx - (stem_width / 2.0),
            "stem_top": cy + r,
            "stem_bottom": min(float(h), (cy + r) + stem_len),
            "stem_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
        })

    @staticmethod
    def _estimate_upper_circle_from_foreground(img: np.ndarray, defaults: dict) -> tuple[float, float, float] | None:
        """Estimate circle geometry from the upper symbol region.

        AC0811_S is very small and Hough-based fitting can drift on anti-aliased
        edges. This fallback uses a simple foreground extraction in the upper part
        of the symbol and derives a robust enclosing circle from the largest blob.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if h <= 0 or w <= 0:
            return None

        _, fg = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        top_limit = int(round(min(float(h), float(defaults.get("cy", h / 2.0)) + float(defaults.get("r", w / 3.0)) * 1.15)))
        top_limit = max(3, min(h, top_limit))
        roi = fg[:top_limit, :]
