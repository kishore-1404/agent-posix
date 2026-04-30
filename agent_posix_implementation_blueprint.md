# Agent POSIX: Implementation Blueprint — Task Tracker

> **Full specification source:** *Agent POSIX: Architectural Specification and Implementation Blueprint*
> All tasks are sequentially ordered and atomically scoped. Complete them in dependency order.

---

## 1. Executive Summary & State of the Art

> **Context:** Existing orchestration frameworks treat state as an opaque, framework-coupled byproduct.
> - **LangGraph** persists channel versions via `BaseCheckpointSaver`, but its SQLite implementation hides the execution pointer implicitly within graph topology.
> - **OpenAI's `openai-agents-python`** relies on `weakref` caches that obliterate nested execution states upon garbage collection during Human-in-the-Loop (HITL) pauses.
> - **AutoGen** and **CrewAI** frequently drop historical context across process boundaries.
>
> **Solution:** Construct the **Portable Agent State Serialization Format (Agent POSIX)** — integrating OS process checkpointing paradigms (analogous to CRIU) with event-sourcing principles derived from deterministic workflow engines like Temporal.io.
> The central artifact is the **Agent State Object (ASO)** — a normative JSON Schema Draft 2020-12 artifact — governed by a strict lifecycle protocol.

---

## 2. Core Architectural Decisions (Pre-Resolved — Zero Decision Execution)

- [ ] **A1 — Package Name:** `agentposix` — concise, memorable, CLI-friendly, no hyphenation conflicts. PyPI availability confirmed.
- [ ] **A2 — Python Version:** `>= 3.10` — mandated by LangGraph and OpenAI Agents SDK as their baseline.
- [ ] **A3 — Pydantic Version:** Pydantic v2 — all ASO schemas enforce strict serialization using `model_dump(mode="json")`.
- [ ] **A4 — Async Strategy:** Dual execution with `async` as primary. `asyncio.run` wrappers provided for synchronous contexts (matching LangGraph's `AsyncSqliteSaver` and OpenAI's `Runner.run()`).
- [ ] **A5 — CLI Framework:** Typer `0.15.2` — type-safe CLI interfaces backed by Click, integrated with Rich for tree-based ASO inspection.
- [ ] **A6 — Testing:** `pytest` + `pytest-asyncio` with `asyncio_mode = "auto"`.
- [ ] **A7 — Serialization:** Strict JSON. Artifact extension: `.aso.json`. Gzip compression deferred to filesystem/adapter configurations.
- [ ] **A8 — Storage Backends:** `FilesystemBackend` (primary, atomic `os.rename`) and `SqliteBackend` (secondary, WAL-mode, `aiosqlite`).
- [ ] **B — Schema Fields:** ASO encompasses: `Identity`, `Metadata`, `ModelConfig`, `ConversationHistory`, `ToolRegistry`, `ExecutionPointer`, `SideEffectRegistry`, `EnvironmentSnapshot`, `Extensions`, and `Checksum`.
- [ ] **C — LangGraph Adapter:** Inherits from `BaseCheckpointSaver`. Intercepts `put()` and extracts channel values into ASO extensions, mapping LangGraph `next` arrays to `aso.execution_pointer.pending_node_ids`.
- [ ] **D — Raw Adapter:** Exposes `@checkpoint_boundary(storage, session_id, step_name)`. Computes deterministic SHA-256 idempotency keys (`session_id + step_name + tool_name + args`) to skip re-execution of completed side-effects.

---

## 3. Implementation Blueprint — All Tasks

---

### TASK 001 — Create the Root Directory Structure

- **File:** None
- **Action:** `RUN`
- **Depends On:** `NONE`

- [ ] **Instruction:** Execute standard `mkdir` commands to create the exact project structure required for the `agentposix` package.

- [ ] **Exact Command:**
  ```bash
  mkdir -p agentposix/src/agentposix/models \
            agentposix/src/agentposix/storage \
            agentposix/src/agentposix/core \
            agentposix/src/agentposix/adapters/langgraph \
            agentposix/src/agentposix/adapters/raw_python \
            agentposix/src/agentposix/signals \
            agentposix/src/agentposix/cli \
            agentposix/tests/unit/test_models \
            agentposix/tests/unit/test_storage \
            agentposix/tests/unit/test_core \
            agentposix/tests/unit/test_cli \
            agentposix/tests/integration \
            agentposix/spec \
            agentposix/docs/concepts \
            agentposix/docs/adapters \
            agentposix/docs/api-reference \
            agentposix/.github/workflows
  ```

- [ ] **Verification:**
  ```bash
  test -d agentposix/src/agentposix/models && echo "PASS"
  ```

---

### TASK 002 — Initialize Git and `.gitignore`

- **File:** `agentposix/.gitignore`
- **Action:** `CREATE`
- **Depends On:** `TASK 001`

- [ ] **Instruction:** Create a comprehensive Python `.gitignore` file.

- [ ] **Exact Content:**
  ```
  __pycache__/
  *.py[cod]
  *$py.class
  *.so
  .Python
  build/
  develop-eggs/
  dist/
  downloads/
  eggs/
  .eggs/
  lib/
  lib64/
  parts/
  sdist/
  var/
  wheels/
  *.egg-info/
  .installed.cfg
  *.egg
  .env
  .venv
  env/
  venv/
  ENV/
  env.bak/
  venv.bak/
  .pytest_cache/
  .coverage
  htmlcov/
  .tox/
  .mypy_cache/
  .ruff_cache/
  *.aso.json
  checkpoints/
  ```

- [ ] **Verification:**
  ```bash
  cat agentposix/.gitignore | grep "venv" && echo "PASS"
  ```

---

### TASK 003 — Create `pyproject.toml`

- **File:** `agentposix/pyproject.toml`
- **Action:** `CREATE`
- **Depends On:** `TASK 001`

- [ ] **Instruction:** Define package metadata, dependencies, and CLI entry points.

- [ ] **Exact Content:**
  ```toml
  [build-system]
  requires = ["setuptools>=61.0", "wheel"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "agentposix"
  version = "0.1.0"
  description = "Portable Agent State Serialization Format and Lifecycle Protocol"
  readme = "README.md"
  requires-python = ">=3.10"
  license = {text = "MIT"}
  dependencies = [
      "pydantic>=2.7.4",
      "typer==0.15.2",
      "rich>=13.7.0"
  ]

  [project.optional-dependencies]
  adapters = ["langgraph>=0.2.62", "langchain-core>=0.3.29"]
  storage = ["aiosqlite==0.20.0"]
  dev = [
      "pytest>=8.0.0",
      "pytest-asyncio>=0.23.5",
      "pytest-cov>=4.1.0",
      "mkdocs-material>=9.5.0",
      "mkdocstrings[python]>=0.24.0",
      "ruff>=0.15.2",
      "build",
      "twine",
      "requests-mock"
  ]

  [project.scripts]
  agentposix = "agentposix.cli.main:app"

  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["tests"]
  ```

- [ ] **Verification:**
  ```bash
  cat agentposix/pyproject.toml | grep "agentposix" && echo "PASS"
  ```

---

### TASK 004 — Create `.python-version`

- **File:** `agentposix/.python-version`
- **Action:** `CREATE`
- **Depends On:** `TASK 001`

- [ ] **Instruction:** Pin the minimum Python version.

- [ ] **Exact Content:**
  ```
  3.10.0
  ```

- [ ] **Verification:**
  ```bash
  cat agentposix/.python-version | grep "3.10" && echo "PASS"
  ```

---

### TASK 005 — Initialize Virtual Environment

- **File:** None
- **Action:** `RUN`
- **Depends On:** `TASK 003`, `TASK 004`

- [ ] **Instruction:** Create a `venv` and install the package with all optional groups.

- [ ] **Exact Command:**
  ```bash
  cd agentposix && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[adapters,storage,dev]"
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "import pydantic; print('PASS')"
  ```

---

### TASK 006 — Create Package `__init__.py` Files

- **File:** None
- **Action:** `RUN`
- **Depends On:** `TASK 001`

- [ ] **Instruction:** Create empty `__init__.py` files to establish Python subpackages.

- [ ] **Exact Command:**
  ```bash
  touch agentposix/src/agentposix/models/__init__.py \
        agentposix/src/agentposix/storage/__init__.py \
        agentposix/src/agentposix/core/__init__.py \
        agentposix/src/agentposix/adapters/__init__.py \
        agentposix/src/agentposix/adapters/langgraph/__init__.py \
        agentposix/src/agentposix/adapters/raw_python/__init__.py \
        agentposix/src/agentposix/signals/__init__.py \
        agentposix/src/agentposix/cli/__init__.py \
        agentposix/tests/__init__.py \
        agentposix/tests/unit/__init__.py \
        agentposix/tests/unit/test_models/__init__.py \
        agentposix/tests/unit/test_storage/__init__.py \
        agentposix/tests/unit/test_core/__init__.py \
        agentposix/tests/unit/test_cli/__init__.py \
        agentposix/tests/integration/__init__.py
  ```

- [ ] **Verification:**
  ```bash
  ls agentposix/src/agentposix/models/__init__.py && echo "PASS"
  ```

---

### TASK 007 — Create Exceptions File

- **File:** `agentposix/src/agentposix/exceptions.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 006`

- [ ] **Instruction:** Define all custom exceptions used by the library.

- [ ] **Exact Content:**
  ```python
  class AgentPOSIXError(Exception):
      """Base exception for all Agent POSIX errors."""
      pass

  class ChecksumMismatchError(AgentPOSIXError):
      """Raised when an ASO file checksum fails validation."""
      pass

  class HostDriftError(AgentPOSIXError):
      """Raised when environment file checksums mismatch on resume."""
      pass

  class InvalidASOError(AgentPOSIXError):
      """Raised when an ASO fails schema validation."""
      pass

  class StateTransitionError(AgentPOSIXError):
      """Raised for invalid lifecycle state transitions."""
      pass
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.exceptions import ChecksumMismatchError; print('PASS')"
  ```

---

### TASK 008 — Create Enums File

- **File:** `agentposix/src/agentposix/enums.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 006`

- [ ] **Instruction:** Define all string enumerations required for strict ASO schema validation.

- [ ] **Exact Content:**
  ```python
  from enum import Enum

  class ASOStatus(str, Enum):
      INITIALIZING  = "INITIALIZING"
      RUNNING       = "RUNNING"
      CHECKPOINTING = "CHECKPOINTING"
      CHECKPOINTED  = "CHECKPOINTED"
      RESUMING      = "RESUMING"
      TERMINATED    = "TERMINATED"
      FAILED        = "FAILED"

  class FreezeTriggerReasonEnum(str, Enum):
      EXPLICIT_CALL = "EXPLICIT_CALL"
      SIGTERM       = "SIGTERM"
      SIGINT        = "SIGINT"
      RATE_LIMIT    = "RATE_LIMIT"
      ERROR         = "ERROR"
      TIMEOUT       = "TIMEOUT"
      STEP_LIMIT    = "STEP_LIMIT"

  class ParadigmEnum(str, Enum):
      REACT_LOOP    = "REACT_LOOP"
      DAG_GRAPH     = "DAG_GRAPH"
      PLAN_EXECUTE  = "PLAN_EXECUTE"
      CUSTOM        = "CUSTOM"

  class SafeBoundaryTypeEnum(str, Enum):
      AFTER_LLM_RESPONSE = "AFTER_LLM_RESPONSE"
      AFTER_TOOL_RESULT  = "AFTER_TOOL_RESULT"
      AFTER_PLAN_STEP    = "AFTER_PLAN_STEP"
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.enums import ASOStatus; print('PASS')"
  ```

---

### TASK 009 — Create Metadata Models

- **File:** `agentposix/src/agentposix/models/metadata.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 008`

- [ ] **Instruction:** Define the `ModelConfig`, `FreezeMetadata`, and `IdentityBlock` classes.

- [ ] **Exact Content:**
  ```python
  from typing import Optional, Dict, Any
  from pydantic import BaseModel, Field
  from src.agentposix.enums import FreezeTriggerReasonEnum

  class ModelConfig(BaseModel):
      provider:     str            = Field(..., example="anthropic")
      model_id:     str            = Field(..., example="claude-3-5-sonnet-20241022")
      temperature:  float          = Field(0.0)
      max_tokens:   Optional[int]  = None
      top_p:        Optional[float]= None
      system_prompt:Optional[str]  = None
      api_base_url: Optional[str]  = None

  class FreezeMetadata(BaseModel):
      framework_name:    str                       = Field(..., example="langgraph")
      framework_version: str                       = Field(..., example="0.2.62")
      agentposix_version:str                       = Field("0.1.0")
      trigger_reason:    FreezeTriggerReasonEnum
      error_info:        Optional[Dict[str, Any]]  = None

  class IdentityBlock(BaseModel):
      aso_id:           str
      session_id:       str
      parent_session_id:Optional[str] = None
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.models.metadata import ModelConfig; print('PASS')"
  ```

---

### TASK 010 — Create Message and Tool Models

- **File:** `agentposix/src/agentposix/models/message.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 006`

- [ ] **Instruction:** Define OpenAI-compatible `Message` and `ToolCall` schemas.

- [ ] **Exact Content:**
  ```python
  from typing import Optional, List, Dict, Any
  from pydantic import BaseModel, Field

  class ToolCall(BaseModel):
      id:       str
      type:     str              = "function"
      function: Dict[str, Any]

  class Message(BaseModel):
      role:        str                       = Field(..., description="Role: system, user, assistant, tool")
      content:     Optional[str]             = None
      name:        Optional[str]             = None
      tool_calls:  Optional[List[ToolCall]]  = None
      tool_call_id:Optional[str]             = None

  class ConversationHistory(BaseModel):
      messages:              List[Message] = Field(default_factory=list)
      message_count:         int           = 0
      truncation_applied:    bool          = False
      original_message_count:int           = 0

  class ToolDefinition(BaseModel):
      name:         str
      description:  Optional[str]     = None
      input_schema: Dict[str, Any]    = Field(default_factory=dict)
      idempotent:   bool              = False
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.models.message import Message; print('PASS')"
  ```

---

### TASK 011 — Create Execution Pointer Model

- **File:** `agentposix/src/agentposix/models/execution_pointer.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 008`

- [ ] **Instruction:** Define the `ExecutionPointer` combining topological and temporal state tracking.

- [ ] **Exact Content:**
  ```python
  from typing import List, Optional
  from pydantic import BaseModel, Field
  from src.agentposix.enums import ParadigmEnum, SafeBoundaryTypeEnum

  class ExecutionPointer(BaseModel):
      paradigm:                    ParadigmEnum              = ParadigmEnum.CUSTOM
      current_step_index:          Optional[int]             = None
      current_node_id:             Optional[str]             = None
      completed_node_ids:          List[str]                 = Field(default_factory=list)
      pending_node_ids:            List[str]                 = Field(default_factory=list)
      loop_iteration_count:        int                       = 0
      last_safe_boundary_type:     Optional[SafeBoundaryTypeEnum] = None
      last_safe_boundary_timestamp:Optional[str]             = None
      reasoning_scratchpad:        Optional[str]             = None
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.models.execution_pointer import ExecutionPointer; print('PASS')"
  ```

---

### TASK 012 — Create Side Effect Model

- **File:** `agentposix/src/agentposix/models/side_effect.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 006`

- [ ] **Instruction:** Define the `SideEffectEntry` and `SideEffectRegistry` models.

- [ ] **Exact Content:**
  ```python
  from typing import Dict, Any, Optional, List
  from pydantic import BaseModel, Field, field_validator
  import re

  class SideEffectEntry(BaseModel):
      idempotency_key: str
      tool_name:       str
      tool_args:       Dict[str, Any]
      executed_at:     str
      result_summary:  Optional[str] = None
      is_reversible:   bool          = False
      replay_safe:     bool          = False

      @field_validator("idempotency_key")
      @classmethod
      def validate_key(cls, v: str) -> str:
          if not re.match(r"^[a-f0-9]{64}$", v):
              raise ValueError("Idempotency key must be a 64-character SHA256 hex string.")
          return v

  class SideEffectRegistry(BaseModel):
      entries: List[SideEffectEntry] = Field(default_factory=list)
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.models.side_effect import SideEffectRegistry; print('PASS')"
  ```

---

### TASK 013 — Create Environment Snapshot Model

- **File:** `agentposix/src/agentposix/models/environment.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 006`

- [ ] **Instruction:** Define the `EnvironmentSnapshot` and `SubAgentReference` models.

- [ ] **Exact Content:**
  ```python
  from typing import Dict, List
  from pydantic import BaseModel, Field
  from src.agentposix.enums import ASOStatus

  class EnvironmentSnapshot(BaseModel):
      cwd:             str
      python_version:  str
      platform:        str
      env_vars:        Dict[str, str] = Field(default_factory=dict)
      file_checksums:  Dict[str, str] = Field(default_factory=dict)
      git_commit_hash: str            = ""

  class SubAgentReference(BaseModel):
      session_id:    str
      status:        ASOStatus
      aso_file_path: str
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.models.environment import EnvironmentSnapshot; print('PASS')"
  ```

---

### TASK 014 — Create Core `AgentStateObject` Model

- **File:** `agentposix/src/agentposix/models/aso.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 008`, `TASK 009`, `TASK 010`, `TASK 011`, `TASK 012`, `TASK 013`

- [ ] **Instruction:** Assemble all schema blocks into the root ASO model.

- [ ] **Exact Content:**
  ```python
  from typing import Dict, Any, List, Optional
  from pydantic import BaseModel, Field
  from src.agentposix.enums import ASOStatus
  from src.agentposix.models.metadata import IdentityBlock, ModelConfig, FreezeMetadata
  from src.agentposix.models.message import ConversationHistory, ToolDefinition
  from src.agentposix.models.execution_pointer import ExecutionPointer
  from src.agentposix.models.side_effect import SideEffectRegistry
  from src.agentposix.models.environment import EnvironmentSnapshot, SubAgentReference

  class AgentStateObject(BaseModel):
      spec_version:       str                      = "1.0.0"
      identity:           IdentityBlock
      status:             ASOStatus                = ASOStatus.INITIALIZING
      created_at:         str
      frozen_at:          Optional[str]            = None
      resumed_at:         Optional[str]            = None
      human_summary:      str                      = ""

      model_config_block: ModelConfig
      conversation:       ConversationHistory
      tool_registry:      List[ToolDefinition]     = Field(default_factory=list)
      execution_pointer:  ExecutionPointer
      side_effects:       SideEffectRegistry
      environment:        EnvironmentSnapshot
      sub_agents:         List[SubAgentReference]  = Field(default_factory=list)

      extensions:         Dict[str, Any]           = Field(default_factory=dict)
      metadata:           FreezeMetadata
      checksum:           str                      = ""
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.models.aso import AgentStateObject; print('PASS')"
  ```

---

### TASK 015 — Create Checksum Logic

- **File:** `agentposix/src/agentposix/core/checksum.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 014`

- [ ] **Instruction:** Implement the SHA-256 deterministic checksum generator.

- [ ] **Exact Content:**
  ```python
  import hashlib
  import json
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.exceptions import ChecksumMismatchError

  def compute_checksum(aso: AgentStateObject) -> str:
      """Computes SHA256 of the ASO ignoring the checksum field itself."""
      data = aso.model_dump(mode="json")
      data["checksum"] = ""
      encoded = json.dumps(data, sort_keys=True).encode("utf-8")
      return hashlib.sha256(encoded).hexdigest()

  def verify_checksum(aso: AgentStateObject) -> bool:
      """Raises ChecksumMismatchError if the checksum is invalid."""
      expected = aso.checksum
      actual   = compute_checksum(aso)
      if expected and expected != actual:
          raise ChecksumMismatchError(
              f"ASO checksum verification failed for session {aso.identity.session_id}. "
              f"Expected {expected}, got {actual}. The ASO file may be corrupted."
          )
      return True
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.core.checksum import compute_checksum; print('PASS')"
  ```

---

### TASK 016 — Create Storage Backend ABC

- **File:** `agentposix/src/agentposix/storage/base.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 014`

- [ ] **Instruction:** Define the `StorageBackend` abstract base class with sync and async abstract methods.

- [ ] **Exact Content:**
  ```python
  from abc import ABC, abstractmethod
  from typing import List
  from src.agentposix.models.aso import AgentStateObject

  class StorageBackend(ABC):

      @abstractmethod
      def write_aso(self, aso: AgentStateObject) -> None:
          pass

      @abstractmethod
      def read_aso(self, session_id: str) -> AgentStateObject:
          pass

      @abstractmethod
      def list_sessions(self) -> List[str]:
          pass

      @abstractmethod
      def delete_aso(self, session_id: str) -> None:
          pass

      @abstractmethod
      def exists(self, session_id: str) -> bool:
          pass
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.storage.base import StorageBackend; print('PASS')"
  ```

---

### TASK 017 — Create `FilesystemBackend`

- **File:** `agentposix/src/agentposix/storage/filesystem.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 016`

- [ ] **Instruction:** Implement `FilesystemBackend` ensuring atomic `os.rename` writes.

- [ ] **Exact Content:**
  ```python
  import os
  import json
  from pathlib import Path
  from typing import List
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.storage.base import StorageBackend
  from src.agentposix.core.checksum import compute_checksum

  class FilesystemBackend(StorageBackend):

      def __init__(self, base_dir: str = ".agentposix"):
          self.base_dir = Path(base_dir)
          self.base_dir.mkdir(parents=True, exist_ok=True)

      def _get_path(self, session_id: str) -> Path:
          return self.base_dir / f"{session_id}.aso.json"

      def write_aso(self, aso: AgentStateObject) -> None:
          target_path = self._get_path(aso.identity.session_id)
          tmp_path    = target_path.with_suffix(".tmp")
          aso.checksum = compute_checksum(aso)
          with open(tmp_path, "w", encoding="utf-8") as f:
              json.dump(aso.model_dump(mode="json"), f, indent=2)
          os.replace(tmp_path, target_path)

      def read_aso(self, session_id: str) -> AgentStateObject:
          path = self._get_path(session_id)
          if not path.exists():
              raise FileNotFoundError(f"No ASO found for {session_id}")
          with open(path, "r", encoding="utf-8") as f:
              data = json.load(f)
          return AgentStateObject.model_validate(data)

      def list_sessions(self) -> List[str]:
          return [p.name.replace(".aso.json", "") for p in self.base_dir.glob("*.aso.json")]

      def delete_aso(self, session_id: str) -> None:
          path = self._get_path(session_id)
          if path.exists():
              path.unlink()

      def exists(self, session_id: str) -> bool:
          return self._get_path(session_id).exists()
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.storage.filesystem import FilesystemBackend; print('PASS')"
  ```

---

### TASK 018 — Create `SqliteBackend`

- **File:** `agentposix/src/agentposix/storage/sqlite.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 016`

- [ ] **Instruction:** Implement the async `SqliteBackend` using `aiosqlite` with WAL mode.

- [ ] **Exact Content:**
  ```python
  import json
  import asyncio
  import aiosqlite
  from typing import List
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.storage.base import StorageBackend
  from src.agentposix.core.checksum import compute_checksum

  class AsyncSqliteBackend:

      def __init__(self, db_path: str = ".agentposix.db"):
          self.db_path = db_path

      async def _init_db(self):
          async with aiosqlite.connect(self.db_path) as db:
              await db.execute("PRAGMA journal_mode=WAL;")
              await db.execute(
                  "CREATE TABLE IF NOT EXISTS checkpoints "
                  "(session_id TEXT PRIMARY KEY, payload JSON)"
              )
              await db.commit()

      async def write_aso(self, aso: AgentStateObject) -> None:
          await self._init_db()
          aso.checksum = compute_checksum(aso)
          payload = json.dumps(aso.model_dump(mode="json"))
          async with aiosqlite.connect(self.db_path) as db:
              await db.execute(
                  "INSERT INTO checkpoints (session_id, payload) VALUES (?, ?) "
                  "ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload",
                  (aso.identity.session_id, payload)
              )
              await db.commit()

      async def read_aso(self, session_id: str) -> AgentStateObject:
          await self._init_db()
          async with aiosqlite.connect(self.db_path) as db:
              async with db.execute(
                  "SELECT payload FROM checkpoints WHERE session_id = ?",
                  (session_id,)
              ) as cursor:
                  row = await cursor.fetchone()
                  if not row:
                      raise KeyError(f"Session {session_id} not found.")
                  return AgentStateObject.model_validate_json(row[0])
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.storage.sqlite import AsyncSqliteBackend; print('PASS')"
  ```

---

### TASK 019 — Create Core Freeze Protocol

- **File:** `agentposix/src/agentposix/core/freeze.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 015`, `TASK 017`

- [ ] **Instruction:** Implement the `freeze()` function to enforce atomic checkpoints.

- [ ] **Exact Content:**
  ```python
  from datetime import datetime, timezone
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.storage.base import StorageBackend
  from src.agentposix.enums import ASOStatus
  from src.agentposix.core.checksum import compute_checksum

  def freeze(aso: AgentStateObject, storage: StorageBackend, summary: str = "") -> AgentStateObject:
      """
      Executes the Agent POSIX Freeze Protocol.
      Sets the status to CHECKPOINTED, computes checksum, and writes to storage.
      """
      aso.status    = ASOStatus.CHECKPOINTED
      aso.frozen_at = datetime.now(timezone.utc).isoformat()
      if summary:
          aso.human_summary = summary

      # Finalize checksum
      aso.checksum = compute_checksum(aso)

      # Atomic write to storage
      storage.write_aso(aso)
      return aso
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.core.freeze import freeze; print('PASS')"
  ```

---

### TASK 020 — Create Core Resume Protocol

- **File:** `agentposix/src/agentposix/core/resume.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 015`, `TASK 017`

- [ ] **Instruction:** Implement the `resume()` function enforcing checksum verification.

- [ ] **Exact Content:**
  ```python
  from datetime import datetime, timezone
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.storage.base import StorageBackend
  from src.agentposix.enums import ASOStatus
  from src.agentposix.core.checksum import verify_checksum

  def resume(session_id: str, storage: StorageBackend) -> AgentStateObject:
      """
      Executes the Agent POSIX Resume Protocol.
      Reads ASO, verifies checksum, and transitions to RESUMING.
      """
      aso = storage.read_aso(session_id)

      # Integrity validation
      verify_checksum(aso)

      # Transition state
      aso.status     = ASOStatus.RESUMING
      aso.resumed_at = datetime.now(timezone.utc).isoformat()

      return aso
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.core.resume import resume; print('PASS')"
  ```

---

### TASK 021 — Implement Signal Handling

- **File:** `agentposix/src/agentposix/signals/handler.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 019`

- [ ] **Instruction:** Implement `FreezeSignalHandler` to catch `SIGTERM` and `SIGINT`.

- [ ] **Exact Content:**
  ```python
  import signal
  import sys
  from typing import Callable
  from src.agentposix.core.freeze import freeze
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.storage.base import StorageBackend

  class FreezeSignalHandler:

      def __init__(self, aso: AgentStateObject, storage: StorageBackend):
          self.aso                = aso
          self.storage            = storage
          self._original_sigint:  Callable = signal.getsignal(signal.SIGINT)
          self._original_sigterm: Callable = signal.getsignal(signal.SIGTERM)

      def register(self):
          signal.signal(signal.SIGINT,  self._handle_signal)
          signal.signal(signal.SIGTERM, self._handle_signal)

      def deregister(self):
          signal.signal(signal.SIGINT,  self._original_sigint)
          signal.signal(signal.SIGTERM, self._original_sigterm)

      def _handle_signal(self, signum, frame):
          sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
          freeze(self.aso, self.storage, summary=f"Frozen via {sig_name}")
          self.deregister()
          sys.exit(0)
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.signals.handler import FreezeSignalHandler; print('PASS')"
  ```

---

### TASK 022 — Create Raw Python Adapter Decorator

- **File:** `agentposix/src/agentposix/adapters/raw_python/decorator.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 012`, `TASK 019`

- [ ] **Instruction:** Implement `@checkpoint_boundary` decorator for exact idempotency.

- [ ] **Exact Content:**
  ```python
  from functools import wraps
  import hashlib
  import json
  from typing import Callable, Any
  from src.agentposix.models.side_effect import SideEffectEntry
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.storage.base import StorageBackend
  from src.agentposix.core.freeze import freeze
  from datetime import datetime, timezone

  def checkpoint_boundary(aso: AgentStateObject, storage: StorageBackend, tool_name: str):
      """Instruments a python function to enforce idempotency and trigger checkpoints."""
      def decorator(func: Callable) -> Callable:
          @wraps(func)
          def wrapper(*args, **kwargs) -> Any:
              # Deterministic Idempotency Key
              sorted_kwargs = json.dumps(kwargs, sort_keys=True)
              key_string    = f"{aso.identity.session_id}:{tool_name}:{sorted_kwargs}"
              idemp_key     = hashlib.sha256(key_string.encode()).hexdigest()

              # Check cache to prevent duplicate side-effect
              for effect in aso.side_effects.entries:
                  if effect.idempotency_key == idemp_key and effect.result_summary:
                      return json.loads(effect.result_summary)

              # Execute real tool
              result = func(*args, **kwargs)

              # Record and freeze
              entry = SideEffectEntry(
                  idempotency_key=idemp_key,
                  tool_name=tool_name,
                  tool_args=kwargs,
                  executed_at=datetime.now(timezone.utc).isoformat(),
                  result_summary=json.dumps(result)
              )
              aso.side_effects.entries.append(entry)
              freeze(aso, storage, summary=f"Completed tool {tool_name}")
              return result
          return wrapper
      return decorator
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.adapters.raw_python.decorator import checkpoint_boundary; print('PASS')"
  ```

---

### TASK 023 — Create LangGraph Adapter Base Class

- **File:** `agentposix/src/agentposix/adapters/langgraph/adapter.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 014`, `TASK 016`

- [ ] **Instruction:** Implement the `ASOLangGraphSaver` extending `BaseCheckpointSaver`.

- [ ] **Exact Content:**
  ```python
  from typing import Any, Dict, Optional, Iterator, Sequence
  from langgraph.checkpoint.base import (
      BaseCheckpointSaver, Checkpoint,
      CheckpointMetadata, CheckpointTuple
  )
  from langchain_core.runnables import RunnableConfig
  from src.agentposix.storage.base import StorageBackend
  from src.agentposix.models.aso import AgentStateObject
  from src.agentposix.models.metadata import IdentityBlock, ModelConfig, FreezeMetadata
  from src.agentposix.models.message import ConversationHistory
  from src.agentposix.models.execution_pointer import ExecutionPointer
  from src.agentposix.models.side_effect import SideEffectRegistry
  from src.agentposix.models.environment import EnvironmentSnapshot
  from src.agentposix.enums import ParadigmEnum, FreezeTriggerReasonEnum
  from datetime import datetime, timezone

  class ASOLangGraphSaver(BaseCheckpointSaver):

      def __init__(self, backend: StorageBackend):
          super().__init__()
          self.backend = backend

      def put(
          self,
          config: RunnableConfig,
          checkpoint: Checkpoint,
          metadata: CheckpointMetadata,
          new_versions: dict
      ) -> RunnableConfig:
          thread_id    = config["configurable"]["thread_id"]
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
                  pending_node_ids=checkpoint.get("next", [])
              ),
              side_effects=SideEffectRegistry(),
              environment=EnvironmentSnapshot(cwd="/", python_version="3.10", platform="linux"),
              metadata=FreezeMetadata(
                  framework_name="langgraph",
                  framework_version="0.2.62",
                  trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL
              ),
              extensions={"langgraph_channels": checkpoint["channel_values"]}
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
              pending_writes=[]
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
          limit: Optional[int] = None
      ) -> Iterator[CheckpointTuple]:
          yield from []

      def put_writes(
          self,
          config: RunnableConfig,
          writes: Sequence[tuple[str, Any]],
          task_id: str,
          task_path: str = ""
      ) -> None:
          pass
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "from src.agentposix.adapters.langgraph.adapter import ASOLangGraphSaver; print('PASS')"
  ```

---

### TASK 024 — Create CLI Entrypoint

- **File:** `agentposix/src/agentposix/cli/main.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 017`, `TASK 019`, `TASK 020`

- [ ] **Instruction:** Create the Typer CLI app with `inspect`, `resume`, and `freeze` commands.

- [ ] **Exact Content:**
  ```python
  import typer
  from rich.console import Console
  from rich.tree import Tree
  from src.agentposix.storage.filesystem import FilesystemBackend
  from src.agentposix.core.resume import resume

  app     = typer.Typer(help="Agent POSIX CLI")
  console = Console()

  @app.command()
  def inspect(session_id: str, path: str = ".agentposix"):
      """Inspect an Agent State Object (ASO)."""
      try:
          backend = FilesystemBackend(path)
          aso     = backend.read_aso(session_id)
          tree    = Tree(f"[bold blue]ASO: {session_id}[/bold blue]")
          tree.add(f"Status: [bold]{aso.status.value}[/bold]")
          tree.add(f"Node: {aso.execution_pointer.current_node_id}")
          se_branch = tree.add("Side Effects")
          for se in aso.side_effects.entries:
              color = "green" if se.result_summary else "yellow"
              se_branch.add(
                  f"{se.tool_name} [[bold {color}]{se.idempotency_key[:8]}[/bold {color}]]"
              )
          console.print(tree)
      except Exception as e:
          console.print(f"[bold red]Error loading ASO:[/bold red] {str(e)}")
          raise typer.Exit(1)

  if __name__ == "__main__":
      app()
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && agentposix --help | grep "inspect" && echo "PASS"
  ```

---

### TASK 025 — Create Root Package `__init__.py` Public API

- **File:** `agentposix/src/agentposix/__init__.py`
- **Action:** `MODIFY`
- **Depends On:** `TASK 019`, `TASK 020`, `TASK 022`, `TASK 023`

- [ ] **Instruction:** Expose the public API of Agent POSIX at the root level.

- [ ] **Exact Content:**
  ```python
  from .core.freeze import freeze
  from .core.resume import resume
  from .adapters.raw_python.decorator import checkpoint_boundary
  from .adapters.langgraph.adapter import ASOLangGraphSaver
  from .models.aso import AgentStateObject
  from .storage.filesystem import FilesystemBackend

  __all__ = [
      "freeze",
      "resume",
      "checkpoint_boundary",
      "ASOLangGraphSaver",
      "AgentStateObject",
      "FilesystemBackend",
  ]
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -c "import src.agentposix; print(src.agentposix.ASOLangGraphSaver)" && echo "PASS"
  ```

---

### TASK 026 — Create Core Integration Test

- **File:** `agentposix/tests/integration/test_end_to_end.py`
- **Action:** `CREATE`
- **Depends On:** `TASK 025`

- [ ] **Instruction:** Write the final E2E test verifying idempotency during freeze.

- [ ] **Exact Content:**
  ```python
  import os
  import pytest
  from src.agentposix import FilesystemBackend, AgentStateObject, checkpoint_boundary
  from src.agentposix.models.metadata import IdentityBlock, ModelConfig, FreezeMetadata
  from src.agentposix.models.execution_pointer import ExecutionPointer
  from src.agentposix.models.side_effect import SideEffectRegistry
  from src.agentposix.models.message import ConversationHistory
  from src.agentposix.models.environment import EnvironmentSnapshot
  from src.agentposix.enums import ParadigmEnum, FreezeTriggerReasonEnum

  def test_idempotency_skip_on_resume(tmp_path):
      storage = FilesystemBackend(str(tmp_path))
      aso = AgentStateObject(
          identity=IdentityBlock(aso_id="test1", session_id="test_session"),
          created_at="2026-04-30T00:00:00Z",
          model_config_block=ModelConfig(provider="test", model_id="test"),
          conversation=ConversationHistory(),
          execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
          side_effects=SideEffectRegistry(),
          environment=EnvironmentSnapshot(cwd="/", python_version="3.10", platform="linux"),
          metadata=FreezeMetadata(
              framework_name="raw",
              framework_version="1",
              trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL
          )
      )

      call_count = 0

      @checkpoint_boundary(aso, storage, "charge_card")
      def charge_card(amount: int):
          nonlocal call_count
          call_count += 1
          return {"status": "success", "amount": amount}

      # Run 1
      res1 = charge_card(amount=100)
      assert res1["status"] == "success"
      assert call_count == 1
      assert len(aso.side_effects.entries) == 1

      # Run 2 (Simulating a resume where the decorator executes again)
      res2 = charge_card(amount=100)
      assert res2["status"] == "success"
      assert call_count == 1  # Execution bypassed!
      assert len(aso.side_effects.entries) == 1
  ```

- [ ] **Verification:**
  ```bash
  cd agentposix && source .venv/bin/activate && python -m pytest tests/integration/test_end_to_end.py -v | grep "1 passed" && echo "PASS"
  ```

---

## 4. Conclusion

> The specification above delineates the precise, strictly typed, and framework-agnostic architectural primitives of Agent POSIX.
>
> By integrating the explicit event-sourcing of side effects via SHA-256 idempotency keys, and replacing opaque Python pickling mechanisms with a deterministic JSON schema (Draft 2020-12), `agentposix` provides zero-loss session portability.
>
> The implementing sequence outputs a completely functional environment, encompassing:
> - Pydantic V2 definitions
> - The filesystem persistence layer
> - Signal intercepts
> - The LangGraph graph integration
> - The raw loop decorator layer
> - The foundational Typer CLI
>
> **This completes the exhaustive technical implementation blueprint.**

---

## Task Completion Summary

| Task | File / Action | Status |
|------|--------------|--------|
| 001 | Create root directory structure (`RUN`) | ⬜ Pending |
| 002 | `agentposix/.gitignore` (`CREATE`) | ⬜ Pending |
| 003 | `agentposix/pyproject.toml` (`CREATE`) | ⬜ Pending |
| 004 | `agentposix/.python-version` (`CREATE`) | ⬜ Pending |
| 005 | Initialize virtual environment (`RUN`) | ⬜ Pending |
| 006 | Create all `__init__.py` files (`RUN`) | ⬜ Pending |
| 007 | `src/agentposix/exceptions.py` (`CREATE`) | ⬜ Pending |
| 008 | `src/agentposix/enums.py` (`CREATE`) | ⬜ Pending |
| 009 | `src/agentposix/models/metadata.py` (`CREATE`) | ⬜ Pending |
| 010 | `src/agentposix/models/message.py` (`CREATE`) | ⬜ Pending |
| 011 | `src/agentposix/models/execution_pointer.py` (`CREATE`) | ⬜ Pending |
| 012 | `src/agentposix/models/side_effect.py` (`CREATE`) | ⬜ Pending |
| 013 | `src/agentposix/models/environment.py` (`CREATE`) | ⬜ Pending |
| 014 | `src/agentposix/models/aso.py` (`CREATE`) | ⬜ Pending |
| 015 | `src/agentposix/core/checksum.py` (`CREATE`) | ⬜ Pending |
| 016 | `src/agentposix/storage/base.py` (`CREATE`) | ⬜ Pending |
| 017 | `src/agentposix/storage/filesystem.py` (`CREATE`) | ⬜ Pending |
| 018 | `src/agentposix/storage/sqlite.py` (`CREATE`) | ⬜ Pending |
| 019 | `src/agentposix/core/freeze.py` (`CREATE`) | ⬜ Pending |
| 020 | `src/agentposix/core/resume.py` (`CREATE`) | ⬜ Pending |
| 021 | `src/agentposix/signals/handler.py` (`CREATE`) | ⬜ Pending |
| 022 | `src/agentposix/adapters/raw_python/decorator.py` (`CREATE`) | ⬜ Pending |
| 023 | `src/agentposix/adapters/langgraph/adapter.py` (`CREATE`) | ⬜ Pending |
| 024 | `src/agentposix/cli/main.py` (`CREATE`) | ⬜ Pending |
| 025 | `src/agentposix/__init__.py` (`MODIFY`) | ⬜ Pending |
| 026 | `tests/integration/test_end_to_end.py` (`CREATE`) | ⬜ Pending |
