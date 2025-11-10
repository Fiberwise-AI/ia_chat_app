"""
Pydantic models for IA Chat App API.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    metadata: Dict[str, Any] = {}
    user: Optional[str] = None
    session_id: Optional[str] = None
