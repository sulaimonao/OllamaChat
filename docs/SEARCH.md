# Search Engine Design (v2)

This document outlines the design and architecture of the v2 local search engine for OllamaChat.

## 1. Overview

The v2 search engine enhances the existing search functionality with hybrid search (lexical + semantic), automatic tool use by the LLM, and a more robust indexing pipeline. It is designed to be modular, configurable, and extensible.

## 2. Components

### 2.1. Indexing Pipeline

The indexing pipeline is responsible for parsing documents, splitting them into chunks, and storing them in two separate indexes: a Whoosh index for lexical search and a FAISS index for semantic search.

*   **Document Parsers:** The `_parse_document` function in `tools/search_engine.py` handles parsing of different file types. It supports `.md`, `.txt`, `.html` (using `BeautifulSoup`), and `.pdf` (using `pypdf`).
*   **Text Chunker:** The `_chunk_text` function uses `RecursiveCharacterTextSplitter` from LangChain to split the document content into smaller chunks (default size: 500 tokens, 100 overlap).
*   **Dual Indexers:**
    *   **Whoosh:** A `FileIndex` is used for lexical search. The schema includes `title`, `path`, `content`, `chunk_id`, and `source_id`.
    *   **FAISS:** A `IndexFlatL2` with `IndexIDMap` is used for semantic search. The embeddings are generated using the `all-MiniLM-L6-v2` model from `sentence-transformers`. The index and a mapping from FAISS IDs to chunk information are saved to disk.
*   **Incremental Indexing:** The `index` method computes the SHA256 hash of each file to determine if it has changed since the last indexing run. Unchanged files are skipped.

### 2.2. Search Pipeline

*   **Hybrid Search:** The `search_hybrid` method combines the results of `search_lexical` and `search_embeddings` using Reciprocal Rank Fusion (RRF) to re-rank the results.
*   **Snippet Generation:** Snippets are generated using Whoosh's highlighting feature.

### 2.3. Agent Integration

*   **Formal Tool Definition:** The `local_search` function is decorated with `@tool` from LangChain. It uses a Pydantic model (`LocalSearchInput`) to define its arguments (`query` and `top_k`).
*   **Agentic Invocation:** The `chat.py` endpoint now uses `create_tool_calling_agent` and `AgentExecutor` from LangChain to create an agent that can automatically decide when to call the `local_search` tool.

### 2.4. Configuration

*   Settings are managed in `backend/config/search.yaml`. The `load_search_config` function in `config.py` loads this file and provides default values.

### 2.5. CLI

*   A command-line interface (`tools/search_cli.py`) is provided for manual indexing and testing. It supports `index` and `search` commands.

## 3. API

The search tool returns a list of JSON objects with the following schema:
```json
[
  {
    "title": "...",
    "snippet": "...",
    "url": "...",
    "source_id": "...",
    "chunk_id": "...",
    "highlights": ["..."],
    "score": 0.0,
    "type": "lexical" | "semantic"
  }
]
```

## 4. Future Improvements

*   [ ] Real-time indexing (e.g., using a file system watcher).
*   [ ] More advanced RAG techniques (e.g., query transformations, reranking with a cross-encoder).
*   [ ] Support for more document types (e.g., `.docx`, `.pptx`).
*   [ ] Better handling of large files (e.g., streaming).
*   [ ] More sophisticated deduplication logic in hybrid search.
