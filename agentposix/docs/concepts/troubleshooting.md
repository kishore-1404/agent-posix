# Troubleshooting Guide

This guide helps adopters and developers diagnose and resolve common issues encountered while using or integrating Agent POSIX.

---

## Checksum Mismatches

### Problem
When attempting to resume an agent session, you encounter a `ChecksumMismatchError`:

```text
ChecksumMismatchError: ASO checksum verification failed for session <session_id>
```

### Cause
The SHA-256 integrity checksum computed during `freeze()` does not match the checksum computed when `resume()` loads the payload. This indicates that the serialized ASO payload has been modified or corrupted.

### Resolution
1. **Accidental Manual Edits:** If you edited the ASO JSON file manually, the checksum became invalid. If you must patch the ASO manually, use the `agentposix freeze` CLI command, which takes a JSON payload, transition-validates it, updates the checksum field properly, and writes it back out.
2. **Transfer/Encoding Issues:** If the ASO was sent over a network, ensure that no character encoding conversions (e.g., CRLF/LF line-ending translations) corrupted the JSON string. Checksums are computed on the raw content representation.
3. **Concurrent Modifications:** Multiple writers modifying the same checkpoint without coordination. Make sure to use session locks or separate session IDs to avoid overlapping writes.

---

## Storage Path and Permission Issues

### Problem
Storage write or read operations fail with `PermissionError` or `FileNotFoundError`:

```text
PermissionError: [Errno 13] Permission denied: '.agentposix/checkpoints'
```

### Cause
The application process lacks read or write access to the configured storage directory or SQLite database file.

### Resolution
1. **Directories / File Permissions:** Ensure that the process has write permissions to the base directory (default is `.agentposix/` for the filesystem backend, or `./` for the default SQLite database path `.agentposix.db`).
2. **SQLite WAL Lockout:** The SQLite backend initializes with WAL (Write-Ahead Logging) mode enabled for high concurrency. If the database file is placed on a network file system (NFS/SMB) that does not support POSIX locks, WAL initialization will fail. Ensure that the database file is stored on a local filesystem.

---

## Packaging and Optional Extra Imports

### Problem
You try to import `ASOLangGraphSaver` or use `AsyncSqliteBackend` and receive a `ModuleNotFoundError` or `ImportError`:

```text
ImportError: ASOLangGraphSaver requires the optional 'adapters' dependencies.
Install agentposix with the 'adapters' extra to enable LangGraph integration.
```

### Cause
Agent POSIX is designed to have a small footprint. External dependencies like `langgraph` or `aiosqlite` are declared as optional dependency groups ("extras") in `pyproject.toml`.

### Resolution
Ensure that you install the package with the appropriate extras:
- For LangGraph support: `pip install agentposix[adapters]`
- For SQLite storage support: `pip install agentposix[storage]`
- To install all optional extras: `pip install agentposix[adapters,storage]`

---

## Python Version and Environment Mismatches

### Problem
On resuming, the system raises a `HostDriftError` indicating a Python environment mismatch:

```text
HostDriftError: Fatal host drift detected: python_version changed from 3.12.9 to 3.10.9
```

### Cause
By default, the Agent POSIX Resume Protocol captures runtime parameters (Python major/minor version, platform, `cwd`, and tracked file checksums). Resuming the state on an incompatible host environment or different directory throws a fatal error to prevent undefined behavior.

### Resolution
1. **Fatal vs Advisory Drift:**
   - **Fatal (raises `HostDriftError`):** `cwd`, `python_version` (major/minor), `platform` (OS/Arch), and modifications to files listed in the tracked file list.
   - **Advisory (logged in `extensions["resume_advisories"]`):** environment variables, git commit hash.
2. **Bypassing / Adapting:** If you are migrating the agent to a new environment on purpose, you must serialize the checkpoint with updated environmental metadata, or disable strict environment drift validation if utilizing custom adapters that handle the migration mapping.

---

## LangGraph Integration Pitfalls

### Problem
LangGraph state transitions do not restore properly, or keys in the restored checkpoint are empty.

### Cause
LangGraph expects specific fields inside checkpoint tuples (`checkpoint`, `metadata`, `parent_config`, `pending_writes`). If these keys are not nested under namespaced ASO extension fields, the adapter cannot reconstruct the exact type representations expected by LangGraph.

### Resolution
1. **Namespaced Keys:** Make sure you are using `ASOLangGraphSaver` directly as the LangGraph checkpoint saver. It writes metadata, node mapping, channel versions, and pending writes under the `extensions["langgraph_*"]` namespaces.
2. **Missing Thread ID:** LangGraph requires `thread_id` to route checkpoints. Ensure that the config passed to `.put()` or `.get_tuple()` contains a valid `thread_id` within the `configurable` key.
