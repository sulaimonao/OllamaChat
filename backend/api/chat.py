import os
import re
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
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
    fetch,
    ingest,
    FetchRequest,
    IngestRequest,
    FetchResponseItem,
)
from tools.live_browse_utils import compute_reliability, pick_hubs
from search.query_bundle import build_query_bundle, CONFIG as SEARCH_CFG
from search.run_bundle import run_bundle
from search.select_and_ingest import select_and_ingest
from tools.multimodal import (
    image_analyze,
    audio_transcribe,
    video_analyze,
    mm_ingest,
    IngestPayload,
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

async def browse_first_pipeline(query: str):
    bundle = build_query_bundle(query)
    hits = run_bundle(bundle, SEARCH_CFG["limits"].get("per_query", 10))
    accepted = select_and_ingest(query, hits)
    path_used = "rss" if accepted else "homepage_fallback"

    if not accepted:
        config = get_config()
        policy = config.get("ingest_policy", {})
        urls = pick_hubs(query, config)[:5]
        fetched = await fetch(FetchRequest(urls=urls))
        accepted = []
        for item in fetched:
            d = item.dict()
            score = compute_reliability(d, policy)
            if score >= policy.get("min_reliability", 0):
                d["score"] = score
                accepted.append(d)
        if accepted:
            ingest_items = [{"url": d["url"], "title": d.get("title", ""), "text": d["text"]} for d in accepted]
            await ingest(IngestRequest(items=ingest_items))

    summary_lines = []
    sources = []
    for i, d in enumerate(accepted, 1):
        url = d.get("canonical_url", d.get("url"))
        summary_lines.append(f"{i}. {d['title']} ({url})")
        sources.append({"url": url, "title": d['title']})
    summary = "\n".join(summary_lines) if summary_lines else "No live results found."
    return summary, sources, path_used


@router.post("/chat", response_model=schemas.ChatResponse)
async def send_chat_message(
    db: Session = Depends(crud.get_db),
    session_id: str = Form(...),
    model_id: str = Form(...),
    message: str = Form(...),
    persona: Optional[str] = Form(None),
    use_browser: bool = Form(False),
    workspace_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    try:
        logging.info(f"Received chat request for session: {session_id}")
        session_obj = crud.get_session(db, session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")

        user_message = message
        crud.create_message(db, session_obj.id, sender="user", content=user_message)

        final_user_message_for_llm = user_message
        analysis_summary = ""
        reasoning_steps = []

        if file and file.filename:
            content_type = file.content_type
            modality = None
            if content_type.startswith("image/"): modality = "image"
            elif content_type.startswith("audio/"): modality = "audio"
            elif content_type.startswith("video/"): modality = "video"

            if modality:
                analysis_result = None
                if modality == "image":
                    analysis_result = await image_analyze(file)
                    caption_text = " ".join(analysis_result.captions)
                    ocr_summary = f"Text found in image: {analysis_result.ocr}" if analysis_result.ocr else ""
                    analysis_summary = f"Image Analysis:\nCaption: {caption_text}\n{ocr_summary}".strip()
                    fragments = [{"type": "caption", "text": cap} for cap in analysis_result.captions]
                    if analysis_result.ocr: fragments.append({"type": "ocr", "text": analysis_result.ocr})

                    payload = IngestPayload(modality="image", metadata={"original_file": file.filename}, text=analysis_summary, fragments=fragments)
                    await mm_ingest(payload)

                elif modality == "audio":
                    analysis_result = await audio_transcribe(file)
                    analysis_summary = f"Audio Transcription:\n{analysis_result.text}"
                    payload = IngestPayload(modality="audio", metadata={"original_file": file.filename}, text=analysis_result.text, fragments=analysis_result.segments)
                    await mm_ingest(payload)

                elif modality == "video":
                    analysis_result = await video_analyze(file)
                    analysis_summary = f"Video Analysis:\nSummary: {analysis_result.summary}\nTranscript: {analysis_result.transcript}"
                    fragments = analysis_result.scenes
                    if analysis_result.transcript: fragments.append({"type": "transcript", "text": analysis_result.transcript})
                    payload = IngestPayload(modality="video", metadata={"original_file": file.filename}, text=analysis_summary, fragments=fragments)
                    await mm_ingest(payload)

                final_user_message_for_llm = f"The user uploaded a {modality} file. Here is the analysis:\n{analysis_summary}\n\nUser's message: {user_message}"
                reasoning_steps.append({"tool": f"multimodal_{modality}_analyzer", "tool_input": {"filename": file.filename}, "observation": analysis_result.dict()})


        current_workspace_id = workspace_id or session_obj.workspace_id
        code_execution_tool = create_code_execution_tool(current_workspace_id)

        if use_browser:
            summary, sources, path_used = await browse_first_pipeline(user_message)
            logger.info(f"browse_path={path_used}")
            model_reply = summary
            crud.create_message(db, session_obj.id, sender="model", content=model_reply)
            reasoning_steps.append({"tool": f"browse_{path_used}", "tool_input": {"query": user_message}, "observation": {"sources": sources}})
            return schemas.ChatResponse(
                session_id=session_obj.id,
                user_message=user_message,
                model_message=model_reply,
                model_id=model_id,
                reasoning=reasoning_steps,
            )

        system_prompt_key = persona or "default"
        system_prompt = system_prompts.get(system_prompt_key, system_prompts["default"])["prompt"]

        llm = ChatOllama(model=model_id)

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
            "input": final_user_message_for_llm,
            "chat_history": chat_history,
            "workspace_id": current_workspace_id
        })

        model_reply = response.get("output", "I could not process that.")
        crud.create_message(db, session_obj.id, sender="model", content=model_reply)

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
            user_message=user_message,
            model_message=model_reply,
            model_id=model_id,
            reasoning=reasoning_steps if reasoning_steps else None,
        )

    except Exception as e:
        logger.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")