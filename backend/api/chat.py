# backend/api/chat.py
import os
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional

import crud
import schemas
from ollama_integration import call_ollama_api
from reasoning import generate_reasoning_prompt
from utils import UPLOAD_DIR
from code_execution.executor import execute_code, read_file, write_file
from config import load_system_prompts
from tools.search_engine import SearchEngine
import json

router = APIRouter()

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installed_models")
SYSTEM_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompts")
system_prompts = load_system_prompts(SYSTEM_PROMPTS_DIR)

# Initialize search engine and index data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "local_data")
search_engine = SearchEngine()
if not search_engine.ix.doccount():
    print("Indexing local data...")
    file_paths = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".md")]
    search_engine.index_files(file_paths)
    print("Indexing complete.")


@router.post("/chat", response_model=schemas.ChatResponse)
async def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(crud.get_db)):
    try:
        logging.info(f"Received chat_request: {chat_request}")
        session_obj = crud.get_session(db, chat_request.session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")

        user_message = chat_request.message
        crud.create_message(db, session_obj.id, sender="user", content=user_message)

        model_path = os.path.join(MODELS_DIR, chat_request.model_id)
        is_custom_model = os.path.exists(model_path)

        system_prompt_key = chat_request.persona or "default"
        if system_prompt_key not in system_prompts:
            system_prompt_key = "default"
        system_prompt = system_prompts[system_prompt_key]["prompt"]

        async def process_message(model_id: str, is_custom: bool, user_message: str, image: Optional[str] = None):
            if is_custom:
                # Custom Model Handling
                payload = {
                    "prompt": f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:",
                    "image": image,
                    "model": model_id,
                }
                try:
                    response = requests.post("http://127.0.0.1:8000/custom_chat", json=payload)
                    response.raise_for_status()
                    model_response = response.json()["response"]
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error calling custom inference: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

            else:
                # Ollama Model Handling
                # 1. Prepare context (history)
                history = crud.get_messages(db, session_obj.id)
                context_messages = []  # We aren't using context yet with LangChain, see below
                for msg in history[-5:]:
                    if msg.sender == 'user':
                        context_messages.append({'role': 'user', 'content': msg.content})
                    else:
                        context_messages.append({'role': 'assistant', 'content': msg.content})


                # 2. Handle file content (if any)
                file_content = ""
                if "[FILE:" in user_message:
                    start_index = user_message.find("[FILE:") + len("[FILE:")
                    end_index = user_message.find("]", start_index)
                    relative_file_path = user_message[start_index:end_index]
                    absolute_file_path = os.path.join(UPLOAD_DIR, relative_file_path)

                    if not os.path.realpath(absolute_file_path).startswith(os.path.realpath(UPLOAD_DIR)):
                        logging.error(f"Invalid file path: {relative_file_path}")
                        raise HTTPException(status_code=403, detail="Invalid file path (access denied)")

                    try:
                        with open(absolute_file_path, "r") as f:
                            file_content = f.read()
                    except FileNotFoundError:
                        logging.error(f"File not found: {absolute_file_path}")
                        raise HTTPException(status_code=404, detail=f"File not found: {relative_file_path}")
                    except Exception as e:
                        logging.exception(f"Error reading file {absolute_file_path}")
                        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

                    user_message = user_message.replace(f"[FILE: {relative_file_path}]", "").strip()

                # 3. Construct the prompt FOR OLLAMA (LangChain handles this internally)
                prompt = f"{system_prompt}\n\nUser: {user_message}\n\nFile Content:\n{file_content}\n\nAssistant:"

                # 4. Call Ollama API (LangChain)
                if chat_request.reasoning_style:
                    # With LangChain, we build the reasoning prompt *before* calling the API
                    prompt = generate_reasoning_prompt(prompt, chat_request.reasoning_style)
                    model_response = call_ollama_api(model_id, prompt, image) #reasoning handled in ollama.
                else:
                    model_response = call_ollama_api(model_id, prompt, image)

            # --- Command Parsing (Regular Expressions) ---
            command_pattern = re.compile(r"```(execute|file_write|file_read|local_search)\s+([^\n]+)?\n([\s\S]*?)```")
            final_response = ""
            last_index = 0

            for match in command_pattern.finditer(model_response):
                command_type = match.group(1)
                args_str = match.group(2)
                code_or_content = match.group(3)
                final_response += model_response[last_index:match.start()]

                try:
                    if command_type == "execute":
                        language = args_str.strip()
                        logging.info(f"Executing code. workspace_id: {session_obj.workspace_id}, language: {language}")
                        result = execute_code(code_or_content, language, session_obj.workspace_id)
                        final_response += f"\nCode Output ({language}):\n```\n{result['output']}\n```\n"

                    elif command_type == "file_write":
                        filename = args_str.strip()
                        write_file(session_obj.workspace_id, filename, code_or_content)
                        final_response += f"\nFile '{filename}' written to workspace.\n"

                    elif command_type == "file_read":
                        filename = args_str.strip()
                        file_content = read_file(session_obj.workspace_id, filename)
                        final_response += f"\nContent of '{filename}':\n```\n{file_content}\n```\n"

                    elif command_type == "local_search":
                        query = code_or_content.strip()
                        logging.info(f"Performing local search for: {query}")
                        search_results = search_engine.search(query)
                        results_json = json.dumps(search_results, indent=2)
                        final_response += f"\nLocal Search Results:\n```json\n{results_json}\n```\n"

                except HTTPException as e:
                    final_response += f"\nError: {e.detail}\n"
                except Exception as e:
                    logging.exception(f"Error during command execution: {e}")
                    final_response += f"\nError during command execution: {e}\n"

                last_index = match.end()

            final_response += model_response[last_index:]
            return final_response.strip()

        model_reply = await process_message(chat_request.model_id, is_custom_model, user_message, chat_request.image)
        crud.create_message(db, session_obj.id, sender="model", content=model_reply)

        return schemas.ChatResponse(
            session_id=session_obj.id,
            user_message=user_message,
            model_message=model_reply,
            model_id=chat_request.model_id,
        )

    except Exception as e:
        logging.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")