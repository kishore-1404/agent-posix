# Alpha Release Criteria

To transition from prototype to an alpha open-source release (`v0.1.0-alpha`), the following criteria must be met and verified:

---

## 1. Code Quality & Test Coverage
- **Unit and Integration Test Success:** The full test suite (`pytest`) must pass with zero failures across all supported Python versions (`3.10`, `3.11`, `3.12`).
- **Pydantic Warning Gates:** Zero Pydantic deprecation warnings. Any Pydantic warnings must trigger test failures.
- **Coverage Gate:** Statement and branch coverage must remain at or above **90%** for all core packages, validated automatically on local runs and CI.
- **Lint and Style Compliance:** All codebase files must pass `ruff check` and `ruff format` checks without any formatting violations.

---

## 2. Storage Backend and Adapter Reliability
- **Filesystem Backend Durability:** Verify that file persistence uses atomic replace-on-write writes, correct file and directory `fsync` flushing, and session-level locks.
- **SQLite Parity:** Verify that `AsyncSqliteBackend` successfully implements all CRUD operations (`write_aso`, `read_aso`, `exists`, `list_sessions`, `delete_aso`) and handles edge cases such as missing sessions and corrupted payload parsing.
- **LangGraph Checkpoint saver:** Verify that the lazy-loaded `ASOLangGraphSaver` successfully round-trips realistic checkpoint tuples (storing channel versions, thread/session pointers, and pending writes inNamespaced extensions).

---

## 3. CLI Functionality
- CLI options `--help` and command `--help` return correct instructions.
- `agentposix inspect <session_id>` successfully prints session status, node ID, and side-effects.
- `agentposix resume <session_id>` correctly triggers checksum and host drift checks, performs transition validation, and prints the result.
- `agentposix freeze --input <aso_json>` parses, validates, transitions, and persists the manually patched state.

---

## 4. Documentation
- Adopter-oriented `README.md` at root and package levels.
- Concepts docs covering `architecture.md`, `storage-backends.md`, and `dependency-policy.md`.
- Adapter docs covering raw decorator usage and adapter extension contract guidelines.
- Python API and CLI Command Reference documentation.
- Troubleshooting guide for common errors.

---

## 5. Packaging & CI/CD
- Editable and Wheel builds compile without error.
- Twine validates built wheel metadata successfully.
- GitHub Actions compatibility workflows are configured and passing.
