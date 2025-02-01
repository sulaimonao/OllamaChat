from pydantic import BaseModel
from datetime import datetime
from typing import List

# Schema for individual message output
class Message(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True

# Schema for a chat session including its messages
class Session(BaseModel):
    id: int
    created_at: datetime
    messages: List[Message] = []

    class Config:
        orm_mode = True

# Request schema when sending a message
class ChatRequest(BaseModel):
    session_id: int
    model_id: str
    message: str

    model_config = {
        "protected_namespaces": ()
    }

# Response schema after processing a chat message
class ChatResponse(BaseModel):
    session_id: int
    user_message: str
    model_message: str
    model_id: str

    model_config = {
        "protected_namespaces": ()
    }
