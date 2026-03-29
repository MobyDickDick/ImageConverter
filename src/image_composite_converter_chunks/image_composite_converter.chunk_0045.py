                    f'  <circle cx="{p["cx"]:.4f}" cy="{p["cy"]:.4f}" r="{p["r"]:.4f}" '
                    f'fill="{Action.grayhex(p["fill_gray"])}" stroke="{Action.grayhex(p["stroke_gray"])}" '
                    f'stroke-width="{p["stroke_circle"]:.4f}"/>'
                )
            )

        if p.get("draw_text", True):
            if p.get("text_mode") == "path_t":
                elements.append(
                    (
                        f'  <path d="{Action.T_PATH_D}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'transform="translate({p["tx"]:.4f},{p["ty"]:.4f}) '
                        f'scale({p["s"]:.6f},{-p["s"]:.6f}) '
                        f'translate({-Action.T_XMIN},{-Action.T_YMAX})"/>'
                    )
                )
            elif p.get("text_mode") == "co2":
                layout = Action._co2_layout(p)
                font_size = float(layout["font_size"])
                y_text = float(layout["y_base"])
                width_scale = float(layout.get("width_scale", 1.0))
                elements.append(
                    (
                        f'  <text x="{float(layout["co_x"]):.4f}" y="{y_text:.4f}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.4f}px" '
                        f'font-style="normal" font-weight="600" text-anchor="middle" dominant-baseline="middle" '
                        f'transform="translate({float(layout["co_x"]):.4f} {y_text:.4f}) scale({width_scale:.4f} 1) '
                        f'translate({-float(layout["co_x"]):.4f} {-y_text:.4f})">CO</text>'
                    )
                )
                elements.append(
                    (
                        f'  <text x="{float(layout["subscript_x"]):.4f}" y="{float(layout["subscript_y"]):.4f}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'font-family="Arial, Helvetica, sans-serif" font-size="{float(layout["sub_font_px"]):.4f}px" '
                        f'font-style="normal" font-weight="600" text-anchor="start" dominant-baseline="middle" '
                        f'transform="translate({float(layout["subscript_x"]):.4f} {float(layout["subscript_y"]):.4f}) scale({width_scale:.4f} 1) '
                        f'translate({-float(layout["subscript_x"]):.4f} {-float(layout["subscript_y"]):.4f})">2</text>'
                    )
                )
            elif p.get("text_mode") == "voc":
                radius = p.get("r", min(w, h) * 0.4)
                font_size = max(4.0, radius * p.get("voc_font_scale", 0.52))
                voc_dy = p.get("voc_dy", 0.0)
                voc_weight = int(p.get("voc_weight", 600))
                elements.append(
                    (
                        f'  <text x="{p["cx"]:.4f}" y="{(p["cy"] + voc_dy):.4f}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.4f}px" '
                        f'font-style="normal" font-weight="{voc_weight}" letter-spacing="0.01em" '
                        f'text-anchor="middle" dominant-baseline="middle">VOC</text>'
                    )
                )
            else:
                elements.append(
                    (
                        f'  <path d="{Action.M_PATH_D}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'transform="translate({p["tx"]:.4f},{p["ty"]:.4f}) '
                        f'scale({p["s"]:.6f},{-p["s"]:.6f}) '
                        f'translate({-Action.M_XMIN},{-Action.M_YMAX})"/>'
                    )
                )

        elements.append("</svg>")
        return "\n".join(elements)

    @staticmethod
    def trace_image_segment(
        img_segment: np.ndarray,
        epsilon_factor: float,
        *,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> list[str]:
        if img_segment is None or img_segment.size == 0:
            return []

        data = np.float32(img_segment).reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
        _, labels, centers = cv2.kmeans(data, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        img_quant = centers[labels.flatten()].reshape(img_segment.shape)

        unique, counts = np.unique(img_quant.reshape(-1, 3), axis=0, return_counts=True)
        bg_color = unique[np.argmax(counts)]

        paths: list[str] = []
        for color in unique:
            if np.array_equal(color, bg_color):
                continue

            mask = cv2.inRange(img_quant, color, color)
            # Keep the raw contour points and let approxPolyDP control how much
            # simplification is applied via `epsilon_factor`.
            #
            # With CHAIN_APPROX_SIMPLE, OpenCV already drops many intermediate
            # points, which can make the iterative epsilon sweep effectively a
            # no-op (same polygon across all iterations).
            contours, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
