import pytest
import sqlite3
from backend.tools.termsearch.core import Index

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test.db"
    idx = Index(path=str(db_path))
    idx.upsert("https://example.com/1", "doc one", "some text content", "hash1")
    idx.upsert("https://example.com/2", "doc two", "today's news is important", "hash2")
    return idx

def test_query_apostrophe_does_not_crash(temp_db):
    try:
        hits = temp_db.query("today's news")
        # We should get the second doc
        assert len(hits) > 0
        assert hits[0]["title"] == "doc two"
    except sqlite3.OperationalError as e:
        pytest.fail(f"FTS5 query with apostrophe crashed: {e}")
