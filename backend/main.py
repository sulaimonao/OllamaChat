import os
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import subprocess
import logging
import crud
import models
import schemas
from database import SessionLocal, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def call_ollama_cli(model: str, prompt: str) -> str:
    command = ["ollama", "run", model, prompt]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling Ollama CLI: {e.stderr}")
        raise Exception(f"Ollama CLI error: {e.stderr}")

@app.post("/session", response_model=schemas.Session)
def create_new_session(db: Session = Depends(get_db)):
    """
    Create a new chat session.
    """
    session_obj = crud.create_session(db)
    return session_obj

@app.get("/models")
def get_installed_models():
    # Use os.path.expanduser to get the full path to the models directory
    models_dir = os.path.expanduser("~/.ollama/models/manifests/registry.ollama.ai/library")
    try:
        if not os.path.exists(models_dir):
            raise HTTPException(status_code=500, detail="Models directory not found")
        # List only directories (model folders) in the directory
        model_names = [
            d for d in os.listdir(models_dir)
            if os.path.isdir(os.path.join(models_dir, d))
        ]
        return {"models": model_names}
    except Exception as e:
        logging.error(f"Error retrieving models: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving installed models")

@app.post("/chat", response_model=schemas.ChatResponse)
def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Receive a chat message, call the selected language model via the CLI,
    save both the user message and model response, and return the responses.
    """
    # Ensure that the session exists
    session_obj = crud.get_session(db, chat_request.session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save the user's message
    crud.create_message(db, session_obj.id, sender="user", content=chat_request.message)

    # Call the CLI to get the model's response
    try:
        model_reply = call_ollama_cli(chat_request.model_id, chat_request.message)
    except Exception as e:
        logging.error(f"Error calling Ollama CLI: {e}")
        raise HTTPException(status_code=500, detail="Error communicating with the language model")

    # Save the model's response
    crud.create_message(db, session_obj.id, sender="model", content=model_reply)

    return schemas.ChatResponse(
        session_id=session_obj.id,
        user_message=chat_request.message,
        model_message=model_reply,
        model_id=chat_request.model_id,
    )

@app.get("/chat/{session_id}", response_model=schemas.Session)
def get_chat_history(session_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the full chat history (i.e. all messages) for a given session.
    """
    session_obj = crud.get_session(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj
