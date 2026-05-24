# Architecture

Agent POSIX is organized around one portable state document, the Agent State
Object (ASO), and a small set of lifecycle operations that validate and persist
that document.

## Agent State Object

The ASO is the framework-neutral checkpoint payload. It contains:

- `identity`: stable ASO id, session id, and optional parent session id.
- `status`: lifecycle state such as `RUNNING`, `CHECKPOINTED`, or `RESUMING`.
- `model_config_block`: model/provider configuration needed to understand the
  execution context.
- `conversation`: portable conversation history and tool call structures.
- `execution_pointer`: current graph node, pending nodes, loop counters, and
  safe-boundary metadata.
- `side_effects`: idempotency records for external actions.
- `environment`: host snapshot data used for drift detection.
- `metadata`: framework name/version, Agent POSIX version, and freeze trigger.
- `extensions`: namespaced framework-specific payloads.
- `checksum`: deterministic integrity checksum over the ASO excluding the
  checksum field itself.

The public JSON Schema artifact is stored at
`spec/agent_state_object.schema.json`.

## Lifecycle Protocol

Agent POSIX lifecycle helpers enforce explicit state transitions:

- `freeze(aso, storage, summary="")` prepares a checkpoint copy, captures the
  current environment snapshot, transitions to `CHECKPOINTED`, computes the final
  checksum, writes through the storage backend, and updates the caller's ASO only
  after storage succeeds.
- `resume(session_id, storage)` checks existence, reads the ASO, verifies the
  checksum, validates host drift, transitions to `RESUMING`, and records a
  resume timestamp.

Invalid lifecycle jumps raise `StateTransitionError`. Checksum mismatches raise
`ChecksumMismatchError`. Fatal host drift raises `HostDriftError`.

## Backend Model

Storage backends implement the `StorageBackend` contract:

- `write_aso(aso)`
- `read_aso(session_id)`
- `list_sessions()`
- `delete_aso(session_id)`
- `exists(session_id)`

Backends should treat incoming ASOs as immutable input and perform
persistence-only checksum fixes on local copies. Read failures should be stable
and actionable. The filesystem backend stores one JSON file per session; the
SQLite backend stores JSON payloads in a checkpoint table keyed by session id.

See `storage-backends.md` for operational tradeoffs.

## Adapter Model

Adapters translate framework-specific checkpoint APIs into ASOs.

The raw Python adapter wraps functions with `checkpoint_boundary`, records
side-effect completion, and prevents duplicate execution for the same
session/tool/argument payload.

The LangGraph adapter implements a checkpoint saver that maps LangGraph thread
ids to ASO session ids and stores framework-specific checkpoint details under
`extensions["langgraph_*"]` keys. This keeps core ASO fields portable while
allowing `get_tuple()` to reconstruct LangGraph checkpoint tuples.

Future adapters should follow `docs/adapters/extension-contract.md`.

## Idempotency Semantics

Agent POSIX does not make external systems transactional. It records completed
side effects and supplies deterministic idempotency keys so callers can avoid
re-executing known completed boundaries.

For the raw Python decorator:

- The key includes session id, tool name, positional arguments, and keyword
  arguments.
- JSON-serializable results are replayed from the stored side-effect entry.
- Non-JSON results are recorded with a `repr()` summary; replay raises
  `SideEffectReplayError` instead of executing the side effect again.

Applications that call external APIs should pass an idempotency key to those APIs
when the API supports it. Agent POSIX can prevent duplicate local execution after
a recorded checkpoint, but it cannot reconcile a process crash that happens
after an external side effect succeeds and before the checkpoint is persisted.
