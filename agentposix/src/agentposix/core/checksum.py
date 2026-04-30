import hashlib
import json

from src.agentposix.exceptions import ChecksumMismatchError
from src.agentposix.models.aso import AgentStateObject


def compute_checksum(aso: AgentStateObject) -> str:
    """Computes SHA256 of the ASO ignoring the checksum field itself."""
    data = aso.model_dump(mode="json")
    data["checksum"] = ""
    encoded = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_checksum(aso: AgentStateObject) -> bool:
    """Raises ChecksumMismatchError if the checksum is invalid."""
    expected = aso.checksum
    actual = compute_checksum(aso)
    if expected and expected != actual:
        raise ChecksumMismatchError(
            f"ASO checksum verification failed for session {aso.identity.session_id}. "
            f"Expected {expected}, got {actual}. The ASO file may be corrupted."
        )
    return True
