from drace.constants import KEYWORDS, LINE_LEN
from drace.types import Context, Dict


def check_z200(context: Context) -> list[Dict]:
    """
    Z200: Encourage compact control blocks.

    Flags control blocks with a single meaningful line,
    suggesting conversion to one-liners (if under line length
    limit), even if nested inside other blocks
    """
    lines   = context["lines"]
    file    = context["file"]
    results = []
    i       = 0
    total   = len(lines)

    while i < total:
        line  = lines[i]
        sline = line.strip()

        i += 1
        if sline.startswith(KEYWORDS) and sline.endswith(":"):
            indent = len(line) - len(line.lstrip())
            block  = []
            j      = i

            while j < total:
                next_line = lines[j]
                if not next_line.strip(): j += 1; continue
                next_indent = len(next_line) \
                            - len(next_line.lstrip())
                if next_indent <= indent: break
                block.append((j, next_line.strip()))
                j += 1

            # Check only meaningful lines
            exclude = list(KEYWORDS) + ["#"]
            body    = [b for _, b in block if b and not
                      (b.startswith(e) for e in exclude)]
            if len(body) == 1:
                compact = f"{line.rstrip()} {body[0]}"
                if len(compact) <= LINE_LEN:
                    results.append({
                        "file": file,
                        "line": i,
                        "col": 1,
                        "code": "Z200",
                        "msg": "control block could be "
                               "compacted to a one-liner"
                    })

    return results
