import os
import re
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional

import crud
import schemas
from reasoning import generate_reasoning_prompt, route_to_browser
from utils import UPLOAD_DIR
from code_execution.executor import execute_code, read_file, write_file
from config import load_system_prompts, load_search_config
from tools.search_engine import local_search, search_engine_instance
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import Tool

router = APIRouter()

# --- Initialization ---
system_prompts = load_system_prompts()
search_config = load_search_config()

# Initialize search engine and index data if needed
if not search_engine_instance.ix.doc_count() and search_config.get("allowlist"):
    print("Indexing local data...")
    all_files = []
    for path in search_config["allowlist"]:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    all_files.append(os.path.join(root, file))
        elif os.path.isfile(path):
            all_files.append(path)
    search_engine_instance.index(all_files)
    print("Indexing complete.")


def _create_code_execution_tool(workspace_id: str) -> Tool:
    """Create a tool for executing and managing code in a workspace."""

    def _run(input_str: str) -> str:
        try:
            data = json.loads(input_str)
        except Exception as e:
            return f"Invalid input: {e}"

        operation = data.get("operation", "execute")
        try:
            if operation == "execute":
                code = data.get("code", "")
                language = data.get("language", "python")
                result = execute_code(code, language, workspace_id)
                return result.get("output", "")
            if operation == "read_file":
                filename = data.get("filename", "")
                return read_file(workspace_id, filename)
            if operation == "write_file":
                filename = data.get("filename", "")
                content = data.get("content", "")
                write_file(workspace_id, filename, content)
                return "File written successfully."
            return f"Unsupported operation: {operation}"
        except Exception as e:
            return str(e)

    return Tool(
        name="code_execution",
        description=(
            "Execute code or read/write files. Input JSON with keys: operation"
            " (execute|read_file|write_file), code, language, filename, content"
        ),
        func=_run,
    )


@router.post("/chat", response_model=schemas.ChatResponse)
async def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(crud.get_db)):
    try:
        logging.info(f"Received chat_request: {chat_request}")
        session_obj = crud.get_session(db, chat_request.session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")

        user_message = chat_request.message
        crud.create_message(db, session_obj.id, sender="user", content=user_message)

        browser_results = None
        if chat_request.use_browser:
            browser_results = await route_to_browser(user_message)
            if browser_results:
                user_message += f"\n\n[BROWSER_RESULTS]\n{browser_results}\n[/BROWSER_RESULTS]"

        # 1. Get system prompt
        system_prompt_key = chat_request.persona or "default"
        if system_prompt_key not in system_prompts:
            system_prompt_key = "default"
        system_prompt = system_prompts[system_prompt_key]["prompt"]

        # 2. Initialize the model
        llm = ChatOllama(model=chat_request.model_id)

        workspace_id = chat_request.workspace_id or session_obj.workspace_id

        # 3. Create the agent
        # Note: The prompt template is simple for now. It could be more complex.
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        tools = [local_search, _create_code_execution_tool(workspace_id)]
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        # 4. Prepare chat history
        history = crud.get_messages(db, session_obj.id)
        chat_history = []
        for msg in history:
            if msg.sender == 'user':
                chat_history.append(HumanMessage(content=msg.content))
            else:
                chat_history.append(AIMessage(content=msg.content))

        # 5. Invoke the agent
        response = await agent_executor.ainvoke({
            "input": user_message,
            "chat_history": chat_history,
            "workspace_id": workspace_id,
        })

        model_reply = response.get("output", "I could not process that.")
        crud.create_message(db, session_obj.id, sender="model", content=model_reply)

        return schemas.ChatResponse(
            session_id=session_obj.id,
            user_message=chat_request.message,  # Return original user message
            model_message=model_reply,
            model_id=chat_request.model_id,
            browser_results=browser_results,
        )

    except Exception as e:
        logging.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

