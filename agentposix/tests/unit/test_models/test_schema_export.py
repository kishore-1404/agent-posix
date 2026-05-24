import json
from pathlib import Path

from agentposix.models.aso import AgentStateObject

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "spec" / "agent_state_object.schema.json"


def test_agent_state_object_schema_artifact_is_stable():
    exported_schema = AgentStateObject.model_json_schema()
    committed_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert committed_schema == exported_schema
    assert committed_schema["title"] == "AgentStateObject"
