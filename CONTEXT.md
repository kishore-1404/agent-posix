# Project Context

## Current Objective
Execute the implementation blueprint in `agent_posix_implementation_blueprint.md` sequentially and keep the repository resumable between agents.

## Completed
- TASK 001: Created the root project directory structure under `agentposix/`.
- Added `.gitkeep` placeholders so empty scaffold directories are preserved in Git.
- TASK 002: Added `agentposix/.gitignore` with Python, virtualenv, test, and artifact ignores.

## In Progress
- TASK 003: Create `pyproject.toml`.

## Open Issues
- TASK 005 may require dependency installation and could be blocked by network or sandbox limits.

## Decisions
- `CONTEXT.md` is the canonical handoff file for ongoing work.
- A task is marked done only after implementation and basic validation complete.

## Next Steps
1. Add and validate `agentposix/pyproject.toml`.
2. Add `.python-version` for Python version pinning.
3. Attempt TASK 005 and record any blockers if installation cannot complete.
