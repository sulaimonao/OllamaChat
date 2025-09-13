import pytest
from backend.tools.termsearch.core import _fts_safe

@pytest.mark.parametrize("text, expected", [
    ("test", '"test"'),
    ("today's news", '"today\'s" "news"'),
    ('a "b" c', '"a" """b""" "c"'),
    ("  leading", '"leading"'),
    ("trailing  ", '"trailing"'),
    (None, ""),
    ("", ""),
    ("  ", ""),
])
def test_fts_safe(text, expected):
    assert _fts_safe(text) == expected
