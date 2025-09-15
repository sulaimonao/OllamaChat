import json
from unittest.mock import patch

from backend.search.run_bundle import run_bundle


def test_run_bundle_dedup_and_order():
    bundle = [
        {"type": "precision", "query": "first"},
        {"type": "recall", "query": "second"},
    ]

    hits1 = json.dumps([
        {"url": "http://a.com", "title": "A"},
        {"url": "http://b.com", "title": "B"},
    ])
    hits2 = json.dumps([
        {"url": "http://b.com", "title": "B2"},
        {"url": "http://c.com", "title": "C"},
    ])

    def fake_run(cmd, capture_output=True, text=True, check=True):
        q = cmd[4]
        class R:
            stdout = hits1 if q == "first" else hits2
        return R

    with patch("subprocess.run", fake_run):
        hits = run_bundle(bundle, limit_per_query=2)
    urls = [h["url"] for h in hits]
    assert urls == ["http://a.com", "http://b.com", "http://c.com"]
