from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

from src.agentposix.enums import FreezeTriggerReasonEnum, ParadigmEnum
from src.agentposix.models.aso import AgentStateObject
from src.agentposix.models.environment import EnvironmentSnapshot
from src.agentposix.models.execution_pointer import ExecutionPointer
from src.agentposix.models.message import ConversationHistory
from src.agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from src.agentposix.models.side_effect import SideEffectRegistry
from src.agentposix.storage.base import StorageBackend


class ASOLangGraphSaver(BaseCheckpointSaver):
    def __init__(self, backend: StorageBackend):
        super().__init__()
        self.backend = backend

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        current_node = metadata.get("step", "unknown")

        aso = AgentStateObject(
            identity=IdentityBlock(aso_id=checkpoint["id"], session_id=thread_id),
            created_at=checkpoint["ts"],
            human_summary=f"LangGraph step: {current_node}",
            model_config_block=ModelConfig(provider="langchain", model_id="unknown"),
            conversation=ConversationHistory(),
            execution_pointer=ExecutionPointer(
                paradigm=ParadigmEnum.DAG_GRAPH,
                current_node_id=current_node,
                pending_node_ids=checkpoint.get("next", []),
            ),
            side_effects=SideEffectRegistry(),
            environment=EnvironmentSnapshot(cwd="/", python_version="3.10", platform="linux"),
            metadata=FreezeMetadata(
                framework_name="langgraph",
                framework_version="0.2.62",
                trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
            ),
            extensions={"langgraph_channels": checkpoint["channel_values"]},
        )
        self.backend.write_aso(aso)
        return config

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        if not self.backend.exists(thread_id):
            return None
        aso = self.backend.read_aso(thread_id)
        checkpoint = Checkpoint(
            v=1,
            ts=aso.created_at,
            id=aso.identity.aso_id,
            channel_values=aso.extensions.get("langgraph_channels", {}),
            channel_versions={},
            versions_seen={},
            pending_writes=[],
        )
        return CheckpointTuple(
            config,
            checkpoint,
            {"step": aso.execution_pointer.current_node_id},
            None,
        )

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        yield from []

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        pass
