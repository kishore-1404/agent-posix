import hashlib
import os
import subprocess
import sys
from pathlib import Path

from agentposix.exceptions import HostDriftError
from agentposix.models.environment import EnvironmentSnapshot


def _current_cwd() -> str:
    return os.getcwd()


def _current_python_version() -> str:
    return sys.version.split()[0]


def _current_platform() -> str:
    return sys.platform


def _current_env_value(name: str) -> str:
    return os.environ.get(name, "")


def _current_file_checksum(path: str) -> str:
    content = Path(path).read_bytes()
    return hashlib.sha256(content).hexdigest()


def _current_git_commit_hash(cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def capture_environment_snapshot(snapshot: EnvironmentSnapshot) -> EnvironmentSnapshot:
    captured = snapshot.model_copy(deep=True)
    captured.cwd = _current_cwd()
    captured.python_version = _current_python_version()
    captured.platform = _current_platform()
    captured.env_vars = {
        name: _current_env_value(name) for name in snapshot.env_vars
    }
    captured.file_checksums = {
        path: _current_file_checksum(path) for path in snapshot.file_checksums
    }
    captured.git_commit_hash = _current_git_commit_hash(captured.cwd)
    return captured


def validate_environment_snapshot(snapshot: EnvironmentSnapshot) -> list[str]:
    """
    Fatal drift:
    - current working directory mismatch
    - Python version mismatch
    - platform mismatch
    - tracked file checksum mismatch or unreadable tracked file

    Advisory drift:
    - tracked environment variable value mismatch
    - git commit hash mismatch
    """
    fatal_mismatches: list[str] = []
    advisories: list[str] = []

    current_cwd = _current_cwd()
    current_python_version = _current_python_version()
    current_platform = _current_platform()

    if snapshot.cwd != current_cwd:
        fatal_mismatches.append(
            f"cwd changed: expected {snapshot.cwd}, got {current_cwd}"
        )
    if snapshot.python_version != current_python_version:
        fatal_mismatches.append(
            "python_version changed: "
            f"expected {snapshot.python_version}, got {current_python_version}"
        )
    if snapshot.platform != current_platform:
        fatal_mismatches.append(
            f"platform changed: expected {snapshot.platform}, got {current_platform}"
        )

    for path, expected_checksum in snapshot.file_checksums.items():
        try:
            current_checksum = _current_file_checksum(path)
        except OSError as exc:
            fatal_mismatches.append(
                f"tracked file unavailable: {path} ({exc.__class__.__name__}: {exc})"
            )
            continue
        if expected_checksum != current_checksum:
            fatal_mismatches.append(
                f"tracked file checksum changed: {path}"
            )

    for name, expected_value in snapshot.env_vars.items():
        current_value = _current_env_value(name)
        if expected_value != current_value:
            advisories.append(
                f"environment variable changed: {name}"
            )

    if snapshot.git_commit_hash:
        current_git_commit_hash = _current_git_commit_hash(current_cwd)
        if current_git_commit_hash and current_git_commit_hash != snapshot.git_commit_hash:
            advisories.append("git commit hash changed")

    if fatal_mismatches:
        raise HostDriftError(
            "Host environment drift detected for resume: "
            + "; ".join(fatal_mismatches)
        )

    return advisories
