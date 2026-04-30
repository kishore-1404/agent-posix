from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from agentposix.enums import FreezeTriggerReasonEnum


class ModelConfig(BaseModel):
    provider: str = Field(..., example="anthropic")
    model_id: str = Field(..., example="claude-3-5-sonnet-20241022")
    temperature: float = Field(0.0)
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    system_prompt: Optional[str] = None
    api_base_url: Optional[str] = None


class FreezeMetadata(BaseModel):
    framework_name: str = Field(..., example="langgraph")
    framework_version: str = Field(..., example="0.2.62")
    agentposix_version: str = Field("0.1.0")
    trigger_reason: FreezeTriggerReasonEnum
    error_info: Optional[Dict[str, Any]] = None


class IdentityBlock(BaseModel):
    aso_id: str
    session_id: str
    parent_session_id: Optional[str] = None
