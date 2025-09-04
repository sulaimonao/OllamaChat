# Local Search Feature

The local search feature allows the LLM to search through a collection of local documents to find relevant information. This is useful for answering questions about a specific domain or a set of documents.

The search engine is built using the `whoosh` library and is completely local. It indexes markdown files located in the `backend/local_data` directory. The search tool is available to the model via the `local_search` command.
