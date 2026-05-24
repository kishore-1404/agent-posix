# CLI Reference

The `agentposix` CLI tool allows operators and developers to inspect, resume, and freeze Agent State Objects directly from the command line.

When the package is installed, the console script `agentposix` is registered and available on your PATH.

---

## Global Options

- `--help`: Show the help message and exit.

---

## Commands

### `inspect`

Inspect details of a stored Agent State Object (ASO) without mutating it.

#### Usage

```bash
agentposix inspect [OPTIONS] SESSION_ID
```

#### Arguments
- `SESSION_ID`: The unique session identifier of the ASO to inspect.

#### Options
- `--path PATH`: The base directory path containing the checkpoints (default: `.agentposix`).

#### Example Output

```text
ASO: session-123
├── Status: CHECKPOINTED
├── Node: generate_summary
└── Side Effects
    ├── call_llm [5f4d8a12]
    └── write_log [a2e7c410]
```

---

### `resume`

Restore an Agent State Object, validating its integrity and reporting any environment drift.

#### Usage

```bash
agentposix resume [OPTIONS] SESSION_ID
```

#### Arguments
- `SESSION_ID`: The unique session identifier of the ASO to resume.

#### Options
- `--path PATH`: The base directory path containing the checkpoints (default: `.agentposix`).

#### Behavior
- Connects to the filesystem storage at the specified path.
- Checks if the session exists and reads the payload.
- Verifies the SHA-256 checksum.
- Compares host drift parameters (fatal drift throws an error; advisory drift is recorded).
- Transitions the state of the ASO to `RESUMING`.
- Prints the session hierarchy, timestamps, and any advisory messages.

#### Example Output

```text
Resumed ASO: session-123
├── Status: RESUMING
├── Frozen At: 2026-05-25T04:00:00Z
├── Resumed At: 2026-05-25T04:20:00Z
├── Checksum: valid
└── Advisories
    └── Tracked environment variable 'API_ENDPOINT' changed from 'http://live' to 'http://staging'
```

---

### `freeze`

Create a manual checkpoint from a local ASO JSON file. This command is primarily designed for debugging and diagnostic purposes, allowing operators to manually save or patch an agent's lifecycle state.

#### Usage

```bash
agentposix freeze [OPTIONS]
```

#### Options
- `--input PATH` (Required): Path to a local JSON file containing the complete `AgentStateObject` payload.
- `--path PATH`: The base directory path where the checkpoint file will be persisted (default: `.agentposix`).
- `--summary TEXT`: Optional checkpoint summary description override.

#### Behavior
- Reads and parses the JSON file at `--input`.
- Validates the JSON against the public `AgentStateObject` Pydantic model.
- Invokes the core `freeze()` lifecycle protocol, transitioning the ASO status to `CHECKPOINTED` and computing the SHA-256 checksum.
- Durably persists the ASO JSON payload using the `FilesystemBackend` at the target path.
- Prints details of the successfully frozen checkpoint.

#### Example Output

```text
Frozen ASO: session-123
├── Status: CHECKPOINTED
├── Frozen At: 2026-05-25T04:20:00Z
├── Checksum: 8a6e74b3...c10d21e8
└── Summary: Manual state patch for debugging session recovery
```
