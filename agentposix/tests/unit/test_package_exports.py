import pytest

import agentposix


def test_langgraph_export_is_lazy():
    assert "ASOLangGraphSaver" in agentposix.__all__
    assert "ASOLangGraphSaver" not in agentposix.__dict__

    saver = agentposix.ASOLangGraphSaver

    assert saver.__name__ == "ASOLangGraphSaver"


def test_langgraph_export_reports_missing_optional_dependency(monkeypatch):
    def fail_import(name: str):
        if name == "agentposix.adapters.langgraph.adapter":
            raise ModuleNotFoundError("langgraph")
        raise AssertionError(f"unexpected import target: {name}")

    monkeypatch.setattr(agentposix, "import_module", fail_import)

    with pytest.raises(ImportError, match="optional 'adapters' dependencies"):
        agentposix.__getattr__("ASOLangGraphSaver")
