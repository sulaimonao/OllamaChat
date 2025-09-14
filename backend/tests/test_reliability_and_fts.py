from datetime import datetime
import sys, pathlib
base = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(base))
from tools.termsearch.core import _fts_safe
from tools.live_browse_utils import compute_reliability

def test_fts_safe_apostrophe():
    assert _fts_safe("today's news") == '"today\'s" "news"'

def test_compute_reliability_trusted():
    doc = {
        "url": "https://www.reuters.com/some-article",
        "text": "a" * 1200 + " http http http",
        "meta": {"fetched_at": datetime.utcnow().isoformat(), "author": "Anon"},
    }
    policy = {"freshness_days": 7}
    score = compute_reliability(doc, policy)
    assert score >= 0.55
