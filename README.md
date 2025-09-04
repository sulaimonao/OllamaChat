# Chat Interface Application

This repository contains a complete chat interface application. The app lets users send messages and receive responses from local language models (accessed via Ollama). All chat messages are stored in an SQLite database, and the code is organized for easy extensibility.

## Features
- **Local Search:** The model can search local documents to answer questions.
- Send messages to language models.
- Select a model for each conversation.
- Store chat messages (user and model responses) in an SQLite database.
- View past conversations (chat history).
- **List Installed Models:** The system locates and shows previously installed models.

### Local Search
The local search feature allows the model to search through documents in the `backend/local_data` directory. You can add your own markdown files to this directory to make them searchable. The search index is built on startup.

The new `whoosh` dependency has been added to `backend/requirements.txt` to support this feature.

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
