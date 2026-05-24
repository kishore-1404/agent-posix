# Agent POSIX

Agent POSIX is a Python library for serializing, checkpointing, and resuming
agent execution state through a portable Agent State Object (ASO).

The project is for developers building agent runtimes, framework adapters, and
tools that need explicit checkpoint boundaries rather than opaque in-memory
state.

## What It Provides

- A Pydantic v2 ASO schema for portable agent state.
- Freeze and resume lifecycle helpers with checksum validation.
- Filesystem and SQLite storage backends.
- A raw Python checkpoint decorator for idempotent side-effect boundaries.
- A LangGraph checkpoint saver adapter.
- A Click CLI for inspecting, freezing, and resuming ASO checkpoints.
- JSON Schema output for external tooling.

## What It Is Not

- It is not a distributed checkpoint database.
- It is not a complete agent framework.
- It does not automatically make external side effects reversible.
- It does not guarantee compatibility with every private framework checkpoint
  representation.

## Maturity

Agent POSIX is in alpha-oriented production-readiness hardening. The core
prototype is implemented and the current workstream is adding tests,
documentation, quality gates, and release readiness. Use it for evaluation and
integration experiments, not yet as an unstated production dependency.

## Installation

From this package directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[adapters,storage,dev]"
```

Minimal runtime install:

```bash
pip install -e .
```

Optional extras:

- `adapters`: LangGraph and LangChain Core integration dependencies.
- `storage`: SQLite async backend support.
- `dev`: tests, coverage, linting, docs, build, and release tools.

## Quickstart

```python
from agentposix import AgentStateObject, FilesystemBackend, freeze, resume
from agentposix.enums import FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry

storage = FilesystemBackend(".agentposix")

aso = AgentStateObject(
    identity=IdentityBlock(aso_id="aso-1", session_id="session-1"),
    created_at="2026-05-25T00:00:00Z",
    model_config_block=ModelConfig(provider="example", model_id="agent-model"),
    conversation=ConversationHistory(),
    execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
    side_effects=SideEffectRegistry(),
    environment=EnvironmentSnapshot(cwd=".", python_version="3.12", platform="linux"),
    metadata=FreezeMetadata(
        framework_name="raw",
        framework_version="1",
        trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
    ),
)

freeze(aso, storage, summary="safe checkpoint")
restored = resume("session-1", storage)
print(restored.status)
```

## CLI

```bash
agentposix --help
agentposix inspect session-1 --path .agentposix
agentposix resume session-1 --path .agentposix
agentposix freeze --input input.aso.json --path .agentposix --summary "manual checkpoint"
```

The `freeze` CLI command accepts a complete ASO JSON payload and is intended as a
debugging/power-user command, not a friendly ASO authoring wizard.

## Storage Options

- `FilesystemBackend`: simple JSON-file checkpointing for local development,
  tests, and single-process deployments.
- `AsyncSqliteBackend`: local transactional storage for async applications that
  need a single database file.

For durability, concurrency, and recovery details, see
[`docs/concepts/storage-backends.md`](docs/concepts/storage-backends.md).

## Adapter Docs

- Raw Python replay semantics: [`docs/adapters/raw-python.md`](docs/adapters/raw-python.md)
- Adapter extension contract:
  [`docs/adapters/extension-contract.md`](docs/adapters/extension-contract.md)

## Development Checks

Run from this package directory:

```bash
pytest
ruff check src tests
ruff format --check src tests
python -m build --no-isolation
```

The current test suite enforces coverage with `pytest-cov`.
