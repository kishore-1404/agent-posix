#!/usr/bin/env bash
set -euo pipefail

# Script to run a smoke test for Agent POSIX in a clean virtual environment.
# Run this from the `agentposix/` package root directory.

echo "=========================================================="
echo "Starting Agent POSIX local smoke test..."
echo "=========================================================="

# 1. Clean previous build files
echo "Cleaning old build files..."
rm -rf dist build *.egg-info

# 2. Build the package distribution wheel
echo "Building the wheel package..."
python3 -m build --no-isolation

# 3. Create a temporary virtual environment
echo "Creating clean temporary virtual environment..."
TEMP_VENV=$(mktemp -d -t agentposix_smoke_venv_XXXXXX)
python3 -m venv "$TEMP_VENV"

# Activate temporary venv
# shellcheck disable=SC1091
source "$TEMP_VENV/bin/activate"

# 4. Install the built wheel
echo "Installing the wheel package..."
WHEEL_PATH=$(find dist/ -name "*.whl" | head -n 1)
if [ -z "$WHEEL_PATH" ]; then
    echo "ERROR: Built wheel not found!"
    exit 1
fi
pip install "$WHEEL_PATH"

# 5. Verify the CLI execution
echo "Verifying CLI help command..."
agentposix --help > /dev/null
echo "CLI check succeeded."

# 6. Execute basic python quickstart to verify imports & freeze/resume
echo "Executing quickstart python validation script..."
python3 -c "
import tempfile
from agentposix import AgentStateObject, FilesystemBackend, freeze, resume
from agentposix.models.metadata import IdentityBlock, ModelConfig, FreezeMetadata
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.enums import ASOStatus, ParadigmEnum, FreezeTriggerReasonEnum

# Create minimal valid ASO
aso = AgentStateObject(
    identity=IdentityBlock(aso_id='aso-smoke-1', session_id='smoke-1'),
    status=ASOStatus.INITIALIZING,
    created_at='2026-05-25T04:00:00Z',
    model_config_block=ModelConfig(provider='test', model_id='test-model'),
    conversation=ConversationHistory(),
    execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
    side_effects=SideEffectRegistry(),
    environment=EnvironmentSnapshot(cwd='/tmp', python_version='3.10.0', platform='linux'),
    metadata=FreezeMetadata(
        framework_name='raw',
        framework_version='1.0.0',
        trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL
    )
)

with tempfile.TemporaryDirectory() as tmpdir:
    backend = FilesystemBackend(tmpdir)
    
    # 1. Freeze ASO
    frozen_aso = freeze(aso, backend, summary='Smoke test check')
    assert frozen_aso.status == ASOStatus.CHECKPOINTED
    assert frozen_aso.checksum is not None
    print('Python ASO freeze successful.')
    
    # 2. Resume ASO
    resumed_aso = resume('smoke-1', backend)
    assert resumed_aso.status == ASOStatus.RESUMING
    print('Python ASO resume successful.')
"

# Deactivate venv and cleanup
deactivate
rm -rf "$TEMP_VENV"

echo "=========================================================="
echo "SUCCESS: Agent POSIX local smoke test passed!"
echo "=========================================================="
