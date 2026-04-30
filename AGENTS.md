# Repository Guidelines

## Project Structure & Module Organization
This repository currently contains the planning document [agent_posix_implementation_blueprint.md](/home/kishore/Projects/Agent_Posix/agent-posix/agent_posix_implementation_blueprint.md), which defines the intended Python package layout for `agentposix`. Contributors should treat that blueprint as the source of truth when creating files and directories.

Planned structure:
- `agentposix/src/agentposix/`: package source
- `agentposix/tests/unit/` and `agentposix/tests/integration/`: test suites
- `agentposix/docs/`: concepts, adapters, and API reference
- `agentposix/spec/`: schema and protocol artifacts
- `agentposix/.github/workflows/`: CI automation

## Build, Test, and Development Commands
Use the commands specified in the blueprint once the package scaffold exists:

```bash
mkdir -p agentposix/src/agentposix/{models,storage,core,signals,cli}
cd agentposix
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[adapters,storage,dev]"
pytest
```

- `python3 -m venv .venv`: create the local virtual environment.
- `pip install -e ".[adapters,storage,dev]"`: install runtime and contributor dependencies.
- `pytest`: run unit and integration tests.

## Coding Style & Naming Conventions
Target Python `>=3.10`. Follow 4-space indentation, explicit type hints, and small, focused modules. Use `snake_case` for files, functions, and variables; `PascalCase` for Pydantic models and other classes; and `UPPER_SNAKE_CASE` for constants.

The blueprint specifies `ruff` for linting and formatting checks. Keep JSON artifacts deterministic and serialize ASO data with Pydantic v2 JSON-safe output.

## Testing Guidelines
Write tests with `pytest` and `pytest-asyncio`. Place fast, isolated cases under `tests/unit/` and cross-component behavior under `tests/integration/`. Prefer names such as `test_filesystem_backend.py` and `test_checkpoint_boundary_skips_completed_side_effects`.

Run `pytest` before opening a PR. Add coverage for every storage backend, schema change, and checkpointing edge case touched by your change.

## Context & Task Tracking
Maintain a root-level `CONTEXT.md` as the handoff document for any agent or contributor continuing the project. Record the current objective, completed work, open issues, decisions made, and the next concrete steps.

Only mark a task as done when implementation, validation, and any required documentation updates are fully complete. If work is partial, blocked, or unverified, do not mark it done; instead add a short review note in `CONTEXT.md` describing what remains, risks, and how the next agent should continue.

## Commit & Pull Request Guidelines
Current Git history is minimal and uses a short subject line style (`first commit`). Keep commit messages concise and descriptive. Prefer imperative subjects such as `add filesystem backend skeleton` or `implement TASK 003 pyproject metadata`, and reference blueprint task IDs when the change maps directly to the plan.

Pull requests should include a short summary, affected blueprint task numbers, test evidence, and any schema or CLI output changes. Include examples or terminal output when behavior changes are user-visible.
