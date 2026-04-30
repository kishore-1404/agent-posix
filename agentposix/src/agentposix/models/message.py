from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]


class Message(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant, tool")
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ConversationHistory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    message_count: int = 0
    truncation_applied: bool = False
    original_message_count: int = 0


class ToolDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    idempotent: bool = False
