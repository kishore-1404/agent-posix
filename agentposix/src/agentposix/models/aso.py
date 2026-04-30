from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.agentposix.enums import ASOStatus
from src.agentposix.models.environment import EnvironmentSnapshot, SubAgentReference
from src.agentposix.models.execution_pointer import ExecutionPointer
from src.agentposix.models.message import ConversationHistory, ToolDefinition
from src.agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from src.agentposix.models.side_effect import SideEffectRegistry


class AgentStateObject(BaseModel):
    spec_version: str = "1.0.0"
    identity: IdentityBlock
    status: ASOStatus = ASOStatus.INITIALIZING
    created_at: str
    frozen_at: Optional[str] = None
    resumed_at: Optional[str] = None
    human_summary: str = ""

    model_config_block: ModelConfig
    conversation: ConversationHistory
    tool_registry: List[ToolDefinition] = Field(default_factory=list)
    execution_pointer: ExecutionPointer
    side_effects: SideEffectRegistry
    environment: EnvironmentSnapshot
    sub_agents: List[SubAgentReference] = Field(default_factory=list)

    extensions: Dict[str, Any] = Field(default_factory=dict)
    metadata: FreezeMetadata
    checksum: str = ""
