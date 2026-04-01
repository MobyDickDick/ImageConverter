def promptInteractiveRange(args: argparse.Namespace) -> tuple[str, str]:
    current_start = str(args.start or "").strip()
    current_end = str(args.end or "").strip()
    prompt_start = f"Namen von [{current_start}]: " if current_start else "Namen von: "
    prompt_end = f"Namen bis [{current_end}]: " if current_end else "Namen bis: "

    start_value = input(prompt_start).strip() or current_start
    end_value = input(prompt_end).strip() or current_end
    if not end_value:
        end_value = start_value

    shared = sharedPartialRangeToken(start_value, end_value)
    if shared and extractRefParts(start_value) is None and extractRefParts(end_value) is None:
        print(f"[INFO] Verwende Teilstring-Filter '{shared}' für die Auswahl der Bilder.")
    else:
        print(f"[INFO] Verwende Bereich von '{start_value or '(Anfang)'}' bis '{end_value or '(Ende)'}'.")
    return start_value, end_value
