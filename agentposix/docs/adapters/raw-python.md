# Raw Python Adapter

The raw Python adapter provides `checkpoint_boundary`, a decorator for wrapping
functions that perform side effects. It records a side-effect entry, freezes the
ASO after successful execution, and prevents duplicate execution when the same
call is reached again after resume.

## Idempotency Key

The idempotency key is a SHA-256 hash of:

- the ASO session id
- the declared tool name
- positional arguments
- keyword arguments

Arguments are converted into a deterministic JSON-safe payload before hashing.
Primitive JSON values are preserved. Lists, tuples, sets, and dictionaries are
normalized recursively. Unsupported objects are represented with `repr()`.

This means `tool(1)` and `tool(2)` produce different idempotency keys, and
`tool(1, mode="safe")` differs from `tool(1, mode="fast")`.

## Replay Behavior

When the decorator finds an existing side-effect entry with the same idempotency
key, it does not call the wrapped function again.

If the original result was JSON-serializable, the stored result is decoded and
returned to the caller. This supports simple return values such as dictionaries,
lists, strings, numbers, booleans, and `None`.

If the original result was not JSON-serializable, the decorator stores a `repr()`
summary for observability. On replay, it raises `SideEffectReplayError` instead
of re-running the side effect or pretending it can reconstruct the original
object.

## Assumptions and Limits

- The wrapped function must perform the side effect only after it is safe for the
  decorator to record completion.
- The embedding application is responsible for making the actual external system
  idempotent when possible, for example by passing the same idempotency key to a
  payment or provisioning API.
- Replay returns JSON-normalized values, so tuples become lists and non-string
  dictionary keys become strings.
- Non-JSON result replay is intentionally conservative and raises instead of
  executing the side effect twice.
- The decorator records completion after the wrapped function returns. If the
  process exits after the external side effect succeeds but before freeze
  completes, the application may need an external reconciliation mechanism.
