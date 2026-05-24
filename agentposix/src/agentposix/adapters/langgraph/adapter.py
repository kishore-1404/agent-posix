from typing import Any, Dict, Iterator, Optional, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

from agentposix.enums import FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.base import StorageBackend


def _configurable(config: RunnableConfig) -> dict[str, Any]:
    return config.get("configurable", {})


def _checkpoint_id(config: RunnableConfig) -> Optional[str]:
    value = _configurable(config).get("checkpoint_id")
    return str(value) if value is not None else None


def _checkpoint_ns(config: RunnableConfig) -> str:
    return str(_configurable(config).get("checkpoint_ns", ""))


def _thread_id(config: RunnableConfig) -> str:
    return str(_configurable(config)["thread_id"])


def _current_node_id(metadata: CheckpointMetadata) -> str:
    writes = metadata.get("writes")
    if isinstance(writes, dict) and writes:
        return str(next(iter(writes)))

    for key in ("node", "langgraph_node"):
        value = metadata.get(key)
        if value is not None:
            return str(value)

    step = metadata.get("step", "unknown")
    return f"step:{step}"


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
        thread_id = _thread_id(config)
        checkpoint_ns = _checkpoint_ns(config)
        parent_checkpoint_id = _checkpoint_id(config)
        current_node = _current_node_id(metadata)

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
            extensions={
                "langgraph_checkpoint": dict(checkpoint),
                "langgraph_metadata": dict(metadata),
                "langgraph_new_versions": dict(new_versions),
                "langgraph_checkpoint_ns": checkpoint_ns,
                "langgraph_parent_checkpoint_id": parent_checkpoint_id,
                "langgraph_pending_writes": [],
            },
        )
        self.backend.write_aso(aso)
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = _thread_id(config)
        if not self.backend.exists(thread_id):
            return None
        aso = self.backend.read_aso(thread_id)
        checkpoint = Checkpoint(**aso.extensions.get("langgraph_checkpoint", {}))
        metadata = CheckpointMetadata(**aso.extensions.get("langgraph_metadata", {}))
        checkpoint_ns = str(aso.extensions.get("langgraph_checkpoint_ns", ""))
        parent_checkpoint_id = aso.extensions.get("langgraph_parent_checkpoint_id")
        checkpoint_config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }
        parent_config = (
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": parent_checkpoint_id,
                }
            }
            if parent_checkpoint_id
            else None
        )
        return CheckpointTuple(
            config=checkpoint_config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=aso.extensions.get("langgraph_pending_writes", []),
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
