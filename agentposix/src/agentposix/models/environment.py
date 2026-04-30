from typing import Dict, List

from pydantic import BaseModel, Field

from src.agentposix.enums import ASOStatus


class EnvironmentSnapshot(BaseModel):
    cwd: str
    python_version: str
    platform: str
    env_vars: Dict[str, str] = Field(default_factory=dict)
    file_checksums: Dict[str, str] = Field(default_factory=dict)
    git_commit_hash: str = ""


class SubAgentReference(BaseModel):
    session_id: str
    status: ASOStatus
    aso_file_path: str
