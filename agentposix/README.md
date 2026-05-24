# Agent POSIX

Agent POSIX provides a portable Agent State Object (ASO) format, checkpoint lifecycle helpers, and storage backends for resumable agent execution on POSIX systems.

This package is currently in production-readiness hardening. See the repository root documentation for the broader project plan and current status.

Storage backend selection guidance is available in
[`docs/concepts/storage-backends.md`](docs/concepts/storage-backends.md).
Raw Python adapter replay semantics are documented in
[`docs/adapters/raw-python.md`](docs/adapters/raw-python.md).
Adapter extension requirements are documented in
[`docs/adapters/extension-contract.md`](docs/adapters/extension-contract.md).

## Development Checks

Run the local quality gates from this package directory:

```bash
pytest
ruff check src tests
ruff format --check src tests
```
