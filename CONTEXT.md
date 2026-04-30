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
- TASK 018: Added the async SQLite backend with WAL initialization and JSON payload storage.
- TASK 019: Added the freeze protocol to checkpoint ASOs and persist them atomically.
- TASK 020: Added the resume protocol with checksum verification and RESUMING transition.
- TASK 021: Added `FreezeSignalHandler` for `SIGINT` and `SIGTERM` checkpointing.
- TASK 022: Added `checkpoint_boundary` for idempotent raw Python side-effect checkpoints.
- TASK 023: Added `ASOLangGraphSaver` to map LangGraph checkpoints into ASO storage.
- TASK 024: Added a working CLI entrypoint with `inspect` and corrected package imports so the installed console script runs.
- TASK 025: Added the root package public API in `src/agentposix/__init__.py`.

## In Progress
- TASK 026: Create integration test.

## Open Issues
- `python3 -m venv` and activation emit `pyenv: cannot rehash ... shims isn't writable`, but environment creation and package installation still succeed.

## Decisions
- `CONTEXT.md` is the canonical handoff file for ongoing work.
- A task is marked done only after implementation and basic validation complete.
- Internal package imports use `agentposix...`, not `src.agentposix...`, so editable installs and console scripts work correctly.
- The CLI uses a Click command object because the pinned Typer version crashes on help output in this environment.

## Next Steps
1. Add the integration test.
2. Run the end-to-end verification flow.
3. Review any remaining compatibility gaps.
