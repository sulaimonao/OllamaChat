# Chat Interface Application

This repository contains a complete chat interface application. The app lets users send messages and receive responses from local language models (accessed via Ollama). All chat messages are stored in an SQLite database, and the code is organized for easy extensibility.

## Features
- **Local Search:** The model can search local documents to answer questions.
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

Happy chatting!
