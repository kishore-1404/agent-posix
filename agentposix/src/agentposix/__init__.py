from importlib import import_module

from .adapters.raw_python.decorator import checkpoint_boundary
from .core.freeze import freeze
from .core.resume import resume
from .models.aso import AgentStateObject
from .storage.filesystem import FilesystemBackend

__all__ = [
    "freeze",
    "resume",
    "checkpoint_boundary",
    "ASOLangGraphSaver",
    "AgentStateObject",
    "FilesystemBackend",
]


def __getattr__(name: str):
    if name == "ASOLangGraphSaver":
        try:
            adapter_module = import_module("agentposix.adapters.langgraph.adapter")
        except ModuleNotFoundError as exc:
            raise ImportError(
                "ASOLangGraphSaver requires the optional 'adapters' dependencies. "
                "Install agentposix with the 'adapters' extra to enable LangGraph integration."
            ) from exc
        return adapter_module.ASOLangGraphSaver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
