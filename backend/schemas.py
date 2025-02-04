# backend/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

# Schema for individual message output
class Message(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# Schema for a chat session including its messages
class Session(BaseModel):
    id: int
    created_at: datetime
    messages: List[Message] = []

    model_config = ConfigDict(from_attributes=True)

# Request schema when sending a message
class ChatRequest(BaseModel):
    session_id: int
    model_id: str
    message: str
    reasoning_style: Optional[str] = None  # Add reasoning_style field

    model_config = ConfigDict(protected_namespaces=())

# Response schema after processing a chat message
class ChatResponse(BaseModel):
    session_id: int
    user_message: str
    model_message: str
    model_id: str

    model_config = ConfigDict(protected_namespaces=())