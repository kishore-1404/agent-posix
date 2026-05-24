from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

from agentposix.adapters.langgraph.adapter import ASOLangGraphSaver
from agentposix.enums import ParadigmEnum
from agentposix.storage.filesystem import FilesystemBackend


def make_checkpoint(checkpoint_id: str = "checkpoint-2") -> Checkpoint:
    return {
        "v": 2,
        "id": checkpoint_id,
        "ts": "2026-05-25T00:00:00+00:00",
        "channel_values": {
            "messages": [{"role": "assistant", "content": "ready"}],
            "route": "tools",
            "scratchpad": {"tokens": 42},
        },
        "channel_versions": {
            "messages": "0002",
            "route": "0001",
            "scratchpad": "0001",
        },
        "versions_seen": {
            "agent": {"messages": "0001"},
            "tools": {"route": "0001"},
        },
        "pending_sends": [],
        "updated_channels": ["messages", "route"],
        "next": ["tools"],
    }


def make_metadata() -> CheckpointMetadata:
    return {
        "source": "loop",
        "step": 2,
        "parents": {},
        "run_id": "run-1",
        "writes": {
            "agent": {"messages": [{"role": "assistant", "content": "ready"}]},
        },
    }


def test_langgraph_put_persists_checkpoint_mapping_and_returns_updated_config(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    saver = ASOLangGraphSaver(backend)
    config = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "main",
            "checkpoint_id": "checkpoint-1",
        }
    }

    returned = saver.put(
        config,
        make_checkpoint(),
        make_metadata(),
        {"messages": "0002", "route": "0001"},
    )

    assert returned == {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "main",
            "checkpoint_id": "checkpoint-2",
        }
    }

    aso = backend.read_aso("thread-1")
    assert aso.identity.aso_id == "checkpoint-2"
    assert aso.identity.session_id == "thread-1"
    assert aso.execution_pointer.paradigm == ParadigmEnum.DAG_GRAPH
    assert aso.execution_pointer.current_node_id == "agent"
    assert aso.execution_pointer.pending_node_ids == ["tools"]
    assert aso.extensions["langgraph_checkpoint"]["channel_values"]["route"] == "tools"
    assert aso.extensions["langgraph_checkpoint"]["channel_versions"]["messages"] == "0002"
    assert aso.extensions["langgraph_metadata"]["step"] == 2
    assert aso.extensions["langgraph_new_versions"] == {
        "messages": "0002",
        "route": "0001",
    }
    assert aso.extensions["langgraph_checkpoint_ns"] == "main"
    assert aso.extensions["langgraph_parent_checkpoint_id"] == "checkpoint-1"


def test_langgraph_get_tuple_round_trips_checkpoint_metadata_and_parent(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    saver = ASOLangGraphSaver(backend)
    config = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "main",
            "checkpoint_id": "checkpoint-1",
        }
    }
    checkpoint = make_checkpoint()
    metadata = make_metadata()
    saver.put(config, checkpoint, metadata, {"messages": "0002", "route": "0001"})

    restored = saver.get_tuple({"configurable": {"thread_id": "thread-1"}})

    assert restored is not None
    assert restored.config == {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "main",
            "checkpoint_id": "checkpoint-2",
        }
    }
    assert restored.checkpoint == checkpoint
    assert restored.metadata == metadata
    assert restored.parent_config == {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "main",
            "checkpoint_id": "checkpoint-1",
        }
    }
    assert restored.pending_writes == []


def test_langgraph_get_tuple_returns_none_for_missing_thread(tmp_path):
    saver = ASOLangGraphSaver(FilesystemBackend(str(tmp_path)))

    assert saver.get_tuple({"configurable": {"thread_id": "missing"}}) is None
