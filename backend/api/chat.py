import os
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional

import crud
import schemas
from reasoning import generate_reasoning_prompt
from utils import UPLOAD_DIR
from code_execution.executor import execute_code, read_file, write_file
from config import load_system_prompts, load_search_config
from tools.search_engine import local_search, search_engine_instance
from api.web_search import web_search
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

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


class CodeExecutionInput(BaseModel):
    """Input schema for the code execution tool."""
    command: str = Field(description="One of 'execute', 'read_file', or 'write_file'")
    language: Optional[str] = Field(default=None, description="Language for the execute command")
    code: Optional[str] = Field(default=None, description="Code to run when command='execute'")
    filename: Optional[str] = Field(default=None, description="Filename for file operations")
    content: Optional[str] = Field(default=None, description="Content to write when command='write_file'")


def create_code_execution_tool(workspace_id: str):
    """Create a LangChain tool bound to a specific workspace."""

    @tool(args_schema=CodeExecutionInput)
    def code_executor(command: str,
                      language: Optional[str] = None,
                      code: Optional[str] = None,
                      filename: Optional[str] = None,
                      content: Optional[str] = None) -> str:
        if command == "execute":
            result = execute_code(code or "", language or "python", workspace_id)
            return result.get("output", "")
        if command == "read_file":
            if not filename:
                return "Filename required"
            return read_file(workspace_id, filename)
        if command == "write_file":
            if not filename:
                return "Filename required"
            write_file(workspace_id, filename, content or "")
            return "File written successfully"
        return "Unknown command"

    return code_executor

@router.post("/chat", response_model=schemas.ChatResponse)
async def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(crud.get_db)):
    try:
        logging.info(f"Received chat_request: {chat_request}")
        session_obj = crud.get_session(db, chat_request.session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")

        user_message = chat_request.message
        crud.create_message(db, session_obj.id, sender="user", content=user_message)

        workspace_id = chat_request.workspace_id or session_obj.workspace_id
        code_execution_tool = create_code_execution_tool(workspace_id)

        # 1. Get system prompt
        system_prompt_key = chat_request.persona or "default"
        if system_prompt_key not in system_prompts:
            system_prompt_key = "default"
        system_prompt = system_prompts[system_prompt_key]["prompt"]

        # 2. Initialize the model
        llm = ChatOllama(model=chat_request.model_id)

        # 3. Create the agent
        # Note: The prompt template is simple for now. It could be more complex.
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        tools = [local_search, code_execution_tool]
        if chat_request.use_browser:
            tools.append(web_search)

        agent = create_tool_calling_agent(llm, tools, prompt)

        reasoning_models = {"gpt-oss"}
        if chat_request.model_id in reasoning_models:
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)
        else:
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
            "workspace_id": workspace_id
        })

        model_reply = response.get("output", "I could not process that.")
        crud.create_message(db, session_obj.id, sender="model", content=model_reply)

        reasoning_steps = []
        if "intermediate_steps" in response:
            for step in response["intermediate_steps"]:
                # Each step is a tuple of (action, observation)
                action, observation = step
                reasoning_steps.append({
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "observation": observation
                })

        return schemas.ChatResponse(
            session_id=session_obj.id,
            user_message=chat_request.message,
            model_message=model_reply,
            model_id=chat_request.model_id,
            reasoning=reasoning_steps if reasoning_steps else None,
        )

    except Exception as e:
        logging.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")