# Backend

This is the FastAPI backend for the Chat Interface Application.

## Setup Instructions

1. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate      # On Linux/macOS
   venv\Scripts\activate         # On Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**

   ```bash
   uvicorn main:app --reload
   ```

   The server will start at [http://127.0.0.1:8000](http://127.0.0.1:8000).

> **Note:** Update the `ollama_endpoint` URL in `main.py` (replace `PORT` with the actual port) so that it correctly points to your local Ollama API.
