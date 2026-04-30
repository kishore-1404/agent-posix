# Project Context

## Current Objective
Execute the implementation blueprint in `agent_posix_implementation_blueprint.md` sequentially and keep the repository resumable between agents.

## Completed
- TASK 001: Created the root project directory structure under `agentposix/`.
- Added `.gitkeep` placeholders so empty scaffold directories are preserved in Git.
- TASK 002: Added `agentposix/.gitignore` with Python, virtualenv, test, and artifact ignores.
- TASK 003: Added `agentposix/pyproject.toml` with packaging metadata, extras, CLI entry point, and pytest config.
- TASK 004: Added `agentposix/.python-version` pinned to Python 3.10.0.
- TASK 005: Created `agentposix/.venv` and installed the package with `adapters`, `storage`, and `dev` extras.
- TASK 006: Added package and test `__init__.py` files across the source and test tree.
- TASK 007: Added the shared Agent POSIX exception hierarchy in `src/agentposix/exceptions.py`.
- TASK 008: Added strict string enums for lifecycle status, freeze triggers, paradigms, and safe boundaries.
- TASK 009: Added `ModelConfig`, `FreezeMetadata`, and `IdentityBlock` in `models/metadata.py`.
- TASK 010: Added message, tool-call, conversation, and tool-definition schemas in `models/message.py`.
- TASK 011: Added `ExecutionPointer` with topological and temporal state tracking.
- TASK 012: Added side-effect entry validation and registry models in `models/side_effect.py`.
- TASK 013: Added environment snapshot and sub-agent reference models in `models/environment.py`.
- TASK 014: Added the root `AgentStateObject` schema in `models/aso.py`.
- TASK 015: Added deterministic checksum computation and verification in `core/checksum.py`.
- TASK 016: Added the `StorageBackend` abstract base class in `storage/base.py`.
- TASK 017: Added `FilesystemBackend` with atomic replace-on-write persistence.

## In Progress
- TASK 018: Create `SqliteBackend`.

## Open Issues
- `python3 -m venv` and activation emit `pyenv: cannot rehash ... shims isn't writable`, but environment creation and package installation still succeed.

## Decisions
- `CONTEXT.md` is the canonical handoff file for ongoing work.
- A task is marked done only after implementation and basic validation complete.

## Next Steps
1. Add the async SQLite backend.
2. Add lifecycle freeze/resume protocols.
3. Add tests as models and storage backends take shape.
