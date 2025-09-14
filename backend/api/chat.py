import os
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Optional, List, Dict, Any
import asyncio
from bs4 import BeautifulSoup
import httpx

import crud
import schemas
from reasoning import generate_reasoning_prompt
from utils import UPLOAD_DIR
from code_execution.executor import execute_code, read_file, write_file
from config import load_system_prompts, load_search_config
from tools.search_engine import local_search, SearchEngine
from tools.live_browse import (
    get_config,
    rss_latest,
    site_search,
    fetch,
    ingest,
    RssRequest,
    SiteSearchRequest,
    FetchRequest,
    IngestRequest,
    RssResponse,
    SiteSearchResponse,
    FetchResponseItem,
)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Initialization ---
system_prompts = load_system_prompts()
search_config = load_search_config()


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

async def _extract_links_from_html(html_content: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html_content, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            links.add(href)
        elif href.startswith("/"):
            try:
                url = httpx.URL(base_url)
                links.add(str(url.join(href)))
            except Exception:
                pass
    return list(links)

async def homepage_fallback_strategy(query: str):
    logger.info("Executing homepage fallback strategy")
    config = get_config()

    ai_keywords = ['ai', 'artificial intelligence', 'ml', 'machine learning']
    is_ai_query = any(keyword in query.lower() for keyword in ai_keywords)

    if is_ai_query:
        hubs = [
            "https://www.nature.com/subjects/artificial-intelligence",
            "https://ai.googleblog.com/",
            "https://openai.com/blog",
            "https://www.deepmind.com/blog",
            "https://venturebeat.com/category/ai/",
        ]
        logger.info("Using AI-focused hubs for fallback.")
    else:
        hubs = [
            "https://www.reuters.com/",
            "https://www.theverge.com/",
            "https://www.npr.org/sections/news/",
            "https://news.ycombinator.com/",
        ]
        logger.info("Using general news hubs for fallback.")

    fetched_pages = await fetch(FetchRequest(urls=hubs[:5]))

    all_links = []
    for page in fetched_pages:
        links = await _extract_links_from_html(page.text, page.url)
        all_links.extend(links)

    if not all_links:
        logger.warning("No links found in fallback hubs.")
        return

    fetched_articles = await fetch(FetchRequest(urls=list(set(all_links))[:20]))

    if fetched_articles:
        ingest_req = IngestRequest(items=[item.dict() for item in fetched_articles])
        await ingest(ingest_req)
        logger.info(f"Fallback ingested {len(fetched_articles)} documents.")


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

        if chat_request.use_browser:
            logger.info("Attempting live browse: RSS latest")
            rss_result: RssResponse = await rss_latest(RssRequest())

            if rss_result.items and not rss_result.error:
                logger.info(f"RSS successful, found {len(rss_result.items)} items.")
                urls_to_fetch = [item.url for item in rss_result.items]
                fetched_items: List[FetchResponseItem] = await fetch(FetchRequest(urls=urls_to_fetch))
                if fetched_items:
                    ingest_req = IngestRequest(items=[item.dict() for item in fetched_items])
                    await ingest(ingest_req)
            else:
                logger.info("RSS empty or failed, attempting site search")
                search_result: SiteSearchResponse = await site_search(SiteSearchRequest(query=user_message))
                if search_result.items and not search_result.error:
                    logger.info(f"Site search successful, found {len(search_result.items)} items.")
                    urls_to_fetch = [item.url for item in search_result.items]
                    fetched_items: List[FetchResponseItem] = await fetch(FetchRequest(urls=urls_to_fetch))
                    if fetched_items:
                        ingest_req = IngestRequest(items=[item.dict() for item in fetched_items])
                        await ingest(ingest_req)
                else:
                    logger.info("Site search empty or failed, attempting homepage fallback.")
                    await homepage_fallback_strategy(user_message)

        system_prompt_key = chat_request.persona or "default"
        system_prompt = system_prompts.get(system_prompt_key, system_prompts["default"])["prompt"]

        llm = ChatOllama(model=chat_request.model_id)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        tools = [local_search, code_execution_tool]

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

        history = crud.get_messages(db, session_obj.id)
        chat_history = [HumanMessage(content=msg.content) if msg.sender == 'user' else AIMessage(content=msg.content) for msg in history]

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
        logger.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")