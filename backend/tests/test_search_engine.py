import unittest
import os
import shutil
import sys

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.search_engine import SearchEngine

class TestSearchEngine(unittest.TestCase):

    def setUp(self):
        self.index_dir = "backend/tests/test_index"
        self.data_dir = "backend/tests/test_data"

        # Create test data directory
        os.makedirs(self.data_dir, exist_ok=True)

        # Create dummy files for indexing
        with open(os.path.join(self.data_dir, "test1.md"), "w") as f:
            f.write("This is a test file about python.")
        with open(os.path.join(self.data_dir, "test2.md"), "w") as f:
            f.write("This is a test file about javascript.")

        self.search_engine = SearchEngine(index_dir=self.index_dir)

        # Index the files
        file_paths = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir)]
        self.search_engine.index_files(file_paths)

    def tearDown(self):
        # Clean up the created directories
        if os.path.exists(self.index_dir):
            shutil.rmtree(self.index_dir)
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def test_initialization(self):
        self.assertIsNotNone(self.search_engine)
        self.assertTrue(os.path.exists(self.index_dir))

    def test_indexing(self):
        self.assertEqual(self.search_engine.ix.doc_count(), 2)

    def test_search(self):
        results = self.search_engine.search("python")
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertIn("title", result)
        self.assertIn("snippet", result)
        self.assertIn("url", result)
        self.assertEqual(result["title"], "test1.md")

    def test_search_no_results(self):
        results = self.search_engine.search("ruby")
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
