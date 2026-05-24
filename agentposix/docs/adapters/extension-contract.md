# Adapter Extension Contract

Agent POSIX adapters connect framework-specific checkpoint or execution APIs to
the framework-neutral Agent State Object (ASO). Adapters may preserve framework
details in `extensions`, but public ASO fields must remain portable across
frameworks.

## Responsibilities

An adapter must:

- Map the framework session or thread identifier to `identity.session_id`.
- Assign a stable checkpoint identifier to `identity.aso_id`.
- Populate `execution_pointer.paradigm` with the closest supported paradigm.
- Preserve enough framework-specific state to resume through the original
  framework API.
- Use a storage backend through the `StorageBackend` contract rather than writing
  files or databases directly.
- Avoid importing optional framework dependencies from `agentposix.__init__` at
  base package import time.

An adapter should:

- Keep framework data under namespaced `extensions` keys.
- Store JSON-safe extension values whenever practical.
- Treat the ASO passed to storage as immutable after write.
- Prefer deterministic ids and ordering for replayable checkpoint data.
- Add tests that use the real framework types when the dependency is available.

## Extension Keys

Adapter-specific keys must be prefixed with the framework name:

- `langgraph_checkpoint`
- `langgraph_metadata`
- `langgraph_new_versions`
- `langgraph_checkpoint_ns`
- `langgraph_parent_checkpoint_id`
- `langgraph_pending_writes`

New adapters should follow the same pattern, for example:

- `myframework_checkpoint`
- `myframework_metadata`
- `myframework_parent_checkpoint_id`

Do not place framework-specific payloads in portable ASO fields such as
`conversation`, `side_effects`, or `environment` unless they match the documented
ASO schema semantics.

## Lifecycle Hooks

Adapters that create checkpoints should align framework operations with Agent
POSIX lifecycle helpers:

- Use `freeze()` when the adapter owns an existing ASO lifecycle transition.
- Use a storage backend directly only when translating an external checkpoint
  object into a newly constructed ASO.
- Use `resume()` or equivalent checksum verification before trusting persisted
  ASO data for execution.
- Preserve framework parent/child checkpoint relationships when the framework
  exposes them.

Adapters must not silently skip checksum validation when resuming from persisted
ASO data. If the framework API requires a checkpoint tuple rather than an ASO,
the adapter should still read through the backend and reconstruct only after the
stored payload validates.

## Compatibility Boundaries

Stable adapter behavior:

- Public imports remain rooted at `agentposix`.
- Optional dependencies remain optional unless the adapter is imported or used.
- Framework-specific payloads are stored under namespaced extension keys.
- Missing sessions return the framework-appropriate "not found" result, such as
  `None` for LangGraph `get_tuple()`.

Non-goals:

- Agent POSIX does not guarantee compatibility with every internal framework
  checkpoint format.
- Agent POSIX does not provide distributed locking for framework adapters.
- Agent POSIX does not automatically migrate opaque framework extension payloads
  across incompatible upstream framework versions.

When an upstream framework changes checkpoint shape, update the adapter tests
with a realistic payload from that framework before changing production mapping
logic.

## Test Requirements

Every adapter should include tests for:

- Session or thread id mapping.
- Checkpoint id mapping.
- Framework state persistence under namespaced extension keys.
- Round-trip reconstruction through the framework-facing API.
- Missing-session behavior.
- Optional dependency import behavior when the adapter is exposed at the package
  root.

Integration tests should cover at least one realistic checkpoint flow using the
real framework classes or typed payloads, not only import validation.
