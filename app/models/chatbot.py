from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" veya "assistant"
    content: str
    timestamp: datetime

class ChatSession(BaseModel):
    id: str
    traineeID: str
    characterType: str  # "happy_customer", "angry_customer" vb.
    messages: List[ChatMessage]
    createdAt: datetime
    updatedAt: datetime
    isActive: bool

class ChatResponse(BaseModel):
    message: str
    analysis: Optional[Dict] = None
    collectedInfo: Optional[Dict] = None 