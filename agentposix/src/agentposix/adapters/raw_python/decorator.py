import hashlib
import json
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from agentposix.core.freeze import freeze
from agentposix.models.aso import AgentStateObject
from agentposix.models.side_effect import SideEffectEntry
from agentposix.storage.base import StorageBackend


def checkpoint_boundary(aso: AgentStateObject, storage: StorageBackend, tool_name: str):
    """Instruments a python function to enforce idempotency and trigger checkpoints."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Deterministic Idempotency Key
            sorted_kwargs = json.dumps(kwargs, sort_keys=True)
            key_string = f"{aso.identity.session_id}:{tool_name}:{sorted_kwargs}"
            idemp_key = hashlib.sha256(key_string.encode()).hexdigest()

            # Check cache to prevent duplicate side-effect
            for effect in aso.side_effects.entries:
                if effect.idempotency_key == idemp_key and effect.result_summary:
                    return json.loads(effect.result_summary)

            # Execute real tool
            result = func(*args, **kwargs)

            # Record and freeze
            entry = SideEffectEntry(
                idempotency_key=idemp_key,
                tool_name=tool_name,
                tool_args=kwargs,
                executed_at=datetime.now(timezone.utc).isoformat(),
                result_summary=json.dumps(result),
            )
            aso.side_effects.entries.append(entry)
            freeze(aso, storage, summary=f"Completed tool {tool_name}")
            return result

        return wrapper

    return decorator
