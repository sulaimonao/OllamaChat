import os
import shutil
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from whoosh.highlight import UppercaseFormatter

class SearchEngine:
    def __init__(self, index_dir="backend/indexdir"):
        self.index_dir = index_dir
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            self.ix = self._create_index()
        else:
            try:
                self.ix = open_dir(self.index_dir)
            except Exception:
                shutil.rmtree(self.index_dir)
                os.makedirs(self.index_dir)
                self.ix = self._create_index()


    def _create_index(self):
        schema = Schema(
            title=TEXT(stored=True),
            path=ID(stored=True),
            content=TEXT(stored=True)
        )
        return create_in(self.index_dir, schema)

    def index_files(self, file_paths):
        writer = self.ix.writer()
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                title = os.path.basename(file_path)
                writer.add_document(title=title, path=file_path, content=content)
            except Exception as e:
                print(f"Failed to index {file_path}: {e}")
        writer.commit()

    def search(self, query_str):
        results_list = []
        with self.ix.searcher() as searcher:
            query = QueryParser("content", self.ix.schema).parse(query_str)
            results = searcher.search(query, limit=5)

            results.formatter = UppercaseFormatter()

            for hit in results:
                # Use searcher.stored_fields(hit.docnum) to get all stored fields
                stored_fields = hit

                # Generate a snippet (highlighted fragment)
                # Ensure the content field is available for highlighting
                snippet = hit.highlights("content")
                if not snippet:
                    # If no highlight, take the first 200 chars
                    content_field = stored_fields.get('content', '')
                    snippet = content_field[:200] + '...' if len(content_field) > 200 else content_field


                results_list.append({
                    "title": stored_fields.get('title', 'No Title'),
                    "snippet": snippet,
                    "url": stored_fields.get('path', 'No Path')
                })
        return results_list
