from pathlib import Path

from cnat import api


def translate(path: str | Path) -> tuple[str | Path, bool]:
    found = False

    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"): continue
            if "@natlang" in line:
                try:
                    lang  = line.split(":::", 1)[1].strip()
                    found = True
                except IndexError: pass

    if not found: return path, False
    return api.cnat(path, lang, get=True), True
