# Python API Reference

This page describes the primary classes, models, and helper functions exposed by the public `agentposix` API.

---

## Core Lifecycle Functions

### `freeze`

```python
def freeze(
    aso: AgentStateObject,
    storage: StorageBackend,
    summary: str = ""
) -> AgentStateObject:
```

Executes the Agent POSIX Freeze Protocol.
- **Parameters:**
  - `aso`: The active `AgentStateObject` to freeze.
  - `storage`: A storage backend instance (implementing `StorageBackend`) used to persist the state.
  - `summary`: An optional human-readable summary string describing the checkpoint's context or trigger.
- **Behavior:**
  - Performs a deep copy of the `AgentStateObject` to prepare the serialization payload defensively, ensuring that a storage failure does not corrupt or leave the in-memory caller state half-transitioned.
  - Transition of lifecycle state to `ASOStatus.CHECKPOINTED` is validated against the allowed transition rules.
  - Populates the `frozen_at` ISO 8601 timestamp and any supplied `human_summary`.
  - Captures the environment snapshot and computes the deterministic checksum on the copy.
  - Invokes `storage.write_aso(persisted_aso)`.
  - If storage succeeds, updates the caller's live `aso` instance in-place with the computed checksum, status, environment, and timestamps, and returns the modified ASO.
- **Errors raised:**
  - `StateTransitionError`: Raised if the current ASO status is not in a state that allows freezing (e.g. terminal states like `COMPLETED` or `FAILED`).

---

### `resume`

```python
def resume(
    session_id: str,
    storage: StorageBackend
) -> AgentStateObject:
```

Executes the Agent POSIX Resume Protocol.
- **Parameters:**
  - `session_id`: The unique string identifying the agent session to restore.
  - `storage`: The storage backend to read from.
- **Returns:**
  - A restored and validated `AgentStateObject` with status set to `ASOStatus.RESUMING`.
- **Behavior:**
  - Checks if the session exists in the backend.
  - Retrieves the serialized payload.
  - Validates payload integrity by verifying the computed checksum matches the stored checksum field.
  - Validates the environment snapshot against the active runtime host (e.g. checking Python version, directory, platform, and tracked files). Fatal drift raises an error; advisory drift is recorded.
  - Transitions lifecycle state to `ASOStatus.RESUMING` and writes a `resumed_at` ISO 8601 timestamp.
  - Saves any advisory drift messages into `aso.extensions["resume_advisories"]`.
- **Errors raised:**
  - `FileNotFoundError`: If no checkpoint is found for the given `session_id`.
  - `InvalidASOError`: If the retrieved checkpoint is malformed or invalid JSON.
  - `ChecksumMismatchError`: If the checksum verification fails (indicating storage corruption or tampering).
  - `HostDriftError`: If fatal host differences are detected (e.g., Python major/minor version change, host OS change, or tracked file modifications).
  - `StateTransitionError`: If the session has already been resumed or is in a terminal state that doesn't permit resumption.

---

## Core Models

### `AgentStateObject`

The root schema representing the state of an agent. Extends `pydantic.BaseModel`.

- **Fields:**
  - `identity`: `IdentityBlock` containing `aso_id` and `session_id`.
  - `status`: `ASOStatus` representing the current lifecycle step (`IDLE`, `RUNNING`, `CHECKPOINTED`, `RESUMING`, `COMPLETED`, `FAILED`).
  - `created_at`: ISO 8601 creation timestamp.
  - `frozen_at`: ISO 8601 freeze timestamp (nullable).
  - `resumed_at`: ISO 8601 resume timestamp (nullable).
  - `human_summary`: A short description of the state snapshot (nullable).
  - `checksum`: SHA-256 integrity checksum (nullable).
  - `model_config_block`: `ModelConfig` containing LLM provider and model settings.
  - `conversation`: `ConversationHistory` holding message history, tool calls, and tool definitions.
  - `execution_pointer`: `ExecutionPointer` documenting current task/step pointers.
  - `side_effects`: `SideEffectRegistry` listing recorded side-effects for replay.
  - `environment`: `EnvironmentSnapshot` listing platform and tracked file states.
  - `metadata`: `FreezeMetadata` listing library version, framework, and trigger reason.
  - `extensions`: A dictionary of custom namespaced extra data (`dict[str, Any]`).

---

## Storage Backends

### `FilesystemBackend`

```python
class FilesystemBackend(StorageBackend):
    def __init__(self, base_dir: str = ".agentposix/checkpoints")
```

A synchronous storage backend that serializes ASOs directly to files.
- **Reliability features:**
  - Recreates parent directory paths dynamically.
  - Uses an atomic replace-on-write pattern: writes to a temporary file in the same directory, calls `flush()` and `os.fsync()`, then executes `os.replace()` to avoid corrupting existing files on half-writes.
  - Performs an `fsync()` on the parent directory after replacement to ensure directory entry durability.
  - Applies a session-level in-process lock to prevent concurrent writers from overlapping on the same session ID.
- **Methods:**
  - `write_aso(aso)`: serializes ASO to file.
  - `read_aso(session_id)`: deserializes ASO from file.
  - `list_sessions()`: returns list of session IDs sorted alphabetically.
  - `delete_aso(session_id)`: deletes the checkpoint file.
  - `exists(session_id)`: checks if the checkpoint file exists.

### `AsyncSqliteBackend`

```python
class AsyncSqliteBackend:
    def __init__(self, db_path: str = ".agentposix.db")
```

An asynchronous storage backend using `aiosqlite` and SQLite WAL (Write-Ahead Logging) mode.
- **Methods:**
  - `async write_aso(aso)`: writes/updates the ASO JSON payload in the SQLite db.
  - `async read_aso(session_id)`: fetches and parses the JSON payload.
  - `async list_sessions()`: returns alphabetically sorted session IDs.
  - `async delete_aso(session_id)`: deletes the checkpoint record.
  - `async exists(session_id)`: checks if a record exists for the session ID.

---

## Adapters

### `checkpoint_boundary`

```python
def checkpoint_boundary(
    session_id: str,
    storage: StorageBackend,
    trigger_reason: FreezeTriggerReasonEnum = FreezeTriggerReasonEnum.EXPLICIT_CALL,
    framework_name: str = "raw"
):
```

A Python decorator used to wrap side-effect-heavy functions or tool executions, automatically registering results and skipping re-execution on resumes.
- **Parameters:**
  - `session_id`: Session ID to associate checkpoint state.
  - `storage`: The storage backend to fetch from/write to.
  - `trigger_reason`: Metadata field for why the checkpoint was made.
  - `framework_name`: Identifier for the adapter wrapper.
- **Idempotency rules:**
  - Generates a unique key using both positional and keyword arguments.
  - Replays successful JSON-serializable results on resumes.
  - Raises `SideEffectReplayError` for non-JSON-serializable results to prevent incorrect mock returns.

### `ASOLangGraphSaver` (Optional Extra)

```python
from agentposix.adapters.langgraph.adapter import ASOLangGraphSaver
```

An adapter subclassing LangGraph's `BaseCheckpointSaver`.
- **Usage:**
  - Placed behind lazy imports to avoid forcing users to install LangGraph if they only need the raw library.
  - Maps LangGraph's complex version numbers, channel values, metadata, and pending writes into `AgentStateObject` extension fields (`extensions["langgraph_*"]`).
  - Supports `put()`, `get_tuple()`, and namespace queries.
