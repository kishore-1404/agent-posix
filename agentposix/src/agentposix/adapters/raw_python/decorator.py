import hashlib
import json
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from agentposix.core.freeze import freeze
from agentposix.exceptions import SideEffectReplayError
from agentposix.models.aso import AgentStateObject
from agentposix.models.side_effect import SideEffectEntry
from agentposix.storage.base import StorageBackend


_RESULT_FORMAT_JSON = "json"
_RESULT_FORMAT_REPR = "repr"


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted((_to_json_safe(item) for item in value), key=repr)
    if isinstance(value, dict):
        return {
            str(key): _to_json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: repr(pair[0]))
        }
    return repr(value)


def _build_call_payload(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "args": _to_json_safe(list(args)),
        "kwargs": _to_json_safe(kwargs),
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _result_summary(result: Any) -> str:
    try:
        json_safe_result = json.loads(json.dumps(result))
    except TypeError:
        return _canonical_json(
            {
                "format": _RESULT_FORMAT_REPR,
                "value": repr(result),
            }
        )
    return _canonical_json(
        {
            "format": _RESULT_FORMAT_JSON,
            "value": json_safe_result,
        }
    )


def _load_replay_result(effect: SideEffectEntry) -> Any:
    if not effect.result_summary:
        return None

    payload = json.loads(effect.result_summary)
    if not isinstance(payload, dict) or "format" not in payload:
        return payload

    if payload["format"] == _RESULT_FORMAT_JSON:
        return payload.get("value")

    raise SideEffectReplayError(
        f"Side-effect {effect.tool_name} already completed with idempotency key "
        f"{effect.idempotency_key}, but its result is not JSON-replayable. "
        "The side-effect was not re-executed."
    )


def checkpoint_boundary(aso: AgentStateObject, storage: StorageBackend, tool_name: str):
    """Instruments a python function to enforce idempotency and trigger checkpoints."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            call_payload = _build_call_payload(args, kwargs)
            key_payload = _canonical_json(call_payload)
            key_string = f"{aso.identity.session_id}:{tool_name}:{key_payload}"
            idemp_key = hashlib.sha256(key_string.encode()).hexdigest()

            for effect in aso.side_effects.entries:
                if effect.idempotency_key == idemp_key and effect.result_summary:
                    return _load_replay_result(effect)

            result = func(*args, **kwargs)

            entry = SideEffectEntry(
                idempotency_key=idemp_key,
                tool_name=tool_name,
                tool_args=call_payload,
                executed_at=datetime.now(timezone.utc).isoformat(),
                result_summary=_result_summary(result),
            )
            aso.side_effects.entries.append(entry)
            freeze(aso, storage, summary=f"Completed tool {tool_name}")
            return result

        return wrapper

    return decorator
