# backend/api/chat.py
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import requests

import crud
import schemas
from ollama import call_ollama_cli, process_ollama_response
from reasoning import call_ollama_with_reasoning
from utils import UPLOAD_DIR

router = APIRouter()

# --- Configuration:  Path to installed_models ---
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installed_models")

@router.post("/chat", response_model=schemas.ChatResponse)
def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(crud.get_db)):
    try:
        session_obj = crud.get_session(db, chat_request.session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")

        crud.create_message(db, session_obj.id, sender="user", content=chat_request.message)

        # --- Check if model is in installed_models ---
        model_path = os.path.join(MODELS_DIR, chat_request.model_id)
        is_custom_model = os.path.exists(model_path)

        if is_custom_model:
            # --- Custom Model Handling ---
            payload = {
                "prompt": chat_request.message,
                "image": chat_request.image,
                "model": chat_request.model_id,
            }
            try:
                response = requests.post("http://127.0.0.1:8000/custom_chat", json=payload)
                response.raise_for_status()
                model_reply = response.json()["response"]
            except requests.exceptions.RequestException as e:
                logging.error(f"Error calling custom inference: {e}")
                raise HTTPException(status_code=500, detail=f"Custom model inference failed: {e}")

        else:
            # --- Ollama Model Handling ---
            history = crud.get_messages(db, session_obj.id)
            context_messages = []
            for msg in history[-5:]:  # Corrected indentation here
                prefix = "You:" if msg.sender == "user" else "Model:"
                context_messages.append(f"{prefix} {msg.content}")
            context = "\n".join(context_messages)

            #File Handling for Ollama Models
            file_content = ""
            if "[FILE:" in chat_request.message:
                start_index = chat_request.message.find("[FILE:") + len("[FILE:")
                end_index = chat_request.message.find("]", start_index)
                relative_file_path = chat_request.message[start_index:end_index]
                absolute_file_path = os.path.join(UPLOAD_DIR, relative_file_path)
                real_path = os.path.realpath(absolute_file_path)
                if os.path.commonpath([UPLOAD_DIR, real_path]) != UPLOAD_DIR:
                    logging.error(f"Invalid file path: {relative_file_path}")
                    raise HTTPException(status_code=400, detail="Invalid file path")
                try:
                    with open(absolute_file_path, "r") as f:
                        file_content = f.read()
                except FileNotFoundError:
                    logging.error(f"File not found: {absolute_file_path}")
                    raise HTTPException(status_code=404, detail=f"File not found at path: {absolute_file_path}")
                chat_request.message = chat_request.message.replace(f"[FILE: {relative_file_path}]", "").strip()


            full_prompt = f"Context:\n{context}\n\nNew message: {chat_request.message}\n\nFile Content:\n{file_content}"

            if chat_request.reasoning_style:
                model_reply = call_ollama_with_reasoning(chat_request.model_id, full_prompt, chat_request.reasoning_style)
                processed_response = process_ollama_response(model_reply)
                model_reply = processed_response["answer"]
            else:
                model_reply = call_ollama_cli(chat_request.model_id, full_prompt)

        crud.create_message(db, session_obj.id, sender="model", content=model_reply)
        return schemas.ChatResponse(
            session_id=session_obj.id,
            user_message=chat_request.message,
            model_message=model_reply,
            model_id=chat_request.model_id,
        )

    except Exception as e:
        logging.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")