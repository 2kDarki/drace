from .z200 import z200, z201, z202, z227, z22_
from drace.constants import IGNORED_RULES
from drace import utils

def rule_z2_series(lines: list[str], tree, file: str) -> list[dict]:
    results = []
    rules   = [z200, z202, z227] 
    methods = [lines, tree]

    for method, rule in zip(methods, rules):
        if (rule.__name__[-4:]).upper() in IGNORED_RULES:
            continue
        results.extend(rule.check(method, file))

    results.extend(z201.check(lines, tree, file))
    results.extend(z22_.check(lines, tree, file))

    return results
