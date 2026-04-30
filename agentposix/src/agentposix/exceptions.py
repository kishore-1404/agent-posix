class AgentPOSIXError(Exception):
    """Base exception for all Agent POSIX errors."""

    pass


class ChecksumMismatchError(AgentPOSIXError):
    """Raised when an ASO file checksum fails validation."""

    pass


class HostDriftError(AgentPOSIXError):
    """Raised when environment file checksums mismatch on resume."""

    pass


class InvalidASOError(AgentPOSIXError):
    """Raised when an ASO fails schema validation."""

    pass


class StateTransitionError(AgentPOSIXError):
    """Raised for invalid lifecycle state transitions."""

    pass
