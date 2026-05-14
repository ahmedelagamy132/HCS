"""
Pydantic schemas for Chatbot API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class ChatMessage(BaseModel):
    model_config = {"protected_namespaces": ()}
    role:    str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request schema for chat and chat-stream endpoints."""
    model_config = {"protected_namespaces": ()}
    question:     str  = Field(..., description="User's question", min_length=1, max_length=2000)
    stream:       bool = Field(default=False,  description="Enable streaming (non-streaming endpoint only)")
    use_rag:      bool = Field(default=True,   description="Retrieve from Qdrant knowledge base")
    use_sensors:  bool = Field(default=True,   description="Include hardware sensor data in prompt")
    use_behavior: bool = Field(default=True,   description="Include CV pipeline behavior data in prompt")


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status:        str = Field(default="success")
    response:      str = Field(..., description="AI agent's response")
    question:      str = Field(..., description="User's question")
    message_count: int = Field(..., description="Total messages in conversation")
    use_rag:      bool = Field(default=True)
    use_sensors:  bool = Field(default=True)
    use_behavior: bool = Field(default=True)


class ModeRequest(BaseModel):
    """Request schema for POST /chatbot/mode."""
    use_rag:      bool = Field(default=True,  description="Enable RAG retrieval")
    use_sensors:  bool = Field(default=True,  description="Enable sensor data channel")
    use_behavior: bool = Field(default=True,  description="Enable behavior/CV data channel")


class ModeResponse(BaseModel):
    """Response schema for GET/POST /chatbot/mode."""
    use_rag:      bool
    use_sensors:  bool
    use_behavior: bool
    status:       str  = Field(description="One-line mode summary from agent.status()")
    mode_label:   str  = Field(description="Human-readable mode name")


class HistorySummary(BaseModel):
    model_config = {"protected_namespaces": ()}
    total_messages: int
    user_messages:  int
    ai_messages:    int
    has_history:    bool


class HistoryResponse(BaseModel):
    status:   str = Field(default="success")
    summary:  HistorySummary
    messages: Optional[List[ChatMessage]] = None


class ClearHistoryResponse(BaseModel):
    status:  str  = Field(default="success")
    message: str  = Field(default="History cleared successfully")
    cleared: bool = Field(..., description="Whether history was cleared")
