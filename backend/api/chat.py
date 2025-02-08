# backend/api/chat.py
import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request #Import Request
from sqlalchemy.orm import Session
import logging
import requests

import crud
import schemas
from ollama import call_ollama_cli, process_ollama_response
from reasoning import call_ollama_with_reasoning, generate_reasoning_prompt
from utils import UPLOAD_DIR
from code_execution.executor import execute_code, read_file, write_file, delete_workspace
from config import load_system_prompts

router = APIRouter()

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installed_models")
SYSTEM_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompts")
system_prompts = load_system_prompts(SYSTEM_PROMPTS_DIR)

@router.post("/chat", response_model=schemas.ChatResponse)
async def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(crud.get_db)):
    try:
        print("Received chat_request:", chat_request)
        session_obj = crud.get_session(db, chat_request.session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")
        # --- 1. Initial User Message Handling ---
        user_message = chat_request.message
        crud.create_message(db, session_obj.id, sender="user", content=user_message)

        # --- 2. Determine Model Type ---
        model_path = os.path.join(MODELS_DIR, chat_request.model_id)
        is_custom_model = os.path.exists(model_path)

        # --- 3. Load System Prompt (based on Persona) ---
        system_prompt_key = chat_request.persona or "default"
        if system_prompt_key not in system_prompts:
            system_prompt_key = "default"
        system_prompt = system_prompts[system_prompt_key]["prompt"]

        # --- 4.  Initial Prompt Construction (for both model types) ---
        # We'll construct a prompt that encourages structured output
        # for intent recognition.

        if is_custom_model:
            initial_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:"
        else: #Ollama
            history = crud.get_messages(db, session_obj.id)
            context_messages = []
            for msg in history[-5:]:
                prefix = "You:" if msg.sender == "user" else "Model:"
                context_messages.append(f"{prefix} {msg.content}")
            context = "\n".join(context_messages)
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

            initial_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser: {user_message}\n\nFile Content:\n{file_content}\n\nAssistant:"

        # --- 5. Process (Potentially) Multi-Turn Interaction ---
        async def process_message(prompt, model_id, is_custom):

            if is_custom:
                payload = {
                    "prompt": prompt,
                    "image": chat_request.image,
                    "model": model_id,
                }
                try:
                    response = requests.post("http://127.0.0.1:8000/custom_chat", json=payload)
                    response.raise_for_status()
                    model_response = response.json()["response"]
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error calling custom inference: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

            else:#Ollama Models
                if chat_request.reasoning_style:
                    model_response = call_ollama_with_reasoning(model_id, prompt, chat_request.reasoning_style)
                    processed_response = process_ollama_response(model_response)  # Ollama reasoning
                    model_response = processed_response["answer"]
                else:
                    model_response = call_ollama_cli(model_id, prompt)  # Regular Ollama call

            # --- Command Parsing (Regular Expressions) ---
            command_pattern = re.compile(r"```(execute|file_write|file_read)\s+([^\n]+)?\n([\s\S]*?)```")

            final_response = ""
            last_index = 0

            for match in command_pattern.finditer(model_response):
                command_type = match.group(1)
                args_str = match.group(2)
                code_or_content = match.group(3)
                final_response += model_response[last_index:match.start()] #Text BEFORE command

                if command_type == "execute":
                    language = args_str.strip()
                    print(f"Executing code.  workspace_id: {session_obj.workspace_id}, language: {language}")  # Keep this
                    result = await execute_code(code_or_content, language, session_obj.workspace_id)
                    final_response += f"\nCode Output ({language}):\n```\n{result['output']}\n```\n"

                elif command_type == "file_write":
                    filename = args_str.strip()
                    write_file(session_obj.workspace_id, filename, code_or_content)
                    final_response += f"\nFile '{filename}' written to workspace.\n"

                elif command_type == "file_read":
                    filename = args_str.strip()
                    try:
                        file_content = read_file(session_obj.workspace_id, filename)
                        final_response += f"\nContent of '{filename}':\n```\n{file_content}\n```\n"
                    except HTTPException as e:
                        final_response += f"\nError reading file '{filename}': {e.detail}\n"

                last_index = match.end() #Text AFTER command

            final_response += model_response[last_index:]
            return final_response.strip()

        # --- 6. Initial Model Call and Iterative Processing ---

        model_reply = await process_message(initial_prompt, chat_request.model_id, is_custom_model)
        crud.create_message(db, session_obj.id, sender="model", content=model_reply)


        return schemas.ChatResponse(
            session_id=session_obj.id,
            user_message=user_message,
            model_message=model_reply,
            model_id=chat_request.model_id,
        )

    except Exception as e:
        logging.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))