from backend.search.query_bundle import build_query_bundle


def test_bundle_structure():
    bundle = build_query_bundle("new ai models")
    types = {b['type'] for b in bundle}
    assert types == {"precision", "recall", "exploration", "validation"}
    for b in bundle:
        assert b['query'].count('"') % 2 == 0
    prec = next(b['query'] for b in bundle if b['type'] == 'precision')
    expl = next(b['query'] for b in bundle if b['type'] == 'exploration')
    assert "--QDF=4" in prec
    assert "--QDF=4" in expl
