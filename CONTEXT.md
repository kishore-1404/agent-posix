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

## In Progress
- TASK 006: Create package `__init__.py` files.

## Open Issues
- `python3 -m venv` and activation emit `pyenv: cannot rehash ... shims isn't writable`, but environment creation and package installation still succeed.

## Decisions
- `CONTEXT.md` is the canonical handoff file for ongoing work.
- A task is marked done only after implementation and basic validation complete.

## Next Steps
1. Create package and test `__init__.py` files.
2. Start core model scaffolding from TASK 007 onward.
3. Add tests as models and storage backends take shape.
