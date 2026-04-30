from typing import List, Optional

from pydantic import BaseModel, Field

from src.agentposix.enums import ParadigmEnum, SafeBoundaryTypeEnum


class ExecutionPointer(BaseModel):
    paradigm: ParadigmEnum = ParadigmEnum.CUSTOM
    current_step_index: Optional[int] = None
    current_node_id: Optional[str] = None
    completed_node_ids: List[str] = Field(default_factory=list)
    pending_node_ids: List[str] = Field(default_factory=list)
    loop_iteration_count: int = 0
    last_safe_boundary_type: Optional[SafeBoundaryTypeEnum] = None
    last_safe_boundary_timestamp: Optional[str] = None
    reasoning_scratchpad: Optional[str] = None
