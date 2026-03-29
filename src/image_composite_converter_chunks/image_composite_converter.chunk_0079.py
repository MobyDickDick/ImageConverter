        )
        observed = {
            "circle": bool(
                (structural.get("circle", False) and (local_support["circle"] if require_circle_mask_confirmation else True))
                or (allow_circle_mask_fallback and local_support["circle"])
                or connector_circle_mask_fallback
                or small_connector_circle_mask_fallback
            ),
            "stem": bool(
                local_support["stem"]
                or (
                    structural.get("stem", False)
                    and not plain_circle_badge
                    and not suppress_structural_stem_for_horizontal_connector
                )
            ),
            "arm": bool(
                local_support["arm"]
                or (
                    structural.get("arm", False)
                    and not structural.get("stem", False)
                    and not plain_circle_badge
                    and not (
                        vertical_connector_family
                        and expected.get("arm", False) is False
                        and local_support["circle"]
                        and local_support["arm"] is False
                    )
                )
            ),
            "text": bool(local_support["text"] or (structural.get("text", False) and not plain_circle_badge)),
        }
        issues = Action._semantic_presence_mismatches(expected, observed)
        if expected.get("circle") and not observed["circle"]:
            issues.append("Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt")
        if expected.get("arm") and not observed["arm"]:
            issues.append("Strukturprüfung: Kein belastbarer waagrechter Linien-Kandidat im Rohbild erkannt")
        if expected.get("text") and not observed["text"]:
            issues.append("Strukturprüfung: Keine belastbare Textstruktur (z.B. CO₂) im Rohbild erkannt")
        if expected_co2 and expected.get("text"):
            if text_mask is None:
                issues.append("Strukturprüfung: CO₂-Textregion enthält keine verwertbaren Vordergrundpixel")
            else:
                ys, xs = np.where(text_mask)
                if ys.size == 0 or xs.size == 0:
                    issues.append("Strukturprüfung: CO₂-Textregion konnte nicht lokalisiert werden")
                else:
                    x1, x2 = int(xs.min()), int(xs.max())
                    y1, y2 = int(ys.min()), int(ys.max())
                    roi = Action._foreground_mask(img_orig)[y1 : y2 + 1, x1 : x2 + 1].astype(np.uint8)
                    n_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(roi, connectivity=8)
                    compact = 0
                    merged_text_blob = False
                    roi_h, roi_w = roi.shape[:2]
                    roi_area = max(1, roi_h * roi_w)
                    for idx in range(1, n_labels):
                        area = int(stats[idx, cv2.CC_STAT_AREA])
                        if area < 2:
                            continue
                        width = int(stats[idx, cv2.CC_STAT_WIDTH])
                        height = int(stats[idx, cv2.CC_STAT_HEIGHT])
                        aspect = float(width) / max(1.0, float(height))
                        if 0.2 <= aspect <= 4.5:
                            compact += 1
                            density = float(area) / max(1.0, float(width * height))
                            coverage = float(area) / float(roi_area)
                            # JPEG anti-aliasing can merge the full CO₂ cluster into
                            # a single compact foreground island, especially in
                            # elongated connector badges such as AC0831_L. Accept
                            # that case when the blob is large/dense enough to be a
                            # plausible merged text cluster instead of noise.
                            if (
                                compact == 1
                                and 0.75 <= aspect <= 1.80
                                and density >= 0.30
                                and coverage >= 0.18
                            ):
                                merged_text_blob = True
                    if compact < 2 and not merged_text_blob:
                        issues.append("Strukturprüfung: Erwartete CO₂-Glyphenstruktur nicht ausreichend belegt")
        return issues

    @staticmethod
    def validate_badge_by_elements(
        img_orig: np.ndarray,
        params: dict,
        *,
        max_rounds: int = 6,
        debug_out_dir: str | None = None,
        apply_circle_geometry_penalty: bool = True,
        stop_when_error_below_threshold: bool = False,
    ) -> list[str]:
        h, w = img_orig.shape[:2]
        logs: list[str] = []
        elements = ["circle"]
        if params.get("stem_enabled"):
            elements.append("stem")
        if params.get("arm_enabled"):
            elements.append("arm")
        if params.get("draw_text", True):
