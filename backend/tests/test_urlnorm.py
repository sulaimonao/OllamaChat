from backend.search.urlnorm import canonicalize


def test_canonicalize_equivalent():
    u1 = "HTTP://Example.com:80//A/B/?q=1#frag"
    u2 = "http://example.com/a/b"
    assert canonicalize(u1) == canonicalize(u2)
