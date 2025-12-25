from drace.constants import KEYWORDS, LINE_LEN


def check(lines: list[str], file: str) -> list[dict]:  
    """  
    Z200: Encourage compact control blocks.  
  
    Flags control blocks with a single meaningful line, 
    suggesting conversion to one-liners (if under line length 
    limit), even if nested inside other blocks  
    """  
    results = []  
    i       = 0  
    total   = len(lines)  
  
    while i < total:  
        line     = lines[i]  
        stripped = line.strip()  
  
        if stripped.startswith(KEYWORDS) and stripped.endswith(":"):  
            indent = len(line) - len(line.lstrip())  
            block  = []  
            j      = i + 1  
  
            while j < total:  
                next_line = lines[j]  
                if not next_line.strip():  
                    j += 1  
                    continue  
                next_indent = len(next_line) - len(next_line.lstrip())  
                if next_indent <= indent:  
                    break  
                block.append((j, next_line.strip()))  
                j += 1  
  
            # Check only meaningful lines  
            body = [b for _, b in block if b and not b.startswith("#")]  
            if len(body) == 1:  
                compact = f"{stripped} {body[0]}"  
                if len(compact) <= LINE_LEN:  
                    results.append({  
                        "file": file,  
                        "line": i + 1,  
                        "col": 1,  
                        "code": "Z200",  
                        "msg": "control block could be compacted to a one-liner"  
                    })  
  
            i += 1
        else: i += 1

    return results
