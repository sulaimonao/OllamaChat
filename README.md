# Chat Interface Application

This repository contains a complete chat interface application. The app lets users send messages and receive responses from local language models (accessed via Ollama). All chat messages are stored in an SQLite database, and the code is organized for easy extensibility.

## Features
- **Local Search:** The model can search local documents to answer questions.
- **Live Browsing:** When `use_browser` is enabled, the backend fetches current news from RSS feeds, site search or topic hubs and returns a summary with citations. Sources are saved under `backend/local_data/web_live` for hybrid search.
- **Multimodal Ingestion:** Images, audio and video can be analyzed and transcribed. Extracted text is written to `backend/local_data/mm` so text-only models can reference it.
- Send messages to language models.
- Select a model for each conversation.
- Store chat messages (user and model responses) in an SQLite database.
- View past conversations (chat history).
- **List Installed Models:** The system locates and shows previously installed models.

### Local Search v2 (Hybrid Search & Auto Tool-Use)
The local search feature has been upgraded to v2. It now features:
- **Hybrid Search:** Combines lexical (BM25F) and semantic search for better results.
- **Automatic Tool Use:** The LLM can now decide on its own when to use the search tool.
- **Expanded Document Support:** Can parse `.md`, `.txt`, `.html`, and `.pdf` files.
- **Configuration:** Search behavior can be configured in `backend/config/search.yaml`.
- **Command-Line Interface:** A new CLI for manual indexing and searching.

#### Optional Dependencies
To enable hybrid search and parsing for all document types, you need to install optional dependencies:
```bash
pip install -r backend/requirements.txt
```
The new optional dependencies are: `sentence-transformers`, `faiss-cpu`, `beautifulsoup4`, `pypdf`, `pyyaml`, `langchain`, and `langchain-text-splitters`.

#### Configuration
You can configure the search engine by editing `backend/config/search.yaml`. The available options are:
- `allowlist`: A list of directories or files to index.
- `enable_hybrid`: Set to `true` to enable hybrid search (requires optional dependencies).
- `top_k`: The default number of results to return.

#### Command-Line Interface
You can use the CLI to manage the search index:
- **Index documents:**
  ```bash
  python -m backend.tools.search_cli index backend/local_data
  ```
- **Search the index:**
  ```bash
  python -m backend.tools.search_cli search "your query"
  ```

## Project Structure

```
project/
├── backend/
│   ├── main.py #modify models_dir if necessary
│   ├── models.py
│   ├── database.py
│   ├── crud.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── README.md
│   └── installed_models/   # dummy folder find where Ollama installs your models
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   ├── ChatWindow.js
│   │   │   ├── MessageInput.js
│   │   │   └── ModelSelector.js
│   │   ├── api.js
│   │   └── index.js
│   └── README.md
└── README.md
```

## Setup Instructions

Download the Ollama Client from [https://ollama.com/](https://ollama.com/).

Open a terminal window and use the following command to install models:

```sh
ollama pull {model choice}
```

### Backend
1. Navigate to the `backend` folder:
   ```bash
   cd OllamaChat/backend
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # On Linux/macOS
   venv\Scripts\activate         # On Windows
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the SQLite database:
   ```bash
   python database.py
   ```
5. Run the FastAPI server:
   ```bash
   uvicorn app:app --reload
   ```
   The backend server will run at [http://127.0.0.1:8000](http://127.0.0.1:8000).
   A root health check is available at `/` and `/healthz`.

### Live Browsing
The live browsing tools read their configuration from `backend/config/sources.yaml` (optional). If the file is absent the defaults in code are used. To enable browsing in the chat UI, toggle the **Use Browser** option. Retrieved documents are stored in `backend/local_data/web_live` and reindexed for search.

### Multimodal
Optional models and settings are configured in `backend/config/mm.yaml`. Endpoints under `/tools/mm/*` handle image captioning/OCR, audio transcription, video keyframes and ingestion. The backend will continue to run even if these models fail to load.

### Frontend
1. Navigate to the `frontend` folder:
   ```bash
   cd project/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the React development server:
   ```bash
   npm start
   ```
   The application will open in your browser at [http://localhost:3000](http://localhost:3000).

#### Backend API URL

The frontend reads the backend base URL from the `REACT_APP_API_URL` environment variable. During development it defaults to `http://127.0.0.1:8000`.
You can override this by creating a `.env` file in the `frontend` directory or by setting the variable at build time:

```bash
REACT_APP_API_URL=https://your-backend.example.com npm start
```

### Code Execution

The backend can execute code inside sandboxed Docker containers.

1. Build the execution image:
   ```bash
   cd backend/code_execution
   docker build -t code-executor:latest .
   ```
2. Make sure Docker is running before starting the backend.
3. Use the API to manage workspaces:
   ```bash
   curl -X POST http://127.0.0.1:8000/workspace/create      # create
   curl http://127.0.0.1:8000/workspaces                    # list
   curl -X DELETE http://127.0.0.1:8000/workspace/<id>      # delete
   ```
4. Run code within a workspace:
   ```python
   from code_execution.executor import execute_code
   execute_code("print('hi')", "python", workspace_id)
   ```

See `backend/code_execution/readme.txt` for more examples.

Happy chatting!
