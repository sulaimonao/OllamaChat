# backend/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class Message(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class Session(BaseModel):
    id: int
    created_at: datetime
    messages: List[Message] = []
    workspace_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    session_id: int
    model_id: str
    message: str
    reasoning_style: Optional[str] = None  # Reasoning style (can be None)
    image: Optional[str] = None
    persona: Optional[str] = None # Add persona
    use_browser: Optional[bool] = False
    workspace_id: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())

class ChatResponse(BaseModel):
    session_id: int
    user_message: str
    model_message: str
    model_id: str
    browser_results: Optional[List[dict]] = None

    model_config = ConfigDict(protected_namespaces=())
