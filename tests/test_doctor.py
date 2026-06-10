import json

from windows_screen_agent.doctor import check_ollama_service, collect_diagnostics


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_check_ollama_service_reports_installed_model():
    calls = []

    def fake_opener(request, timeout):
        calls.append((request.full_url, timeout))
        return FakeHTTPResponse({"models": [{"name": "qwen2.5vl:7b"}]})

    ok, detail = check_ollama_service(
        "http://localhost:11434",
        "qwen2.5vl:7b",
        opener=fake_opener,
    )

    assert ok is True
    assert detail == "qwen2.5vl:7b available at http://localhost:11434"
    assert calls == [("http://localhost:11434/api/tags", 2.0)]


def test_check_ollama_service_warns_when_model_is_missing():
    def fake_opener(request, timeout):
        return FakeHTTPResponse({"models": [{"name": "gemma3:4b"}]})

    ok, detail = check_ollama_service(
        "http://localhost:11434",
        "qwen2.5vl:7b",
        opener=fake_opener,
    )

    assert ok is False
    assert "ollama pull qwen2.5vl:7b" in detail


def test_collect_diagnostics_includes_ollama_for_offline_backend(tmp_path):
    def fake_opener(request, timeout):
        return FakeHTTPResponse({"models": [{"name": "qwen2.5vl:7b"}]})

    diagnostics = collect_diagnostics(
        runtime_dir=tmp_path,
        planner_backend="ollama",
        codex_bin="codex",
        openai_api_key=None,
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen2.5vl:7b",
        opener=fake_opener,
    )

    assert any(item.name == "Ollama" and item.ok for item in diagnostics)
