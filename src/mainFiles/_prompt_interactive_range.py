def _prompt_interactive_range(args: argparse.Namespace) -> tuple[str, str]:
    current_start = str(args.start or "").strip()
    current_end = str(args.end or "").strip()
    prompt_start = f"Namen von [{current_start}]: " if current_start else "Namen von: "
    prompt_end = f"Namen bis [{current_end}]: " if current_end else "Namen bis: "

    entered_start = input(prompt_start).strip()
    entered_end = input(prompt_end).strip()
    start_value = entered_start or current_start
    end_value = entered_end or current_end

    # If users already enter a full range in "Namen von" (e.g. "AC080 - AC080")
    # and leave "Namen bis" empty, prefer the inline range over a potentially
    # stale default from a previous run.
    if entered_start and not entered_end and re.search(r"(?:-|–|—|BIS|TO|\.{2,3})", entered_start, flags=re.IGNORECASE):
        end_value = ""

    if not end_value:
        end_value = start_value
    start_value, end_value = _normalize_range_bounds(start_value, end_value)

    shared = _shared_partial_range_token(start_value, end_value)
    if shared and _extract_ref_parts(start_value) is None and _extract_ref_parts(end_value) is None:
        print(f"[INFO] Verwende Teilstring-Filter '{shared}' für die Auswahl der Bilder.")
    else:
        print(f"[INFO] Verwende Bereich von '{start_value or '(Anfang)'}' bis '{end_value or '(Ende)'}'.")
    return start_value, end_value
