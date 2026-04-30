import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SideEffectEntry(BaseModel):
    idempotency_key: str
    tool_name: str
    tool_args: Dict[str, Any]
    executed_at: str
    result_summary: Optional[str] = None
    is_reversible: bool = False
    replay_safe: bool = False

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not re.match(r"^[a-f0-9]{64}$", v):
            raise ValueError("Idempotency key must be a 64-character SHA256 hex string.")
        return v


class SideEffectRegistry(BaseModel):
    entries: List[SideEffectEntry] = Field(default_factory=list)
