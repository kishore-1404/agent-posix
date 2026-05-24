# Contributing to Agent POSIX

Thank you for your interest in contributing to Agent POSIX! We welcome bug reports, feature proposals, documentation improvements, and pull requests.

Please read through these guidelines to get started.

---

## Development Environment Setup

We support Python **3.10**, **3.11**, and **3.12**.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kishore-1404/agent-posix.git
   cd agent-posix
   ```

2. **Set up a virtual environment (using the package root `agentposix/`):**
   ```bash
   cd agentposix
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the package in editable mode with development dependencies:**
   ```bash
   pip install -e ".[adapters,storage,dev]"
   ```

---

## Code Quality Gates

Before opening a pull request, please ensure that your code satisfies all quality gates.

### 1. Run the Test Suite
We use `pytest` for unit and integration tests, with strict warning-to-error gates for Pydantic deprecation warnings.
```bash
pytest
```
*Note: A 90% branch and statement coverage threshold is enforced by default configuration.*

### 2. Linting and Formatting
We use `ruff` to enforce code style. Run the following checks locally:
```bash
ruff check src tests
ruff format --check src tests
```

To automatically format the code and apply safe autofixes:
```bash
ruff format src tests
ruff check --fix src tests
```

---

## Context & Task Tracking

We maintain a root-level [CONTEXT.md](file:///home/kishore/Projects/Agent_Posix/agent-posix/CONTEXT.md) file to coordinate work across sessions and contributors.
- When starting a task, mark it as in-progress or describe it in `CONTEXT.md`.
- When a task is complete (including implementation, tests, and documentation), mark it done.
- If you leave work in a partial, blocked, or unverified state, do not mark it done; instead, add a short review note in `CONTEXT.md` describing what remains, potential risks, and next steps for the next contributor.

---

## Test Development Guidelines

- Put fast, isolated tests under `tests/unit/`.
- Put multi-component, end-to-end flow tests under `tests/integration/`.
- Name files following the `test_<module_name>.py` pattern.
- If you modify or add storage backend or adapter behaviors, make sure to add corresponding unit coverage and verify against the entire test matrix.

---

## Commit & Pull Request Guidelines

- Use short, imperative commit messages (e.g., `add SQLite backend exists method` or `implement CLI resume error path`).
- Reference blueprint or issue task IDs in commits when applicable.
- In your PR, include:
  - A summary of the changes.
  - Affected task numbers from the blueprints.
  - Verification results (test outputs, smoke test results, CLI commands output).
  - Schema change details if any.
