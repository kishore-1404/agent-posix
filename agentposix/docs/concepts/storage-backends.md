# Storage Backend Selection

Agent POSIX stores Agent State Objects (ASOs) through backend implementations. The
backend choice affects operational durability, concurrency behavior, and deployment
complexity.

## Filesystem Backend

Use `FilesystemBackend` when:

- You need the simplest local development or single-process deployment path.
- Checkpoints should be easy to inspect, copy, diff, or back up as JSON files.
- A single worker process owns writes for a given session.
- The storage directory is on a local POSIX filesystem with reliable rename
  semantics.

Operational behavior:

- Each checkpoint is written to a temporary file and then atomically replaced into
  the target session file.
- File contents are flushed and fsynced before replacement.
- The parent directory is fsynced after replacement when the platform supports it.
- Writers are serialized per session only inside the current Python process.

Limits:

- There is no cross-process or distributed lock. Two processes writing the same
  session can race, and last writer wins.
- Durability depends on the host filesystem, mount options, and OS behavior.
- Network filesystems can weaken atomic rename or fsync assumptions.
- Corrupted JSON, unreadable files, malformed payloads, and checksum mismatches
  are surfaced as deterministic exceptions, but recovery is operator-driven.

Use this backend for prototypes, local tools, tests, and single-process agents.
Avoid it for multi-worker production services unless an external lock or ownership
model guarantees one writer per session.

## SQLite Backend

Use `AsyncSqliteBackend` when:

- You need a single local database file instead of one JSON file per session.
- Multiple async tasks in one service need a shared checkpoint store.
- Ordered session listing and update/delete operations should be backed by a
  transactional database.
- The deployment can install the `storage` extra and use async storage calls.

Operational behavior:

- Checkpoints are stored as JSON payloads in a `checkpoints` table keyed by
  `session_id`.
- Writes use SQLite upsert semantics.
- The backend initializes the database on demand and enables WAL mode.
- Missing sessions, malformed payloads, invalid JSON, and checksum mismatches
  fail with stable, actionable exceptions.

Limits:

- SQLite is still a single-node local persistence mechanism, not a distributed
  checkpoint service.
- High write concurrency can require application-level retry and timeout policy.
- Database file placement matters; avoid unreliable network filesystems.
- The backend does not perform automatic repair of corrupted payloads.

Use this backend for local services, desktop/server deployments, and async
applications that need stronger transactional behavior than JSON files. Avoid it
when checkpoints need to be shared across hosts without a separate replication or
coordination layer.

## Failure Handling

Both backends validate persisted ASOs when reading:

- Missing session: `FileNotFoundError`.
- Partial or invalid JSON: `InvalidASOError`.
- Unexpected ASO shape: `InvalidASOError`.
- Checksum mismatch during resume or explicit verification:
  `ChecksumMismatchError`.

Recovery is intentionally conservative. Agent POSIX reports deterministic failures
and leaves repair decisions to the operator or embedding application. Recommended
operator actions are:

- Restore the last known-good checkpoint from backup.
- Inspect the corrupted payload before deletion.
- Delete only the affected session checkpoint if the application can safely
  restart that session.
- Treat checksum mismatch as evidence of tampering, partial writes outside the
  backend contract, or manual file/database edits.

## Selection Summary

Choose `FilesystemBackend` for simple, inspectable, single-process checkpointing.
Choose `AsyncSqliteBackend` for local transactional storage in async applications.
For multi-host or high-concurrency production systems, build a dedicated backend
with explicit locking, transactional guarantees, and operational monitoring.
