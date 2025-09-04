import unittest
import os
import shutil
import sys
import yaml

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.search_engine import SearchEngine, _parse_document, _chunk_text

class TestSearchEngineV2(unittest.TestCase):

    def setUp(self):
        self.test_dir = "backend/tests/test_artifacts"
        self.index_dir = os.path.join(self.test_dir, "index")
        self.data_dir = os.path.join(self.test_dir, "data")
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")

        # Create test directories
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # Create test config file
        with open(self.config_path, "w") as f:
            yaml.dump({"enable_hybrid": True}, f)

        # Create dummy files for indexing
        with open(os.path.join(self.data_dir, "test.txt"), "w") as f:
            f.write("This is a test file about python programming.")
        with open(os.path.join(self.data_dir, "test.md"), "w") as f:
            f.write("# Markdown Test\n\nThis is a test file about javascript frameworks.")
        with open(os.path.join(self.data_dir, "test.html"), "w") as f:
            f.write("<html><body><h1>HTML Test</h1><p>This is a test file about rust language.</p></body></html>")

        # A longer file for chunking test
        long_text = "This is a very long document that is used for testing the chunking functionality. " * 10
        with open(os.path.join(self.data_dir, "long_doc.txt"), "w") as f:
            f.write(long_text)

        self.search_engine = SearchEngine(config_path=self.config_path, index_dir=self.index_dir)

        # Index the files
        file_paths = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir)]
        self.search_engine.index(file_paths)

    def tearDown(self):
        # Clean up the created directories
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        self.assertIsNotNone(self.search_engine)
        self.assertTrue(os.path.exists(self.search_engine.whoosh_dir))
        if self.search_engine.config.get("enable_hybrid"):
            self.assertIsNotNone(self.search_engine.faiss_index)

    def test_file_parsing(self):
        self.assertIn("python", _parse_document(os.path.join(self.data_dir, "test.txt")))
        self.assertIn("javascript", _parse_document(os.path.join(self.data_dir, "test.md")))
        self.assertIn("rust", _parse_document(os.path.join(self.data_dir, "test.html")))

    def test_chunking(self):
        text = "This is a long sentence. " * 50
        chunks = _chunk_text(text, chunk_size=100, chunk_overlap=20)
        self.assertGreater(len(chunks), 1)

    def test_indexing(self):
        # Check Whoosh index
        self.assertGreater(self.search_engine.ix.doc_count(), 0)
        # Check FAISS index
        if self.search_engine.config.get("enable_hybrid"):
            self.assertGreater(self.search_engine.faiss_index.ntotal, 0)

    def test_lexical_search(self):
        results = self.search_engine.search_lexical("python")
        self.assertEqual(len(results), 1)
        self.assertIn("python", results[0]["snippet"])

    def test_semantic_search(self):
        if self.search_engine.config.get("enable_hybrid"):
            results = self.search_engine.search_embeddings("javascript")
            self.assertGreaterEqual(len(results), 1)
            # The exact content is not guaranteed, but it should find the relevant document
            self.assertIn("javascript", results[0]["snippet"].lower())

    def test_hybrid_search(self):
        if self.search_engine.config.get("enable_hybrid"):
            results = self.search_engine.search_hybrid("rust")
            self.assertGreaterEqual(len(results), 1)
            self.assertIn("rust", results[0]["snippet"].lower())

    def test_search_result_format(self):
        results = self.search_engine.search("python")
        self.assertGreaterEqual(len(results), 1)
        result = results[0]
        self.assertIn("title", result)
        self.assertIn("snippet", result)
        self.assertIn("url", result)
        self.assertIn("source_id", result)
        self.assertIn("highlights", result)
        self.assertIn("score", result)

if __name__ == '__main__':
    unittest.main()
