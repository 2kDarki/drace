from drace.types import Context, Fix


def fixes_z104(context: Context) -> list[Fix]:
    """
    Collapse blank-line runs to at most two lines.
    """
    lines = context["lines"]
    fixes: list[Fix] = []
    start = None

    for i, line in enumerate(lines, start=1):
        is_blank = line.strip() == ""
        if is_blank and start is None:
            start = i
            continue
        if not is_blank and start is not None:
            end = i - 1
            count = end - start + 1
            if count > 2:
                fixes.append({
                    "op": "replace_block",
                    "start": start,
                    "end": end,
                    "content": ["", ""],
                })
            start = None

    if start is not None:
        end = len(lines)
        count = end - start + 1
        if count > 2:
            fixes.append({
                "op": "replace_block",
                "start": start,
                "end": end,
                "content": ["", ""],
            })

    return fixes
