import os
import shutil
import hashlib
import json
import numpy as np
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.qparser import QueryParser
from whoosh.highlight import UppercaseFormatter, HtmlFormatter
from bs4 import BeautifulSoup
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from config import load_search_config

# --- Document Parsing and Chunking ---

def _parse_document(file_path):
    """Parses a document and returns its text content."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".txt" or ext == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".html":
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                return soup.get_text()
        elif ext == ".pdf":
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                return "\n".join(page.extract_text() for page in reader.pages)
        else:
            return None
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
        return None

def _chunk_text(text, chunk_size=500, chunk_overlap=100):
    """Splits text into chunks."""
    if not text:
        return []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

# --- Pydantic Schema for the Tool ---

class LocalSearchInput(BaseModel):
    """Input for the local_search tool."""
    query: str = Field(description="The search query to execute.")
    top_k: int = Field(default=8, description="The number of top results to return.")

# --- The SearchEngine Class ---

class SearchEngine:
    def __init__(self, config_path=None, index_dir="backend/indexdir"):
        self.config = load_search_config(config_path)
        self.index_dir = index_dir
        self.whoosh_dir = os.path.join(self.index_dir, "whoosh")
        self.faiss_index_path = os.path.join(self.index_dir, "faiss.index")
        self.faiss_mapping_path = os.path.join(self.index_dir, "faiss_mapping.json")
        self.file_hashes_path = os.path.join(self.index_dir, "file_hashes.json")

        self.ix = None
        self.embedding_model = None
        self.faiss_index = None
        self.faiss_id_to_chunk = {}
        self.schema = Schema(
            title=TEXT(stored=True),
            path=ID(stored=True),
            content=TEXT(stored=True),
            chunk_id=ID(stored=True, unique=True),
            source_id=ID(stored=True)
        )

    def load(self):
        """Loads the search index. This should be called before any search or index operations."""
        if self.ix is not None:
            return

        os.makedirs(self.whoosh_dir, exist_ok=True)

        try:
            self.ix = open_dir(self.whoosh_dir)
        except Exception:
            self.ix = create_in(self.whoosh_dir, self.schema)

        if self.config.get("enable_hybrid", False):
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            if os.path.exists(self.faiss_index_path):
                self.faiss_index = faiss.read_index(self.faiss_index_path)
                with open(self.faiss_mapping_path, 'r') as f:
                    self.faiss_id_to_chunk = json.load(f)
            else:
                d = self.embedding_model.get_sentence_embedding_dimension()
                self.faiss_index = faiss.IndexFlatL2(d)
                self.faiss_index = faiss.IndexIDMap(self.faiss_index)

    def _get_file_hash(self, file_path):
        """Computes the SHA256 hash of a file."""
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    def index(self, file_paths):
        """Indexes documents, including parsing, chunking, and vectorization."""
        writer = self.ix.writer()

        if os.path.exists(self.file_hashes_path):
            with open(self.file_hashes_path, 'r') as f:
                file_hashes = json.load(f)
        else:
            file_hashes = {}

        new_chunks = []
        new_faiss_ids = []
        new_faiss_vectors = []

        for file_path in file_paths:
            file_hash = self._get_file_hash(file_path)
            if file_hashes.get(file_path) == file_hash:
                print(f"Skipping unchanged file: {file_path}")
                continue

            content = _parse_document(file_path)
            if not content:
                continue

            chunks = _chunk_text(content)
            title = os.path.basename(file_path)
            source_id = file_path

            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{file_path}_{i}"

                # Whoosh indexing
                writer.add_document(
                    title=title,
                    path=file_path,
                    content=chunk_text,
                    chunk_id=chunk_id,
                    source_id=source_id
                )

                # FAISS indexing
                if self.config.get("enable_hybrid", False):
                    chunk_info = {
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "title": title,
                        "url": file_path,
                        "source_id": source_id,
                    }
                    new_chunks.append(chunk_info)

            file_hashes[file_path] = file_hash
            print(f"Indexing {file_path}...")

        if self.config.get("enable_hybrid", False) and new_chunks:
            embeddings = self.embedding_model.encode([c['text'] for c in new_chunks], convert_to_tensor=True)
            embeddings_np = embeddings.cpu().numpy().astype('float32')

            start_id = len(self.faiss_id_to_chunk)
            ids = np.arange(start_id, start_id + len(new_chunks))

            self.faiss_index.add_with_ids(embeddings_np, ids)

            for i, chunk_info in enumerate(new_chunks):
                self.faiss_id_to_chunk[str(start_id + i)] = chunk_info

        writer.commit()

        with open(self.file_hashes_path, 'w') as f:
            json.dump(file_hashes, f)

        if self.config.get("enable_hybrid", False):
            faiss.write_index(self.faiss_index, self.faiss_index_path)
            with open(self.faiss_mapping_path, 'w') as f:
                json.dump(self.faiss_id_to_chunk, f)

        print("Indexing complete.")

    def search(self, query, top_k=8):
        """Dispatches to the correct search method based on configuration."""
        if self.config.get("enable_hybrid", False):
            return self.search_hybrid(query, top_k)
        else:
            return self.search_lexical(query, top_k)

    def search_lexical(self, query_str, top_k=8):
        """Performs a lexical search using Whoosh."""
        results_list = []
        with self.ix.searcher() as searcher:
            query = QueryParser("content", self.ix.schema).parse(query_str)
            results = searcher.search(query, limit=top_k)
            results.formatter = HtmlFormatter(tagname="strong")

            for hit in results:
                snippet = hit.highlights("content", top=1)
                if not snippet:
                    snippet = hit['content'][:200] + '...'

                results_list.append({
                    "title": hit["title"],
                    "snippet": snippet,
                    "url": hit["path"],
                    "source_id": hit["source_id"],
                    "highlights": [hit.highlights("content", top=3)],
                    "score": float(hit.score),
                    "type": "lexical"
                })
        return results_list

    def search_embeddings(self, query_str, top_k=8):
        """Performs a semantic search using FAISS."""
        if not self.embedding_model or not self.faiss_index:
            return []

        query_embedding = self.embedding_model.encode([query_str], convert_to_tensor=True).cpu().numpy().astype('float32')
        distances, ids = self.faiss_index.search(query_embedding, top_k)

        results_list = []
        for i, doc_id in enumerate(ids[0]):
            if doc_id != -1:
                chunk_info = self.faiss_id_to_chunk[str(doc_id)]
                results_list.append({
                    "title": chunk_info["title"],
                    "snippet": chunk_info["text"][:200] + '...',
                    "url": chunk_info["url"],
                    "source_id": chunk_info["source_id"],
                    "chunk_id": chunk_info["chunk_id"],
                    "highlights": [],
                    "score": float(1 / (1 + distances[0][i])), # Convert distance to similarity score
                    "type": "semantic"
                })
        return results_list

    def search_hybrid(self, query, top_k=8, k_lexical=20, k_semantic=20, rrf_k=60):
        """Performs a hybrid search using Reciprocal Rank Fusion."""
        lexical_results = self.search_lexical(query, top_k=k_lexical)
        semantic_results = self.search_embeddings(query, top_k=k_semantic)

        # RRF scoring
        rrf_scores = {}
        for i, res in enumerate(lexical_results):
            chunk_id = res.get("chunk_id")
            if not chunk_id: continue
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"score": 0, "doc": res}
            rrf_scores[chunk_id]["score"] += 1 / (rrf_k + i + 1)

        for i, res in enumerate(semantic_results):
            chunk_id = res.get("chunk_id")
            if not chunk_id: continue
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"score": 0, "doc": res}
            rrf_scores[chunk_id]["score"] += 1 / (rrf_k + i + 1)

        # Sort by RRF score
        sorted_results = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)

        # Format the results
        final_results = [res['doc'] for res in sorted_results]
        return final_results[:top_k]

# --- Tool Definition ---

_search_engine_instance = None

def get_search_engine():
    """Returns a singleton instance of the SearchEngine."""
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = SearchEngine()
        _search_engine_instance.load()
    return _search_engine_instance

@tool(args_schema=LocalSearchInput)
def local_search(query: str, top_k: int = 8) -> list[dict]:
    """
    Search the local document index for information.
    Use this tool when you need to answer questions based on local files,
    or when the user asks for information that might be in the local documentation.
    """
    search_engine = get_search_engine()
    return search_engine.search(query, top_k=top_k)
