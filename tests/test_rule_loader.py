from drace.darkian import get_rules


def _modules(rules):
    return {rule.__module__.split(".")[-1] for rule in rules}


def test_only_filters_by_rule_code():
    rules = get_rules(ignore=(), only=["Z221"])
    assert _modules(rules) == {"z221"}


def test_ignore_excludes_rule_code():
    rules = get_rules(ignore=("Z221",), only=[])
    assert "z221" not in _modules(rules)


def test_monolith_rule_file_not_discovered():
    rules = get_rules(ignore=(), only=[])
    assert "z22_" not in _modules(rules)
