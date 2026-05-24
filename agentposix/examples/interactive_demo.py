#!/usr/bin/env python3
import os
import shutil

from agentposix import AgentStateObject, FilesystemBackend, checkpoint_boundary, resume
from agentposix.core.checksum import compute_checksum
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry

DEMO_DIR = ".agentposix_demo"
SESSION_ID = "session-demo"


def print_banner(text: str):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def cleanup():
    if os.path.exists(DEMO_DIR):
        shutil.rmtree(DEMO_DIR)


cleanup()

# Set up storage backend
storage = FilesystemBackend(DEMO_DIR)

print_banner("AGENT POSIX INTERACTIVE DEMO")
print("This script demonstrates freezing, resuming, and replaying side effects.")
print(f"Checkpoints will be saved in the local directory: '{DEMO_DIR}'")

# Initialize the Agent State Object first so we can pass it to the decorators
print("\n1. Initializing AgentStateObject...")
aso = AgentStateObject(
    identity=IdentityBlock(aso_id="aso-demo", session_id=SESSION_ID),
    status=ASOStatus.INITIALIZING,
    created_at="2026-05-25T00:00:00Z",
    model_config_block=ModelConfig(provider="openai", model_id="gpt-4o"),
    conversation=ConversationHistory(),
    execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.REACT_LOOP, current_node_id="start"),
    side_effects=SideEffectRegistry(),
    environment=EnvironmentSnapshot(cwd=".", python_version="3.10.0", platform="linux"),
    metadata=FreezeMetadata(
        framework_name="raw",
        framework_version="1.0.0",
        trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
    ),
)

# 2. Define side-effects with the decorator
llm_call_count = 0
db_write_count = 0


@checkpoint_boundary(aso, storage, "mock_llm_call")
def mock_llm_call(prompt: str):
    global llm_call_count
    llm_call_count += 1
    print(f"--> [REAL API CALL] Calling LLM (Prompt: '{prompt}')...")
    return f"LLM response to '{prompt}'"


@checkpoint_boundary(aso, storage, "mock_db_write")
def mock_db_write(key: str, value: str):
    global db_write_count
    db_write_count += 1
    print(f"--> [REAL DB WRITE] Writing '{key}': '{value}' to Database...")
    return f"DB_WRITE_OK: {key}={value}"


# First Run (Executes the real function and saves it)
print("\n--- FIRST RUN ---")

# Transition to RUNNING before starting agent execution steps
aso.status = ASOStatus.RUNNING

print("\nExecuting Step 1 (Calling LLM)...")
aso.execution_pointer.current_node_id = "step_1"
response_1 = mock_llm_call("Translate hello to French")
print(f"Step 1 Result: {response_1}")

# Note: Calling the decorated function mock_llm_call above automatically
# triggered a freeze() at the end, transitioning the status to CHECKPOINTED.

# Print the inspect command instructions
print("\n" + "-" * 50)
print("TIP: You can now inspect this checkpoint using the CLI:")
print(f"  agentposix inspect {SESSION_ID} --path {DEMO_DIR}")
print("-" * 50)

# Transition to RUNNING again to perform the next step of work
aso.status = ASOStatus.RUNNING

print("\nExecuting Step 2 (Calling LLM)...")
aso.execution_pointer.current_node_id = "step_2"
response_2 = mock_llm_call("Translate world to French")
print(f"Step 2 Result: {response_2}")

print("\n*** SIMULATING CRASH BEFORE DB WRITE COMPLETES ***")
print("Agent process terminated abruptly. State in-memory is lost.")
print("But the Step 1 checkpoint remains safely in storage.")

# Reset in-memory counts to simulate a brand-new process execution
llm_call_count = 0
db_write_count = 0

print_banner("RESUMING AGENT RUN")
print("New process started. Resuming session state...")

# Load from storage
resumed = resume(SESSION_ID, storage)
print(f"Loaded session status: {resumed.status}")
print(f"Last successful node pointer: {resumed.execution_pointer.current_node_id}")

# Update the original ASO object in-place so that the decorators
# (which closed over the original 'aso' reference) see the resumed state
aso.status = resumed.status
aso.side_effects.entries = resumed.side_effects.entries
aso.execution_pointer = resumed.execution_pointer

print("\nRe-executing the Agent code flow...")

# Step 1 is re-executed in code, but because it's wrapped in @checkpoint_boundary,
# the decorator intercepts it, skips the actual function execution, and returns the cached result!
print("\nRe-running Step 1 (should skip LLM call and replay)...")
response_1_replay = mock_llm_call("Translate hello to French")
print(f"Step 1 Replay Result (Cached): {response_1_replay}")
print(f"Total real LLM calls executed during this run: {llm_call_count} (Expected: 0)")

# Since we want to run new steps, we transition the agent back to RUNNING
aso.status = ASOStatus.RUNNING

# Now we execute Step 2 (which crashed previously, so it wasn't checkpointed)
print("\nRe-running Step 2 (will execute LLM and DB write)...")
response_2_run = mock_llm_call("Translate world to French")
print(f"Step 2 LLM Result: {response_2_run}")

# Transition to RUNNING for the next DB write step
aso.status = ASOStatus.RUNNING

db_result = mock_db_write("french_translation", "Bonjour Le Monde")
print(f"Step 2 DB Result: {db_result}")

# Mark ASO complete and write the final TERMINATED state directly to storage
print("\nSaving final terminated session state...")
aso.status = ASOStatus.TERMINATED
aso.execution_pointer.current_node_id = "done"
aso.checksum = compute_checksum(aso)
storage.write_aso(aso)

print("\n5. Verification Statistics:")
print(f"  Real LLM Calls executed in resume phase: {llm_call_count}")
print(f"  Real DB Writes executed in resume phase: {db_write_count}")
print("\nDemo completed successfully. Cleaning up demo folder...")
cleanup()
