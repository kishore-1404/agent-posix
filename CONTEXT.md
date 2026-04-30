# Project Context

## Current Objective
Turn the completed prototype into an adoptable open-source release using a dedicated production-readiness blueprint and keep the repository resumable between agents.

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
- TASK 026: Added and passed the end-to-end idempotency integration test.
- Created `agent_posix_production_readiness_blueprint.md` to define the post-prototype hardening plan for OSS/production adoption.
- TASK P001: Normalized `agentposix/pyproject.toml` for distribution by adding authors, keywords, classifiers, project URLs, optional dependency purpose comments, and replacing the unused `typer` runtime dependency with the actual `click` dependency used by the CLI.
- Added `agentposix/README.md` so builds run from the package project root have a valid local readme target.
- Validated packaging metadata with `./.venv/bin/python -m build --no-isolation` and `./.venv/bin/python -m twine check dist/*`.

## In Progress
- None.

## Open Issues
- `python3 -m venv` and activation emit `pyenv: cannot rehash ... shims isn't writable`, but environment creation and package installation still succeed.
- `python -m build` without `--no-isolation` still cannot run in this environment unless network access is available, because the isolated build bootstrap tries to resolve build requirements from package indexes.

## Decisions
- `CONTEXT.md` is the canonical handoff file for ongoing work.
- A task is marked done only after implementation and basic validation complete.
- Internal package imports use `agentposix...`, not `src.agentposix...`, so editable installs and console scripts work correctly.
- The CLI uses a Click command object because the pinned Typer version crashes on help output in this environment.
- Runtime dependencies must match actual imports; the package now declares `click` directly and keeps LangGraph and SQLite behind optional extras.
- The package build root is `agentposix/`, so package metadata must reference files that exist inside that directory rather than only at the repository root.

## Next Steps
1. Execute `P002` by adding explicit setuptools `src`-layout package discovery and verifying imports from a clean wheel install.
2. Execute `P003` by defining and later enforcing the supported Python matrix in CI.
3. Continue with model and lifecycle hardening after packaging compatibility is stable.
