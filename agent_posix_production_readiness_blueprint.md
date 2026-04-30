# Agent POSIX: Production Readiness Blueprint

> **Purpose:** Convert the current working prototype into a production-grade open-source project that can be adopted, evaluated, and integrated by external users with clear operational expectations.
>
> **Baseline:** The implementation blueprint has been completed. This document covers the hardening work required after prototype completion.

---

## 1. Release Standard

The project is considered production-ready for open-source adoption only when all of the following are true:

- Packaging works in editable and wheel installs on supported Python versions.
- Filesystem and SQLite backends pass unit, integration, and failure-mode tests.
- Freeze/resume semantics are explicitly documented and validated under realistic scenarios.
- The CLI exposes the expected lifecycle operations and is tested as an installed package.
- LangGraph integration is exercised against real checkpoint flows, not just import validation.
- CI enforces linting, tests, packaging, and release checks on every change.
- User documentation is sufficient for installation, first-run usage, adapter integration, storage selection, and troubleshooting.
- Public APIs, compatibility guarantees, and non-goals are documented.

---

## 2. Current Gaps

- Test coverage is minimal.
- The CLI only implements `inspect`.
- The SQLite backend is incomplete relative to the storage contract.
- Filesystem persistence lacks fsync, locking, and corruption-handling safeguards.
- Lifecycle transitions are permissive and not validated by a state machine.
- Pydantic deprecation warnings exist in model fields.
- LangGraph support is only minimally exercised.
- No CI workflow, release process, or contributor-facing developer commands exist yet.

---

## 3. Execution Rules

- Complete tasks in dependency order.
- Mark a task done only after code, tests, docs, and verification are complete.
- If a task reveals a design flaw, add a review note to `CONTEXT.md` before continuing.
- Every behavior change must include tests unless the task is documentation-only.
- Keep public imports rooted at `agentposix`, never `src.agentposix`.

---

## 4. Workstreams

### WORKSTREAM A — Packaging and Compatibility

#### TASK P001 — Normalize package metadata [DONE 2026-05-01]
- **Goal:** Make `pyproject.toml` suitable for distribution.
- **Requirements:**
  - Add `authors`, `keywords`, `classifiers`, `urls`, and explicit optional dependency group purpose.
  - Remove or replace dependencies that are not actually used in runtime.
  - Decide whether CLI stays on Click or moves to a Typer version that is verified to work.
- **Done when:**
  - `python -m build` succeeds.
  - Wheel metadata is valid.
- **Completion notes:**
  - Added distribution metadata, project URLs, and optional dependency group purpose comments.
  - Replaced unused `typer` runtime dependency with `click` because the CLI implementation is Click-based and prior context recorded Typer help-output instability in this environment.
  - Added a package-local `README.md` so builds from the `agentposix/` project root resolve the declared readme correctly.
  - Verified with `./.venv/bin/python -m build --no-isolation` and `./.venv/bin/python -m twine check dist/*`. `--no-isolation` was required because the sandboxed environment blocks package index access for isolated build env bootstrap.

#### TASK P002 — Add setuptools package discovery config [DONE 2026-05-01]
- **Goal:** Ensure wheel builds include the `src/agentposix` package reliably.
- **Requirements:**
  - Add explicit package discovery for the `src` layout.
  - Verify imports from a clean wheel install.
- **Verification:**
  ```bash
  python -m build
  pip install dist/*.whl
  python -c "import agentposix; print(agentposix.__all__)"
  ```
- **Completion notes:**
  - Added explicit setuptools `src`-layout discovery via `[tool.setuptools]` and `[tool.setuptools.packages.find]`.
  - Made `agentposix.ASOLangGraphSaver` a lazy optional export so `import agentposix` does not require LangGraph extras at import time.
  - Added unit tests for the lazy optional export behavior.
  - Verified with `./.venv/bin/python -m build --no-isolation`, `./.venv/bin/python -m pip install --force-reinstall --no-deps dist/agentposix-0.1.0-py3-none-any.whl`, and `./.venv/bin/python -c "import agentposix; print(agentposix.__all__)"`.

#### TASK P003 — Define supported Python matrix [DONE 2026-05-01]
- **Goal:** Set a real compatibility target.
- **Requirements:**
  - Test at least Python `3.10`, `3.11`, and `3.12`.
  - Downgrade or pin dependencies only if matrix failures require it.
- **Done when:** CI passes on every supported version.
- **Completion notes:**
  - Added a GitHub Actions compatibility workflow covering Python `3.10`, `3.11`, and `3.12`.
  - Installed Python `3.11.11` and `3.12.9` locally via `pyenv` to supplement the existing `3.10.9` interpreter.
  - Validated the matrix locally in clean virtualenvs for each version with editable install of `.[adapters,storage,dev]`, `pytest`, `python -m build --no-isolation`, and `python -c "import agentposix; print(agentposix.__all__)"`.
  - No dependency downgrades or pins were required based on the local matrix results.

### WORKSTREAM B — Model and Schema Hardening

#### TASK P010 — Remove Pydantic deprecations
- **Goal:** Eliminate warnings and future breakage.
- **Requirements:**
  - Replace deprecated `Field(..., example=...)` usage with supported schema metadata.
  - Run tests with warnings treated as failures for project code.

#### TASK P011 — Add schema validation tests
- **Goal:** Guarantee ASO serialization stability.
- **Requirements:**
  - Add unit tests for every core model.
  - Cover valid defaults, invalid enum values, bad idempotency keys, and missing required blocks.
- **Verification:**
  ```bash
  pytest tests/unit/test_models -q
  ```

#### TASK P012 — Add ASO schema export
- **Goal:** Make the format consumable by external users.
- **Requirements:**
  - Generate and store a JSON Schema artifact under `spec/`.
  - Add a test ensuring schema generation remains stable.

### WORKSTREAM C — Lifecycle Safety

#### TASK P020 — Introduce explicit state transition validation
- **Goal:** Prevent invalid lifecycle jumps.
- **Requirements:**
  - Define allowed transitions for `ASOStatus`.
  - Raise `StateTransitionError` for illegal transitions.
  - Cover transitions in unit tests.

#### TASK P021 — Harden `freeze()`
- **Goal:** Make checkpoint writes safer.
- **Requirements:**
  - Add transition checks.
  - Clarify checksum-write ordering.
  - Add defensive behavior around incomplete storage writes.
  - Document atomicity guarantees and limits.

#### TASK P022 — Harden `resume()`
- **Goal:** Make restore behavior explicit.
- **Requirements:**
  - Validate checksum failures.
  - Handle missing sessions cleanly.
  - Define behavior for already-resumed or terminal states.

#### TASK P023 — Implement host drift detection
- **Goal:** Use `HostDriftError` for real validation.
- **Requirements:**
  - Compute tracked file checksums.
  - Compare environment snapshot values on resume.
  - Document which drift conditions are fatal vs advisory.

### WORKSTREAM D — Storage Reliability

#### TASK P030 — Complete `AsyncSqliteBackend`
- **Goal:** Bring SQLite to feature parity with the storage contract.
- **Requirements:**
  - Add `list_sessions`, `delete_aso`, and `exists`.
  - Add tests for create, update, delete, and missing session behavior.

#### TASK P031 — Add filesystem durability safeguards
- **Goal:** Improve write reliability.
- **Requirements:**
  - Add parent directory creation checks.
  - Add flush and fsync before replace.
  - Decide on session-level locking strategy.
  - Document single-process vs multi-process guarantees.

#### TASK P032 — Add corruption and recovery tests
- **Goal:** Verify failure behavior.
- **Requirements:**
  - Test partial JSON, invalid checksum, unreadable files, and unexpected payload shape.
  - Ensure failures are deterministic and actionable.

#### TASK P033 — Define backend selection guidance
- **Goal:** Help adopters choose storage correctly.
- **Requirements:**
  - Document when to use filesystem vs SQLite.
  - Document durability, concurrency, and operational tradeoffs.

### WORKSTREAM E — Adapters and Integrations

#### TASK P040 — Harden raw checkpoint decorator
- **Goal:** Make idempotency semantics explicit and reliable.
- **Requirements:**
  - Decide whether positional args are part of the idempotency key.
  - Add handling for non-JSON-serializable results.
  - Document replay assumptions.

#### TASK P041 — Add LangGraph integration tests
- **Goal:** Verify real adapter behavior.
- **Requirements:**
  - Test `put()` and `get_tuple()` against realistic checkpoint payloads.
  - Validate node mapping, channel persistence, and thread/session mapping.

#### TASK P042 — Define adapter extension contract
- **Goal:** Allow future integrations.
- **Requirements:**
  - Document expectations for framework adapters.
  - Specify required extension keys, lifecycle hooks, and compatibility boundaries.

### WORKSTREAM F — CLI and User Experience

#### TASK P050 — Implement `resume` CLI command
- **Goal:** Expose restore behavior to end users.
- **Requirements:**
  - Accept `session_id` and backend path/db options.
  - Print status, timestamps, and checksum result.

#### TASK P051 — Implement `freeze` CLI command
- **Goal:** Support manual checkpoint creation.
- **Requirements:**
  - Decide the CLI input shape for creating or updating ASOs.
  - Document whether this is primarily a debugging command.

#### TASK P052 — Add CLI tests
- **Goal:** Validate the installed console script behavior.
- **Requirements:**
  - Test `--help`, `inspect`, error paths, and backend path options.
  - Run through subprocess or Click runner tests.

### WORKSTREAM G — Testing and Quality Gates

#### TASK P060 — Build unit test suite
- **Goal:** Cover every module with focused tests.
- **Scope:**
  - models
  - checksum
  - freeze/resume
  - storage backends
  - signal handler
  - raw decorator
  - CLI

#### TASK P061 — Build integration test suite
- **Goal:** Cover realistic multi-step flows.
- **Requirements:**
  - freeze -> persist -> resume
  - duplicate side-effect suppression
  - checksum mismatch rejection
  - filesystem and SQLite parity
  - LangGraph checkpoint round-trip

#### TASK P062 — Add coverage threshold
- **Goal:** Enforce minimum quality.
- **Requirements:**
  - Add `pytest-cov` configuration.
  - Start with a threshold that is meaningful, then ratchet upward.
- **Suggested initial gate:** `85%` overall, with higher expectations for core modules.

#### TASK P063 — Add lint and format enforcement
- **Goal:** Keep the codebase consistent.
- **Requirements:**
  - Configure Ruff for linting and formatting rules.
  - Add commands to run checks locally and in CI.

### WORKSTREAM H — Documentation and OSS Readiness

#### TASK P070 — Rewrite README for adopters
- **Goal:** Make the project understandable from the outside.
- **Requirements:**
  - Problem statement
  - what Agent POSIX is and is not
  - install instructions
  - quickstart
  - storage options
  - current maturity level

#### TASK P071 — Add architecture docs
- **Goal:** Explain the system beyond code.
- **Requirements:**
  - ASO structure
  - lifecycle protocol
  - backend model
  - adapter model
  - idempotency semantics

#### TASK P072 — Add API reference docs
- **Goal:** Support external integration.
- **Requirements:**
  - Public API docs for root exports
  - CLI docs
  - backend docs
  - adapter docs

#### TASK P073 — Add troubleshooting guide
- **Goal:** Reduce adopter friction.
- **Requirements:**
  - checksum mismatch
  - storage path issues
  - packaging/install issues
  - Python version issues
  - LangGraph integration pitfalls

#### TASK P074 — Add OSS governance files
- **Goal:** Make the repo publishable.
- **Requirements:**
  - `LICENSE`
  - `CONTRIBUTING.md`
  - `CODE_OF_CONDUCT.md`
  - issue and PR templates
  - security contact guidance

### WORKSTREAM I — CI/CD and Release Management

#### TASK P080 — Add CI workflow
- **Goal:** Enforce quality automatically.
- **Requirements:**
  - Run lint, tests, coverage, and build.
  - Test supported Python versions.
  - Fail on warnings from project code once deprecations are cleared.

#### TASK P081 — Add release workflow
- **Goal:** Make tagged releases reproducible.
- **Requirements:**
  - Build sdist and wheel.
  - Validate artifacts.
  - Optionally publish on tag after manual approval.

#### TASK P082 — Add dependency management policy
- **Goal:** Keep the project maintainable.
- **Requirements:**
  - Decide pinning strategy for runtime vs dev dependencies.
  - Add dependency review/update guidance.

### WORKSTREAM J — Product Acceptance

#### TASK P090 — Define alpha release criteria
- **Goal:** Establish a truthful first public milestone.
- **Suggested criteria:**
  - all unit and integration tests green
  - CI enabled
  - README and docs usable
  - both storage backends functional
  - CLI commands implemented
  - known limitations documented

#### TASK P091 — Run smoke tests from a clean environment
- **Goal:** Validate actual install and usage.
- **Requirements:**
  - fresh venv
  - wheel install
  - quickstart execution
  - CLI inspect/resume/freeze checks

#### TASK P092 — Publish v0.1.0-alpha checklist
- **Goal:** Prevent accidental overclaiming.
- **Requirements:**
  - explicitly list supported scenarios
  - explicitly list unsupported scenarios
  - include migration and compatibility notes

---

## 5. Recommended Execution Order

1. `P001`–`P003`
2. `P010`–`P012`
3. `P020`–`P023`
4. `P030`–`P033`
5. `P040`–`P042`
6. `P050`–`P052`
7. `P060`–`P063`
8. `P070`–`P074`
9. `P080`–`P082`
10. `P090`–`P092`

---

## 6. Definition of Done

This production-readiness effort is complete only when:

- All tasks above are implemented or explicitly deferred with documented rationale.
- `pytest`, coverage, lint, and build checks pass in CI.
- The package works as an installed dependency, not just from the repository root.
- Documentation is sufficient for a new external user to install, run, and evaluate the project.
- The project can be honestly labeled as an alpha open-source release with known limits, rather than a prototype.
